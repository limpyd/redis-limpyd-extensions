#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs

from setuptools import setup, find_packages

import limpyd_extensions

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
    packages = find_packages(),
    include_package_data=True,
    install_requires=["redis-limpyd", ],
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
    ],
)

