from skbuild import setup

setup(
    cmake_languages=('C', 'CXX'),
    cmake_install_dir='baseballmetrics',
    include_package_data=True,
    packages=["baseballmetrics"],
    package_data={},
)
