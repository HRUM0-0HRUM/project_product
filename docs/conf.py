import sys
import os

sys.path.insert(0, os.path.abspath('..'))

project = 'grocery-bot'
copyright = '2025, Ердякова М.А., Козлова П.Д., Скорик Е.В.'
author = 'Ердякова М.А., Козлова П.Д., Скорик Е.В.'
version = '1.0.0'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',     
    'sphinx.ext.napoleon',    
    'sphinx.ext.viewcode',    
    'sphinx.ext.githubpages',  
]

templates_path = ['_templates']
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}


sys.path.insert(0, os.path.abspath('../bot'))