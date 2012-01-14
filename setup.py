#!/usr/bin/env python

from distutils.core import setup
import minipy

setup(
    author = minipy.__author__,
    author_email = minipy.__email__,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Pre-processors',
        ],
    description = 'Minify Python 2 source code',
    license = minipy.__license__,
    long_description = open('README.rst').read(),
    maintainer = minipy.__maintainer__,
    maintainer_email = minipy.__email__,
    name = 'minipy',
    py_modules = ['minipy', 'test_minipy'],
    url = 'https://github.com/gareth-rees/minipy',
    version = minipy.__version__,
    entry_points = {
        'console_scripts': [
            'minipy = minipy:main',
        ]
    }
)
