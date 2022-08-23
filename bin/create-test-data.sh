#!/bin/bash

# [description] generate test tarballs

rm -rf /tmp/base-package
mkdir -p /tmp/base-package
touch /tmp/base-package/__init__.py

cat << EOF > /tmp/base-package/thing.py
def do_stuff():
    return True
EOF

zip \
    -r base-package.zip \
    /tmp/base-package

mv ./base-package.zip ./tests/data/

tar \
    -czvf base-package.tar.gz \
    /tmp/base-package

mv ./base-package.tar.gz ./tests/data/
