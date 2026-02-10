#================================================================================
# FILE: setup.py
#
# Purpose:
# 1. Setup script for Embedded Test Framework
# 2. Compiles C++ module and installs Python package
# 
# Author: Diksha Ravindran
# Year: Jan - 2025
#================================================================================

from setuptools import setup, Extension, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext
import sys

__version__ = "0.1.0"

# C++ extension module
ext_modules = [
    Pybind11Extension(
        "fast_comms_cpp",
        sources=[
            "src/cpp/fast_comms.cpp",
            "src/cpp/bindings.cpp",
        ],
        include_dirs=["src/cpp"],
        extra_compile_args=["-std=c++14", "-O3"],
        extra_link_args=[],
        language="c++",
    ),
]

setup(
    name="embedded_test_framework",
    version=__version__,
    author="Diksha Ravindran",
    author_email="diksharavindran94@gmail.com",
    description="A modular test framework for embedded devices",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/diksharavindran/testFrameWork",
    packages=find_packages(),
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    install_requires=[
        "pybind11>=2.10.0",
        "netifaces>=0.11.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "etf=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: C++",
    ],
)

