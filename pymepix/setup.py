#!/usr/bin/env python


import os
import imp
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
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development :: Libraries',
]


long_description = None
with open('README.md') as f:
    long_description = f.read()

setup(name='pymepix',
      author='CFEL-CMI group, et al (see AUTHORS)',
      author_email='cmidaq@cfel.de',
      maintainer='CFEL-CMI group',
      version='1.0',
      description='Timepix python library',
      download_url="https://stash.desy.de/projects/CMIPUBLIC/repos/timepix/browse",
      classifiers=classifiers,
      packages=packages,
      include_package_data=True,
      entry_points=entry_points,
      long_description=long_description,
      long_description_content_type='text/markdown',
      provides=provides,
      requires=requires,
      install_requires=install_requires,
)