pydistcheck
===========

``pydistcheck`` is a command-line interface (CLI) used to perform the following activities on Python package distributions.

**inspect the distribution's contents during development**

- *how large is the package, compressed and uncompressed?*
- *how many files does it contain?*
- *what % of the package is Python files? compiled objects?*
- *what's the difference between the compressed and uncompressed size?*

**enforce constraints in continuous integration**

- *should not be larger than* ``n`` *MB uncompressed*
- *should not contain more than* ``x`` *files*
- *should not contain non-portable filepaths*
- *should not contain compiled code with debugging symbols*

.. code-block:: shell

    # install
    pipx install pydistcheck

    # run checks
    pydistcheck dist/*

    # run checks and view diagnostic information
    pydistcheck --inspect dist/*

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   Installation <installation>
   Configuration <configuration>
   Check Reference <check-reference>
   How to Test a Python Distribution <how-to-test-a-python-distribution>
