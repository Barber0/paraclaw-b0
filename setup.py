#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="para-branch",
    version="1.0.0",
    author="Zilin Fang",
    description="Git branch session manager for parallel development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Barber0/para-branch",
    py_modules=["para_branch"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "para-branch=para_branch:main",
        ],
    },
)
