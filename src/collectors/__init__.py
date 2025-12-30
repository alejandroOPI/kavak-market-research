"""
Data collectors for various sources
"""
from .autocosmos import AutocosmosScraper
from .inegi import INEGICollector

__all__ = ["INEGICollector", "AutocosmosScraper"]
