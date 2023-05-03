How to Test a Python Distribution
=================================

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

* Are those distributions valid zip or tar files?
* Will their READMEs look pretty when rendered on the PyPI homepage?
* Do they have correctly-formatted platform tags?
* Are they as small as possible, to be kind to package repositories and users with weak internet connections?
* Are they free from filepaths and file names that some operating systems will struggle with?

You checked those things, right? And in continuous integration, with open-source tools, not with manual 

This page describes each of the checks that ``pydistcheck`` performs.
The section headings correspond to the error codes printed in ``pydistcheck``'s output.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

compiled-objects-have-debug-symbols
***********************************

The distribution contains compiled objects, like C/C++ shared libraries, with debug symbols.

Compilers for languages like C, C++, Fortran, and Rust can optionally include additional information like source code file names and line numbers, and other information useful for printing stack traces or enabling interactive debugging.

The inclusion of such information can increase the size of built objects substantially.
It's ``pydistcheck``'s position that the inclusion of such debug symbols in a shared library distributed as part of Python wheel is rarely desirable, and that by default wheels shouldn't include that type of information.

This check attempts to run the following tools with ``subprocess.run()``.

* ``dsymutil``
* ``llvm-nm``
* ``llvm-objdump``
* ``nm``
* ``objdump``
* ``readelf``

Installing more of these in the environment where you run ``pydistcheck`` improves its ability to detect debug symbols.

.. warning::
    If ``pydistcheck`` invoking these other tools with ``subprocess.run()`` is a concern for you (for example, if it causes permissions-related issues),
    turn this check off by passing it to ``--ignore``.

For a LOT more information about this topic, see these discussions in other open source projects.

* `"(auditwheel) Add --strip option to 'repair'" <https://github.com/pypa/auditwheel/pull/255>`_
* `"(cibuildwheel) Strip debug symbols of wheels" <https://github.com/pypa/cibuildwheel/issues/331>`_
* `"(numpy) ENH:Distutils Remove debugging symbols by default" <https://github.com/numpy/numpy/pull/16110>`_
* `"(psycopg2) Excessive size of wheel packages" <https://github.com/psycopg/psycopg/issues/142>`_
* `"(scikit-image) Add linker flags to strip debug symbols during wheel building " <https://github.com/scikit-image/scikit-image/pull/6109>`_
* `"(scylladb/python-driver) scylla-driver is 100 times larger than cassandra-driver" <https://github.com/scylladb/python-driver/issues/132>`_

And these other resources.

* `"Adding debugging information to your native extension" (memray docs) <https://bloomberg.github.io/memray/native_mode.html#adding-debugging-information-to-your-native-extension>`_
* `"How can I tell if a binary was compiled with debug symbols?" (vscode-lldb docs) <https://github.com/vadimcn/vscode-lldb/wiki/How-can-I-tell-if-a-binary-was-compiled-with-debug-symbols%3F>`_

distro-too-large-compressed
***************************

The package distribution is larger (compressed) than the allowed size.

Change that limit using configuration option ``max-distro-size-compressed``.

distro-too-large-uncompressed
*****************************

The package distribution is larger (uncompressed) than the allowed size.

Change that limit using configuration option ``max-distro-size-uncompressed``.

files-only-differ-by-case
*************************

The package distribution contains filepaths which are identical after lowercasing.

Such paths are not portable, as some filesystems (notably macOS), are case-insensitive.

mixed-file-extensions
*********************

Filepaths in the package distribution use a mix of file extensions for the same type of file.

For example, ``some_file.yaml`` and ``other_file.yml``.

Some programs may use file extensions, instead of more reliable mechanisms like `magic bytes <https://en.wikipedia.org/wiki/List_of_file_signatures>`_ to detect file types, like this:

.. code-block:: python

    if filepath.endswith(".yaml"):

In such cases, having a mix of file extensions can lead to only a subset of relevant files being matched.

Standardizing on a single extension for files of the same type improves the probability of either catching or completely avoiding such bugs... either all intended files will be matched or none will.

path-contains-non-ascii-characters
**********************************

At least one filepath in the package distribution contains non-ASCII characters.

Non-ASCII characters are not portable, and their inclusion in filepaths can lead to installation and usage issues on different platforms.

For more information, see:

* `"Archives Containing Non-ASCII Filenames" (Oracle docs) <https://docs.oracle.com/cd/E36784_01/html/E36823/glnlx.html>`_
* `example issue from pillow/PIL <https://github.com/python-pillow/Pillow/issues/5077>`_
* `"Unix and non-ASCII file names, a summary of issues" <https://www.lesbonscomptes.com/recoll/faqsandhowtos/NonAsciiFileNames.html>`_

path-contains-spaces
********************

At least one filepath in the package distribution contains spaces.

Filepaths with spaces require special treatment, like quoting in some settings.
Avoiding paths with spaces eliminates a whole class of potential issues related to software that doesn't handle such paths well.

For more information, see:

* `"Long filenames or paths with spaces require quotation marks" (Windows docs) <https://learn.microsoft.com/en-us/troubleshoot/windows-server/deployment/filenames-with-spaces-require-quotation-mark>`_
* `"Don't use spaces or underscores in file paths" (blog post) <https://yihui.org/en/2018/03/space-pain/>`_
* `"What technical reasons exist for not using space characters in file names?" (Stack Overflow) <https://superuser.com/questions/29111/what-technical-reasons-exist-for-not-using-space-characters-in-file-names>`_

too-many-files
**************

The package distribution contains more than the allowed number of files.

This is a very very rough way to detect that unexpected files have been included in a new release of a project.

``pydistcheck`` defaults to raising this error when a distribution has more than 2000 files...a totally arbitrary number chosen by the author.

To change that limit, use configuration option ``max-allowed-files``.

unexpected-files
****************

Files were found in the distribution which weren't expected to be included.

With ``pydistcheck``'s default settings, this check raises errors for the inclusion of files that are commonly found in source control during development but are not useful in distributions, like ``.gitignore``.

Which files are "expected" is highly project-specific.
See :doc:`configuration` for a list of the files ``pydistcheck`` complains about by default, and for information about how to customize that list.
