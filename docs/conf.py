"""Sphinx documentation, built independently of the monitoring service."""

import tomllib
from pathlib import Path

metadata = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())
project = "AIO Server Status"
author = "hotchilipowder"
copyright = "2026, hotchilipowder"
release = metadata["project"]["version"]
version = release
language = "zh_CN"

extensions = ["myst_parser", "sphinx.ext.githubpages"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
exclude_patterns = ["_build", "plans", "Thumbs.db", ".DS_Store"]
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3

html_theme = "furo"
html_title = f"{project} {release}"
html_theme_options = {
    "light_css_variables": {"color-brand-primary": "#17745c", "color-brand-content": "#17745c"},
    "dark_css_variables": {"color-brand-primary": "#5cd9b3", "color-brand-content": "#5cd9b3"},
}
html_show_sourcelink = False
