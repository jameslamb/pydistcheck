#!/usr/bin/env bash

# [description] generate test tarballs

set -e -u -o pipefail

pip install \
    'build>=0.9.0' \
    'setuptools>=42'

rm -rf /tmp/base-package
mkdir -p /tmp/base-package/base_package
touch /tmp/base-package/base_package/__init__.py

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
include_package_data = True
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

rm -rf /tmp/base-package/base-package
rm -rf /tmp/base-package/dist
rm -rf /tmp/base-package/*.egg-info
mkdir -p /tmp/problematic-package
cp -R /tmp/base-package/* /tmp/problematic-package/
mv \
    /tmp/problematic-package/base_package \
    /tmp/problematic-package/problematic_package
sed \
    -i.bak \
    -e "s/base/problematic/g" \
    /tmp/problematic-package/setup.cfg

cat << EOF > /tmp/problematic-package/problematic_package/question.py
try:
    from spongebobcase import tospongebob
except ImportError:
    def tospongebob(x):
        return("install 'spongebobcase' to use this")
SPONGEBOB_STR = tospongebob("but does it scale?")
EOF

# different extensions
cat << EOF > /tmp/problematic-package/config.yml
do_stuff: true
EOF
cp \
    /tmp/problematic-package/config.yml \
    /tmp/problematic-package/config.yaml

cat << EOF > /tmp/problematic-package/data.jsonl
{"city": "Boston", "team": "Red Sox"}
{"city": "Chicago", "team": "White Sox"}
EOF
cp \
    /tmp/problematic-package/data.jsonl \
    /tmp/problematic-package/other_data.NDJSON
cp \
    /tmp/problematic-package/data.jsonl \
    /tmp/problematic-package/more_data.ndjson

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
touch "/tmp/problematic-package/problematic_package/bad code/__init__.py"
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

cat << EOF > "/tmp/problematic-package/MANIFEST.in"
include .git/*
include *.gitignore
include *.ini
include *.jsonl
include *.ndjson
include *.NDJSON
include problematic_package/.gitignore
include problematic_package/*.PY
include *.yaml
include *.yml
EOF

# non-ASCII character in path
cat << EOF > "/tmp/problematic-package/problematic_package/€veryone-loves-python.py"
print('Python is great.')
EOF

# files and directories that don't need to be in a Python distribution
pushd /tmp/problematic-package
git init --initial-branch='main'
echo '*.csv' > ./.gitignore
echo 'ignored: [DL3008]' > ./.hadolint.yaml
# nested file
echo '*.csv' > ./problematic_package/.gitignore
popd

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
