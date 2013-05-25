# -*- coding: utf-8 -*-
import os
import sys

try:
    from setuptools import setup
    setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='snor',
    version='0.0.1',
    author='Paul Tax',
    author_email='paultax@gmail.com',
    include_package_data=True,
    install_requires = [
        'requests>=0.14.0',
        'transmissionrpc>=0.9',
        'peewee>=2.0.8',
        'Flask>=0.9',
        'Jinja2>=2.6'
    ],
    py_modules=['snor'],
    url='https://github.com/tax/snor',
    license='BSD licence, see LICENCE.txt',
    description='A very lightweight "sickbeard for torrents" ',
    long_description=open('README.md').read(),
)