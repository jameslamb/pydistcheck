pydistcheck
===========

``pydistcheck`` is a command-line interface (CLI) used to perform the following activities on Python package distributions.

**enforce constraints in continuous integration**

- *package contains all the expected files*
- *package is free from any unexpected files*
- *maximum package size (compressed and uncompressed)*
- *filepaths portable to different operating systems*
- *binary objects do not contain debugging symbols*

**inspect the distribution's contents during development**

- *how large is the package, compressed and uncompressed?*
- *how many files does it contain?*
- *what % of the package is Python files? compiled objects?*
- *what are the largest files in the package?*

.. code-block:: shell

    # install
    pip install pydistcheck

    # run checks and view diagnostic information
    pipx run pydistcheck --inspect dist/*

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   Installation <installation>
   Configuration <configuration>
   Check Reference <check-reference>
   How to Test a Python Distribution <how-to-test-a-python-distribution>
