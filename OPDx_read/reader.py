#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May  5 20:41:38 2022

@author: usera
"""

import numpy as np
import struct
import ctypes as ct
import matplotlib.pylab as plt

MAGIC=b'VCA DATA\x01\x00\x00U' #This sequence is the beginning of each file
MAGIC_SIZE=12
DEBUG=False

class DektakItem:
    
    def __init__(self, name=None, data_type=None, data=None):
        self.name=name
        self.data_type=data_type
        self.data=data


class DektakLoad:
    data_types=dict({'DEKTAK_MATRIX'       : 0x00, # Too lazy to assign an actual type id?
                    'DEKTAK_BOOLEAN'      : 0x01, # Takes value 0 and 1 */
                    'DEKTAK_SINT32'       : 0x06,
                    'DEKTAK_UINT32'       : 0x07,
                    'DEKTAK_SINT64'       : 0x0a,
                    'DEKTAK_UINT64'       : 0x0b,
                    'DEKTAK_FLOAT'        : 0x0c, # Single precision float */
                    'DEKTAK_DOUBLE'       : 0x0d, # Double precision float */
                    'DEKTAK_TYPE_ID'      : 0x0e, # Compound type holding some kind of type id */
                    'DEKTAK_STRING'       : 0x12, # Free-form string value */
                    'DEKTAK_QUANTITY'     : 0x13, # Value with units (compound type) */
                    'DEKTAK_TIME_STAMP'   : 0x15, # Datetime (string/9-byte binary) */
                    'DEKTAK_UNITS'        : 0x18, # Units (compound type) */
                    'DEKTAK_DOUBLE_ARRAY' : 0x40, # Raw data array, in XML Base64-encoded */
                    'DEKTAK_STRING_LIST'  : 0x42, # List of Str */
                    'DEKTAK_ANON_MATRIX'  : 0x45, # Like DEKTAK_MATRIX, but with no name. */
                    'DEKTAK_RAW_DATA'     : 0x46, # Parent/wrapper tag of raw data */
                    'DEKTAK_RAW_DATA_2D'  : 0x47, # Parent/wrapper tag of raw data */
                    'DEKTAK_POS_RAW_DATA' : 0x7c, # Base64-encoded positions, not sure how
                                                  # it differs from 64 */
                    'DEKTAK_CONTAINER'    : 0x7d, # General nested data structure */
                    'DEKTAK_TERMINATOR'   : 0x7f # Always the last item.
                                                   #Usually a couple of 0xff bytes inside. */
                                                   })
    
    
    def __init__(self,filename):
        self.filename=filename
        self.items=[]
        self.reading_2D=False
        self.reading_1D=False
        self.terminator=False
        self.current_count=0
        with open(self.filename, 'rb') as f:
            f.seek(0,2)
            self.eof=f.tell()
            f.seek(0,0)
        self.read()
    
    def read_varlen(self, f):
        length=int.from_bytes(f.read(1),"big")
        if length==1:
            return int.from_bytes(f.read(1),"big")
        elif length==2:
            return int.from_bytes(f.read(2),"big")
        elif length==4:
            return int.from_bytes(f.read(4),"big")
        else:
            print('The varlength format was not respected')
            return -1
    
    def read_structured(self, item, f):
        self.read_varlen(f)
        item.data=dict()
        item.data['items']=[]
        last_item=self.read_item(f)
        while(not self.terminator and last_item is not None):
            item.data['items'].append(last_item)
            last_item=self.read_item(f)
        self.terminator=False
        return item
    
    def read_name(self, f):
        data=f.read(4)
        length=struct.unpack('i',data)[0]
        return f.read(length).decode()
            

    
    def read_item(self, f):
        if f.tell()==self.eof:
            return None
        item=DektakItem()
        item.name=self.read_name(f)
        datatype=f.read(1)
        if DEBUG:
            print('the datatype of this item is: {:}'.format(datatype))
        item.data_type=int.from_bytes(datatype, "big")
        if item.data_type==DektakLoad.data_types['DEKTAK_BOOLEAN']:
            item.data=f.read(1)
        elif item.data_type==DektakLoad.data_types['DEKTAK_SINT32']:
            item.data=struct.unpack('I',f.read(4))[0]
        elif item.data_type==DektakLoad.data_types['DEKTAK_UINT32']:
            item.data=struct.unpack('I',f.read(4))[0]
        elif item.data_type==DektakLoad.data_types['DEKTAK_SINT64']:
            data=f.read(8)
            item.data=struct.unpack('Q',data)[0]
        elif item.data_type==DektakLoad.data_types['DEKTAK_UINT64']:
            item.data=struct.unpack('Q',f.read(8))[0]
            if item.name=='SamplesToLog':
                self.current_count=item.data
        elif item.data_type==DektakLoad.data_types['DEKTAK_FLOAT']:
            item.data=struct.unpack('f',f.read(4))[0]
        elif item.data_type==DektakLoad.data_types['DEKTAK_DOUBLE']:
            item.data=struct.unpack('d',f.read(8))[0]
        elif item.data_type==DektakLoad.data_types['DEKTAK_TIME_STAMP']:
            item.data=f.read(9)
        elif item.data_type==DektakLoad.data_types['DEKTAK_STRING']:
            length=self.read_varlen(f)
            item.data=f.read(length).decode()
        elif item.data_type==DektakLoad.data_types['DEKTAK_STRING_LIST']:
            item.data=dict()
            item.data['datatype']=self.read_name(f)
            length=self.read_varlen(f)
            if length>0:
                item.data['strings']=[self.read_name(f)]
            else:
                item.data['strings']=[]
        elif item.data_type==DektakLoad.data_types['DEKTAK_DOUBLE_ARRAY']:
            
            item.data=dict()
            item.data['datatype']=self.read_name(f)
            #First try to skip 8, then 10
            ini=f.tell()
            f.read(8+self.current_count*8)
            data=f.read(4)
            length=struct.unpack('i',data)[0]
            try:
                f.read(length).decode()
                f.seek(ini)
                f.read(8)
                item.data['data']=np.frombuffer(f.read(self.current_count*8),
                     dtype=float)
            except UnicodeDecodeError:
                f.seek(ini)
                f.read(10)
                item.data['data']=np.frombuffer(f.read(self.current_count*8),
                     dtype=float)
        elif item.data_type==DektakLoad.data_types['DEKTAK_UNITS']:
            item.data=dict()
            item.data['length']=self.read_varlen(f)
            item.data['name']=self.read_name(f)
            item.data['symbol']=self.read_name(f)
            item.data['value']=struct.unpack('d',f.read(8))[0]
            f.read(12)
        elif item.data_type==DektakLoad.data_types['DEKTAK_QUANTITY']:
            item.data=dict()
            item.data['length']=self.read_varlen(f)
            item.data['value']=struct.unpack('d',f.read(8))[0]
            item.data['name']=self.read_name(f)
            item.data['symbol']=self.read_name(f)
            if len(item.data['name'])>0:
                f.read(20)
            else:
                f.read(16)
        elif item.data_type==DektakLoad.data_types['DEKTAK_TERMINATOR']:
            self.reading_2D=False
            self.reading_1D=False
            self.terminator=True
            item.data=f.read(2)
        elif item.data_type==DektakLoad.data_types['DEKTAK_TYPE_ID']:
            item.data=dict()
            item.data['name']=self.read_name(f)
            length=self.read_varlen(f)
            item.data['value']=int.from_bytes(f.read(length), 'little')
        elif item.data_type==DektakLoad.data_types['DEKTAK_POS_RAW_DATA']:
            if self.reading_2D:
                item.data=dict()
                item.data['name']=self.read_name(f)
                item.data['length']=self.read_varlen(f)
                item.data['value_x']=struct.unpack('d',f.read(8))[0]
                item.data['unit_name_x']=self.read_name(f)
                item.data['unit_symbol_x']=self.read_name(f)
                item.data['divisor_x']=struct.unpack('d',f.read(8))[0]
                f.read(12)
                item.data['value_y']=struct.unpack('d',f.read(8))[0]
                item.data['unit_name_y']=self.read_name(f)
                item.data['unit_symbol_y']=self.read_name(f)
                item.data['divisor_y']=struct.unpack('d',f.read(8))[0]
                f.read(12)
            elif self.reading_1D:
                item.data=dict()
                item.data['name']=self.read_name(f)
                item.data['length']=self.read_varlen(f)
                item.data['unit_name']=self.read_name(f)
                item.data['unit_symbol']=self.read_name(f)
                item.data['divisor']=struct.unpack('d',f.read(8))[0]
                f.read(12)
                item.data['count']=struct.unpack('Q',f.read(8))[0]
                self.current_count=item.data['count']
                N=item.data['length']
                N=item.data['count']
                item.data['data']=np.frombuffer(f.read(N*8), dtype=float)
                
        elif item.data_type==DektakLoad.data_types['DEKTAK_ANON_MATRIX']:
            item.data=dict()
            item.data['name']=self.read_name(f)
            item.data['size']=self.read_varlen(f)
            item.data['yres']=struct.unpack('I',f.read(4))[0]
            item.data['xres']=struct.unpack('I',f.read(4))[0]
            if item.data['size']<2*ct.sizeof(ct.c_uint32):
                print('PROBLEM')
            item.data['size']-=2*ct.sizeof(ct.c_uint32)
            N=item.data['xres']*item.data['yres']
            data=f.read(4*N)
            item.data['data']=np.reshape(np.frombuffer(data,
                     dtype="float32"), (item.data['yres'],
                                    item.data['xres']))
            
            
        elif item.data_type==DektakLoad.data_types['DEKTAK_MATRIX']:
            item.data=dict()
            item.data['name']=f.read(4)
            item.data['size']=self.read_varlen(f)
            item.data['xres']=struct.unpack('I',f.read(4))[0]
            item.data['yres']=struct.unpack('I',f.read(4))[0]
            if item.data['size']<2*ct.sizeof(ct.c_uint32):
                print('PROBLEM')
            item.data['size']-=2*ct.sizeof(ct.c_uint32)
        elif item.data_type==DektakLoad.data_types['DEKTAK_CONTAINER']:
            if item.name=='1D_Data':
                self.reading_1D=True
            elif item.name=='2D_Data':
                self.reading_2D=True
            item=self.read_structured(item, f)
        elif item.data_type==DektakLoad.data_types['DEKTAK_RAW_DATA']:
            item=self.read_structured(item, f)
        elif item.data_type==DektakLoad.data_types['DEKTAK_RAW_DATA_2D']:
            item=self.read_structured(item, f)
        else:
            print('unknown data_type')
            print(f.read(100))
            print(item.data_type)
        if DEBUG:
            print('{:},{:},{:}===>>>>{:} ; {:}'.format(item.data_type,
              f.tell(), datatype, item.name, item.data))
        return item
    
    def read_until(self, f, limit='\x06\x00\x00\x00Extent'):
        string=b''
        N=len(limit)
        while(len(string)<N):
            string+=f.read(1)
        while(f.tell()!=self.eof):
            if(string.endswith(limit)):
                return string[:-N]
            else:
                string+=f.read(1)
        return None
            
        
    def read(self):
        with open(self.filename, 'rb') as f:
            while(f.tell()!=MAGIC_SIZE):
                f.read(1)
            while(len(self.items)<10):
                item=self.read_item(f)
                self.items.append(item)
    
    
    def get_data_1D(self):
        x,y,scale, divisor=None, None, None, None
        for item in self.items:
            if item is not None:
                if item.name=='1D_Data':
                    break
        subitem=None
        for k in item.data['items']:
            if k.name=='Raw':
                subitem=k
                break
        if subitem is not None:
            for k in subitem.data['items']:
                if k.name=='PositionFunction':
                    x=k.data['data']
                    divisor=k.data['divisor']
                elif k.name=='Array':
                    y=k.data['data']
                elif k.name=='DataScale':
                    scale=k.data['value']
            return x/divisor, y*scale/divisor
        else:
            return None, None
    
    
    def get_data_2D(self, plot=True):
        for item in self.items:
            if item is not None:
                if item.name=='2D_Data':
                    break
        subitem=None
        for k in item.data['items']:
            if k.name=='Raw':
                subitem=k
                break
        if subitem is not None:
            divisor=1
            for mat in subitem.data['items']:
                if mat.name=='Matrix':
                    break
            for scale in subitem.data['items']:
                if scale.name=='DataScale':
                    if scale.data['name']=='Micrometer':
                        divisor=1e6
                    break
            for dim1 in subitem.data['items']:
                if dim1.name=='Dimension1Extent':
                    break
            for dim2 in subitem.data['items']:
                if dim2.name=='Dimension2Extent':
                    break
            for subsubitem in subitem.data['items']:
                if subsubitem.name=='PositionFunction':
                    symbol_x, symbol_y=(subsubitem.data['unit_symbol_x'],
                                        subsubitem.data['unit_symbol_y'])
                    break
            if plot:
            
                plt.imshow(mat.data['data']*scale.data['value'],
                           extent=[0,dim2.data['value'],
                                   0,dim1.data['value']])
                plt.xlabel(symbol_x)
                plt.ylabel(symbol_y)
            zs=mat.data['data']*scale.data['value']/divisor
            xs=np.linspace(0, dim1.data['value'],
                           np.shape(mat.data['data'])[1])
            ys=np.linspace(0, dim2.data['value'],
                           np.shape(mat.data['data'])[0])
            return (xs, ys, zs)
        else:
            return None, None, None
    
    
    def get_metadata(self):
        for item in self.items:
            if item is not None:
                if item.name=='MetaData':
                    break
        res=dict()
        for k in item.data['items']:
            if not isinstance(k.data, dict):
                res[k.name]=k.data
            else:
                res[k.name]=dict()
                for child in k.data['items']:
                    res[k.name][child.name]=child.data
        return res