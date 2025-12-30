"""
Data collectors for various sources
"""
from .autocosmos import AutocosmosScraper
from .inegi import INEGICollector
from .inegi_pdf_parser import parse_raiavl_bulletin, RAIAVLMonthlyData

__all__ = ["INEGICollector", "AutocosmosScraper", "parse_raiavl_bulletin", "RAIAVLMonthlyData"]
