#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Python Setuptools for installation of a suite of Mathics3 PyPI packages."""

setup(
    name="Mathics-benchmark",
    version=1.0.0,
    author="The Mathics team",
    author_email="mathics-devel@googlegroups.com",
    classifiers=classifiers,
    description=short_desc,
    extras_require=EXTRAS_REQUIRE,
    scripts=scripts,
    install_requires=["click"]
)
