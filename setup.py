#!/usr/bin/env python

from distutils.core import setup
import minipy
import os

# added by cpbotha to make sure we find the README.rst
# (with minipy 0.1, this broke the PyPI install)
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

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
    long_description = read('README.rst'),
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
