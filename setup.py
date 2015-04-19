# -*- coding: utf-8 -*-

import os
import sys

from setuptools import setup, find_packages

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

def get_readme():
    readme_path = os.path.abspath(os.path.join(CURRENT_DIR, 'README.rst'))
    if os.path.exists(readme_path):
        with open(readme_path) as fp:
            return fp.read()
    return ""

setup(
    name='mongo-mail-tools',
    version="0.1.0",
    url='https://github.com/srault95/mongo-mail-tools', 
    description='Mail Tools for testing and demo',
    long_description=get_readme(),
    author='Stéphane RAULT',
    author_email='stephane.rault@radicalspam.org',
    classifiers=[
        'Topic :: Communications :: Email',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators'
    ],
    include_package_data=True,
    zip_safe=False,
    packages=('mm_tools',),
    install_requires=[
        'python-dateutil',
        'gevent>=1.0',
        'python-decouple',
        'fake-factory',
        'arrow',
    ],
)
