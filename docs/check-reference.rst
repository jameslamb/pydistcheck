Check Reference
===============

This page describes each of the checks that ``pydistcheck`` performs.
The section headings correspond to the error codes printed in ``pydistcheck``'s output.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

distro-too-large-compressed
***************************

Indicates that the package distribution is larger (compressed) than the allowed size.

Change that limit using configuration option ``max-distro-size-compressed``.

too-many-files
**************

``too-many-files`` is raised whenever ``pydistcheck`` encounters a package distribution
that contains more than the allowed number of files.

This is a very very rough way to detect that unexpected files have been included in a new release of a project.

``pydistcheck`` defaults to raising this error when a distribution has more than 2000 files...a totally arbitrary number chosen by the author.

To change that limit, use configuration option ``max-allowed-files``.
