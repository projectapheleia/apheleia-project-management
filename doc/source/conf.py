# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import re
import sys

sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'apheleia-project-management'
copyright = '2026, apheleia'
author = 'apheleia'

# Read out of pyproject.toml rather than written here, so that it cannot fall
# behind the released version. Not taken from the installed package, because an
# editable install reports the version it was last installed at, not the one in
# the tree.
with open(os.path.join(os.path.dirname(__file__), '..', '..', 'pyproject.toml')) as f:
    release = re.search(r'^version = "(.*?)"', f.read(), re.MULTILINE).group(1)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.autosummary'
]

templates_path = ['_templates']
exclude_patterns = []

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

graphviz_output_format = 'svg'
html_theme = 'sphinx_rtd_theme'

# -- Options for LaTeX (PDF) output -------------------------------------------
latex_elements = {
    # Paper size
    'papersize': 'a4paper',

    # Font size
    'pointsize': '11pt',

    # Additional LaTeX preamble
    'preamble': r'''
\usepackage{amsmath}
\usepackage{amssymb}
''',

    # Figure alignment
    'figure_align': 'H',
}

# Name of the master document
master_doc = 'index'
