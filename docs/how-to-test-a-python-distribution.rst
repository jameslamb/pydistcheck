How to Test a Python Distribution
=================================

Introduction
************

Your code is good. Really good.

You enforced consistent style with ``black``, ``isort``, and ``pydocstyle``.

You checked for a wide range of performance, correctness, and readability issues with ``flake8``, ``mypy``, ``pylint``, and ``ruff``.

You ran extensive tests with ``pytest`` and ``hypothesis``.

You even scanned for legal and security issues with tools like ``pip-audit``, ``pip-licenses``, and ``safety``.

So finally, FINALLY, it's time to package it up into a tarball and upload it to PyPI.

.. code-block:: shell

    python -m build .

\.\.\. right?

Hopefully! But let's check.

* `Are those distributions valid zip or tar files?`
* `Will their READMEs look pretty when rendered on the PyPI homepage?`
* `Do they have correctly-formatted platform tags?`
* `Are they as small as possible, to be kind to package repositories and users with weak internet connections?`
* `Are they free from filepaths and file names that some operating systems will struggle with?`

You checked those things, right? And in continuous integration, with open-source tools, not with manual steps and random ``tar`` incantations copied from Stack Overflow?

If yes, great! I'm proud of you.

If you're feeling like you could use some help with that... read on.

Quickstart
**********

After building at least one wheel and sdist...

.. code-block:: shell

    python -m build -o dist .

Run the following on those distributions to catch a wide range of packaging issues.

.. code-block:: shell

    # are all the sdists valid gzipped tar files?
    gunzip -tv dist/*.tar.gz

    # are all the wheels valid zip files?
    zip -T dist/*.whl

    # is the package metadata well-formatted?
    pyroma --min=10 dist/*.tar.gz
    twine check --strict dist/*

    # is the distribution properly structured and portable?
    check-wheel-contents dist/*.whl
    pydistcheck --inspect dist/*

List of Tools
*************

The following open-source tools can be used to detect (and in some cases repair) a wide range of Python packaging issues.

* ``abi3audit`` (`link <https://github.com/trailofbits/abi3audit>`__) = detect ABI incompatibilities in wheels with CPython extensions
* ``auditwheel`` (`link <https://github.com/pypa/auditwheel>`__) = detect and repair issues in Linux wheels that link to external shared libraries
* ``auditwheel-emscripten`` (`link <https://github.com/ryanking13/auditwheel-emscripten>`__) = like ``auditwheel``, but focused on Python-in-a-web-browser applications (e.g. `pyodide auditwheel`_)
* ``auditwheel-symbols`` (`link <https://github.com/messense/auditwheel-symbols>`__) = detect which symbols in a Linux wheel's shared library are causing ``auditwheel`` to sugggest a more recent ``manylinux`` tag
* ``check-manifest`` (`link <https://github.com/mgedmin/check-manifest>`__) = check that sdists contain all the files you expect them to, based on what you've checked into version control
* ``check-wheel-contents`` (`link <https://github.com/jwodder/check-wheel-contents>`__) = detect unnecessary files, import issues, portability problems in wheels
* ``conda-verify`` (`link <https://github.com/conda/conda-verify/tree/main>__`) = detect portability and correctness problems in conda packages
* ``delocate`` (`link <https://github.com/matthew-brett/delocate>`__) = detect and repair issues in macOS wheels that link to external shared libraries
* ``delvewheel`` (`link <https://github.com/adang1345/delvewheel>`__) = detect and repair issues in Windows wheels that link to external shared libraries
* ``pkginfo`` (`link https://pythonhosted.org/pkginfo/`__) = print sdist and wheel metadata
* ``pydistcheck`` (`link <https://github.com/jameslamb/pydistcheck>`__) = detect portability problems in conda packages, wheels, and sdists
* ``pyroma`` (`link <https://github.com/regebro/pyroma>`__) = detect incomplete or malformed metadata in sdists
* ``repairwheel`` (`link <https://github.com/jvolkman/repairwheel>`__) = repair issues in Linux, macOS, and Windows wheels (wraps ``auditwheel``, ``delocate``, and ``delvewheel``)
* ``twine`` (`link <https://github.com/pypa/twine>`__) = detect issues in package metadata (via ``twine check``)
* ``wheel-inspect`` (`link <https://github.com/jwodder/wheel-inspect>`__) = dump summary information about wheels into machine-readable formats

.. _pyodide auditwheel: https://pyodide.org/en/stable/usage/api/pyodide-cli.html
