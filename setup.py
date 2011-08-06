#!/usr/bin/env python

from distutils.core import setup
import minipy

setup(
    author = minipy.__author__,
    author_email = minipy.__email__,
    license = minipy.__license__,
    long_description = open('README').read(),
    maintainer = minipy.__maintainer__,
    maintainer_email = minipy.__email__,
    name = 'minipy',
    py_modules = ['minipy', 'test_minipy'],
    url = 'https://github.com/gareth-rees/minipy',
    version = minipy.__version__,
)
