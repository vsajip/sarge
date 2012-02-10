#!/usr/bin/env python

from distutils.core import setup, Command
from os.path import join, dirname, abspath
import re

import sarge

class TestCommand(Command):
    user_options = []

    def run(self):
        import sys
        import unittest

        import test_sarge
        loader = unittest.TestLoader()
        runner = unittest.TextTestRunner()
        runner.run(loader.loadTestsFromModule(test_sarge))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

def description():
    f = open(join(dirname(__file__), 'README'))
    read_me = f.read()
    f.close()
    regexp = r'^sarge\s*[\d.]*\s*\n=======+\s*\n(.*)Requirements '
    requires, = re.findall(regexp, read_me, re.DOTALL)
    regexp = r'Availability & Documentation\s*\n-----+\s*\n(.*)'
    avail, = re.findall(regexp, read_me, re.DOTALL)
    return requires + avail

setup(
    name='sarge',
    description=('A wrapper for subprocess which provides command '
                 'pipeline functionality.'),
    long_description=description(),
    version=sarge.__version__,
    author='Vinay Sajip',
    author_email='vinay_sajip@yahoo.co.uk',
    maintainer='Vinay Sajip',
    maintainer_email='vinay_sajip@yahoo.co.uk',
    url='http://sarge.readthedocs.org/',
    packages=['sarge'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: Implementation',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Shells',
    ],
    cmdclass={ 'test': TestCommand },
)
