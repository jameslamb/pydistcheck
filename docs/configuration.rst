Check Reference
===============

This page describes how to configure ``pydistcheck``.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

CLI arguments
*************

.. click:: pydistcheck.cli:check
  :prog: pydistcheck
  :nested: none

pyproject.toml
**************

If a file ``pyproject.toml`` exists in the working directory ``pydistcheck`` is run from, ``pydistcheck`` will look there for configuration.

Put configuration in a ``[tool.pydistcheck]`` section, like the following example.

.. code-block:: toml

    [tool.pydistcheck]
    inspect = False
    max_allowed_size_compressed = '1G'
    max_allowed_size_uncompressed = '4.5G'
