#!/bin/bash

# [description] generate test tarballs

set -e -u -o pipefail

pip install \
    'build>=0.9.0' \
    'setuptools>=42'

rm -rf /tmp/base-package
mkdir -p /tmp/base-package
touch /tmp/base-package/__init__.py

mkdir -p /tmp/base-package/base_package
cat << EOF > /tmp/base-package/base_package/thing.py
def do_stuff():
    return True
EOF

cat << EOF > /tmp/base-package/setup.py
from setuptools import setup

setup()
EOF

cat << EOF > /tmp/base-package/README.md
read me please
EOF

cat << EOF > /tmp/base-package/setup.cfg
[metadata]
name = base-package
version = 0.1.0
description = base_package (pydistcheck test package)
maintainer_email = jaylamb20@gmail.com
license = BSD-3-Clause

[options]
packages = find:
EOF

curl https://www.apache.org/licenses/LICENSE-2.0.txt \
    --output /tmp/base-package/LICENSE.txt

pushd /tmp/base-package
    python setup.py sdist \
        --format=zip
    rm -rf ./base-package.egg-info

    python -m build \
        --no-isolation \
        --sdist
popd

mv \
    /tmp/base-package/dist/*.tar.gz \
    ./tests/data
mv \
    /tmp/base-package/dist/*.zip \
    ./tests/data

#-----------------------#
# package with problems #
#-----------------------#

rm -rf /tmp/base-package/dist
rm -rf /tmp/base-package/*.egg-info
cp -R /tmp/base-package /tmp/problematic-package
mkdir -p /tmp/problematic-package/problematic_package
sed \
    -i.bak \
    -e "s/base/problematic/" \
    /tmp/problematic-package/setup.cfg

cat << EOF > /tmp/problematic-package/problematic_package/question.py
from spongebobcase import tospongebob
SPONGEBOB_STR = tospongebob("but does it scale?")
EOF

# only differs by one letter in name
cp \
    /tmp/problematic-package/problematic_package/question.py \
    /tmp/problematic-package/problematic_package/Question.py

# only differs by extension
cp \
    /tmp/problematic-package/problematic_package/question.py \
    /tmp/problematic-package/problematic_package/question.PY

# spaces in directory name
mkdir -p "/tmp/problematic-package/problematic_package/bad code"
cat << EOF > "/tmp/problematic-package/problematic_package/bad code/ship-it.py"
def is_even(num: int) -> bool:
    if num == 1:
        return False
    elif num == 2:
        return True
    else:
        import random
        return random.random() > 0.5
EOF

# spaces in file name but not directory name
cat << EOF > "/tmp/problematic-package/beep boop.ini"
[config]
allow_bugs = False
EOF

# non-ASCII character in path
cat << EOF > "/tmp/problematic-package/problematic_package/€veryone-loves-python.py"
print('Python is great.')
EOF

pushd /tmp/problematic-package
    python setup.py sdist \
        --format=zip
    rm -rf ./problematic-package.egg-info

    python -m build \
        --no-isolation \
        --sdist
popd

mv \
    /tmp/problematic-package/dist/*.tar.gz \
    ./tests/data
mv \
    /tmp/problematic-package/dist/*.zip \
    ./tests/data
