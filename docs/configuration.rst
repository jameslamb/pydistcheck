Configuration
=============

This page describes how to configure ``pydistcheck``.

``pydistcheck`` combines different sources of configuration in the following order.

1. default values
2. `pyproject-toml`_ (or custom TOML file passed via ``--config``)
3. `cli-arguments`_

Configuration found further down the list overrides configuration found earlier in the list.

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

Alternatively, a path to a TOML file can be provided via CLI argument ``--config``.

Put configuration in a ``[tool.pydistcheck]`` section.

The example below contains all of the configuration options for ``pydistcheck``, set to their default values.

.. literalinclude:: ./_static/defaults.toml
    :language: toml
