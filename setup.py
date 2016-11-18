#!/usr/bin/env python

import os
import os.path
from setuptools import setup

os.chdir(os.path.abspath(os.path.dirname(__file__)))

setup(
    version="0.1.9",
    url="https://github.com/nathforge/custom_resource",
    name="custom_resource",
    description="Implement custom AWS CloudFormation resources with Python Lambda functions.",
    long_description=open("README.rst").read(),
    author="Nathan Reynolds",
    author_email="email@nreynolds.co.uk",
    packages=["custom_resource"],
    package_dir={"": "src"},
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if not line.startswith("#")
        and line.strip() != ""
    ],
    test_suite="tests",
    tests_require=["mock"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7"
    ]
)
