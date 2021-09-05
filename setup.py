#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python Setuptools for installation of a suite of Mathics3 PyPI packages."""

import sys

python_version = sys.version_info[:2]
if python_version < (3, 7):
    raise Exception(
        f"This package requires Python 3.7 or greater. You have {python_version}."
    )

from setuptools import setup

setup(
    name="Mathics-benchmark",
    version="1.0.0",
    author="The Mathics Team",
    author_email="mathics-devel@googlegroups.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={
        "console_scripts": [
            "mathics-bench = mathics_benchmark.bench:main",
            "mathics-bench-compare = mathics_benchmark.compare:main",
        ]
    },
    install_requires=[
        "click",
        "psutil",
        "GitPython",
        "PyYAML",
        'matplotlib>="3.4.0',
    ],
    license="GPLv3",
    url="https://github.com/Mathics3/mathics-benchmark/",
)
