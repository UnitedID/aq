#!/usr/bin/env python
#
import re
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

__author__ = 'roland'


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.test_args)
        sys.exit(errno)

version = ''
with open('src/atsrv/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

setup(
    name="atsrv",
    version=version,
    description="Python implementation of a Attestation Server",
    author="Roland Hedberg",
    author_email="roland@catalogix.se",
    license="Apache 2.0",
    url='https://github.com/UnitedID/atsrv',
    packages=["atsrv"],
    # 'oic/v2'],
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Libraries :: Python Modules"],
    install_requires=[
         "argparse",
         "requests",
         'oic >= 0.9.5.0',
         "Cherrypy",
         'cherrypy-cors >= 1.5'],
    zip_safe=False,
    cmdclass={'test': PyTest},
)
