#!/usr/bin/env python3
"""
Setup script for Ontology Mapping Tool
"""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ontology-mapper",
    version="1.0.0",
    author="Jonas Heinicke",
    author_email="jonas.heinicke@helmholtz-hzi.de",
    description="A modular command-line interface for mapping and enriching ontologies using BioPortal and OLS APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jonasjjj96/ontology-mapper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ontology-mapping=main:main",
            "ontology-gui=gui.launch_gui:main",
        ],
    },
    extras_require={
        "gui": ["tkinter"],
        "dev": ["pytest", "pytest-cov", "flake8", "black"],
    },
    include_package_data=True,
    package_data={
        "config": ["*.py"],
    },
)
