#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs

from setuptools import setup, find_packages

import limpyd

long_description = codecs.open('README.md', "r", "utf-8").read()

setup(
    name = "redis-limpyd-extensions",
    version = limpyd.__version__,
    author = limpyd.__author__,
    author_email = limpyd.__contact__,
    description = limpyd.__doc__,
    keywords = "redis",
    url = limpyd.__homepage__,
    download_url = "https://github.com/twidi/redis-limpyd-extensions/downloads",
    packages = find_packages(),
    include_package_data=True,
    #license = "MIT",
    platforms=["any"],
    zip_safe=True,

    long_description = long_description,

    classifiers = [
        "Development Status :: 3 - Alpha",
        #"Environment :: Web Environment",
        "Intended Audience :: Developers",
        #"License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
    ],
)

