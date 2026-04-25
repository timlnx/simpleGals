project = "simpleGals"
copyright = "2026, timlnx"
author = "timlnx"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
]

html_theme = "sphinx_rtd_theme"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# exclude design specs and internal planning docs from the built docs
exclude_patterns = ["_build", "superpowers/**"]
