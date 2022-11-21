Configuration
=============

This page describes how to configure ``pydistcheck``.

``pydistscheck`` resolves different sources of configuration in the following order.

1. default values
2. :ref:`pyproject-toml`
3. :ref:`cli-arguments`

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. _cli-arguments:

CLI arguments
*************

.. click:: pydistcheck.cli:check
  :prog: pydistcheck
  :nested: none

.. _pyproject-toml:

pyproject.toml
**************

If a file ``pyproject.toml`` exists in the working directory ``pydistcheck`` is run from, ``pydistcheck`` will look there for configuration.

Put configuration in a ``[tool.pydistcheck]`` section, like the following example.

.. code-block:: toml

    [tool.pydistcheck]
    inspect = False
    max_allowed_size_compressed = '1G'
    max_allowed_size_uncompressed = '4.5G'
