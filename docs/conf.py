# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import datetime, timezone

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pydistcheck"
current_year = datetime.now(tz=timezone.utc).year
copyright = f"2022-{current_year}, James Lamb"  # noqa: A001
author = "James Lamb"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_click"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Options for linkcheck -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-linkcheck_anchors_ignore_for_url
linkcheck_anchors_ignore_for_url = [
    "https://github.com/conda/conda-build.*",
    "https://github.com/pypi/support/blob/.*",
]
