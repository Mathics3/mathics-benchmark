#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Python Setuptools for installation of a suite of Mathics3 PyPI packages."""
from setuptools import setup

setup(
    name="Mathics-benchmark",
    version="1.0.0",
    author="The Mathics Team",
    author_email="mathics-devel@googlegroups.com",
    install_requires=["click", "psutil", "pygit"],
    license='GPLv3',
)
