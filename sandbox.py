#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May  5 20:41:38 2022

@author: usera
"""

import numpy as np
import os
import struct
import ctypes as ct

filename='2dscan.OPDx'
MAGIC=b'VCA DATA\x01\x00\x00U'
MAGIC_SIZE=12

class DektakItem:
    
    def __init__(self, name=None, data_type=None, data=None):
        self.name=name
        self.data_type=data_type
        self.data=data
        self.flag=False

class DektakLoad:
    data_types=dict({'DEKTAK_MATRIX'       : 0x00, # Too lazy to assign an actual type id?
                    'DEKTAK_BOOLEAN'      : 0x01, # Takes value 0 and 1 */
                    'DEKTAK_SINT32'       : 0x06,
                    'DEKTAK_UINT32'       : 0x07,
                    'DEKTAK_SINT64'       : 0x0a,
                    'DEKTAK_UINT64'       : 0x0b,
                    'DEKTAK_FLOAT'       : 0x0c, # Single precision float */
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
    
    def read_varlen(self, f):
        length=int.from_bytes(f.read(1),"big")

        if length==1:
            return int.from_bytes(f.read(1),"big")
        elif length==2:
            return int.from_bytes(f.read(2),"big")
        elif length==4:
            return int.from_bytes(f.read(4),"big")
        else:
            print('there was a problem')
            return -1
    
    def read_name(self, f):
        data=f.read(4)
        length=struct.unpack('i',data)[0]
        return f.read(length).decode()
    
    def read(self):
        with open(filename, 'rb') as f:
            while(f.tell()!=MAGIC_SIZE):
                f.read(1)
            while(len(self.items)<=10):
                item=DektakItem()
                item.name=self.read_name(f)
                datatype=f.read(1)
                try:
                    item.data_type=int(datatype, 16)
                except ValueError:
                    item.data_type=int.from_bytes(datatype, "big")
                if item.data_type==DektakLoad.data_types['DEKTAK_BOOLEAN']:
                    print('yolo')
                    item.data=f.read(1)
                elif item.data_type==DektakLoad.data_types['DEKTAK_SINT32']:
                    item.data=struct.unpack('I',f.read(4))[0]
                elif item.data_type==DektakLoad.data_types['DEKTAK_UINT32']:
                    item.data=struct.unpack('I',f.read(4))[0]
                elif item.data_type==DektakLoad.data_types['DEKTAK_SINT64']:
                    data=f.read(8)
                    print(data)
                    item.data=struct.unpack('Q',data)[0]
                elif item.data_type==DektakLoad.data_types['DEKTAK_UINT64']:
                    item.data=struct.unpack('Q',f.read(8))[0]
                elif item.data_type==DektakLoad.data_types['DEKTAK_FLOAT']:
                    item.data=struct.unpack('f',f.read(4))[0]
                elif item.data_type==DektakLoad.data_types['DEKTAK_DOUBLE']:
                    item.data=struct.unpack('d',f.read(8))[0]
                elif item.data_type==DektakLoad.data_types['DEKTAK_TIME_STAMP']:
                    item.data=f.read(9)
                elif item.data_type==DektakLoad.data_types['DEKTAK_STRING']:
                    item.data=f.read(9)
                elif item.data_type==DektakLoad.data_types['DEKTAK_MATRIX']:
                    item.data=dict()
                    item.data['int']=struct.unpack('i',f.read(4))[0]
                    item.data['name']=f.read(4)
                    item.data['size']=self.read_varlen(f)
                    item.data['xres']=struct.unpack('i',f.read(4))[0]
                    item.data['yres']=struct.unpack('i',f.read(4))[0]
                    if item.data['size']<2*ct.sizeof(ct.c_uint32):
                        print('PROBLEM')
                    item.data['size']-=2*ct.sizeof(ct.c_uint32)
                elif item.data_type==DektakLoad.data_types['DEKTAK_CONTAINER']:
                    number_of_items=self.read_varlen(f)
                    
                    #print(f.read(10))
                else:
                    print('new data_type')
                    print(item.data_type)#DektakItem.data_types['DEKTAK_BOOLEAN'])
                    item.flag=True
                print('{:},{:},{:}===>>>>{:} ; {:}'.format(item.data_type,
                      f.tell(), datatype, item.name, item.data))
                self.items.append(item)

loader=DektakLoad(filename)
loader.read()
#%%
filename='test.OPDx'
with open(filename, 'rb') as f:
    print(f.read(200))
