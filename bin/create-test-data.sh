#!/bin/bash

# [description] generate test tarballs

rm -rf /tmp/base-package
mkdir -p /tmp/base-package
touch /tmp/base-package/__init__.py

cat << EOF > /tmp/base-package/thing.py
def do_stuff():
    return True
EOF

curl https://www.apache.org/licenses/LICENSE-2.0.txt \
    --output /tmp/base-package/LICENSE.txt

zip \
    -r base-package.zip \
    /tmp/base-package

mv ./base-package.zip ./tests/data/

tar \
    -czvf base-package.tar.gz \
    /tmp/base-package

mv ./base-package.tar.gz ./tests/data/

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

zip \
    -r problematic-package.zip \
    /tmp/problematic-package

mv ./problematic-package.zip ./tests/data/

tar \
    -czvf problematic-package.tar.gz \
    /tmp/problematic-package

mv ./problematic-package.tar.gz ./tests/data/
