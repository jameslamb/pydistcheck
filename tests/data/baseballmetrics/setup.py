from skbuild import setup
from setuptools import find_namespace_packages

setup(
    cmake_languages=('C', 'CXX'),
    cmake_install_dir='baseballmetrics',
    include_package_data=False,
    packages=find_namespace_packages(),
)
