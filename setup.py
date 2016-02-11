#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='postagemq',
    version='0.1.0',
    description="A Python library for AMQP-based network components",
    long_description=readme + '\n\n' + history,
    author='Leonardo Giordani',
    author_email='giordani.leonardo@gmail.com',
    url='https://github.com/postagemq/postagemq',
    packages=[
        'postagemq',
    ],
    package_dir={'postagemq': 'postagemq'},
    include_package_data=True,
    install_requires=[
    ],
    license="LGPLv3 or later",
    zip_safe=False,
    keywords='postagemq',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)'
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking ',
    ],
    test_suite='tests',
)
