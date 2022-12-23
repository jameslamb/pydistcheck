Check Reference
===============

This page describes each of the checks that ``pydistcheck`` performs.
The section headings correspond to the error codes printed in ``pydistcheck``'s output.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

distro-too-large-compressed
***************************

The package distribution is larger (compressed) than the allowed size.

Change that limit using configuration option ``max-distro-size-compressed``.

distro-too-large-uncompressed
*****************************

The package distribution is larger (uncompressed) than the allowed size.

Change that limit using configuration option ``max-distro-size-uncompressed``.

executable-files
****************

The package distribution contains executable files.

It shouldn't be necessary to include executable files in a Python distribution, and their
inclusion can lead to packages by flagged by security scanning tools.

Executable-ness is tracked in files' content on disk, and therefore in source control.
On a Unix-like operating system, use ``chmod`` to reduce the affected files' permissions, and re-build the affected distributions.

For more information, see:

* `"Understanding Linux File Permissions" (Linux Foundation blog) <https://www.linuxfoundation.org/blog/blog/classic-sysadmin-understanding-linux-file-permissions>`_
* `"Package Structure" (CRAN docs) <https://cran.r-project.org/doc/manuals/R-exts.html#Package-structure>`_

files-only-differ-by-case
*************************

The package distribution contains filepaths which are identical after lowercasing.

Such paths are not portable, as some filesystems (notably macOS), are case-insensitive.

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
