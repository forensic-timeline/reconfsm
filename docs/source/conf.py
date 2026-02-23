# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ReconFSM'
copyright = '2026, Fawwaz Haidar, Hudan Studiawan, Baskoro Adi Pratomo, Arkananta Masarief, Kemal Tangguh Aji Rajasa'
author = 'Fawwaz Haidar, Hudan Studiawan, Baskoro Adi Pratomo, Arkananta Masarief, Kemal Tangguh Aji Rajasa'
release = '0.0.1'

import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Custom sidebar configuration to list all parts and remove relations (prev/next)
html_sidebars = {
    '**': ['globaltoc.html', 'searchbox.html']
}

html_theme_options = {
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}
