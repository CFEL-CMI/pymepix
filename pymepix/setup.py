#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of pymepix
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# If you use this programm for scientific work, you should correctly reference it; see LICENSE file
# for details.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <http://www.gnu.org/licenses/>.


import os
from setuptools import Distribution
from setuptools import setup, find_packages
from setuptools.command.install import install

from distutils.core import setup
from distutils.command.install_scripts import install_scripts
from distutils import log



packages = find_packages(exclude=('tests', 'doc'))

provides = ['pymepix',]

requires = []

install_requires = ['numpy','sklearn']

console_scripts = ['pymepix-acq=pymepix.pymepix:main']

entry_points = {'console_scripts': console_scripts,}

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Environment :: No Input/Output (Daemon)',
    'Environment :: Win32 (MS Windows)',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development :: Libraries',
    'Topic :: System :: Hardware :: Hardware Drivers',
]

long_description = None
with open('README.md') as f:
    long_description = f.read()

setup(name = 'pymepix',
      author = 'Ahmed Al-Refaie and the CFEL-CMI group',
      author_email = 'cmidaq@cfel.de',
      maintainer = 'CFEL-CMI group',
      version = '1.0',
      description = 'Timepix Python library',
      download_url = 'https://stash.desy.de/projects/CMIPUBLIC/repos/timepix',
      classifiers = classifiers,
      packages = packages,
      include_package_data = True,
      entry_points = entry_points,
      long_description = long_description,
      long_description_content_type = 'text/markdown',
      provides = provides,
      requires = requires,
      install_requires = install_requires,
)



### Local Variables:
### fill-column: 100
### truncate-lines: t
### End:
