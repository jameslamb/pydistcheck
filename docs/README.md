# docs

This page describes how to test and develop changes to ``pydistcheck``'s documentation.

## Build Locally

To build the documentation locally, create a ``conda`` environment using [`mamba`](https://github.com/mamba-org/mamba).

```shell
mamba env create \
    -n pydistcheck-docs \
    --file ./env.yml
```

Activate the environment and generate the documentation.

```shell
source activate pydistcheck-docs
make html
```

Open `_build/html/index.html` in a web browser to view the local copy of the documentation.
