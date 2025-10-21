"""
File Conversion Module

Handles conversion of proprietary mass spectrometry formats to open standards.
- RAW → mzML conversion (ThermoRawFileParser)
- mzML parsing and spectrum extraction (Pyteomics)
"""

from .raw_converter import RawConverter
from .mzml_parser import MzMLParser

__all__ = ["RawConverter", "MzMLParser"]
