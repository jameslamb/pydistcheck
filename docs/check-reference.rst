Check Reference
===============

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

expected-files
**************

The package distribution does not contain a file or directory that it was expected to contain.

This can be used to test that changes to ``MANIFEST.in``, ``package_data``, and similar don't
accidentally result in the exclusion of any expected files.

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
* ``jqlang/jq#811``: `"File names with non ASCII characters" <https://github.com/jqlang/jq/issues/811>`_

path-contains-spaces
********************

At least one filepath in the package distribution contains spaces.

Filepaths with spaces require special treatment, like quoting in some settings.
Avoiding paths with spaces eliminates a whole class of potential issues related to software that doesn't handle such paths well.

For more information, see:

* `"Long filenames or paths with spaces require quotation marks" (Windows docs) <https://learn.microsoft.com/en-us/troubleshoot/windows-server/deployment/filenames-with-spaces-require-quotation-mark>`_
* `"Don't use spaces or underscores in file paths" (blog post) <https://yihui.org/en/2018/03/space-pain/>`_
* `"What technical reasons exist for not using space characters in file names?" (Stack Overflow) <https://superuser.com/questions/29111/what-technical-reasons-exist-for-not-using-space-characters-in-file-names>`_

path-too-long
*************

A file or directory in the distribution has a path that has too many characters.

Some operating systems have limits on path lengths, and distributions with longer paths
might not be installable on those systems.

By default, ``pydistcheck`` reports this check failure if it detects any paths longer than ``200`` characters.
This is primarily informed by the following limitations:

* many Windows systems limit the total filepath length (excluding drive specifiers like ``C://``) to 256 characters
* some older ``tar`` implementations will not support paths longer than 256 characters

See below for details.

> *Tarballs are only required to store paths of up to 100 bytes and cannot store those of more than 256 bytes*.

`R CMD check source code <https://github.com/wch/r-source/blob/29559f9bf4df2c55ef5eace203cbe335bbd03f2f/src/library/tools/R/check.R#L839>`__

> *...packages are normally distributed as tarballs, and these have a limit on path lengths: for maximal portability 100 bytes.*

`"Package Structure" (Writing R Extensions) <https://cran.r-project.org/doc/manuals/R-exts.html#Package-structure>`__

> *Windows historically has limited path lengths to 260 characters.*
> *This meant that paths longer than this would not resolve and errors would result.*
>
> *In the latest versions of Windows, this limitation can be expanded to approximately 32,000 characters.*
> *Your administrator will need to activate the ``“Enable Win32 long paths”`` group policy, or set ``LongPathsEnabled`` to 1 in the registry key ``HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem``.*
>
> *This allows the open() function, the os module and most other path functionality to accept and return paths longer than 260 characters.*

`"Removing the Max Path Limitation" (Python Windows docs) <https://docs.python.org/3/using/windows.html#removing-the-max-path-limitation>`__

> *Git has a limit of 4096 characters for a filename, except on Windows when Git is compiled with msys.*
> *It uses an older version of the Windows API and there's a limit of 260 characters for a filename.*
>
> *You can circumvent this by using another Git client on Windows or set ``core.longpaths`` to ``true``...*

`Filename too long in Git for Windows (Stack Overflow answer) <https://stackoverflow.com/a/22575737/3986677>`__

Other relevant discussions:

* `"Maximum Path Length" (Windows docs) <https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry>`__
* `"Comparison of Filesystems: Limits" (Wikipedia) <https://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits>`__
* `"Could the 100 byte path length limit be lifted?" (r-pkg-devel, 2023) <https://stat.ethz.ch/pipermail/r-package-devel/2023q4/010203.html>`__
* `"R CMD check NOTE - Long paths in package" (r-pkg-devel, 2015) <https://stat.ethz.ch/pipermail/r-package-devel/2015q4/000511.html>`__
* `"Filename length limits on linux?" (serverfault answer, 2009-2016) <https://serverfault.com/a/9548>`__
* `"Command prompt (Cmd. exe) command-line string limitation" (Windows docs, 2023) <https://learn.microsoft.com/en-us/troubleshoot/windows-client/shell-experience/command-line-string-limitation>`__
* `conda-build discussion about 255-character prefix limit (conda/conda-build#1482) <https://github.com/conda/conda-build/issues/1482#issuecomment-256530225>`__
* `discussion about paths lengths (Python Discourse, 2023) <https://discuss.python.org/t/you-can-now-download-pypi-locally/32662/8>`__

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
