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

cat << EOF > /tmp/base-package/setup.cfg
[metadata]
name = base_package
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
    rm -rf ./base_package.egg-info

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

cp -R /tmp/base-package /tmp/problematic-package

cat << EOF > /tmp/problematic-package/question.py
from spongebobcase import tospongebob
tospongebob("but does it scale?")
EOF

# only differs by one letter in name
cp \
    /tmp/problematic-package/question.py \
    /tmp/problematic-package/Question.py

# only differs by extension
cp \
    /tmp/problematic-package/question.py \
    /tmp/problematic-package/question.PY

# spaces in directory name
mkdir -p "/tmp/problematic-package/bad code"
cat << EOF > "/tmp/problematic-package/bad code/ship-it.py"
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
cat << EOF > "/tmp/problematic-package/€veryone-loves-python.py"
print('Python is great.')
EOF

zip \
    -r problematic-package.zip \
    /tmp/problematic-package

mv ./problematic-package.zip ./tests/data/

tar \
    -czvf problematic-package.tar.gz \
    /tmp/problematic-package

mv ./problematic-package.tar.gz ./tests/data/
