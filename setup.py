#!/usr/bin/env python3
"""
PriorityQueue - Setup Script

Allows installation via pip:
    pip install -e .

Then use from anywhere:
    priorityqueue --help
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="priorityqueue",
    version="1.0.0",
    author="Forge (Team Brain)",
    author_email="logan@metaphyllc.com",
    description="Intelligent Task Prioritization for Team Brain",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonkRonk17/PriorityQueue",
    py_modules=["priorityqueue"],
    python_requires=">=3.7",
    install_requires=[],  # Zero dependencies!
    entry_points={
        "console_scripts": [
            "priorityqueue=priorityqueue:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    keywords="task priority queue scheduling team ai agent",
    project_urls={
        "Bug Reports": "https://github.com/DonkRonk17/PriorityQueue/issues",
        "Source": "https://github.com/DonkRonk17/PriorityQueue",
    },
)
