from setuptools import find_namespace_packages
from skbuild import setup

setup(
    cmake_languages=("C", "CXX"),
    cmake_install_dir="baseballmetrics",
    include_package_data=False,
    packages=find_namespace_packages(),
)
