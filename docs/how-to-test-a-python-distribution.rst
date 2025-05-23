How to Test a Python Distribution
=================================

Introduction
************

Your code is good. Really good.

You enforced consistent style with ``black``, ``isort``, ``ruff``, and ``pydocstyle``.

You checked for a wide range of performance, correctness, and readability issues with ``flake8``, ``mypy``, ``pylint``, and ``ruff``.

You ran extensive tests with ``pytest`` and ``hypothesis``.

You even scanned for legal and security issues with tools like ``pip-audit``, ``pip-licenses``, and ``safety``.

So finally, FINALLY, it's time to package it up into a tarball and upload it to PyPI.

.. code-block:: shell

    python -m build .

\.\.\. right?

Hopefully! But let's check.

* `Are those distributions valid zip or tar files?`
* `Are they small enough to fit on PyPI?`
* `Are they as small as possible, to be kind to package repositories and users with weak internet connections?`
* `Are they free from filepaths and file names that some operating systems will struggle with?`
* `Do they have correctly-formatted platform tags?`
* `Will their READMEs look pretty when rendered on the PyPI homepage?`

You checked those things, right? And in continuous integration, with open-source tools, not with manual steps and random ``tar`` incantations copied from Stack Overflow?

If yes, great! I'm proud of you.

If you're feeling like you could use some help with that... read on.

Quickstart
**********

After building at least one wheel and sdist...

.. code-block:: shell

    python -m build --outdir dist .

Run the following on those distributions to catch a wide range of packaging issues.

.. code-block:: shell

    # are all the sdists valid gzipped tar files?
    gunzip -tv dist/*.tar.gz

    # are all the wheels valid zip files?
    zip -T dist/*.whl

    # is the package metadata well-formatted?
    pyroma --min=10 dist/*.tar.gz
    twine check --strict dist/*

    # (INFO-level) print some details to logs
    pkginfo --json dist/*.tar.gz
    pkginfo --json dist/*.whl

    # (DEBUG-level) print even more details to logs
    wheel2json dist/*.whl

    # is the distribution properly structured and portable?
    check-wheel-contents dist/*.whl
    pydistcheck --inspect dist/*

Some of those tools can also dump package data to machine-readable formats, that could
then be passed through your own custom scripts.

.. code-block:: shell

    # simple list of filepaths in the wheel
    unzip -l dist/*.whl > filepaths.txt

    # JSON representation of the wheel metadata
    pkginfo --json dist/*.whl > pkginfo.json

    # this has most of what pkginfo has, plus things like
    # md5 and sha256 checksums for every file in the distribution
    wheel2json dist/*.whl > wheel-inspect.json

Consider using ``pre-commit`` (https://pre-commit.com/), with at least the following configuration to catch
portability-related issues before they even make it into distributions.

.. code-block:: yaml

    repos:
    - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.5.0
        hooks:
        # large files checked into source control
        - id: check-added-large-files
          args: ['--maxkb=512']
        # files whose names only differ by case
        - id: check-case-conflict
        # symlinks that don't point to anything
        - id: check-symlinks
        # symlinks changed to regular files with content of a path
        - id: destroyed-symlinks
        # ensure all files end in a newline
        - id: end-of-file-fixer
        # mixed line endings
        - id: mixed-line-ending
        # superfluous whitespace
        - id: trailing-whitespace
    - repo: https://github.com/shellcheck-py/shellcheck-py
        rev: v0.10.0.1
        hooks:
        - id: shellcheck

If you use GitHub Actions for continuous integration, consider adding a step
with the ``hynek/build-and-inspect-python-package`` action (https://github.com/hynek/build-and-inspect-python-package)
running prior to publishing packages.

List of Tools
*************

The following open-source tools take packages as input, and can be used to detect (and in some cases repair) a wide range of Python packaging issues.

* ``abi3audit`` (`link <https://github.com/pypa/abi3audit>`__) = detect ABI incompatibilities in wheels with CPython extensions
* ``auditwheel`` (`link <https://github.com/pypa/auditwheel>`__) = detect and repair issues in Linux wheels that link to external shared libraries
* ``auditwheel-emscripten`` (`link <https://github.com/ryanking13/auditwheel-emscripten>`__) = like ``auditwheel``, but focused on Python-in-a-web-browser applications (e.g. `pyodide auditwheel`_)
* ``auditwheel-symbols`` (`link <https://github.com/messense/auditwheel-symbols>`__) = detect which symbols in a Linux wheel's shared library are causing ``auditwheel`` to suggest a more recent ``manylinux`` tag
* ``check-wheel-contents`` (`link <https://github.com/jwodder/check-wheel-contents>`__) = detect unnecessary files, import issues, portability problems in wheels
* ``conda-verify`` (`link <https://github.com/conda/conda-verify/tree/main>`__) = detect portability and correctness problems in conda packages
* ``cph`` (`link <https://github.com/conda/conda-package-handling>`__) = work with conda packages (e.g. ``cph extract`` to decompress them, ``cph list`` to list their contents)
* ``delocate`` (`link <https://github.com/matthew-brett/delocate>`__) = detect and repair issues in macOS wheels that link to external shared libraries
* ``delvewheel`` (`link <https://github.com/adang1345/delvewheel>`__) = detect and repair issues in Windows wheels that link to external shared libraries
* ``pkginfo`` (`link <https://pythonhosted.org/pkginfo>`__) = print sdist and wheel metadata
* ``pydistcheck`` (`link <https://github.com/jameslamb/pydistcheck>`__) = detect portability problems in conda packages, wheels, and sdists
* ``pyroma`` (`link <https://github.com/regebro/pyroma>`__) = detect incomplete or malformed metadata in sdists
* ``repairwheel`` (`link <https://github.com/jvolkman/repairwheel>`__) = repair issues in Linux, macOS, and Windows wheels (wraps ``auditwheel``, ``delocate``, and ``delvewheel``)
* ``twine`` (`link <https://github.com/pypa/twine>`__) = detect issues in package metadata (via ``twine check``)
* ``wheel-inspect`` (`link <https://github.com/wheelodex/wheel-inspect>`__) = dump summary information about wheels into machine-readable formats

These take a source tree as input and find problems in the files uses to create packages.

* ``check-manifest`` (`link <https://github.com/mgedmin/check-manifest>`__) = check that sdists contain all the files you expect them to, based on what you've checked into version control
* ``pre-commit/pre-commit-hooks`` (`link <https://github.com/pre-commit/pre-commit-hooks>`__) = many checks, including the following related to portability:
    - ``check-added-large-files`` = check for too-large files in source control
    - ``check-case-conflict`` = check for files whose names only differ by case
    - ``check-symlinks`` = check for symlinks that don't point to real files
    - ``destroyed-symlinks`` = check for symlinks replaced with the content of the regular file they previously pointed to
* ``validate-pyproject`` (`link <https://github.com/abravalheri/validate-pyproject/>`__) = check that ``pyproject.toml`` files are valid

These take compiled files like ELF (``.so``), Mach-O (``.dylib``), or PE (``.dll``, ``.exe``) files as input and can be used to test and modify them.

* ``dsymutil`` (`link <https://llvm.org/docs/CommandGuide/dsymutil.html>`__) = dump DWARF debug symbols or link debug information into an executable
* ``dumpbin`` (`link <https://learn.microsoft.com/en-us/cpp/build/reference/dumpbin-reference?view=msvc-170>`__) = describe COFF files (including PE files)
* ``install_name_tool`` (`link <https://manp.gs/mac/1/install_name_tool>`__) = modify Mach-O files (shipped with macOS developer tools)
* ``machomangler`` (`link <https://github.com/njsmith/machomachomangler>`__) = patch Mach-O and PE files
* ``ldd`` (`link <https://man7.org/linux/man-pages/man1/ldd.1.html>`__) = display dependencies of shared objects
* ``listdlls`` (`link <https://learn.microsoft.com/en-us/sysinternals/downloads/listdlls>`__) = list all of the DLLs loaded into a process, useful for tracing DLL dependencies (similar to ``ldd``, but for Windows)
* ``llvm-install-name-tool`` (`link <https://llvm.org/docs/CommandGuide/llvm-install-name-tool.html>`__) = ``install_name_tool`` re-implementation from the LLVM project
* ``llvm-objdump`` (`link <https://llvm.org/docs/CommandGuide/llvm-objdump.html>`__) = ``objdump`` re-implementation from the LLVM project
* ``llvm-otool`` (`link <https://llvm.org/docs/CommandGuide/llvm-otool.html>`__) = ``otool`` re-implementation from the LLVM project
* ``llvm-readelf`` (`link <https://llvm.org/docs/CommandGuide/llvm-readelf.html>`__) = ``readelf`` re-implementation from the LLVM project
* ``objdump`` (`link <https://man7.org/linux/man-pages/man1/objdump.1.html>`__) = display information about object files, including ELF files
* ``otool`` (`link <https://manp.gs/mac/1/otool-classic>`__) = display information about Mach-O files (shipped with macOS developer tools)
* ``patchelf`` (`link <https://github.com/NixOS/patchelf>`__) = modify the RPATH of ELF files
* ``pecheck`` (`link <https://github.com/DidierStevens/DidierStevensSuite/blob/78d34c9f59730a10f40ff14889131cc108a3300b/pecheck.py>`__) = single-file Python module that can be used to print some information about PE files
* ``peframe`` (`link <https://github.com/guelfoweb/peframe>`__) = find malware in PE files
* ``pyelftools`` (`link <https://github.com/eliben/pyelftools>`__) = Python library for inspecting and modifying ELF files, including a Python re-implementation of ``readelf``
* ``readelf`` (`link <https://man7.org/linux/man-pages/man1/readelf.1.html>`__) = display information about ELF files (multiple implementations exist)

.. _pyodide auditwheel: https://pyodide.org/en/stable/usage/api/pyodide-cli.html
