#!/usr/bin/env python
# Copyright (c) 2014 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from setuptools import setup

INSTALL_REQUIREMENTS = [
    'jsonrpclib',
    'cjson'
    ]

setup(
      name='simApi',
      version=open('VERSION').read().split()[0],
      description='vEOS extension to serve custom eAPI responses',
      long_description=open('README.md').read(),
      author='Andrei Dvornic, Arista EOS+',
      author_email='andrei@arista.com',
      license='BSD-3',
      url='http://eos.arista.com',
      py_modules=['SimApi'],
      install_requires=INSTALL_REQUIREMENTS,
      data_files=[
          ('/etc/nginx/external_conf', ['conf/simApi.conf']),
          ('/etc/uwsgi', ['conf/simApi.ini']),
          ('/persist/sys', ['conf/simApi.json'])
      ]
)
