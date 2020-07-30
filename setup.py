# -*- coding: utf-8 -*
from setuptools.command.install import install
from setuptools import find_packages
from setuptools import setup
from sys import version_info, stderr, exit
import codecs
import sys
import os


def read(*parts):
    # intentionally *not* adding an encoding option to open
    # see here: https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts), 'r').read()


setup(name="hitchpylibrarytoolkit",
      version=read('VERSION').replace('\n', ''),
      description="Build, test, documentation, linting, reformatting and specification code for hitch libraries.",
      long_description=read('README.md'),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Topic :: Text Processing :: Markup',
          'Topic :: Software Development :: Libraries',
          'Natural Language :: English',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
      ],
      keywords='yaml',
      author='Colm O\'Connor',
      author_email='colm.oconnor.github@gmail.com',
      url='http://hitchdev.com/hitchpylibrarytoolkit',
      license='MIT',
      install_requires=[
          "hitchstory>=0.12.0",
          "hitchrunpy>=0.6.1",
          "hitchbuildpy>=0.4.5",
          "dirtemplate>=0.1.4",
          "templex>=0.2.0",
          "kaching>=0.4",
          "twine>=0.11.0",
          "flake8>=3.5.0",
          "hitchrun",
          "gitpython",
          "black",
          "ipython",
          "q>=2.6",
      ],
      packages=find_packages(exclude=["tests", "docs", ]),
      package_data={},
      zip_safe=False,
      include_package_data=True,
)
