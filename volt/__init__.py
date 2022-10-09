"""
    A versatile static website generator.

    :copyright: (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>
    :license: BSD

"""
from .config import SiteConfig  # noqa: F401
from .resource import (  # noqa: F401
    Engine,
    MarkdownSource,
    Target,
    TemplateTarget,
    CopyTarget,
)

NAME = "volt"

__author__ = "Wibowo Arindrarto"
__contact__ = "contact@arindrarto.dev"
__homepage__ = "https://github.com/bow/volt"
__version__ = "0.0.0"
