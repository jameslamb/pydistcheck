## end-to-end

```shell
# both source distro and wheels contain lots of website stuff
# - images (.gif, .png)
# - website (.js, .css, .rst, .html)
#
# source distro contains even more stuff
# - CI configs (.stylelintignore, .stylelintrc, .eslintignore, .eslintrc)
#
make full-run \
    -e PACKAGE_NAME=apache-airflow

# FAILS after "searching for source artifact"
# wheel-only distribution?
make full-run \
    -e PACKAGE_NAME=catboost

# very nice, just a .so mostly
make full-run \
    -e PACKAGE_NAME=datatable

# - images (.png. svg)
# - website (.rst, .html)
make full-run \
    -e PACKAGE_NAME=distributed

# most of the wheel is the website (maybe?)
# - .rst, .png, .svg, .html, .css
make full-run \
    -e PACKAGE_NAME=flask

# super tight
# FAILS: "searching for a manylinux wheel"
make full-run \
    -e PACKAGE_NAME=kafka-python

# wild stuff
# 4.4 MB of .rst files
# 4.0 MB of Javascript code
# 2.6 MB CSV
# audio files??? (.ogg, .mp3)
make full-run \
    -e PACKAGE_NAME=numpy

make full-run \
    -e PACKAGE_NAME=s3transfer

# tons of stuff in source distro, including:
# - images (.png, .jpg, .jpeg, .svg, .bmp)
# - a website (.rst, .css, .html, .js)
# - testing-only files (.coveragerc)
# - source-control files (.gitignore)
make full-run \
    -e PACKAGE_NAME=scikit-learn

# very small wheel
# - 8.7% RST files
make full-run \
    -e PACKAGE_NAME=urllib3

# nothing obviously out of place
make full-run \
    -e PACKAGE_NAME=xgboost
```

### Cuurrently broken

```text
catboost
tensorflow (weird 15M in the data frame)
torch
```
