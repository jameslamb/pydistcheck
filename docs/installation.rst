Installation
============

``pydistcheck`` is a command-line interface (CLI) written in Python.

Because of this, the preferred way to install it from PyPI is with ``pipx`` (`docs <https://pypa.github.io/pipx/>`_).

.. code-block:: shell

    pipx install pydistcheck

If that doesn't work for you, see the sections below for other options.

PyPI
****

If you do not want to use ``pipx`` but want to install from PyPI, install with ``pip``.

.. code-block:: shell

    pip install pydistcheck

conda-forge
***********

If you use tools like ``conda`` or ``mamba`` to manage environments, install ``pydistcheck`` from conda-forge.

.. code-block:: shell

    conda install -c conda-forge pydistcheck

or

.. code-block:: shell

    mamba install pydistcheck

development version
*******************

To install the latest development (not released) version of ``pydistcheck``, clone the repo.

.. code-block:: shell

    git clone https://github.com/jameslamb/pydistcheck.git
    cd pydistcheck
    pipx install .
