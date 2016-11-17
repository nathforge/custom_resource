#!/usr/bin/env python

import os.path

from setuptools import setup

ROOT = os.path.dirname(__file__)

setup(
    version="0.1.7",
    url="https://github.com/nathforge/custom_resource",
    name="custom_resource",
    description="Helps you implement custom CloudFormation resources via Python Lambda functions.",
    long_description=open(os.path.join(ROOT, "README.rst")).read(),
    author="Nathan Reynolds",
    author_email="email@nreynolds.co.uk",
    packages=["custom_resource"],
    package_dir={"": os.path.join(ROOT, "src")},
    install_requires=[
        line.strip()
        for line in open(os.path.join(ROOT, "requirements.txt"))
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
