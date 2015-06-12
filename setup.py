#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
from pip.req import parse_requirements
from setuptools import setup, find_packages

import limpyd_extensions

# The `session` argument for the `parse_requirements` function is available (but
# optional) in pip 1.5, and mandatory in next versions
try:
    from pip.download import PipSession
except ImportError:
    parse_args = {}
else:
    parse_args = {'session': PipSession()}


def get_requirements(source):
    install_reqs = parse_requirements(source, **parse_args)
    return set([str(ir.req) for ir in install_reqs])


requirements = get_requirements('requirements.txt')


long_description = codecs.open('README.rst', "r", "utf-8").read()

setup(
    name = "redis-limpyd-extensions",
    version = limpyd_extensions.__version__,
    author = limpyd_extensions.__author__,
    author_email = limpyd_extensions.__contact__,
    description = limpyd_extensions.__doc__,
    keywords = "redis",
    url = limpyd_extensions.__homepage__,
    download_url = "https://github.com/twidi/redis-limpyd-extensions/tags",
    packages = find_packages(exclude=["tests.*", "tests"]),
    include_package_data=True,
    install_requires=requirements,
    platforms=["any"],
    zip_safe=True,
    license = "DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE",

    long_description = long_description,

    classifiers = [
        "Development Status :: 3 - Alpha",
        #"Environment :: Web Environment",
        "Intended Audience :: Developers",
        #"License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],
)
