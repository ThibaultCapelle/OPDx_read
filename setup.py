# -*- coding: utf-8 -*-
"""
Created on Sat Dec 25 17:25:42 2021

@author: Thibault
"""

from setuptools import setup

setup(name='OPDx_read',
      version='1.0',
      description='Reader for OPDx files',
      author='Thibault CAPELLE',
      author_email='capelle_thibault@riseup.net',
      packages=['OPDx_read'],
	  package_dir={'OPDx_read': 'OPDx_read'}
     )