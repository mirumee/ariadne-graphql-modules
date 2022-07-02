#! /usr/bin/env python
import os
from setuptools import setup

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

README_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
with open(README_PATH, "r", encoding="utf8") as f:
    README = f.read()

setup(
    name="ariadne-graphql-modules",
    author="Mirumee Software",
    author_email="hello@mirumee.com",
    description="GraphQL Modules for Ariadne",
    long_description=README,
    long_description_content_type="text/markdown",
    license="BSD",
    version="0.5.0",
    url="https://github.com/mirumee/ariadne-graphql-modules",
    packages=["ariadne_graphql_modules"],
    include_package_data=True,
    install_requires=[
        "ariadne>=0.15.0",
    ],
    classifiers=CLASSIFIERS,
    platforms=["any"],
    zip_safe=False,
)
