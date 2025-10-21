"""
Scoring Module

Implements SEQUEST-inspired scoring algorithms for glycopeptide identification:
- Spectrum preprocessing (binning, normalization)
- Theoretical spectrum generation (b/y, B/Y, oxonium ions)
- Preliminary scoring (Sp)
- Cross-correlation scoring (XCorr)
- FDR calculation (target-decoy)

Phase: 3 (Week 3)
Status: In Development
"""

from .spectrum_preprocessor import SpectrumPreprocessor, ProcessedSpectrum
from .theoretical_spectrum import TheoreticalSpectrumGenerator, TheoreticalPeak
from .sp_scorer import SpScorer, SpScore
from .xcorr_scorer import XCorrScorer, XCorrScore
from .fdr_calculator import FDRCalculator, PSM, DatabaseType

__all__ = [
    "SpectrumPreprocessor",
    "ProcessedSpectrum",
    "TheoreticalSpectrumGenerator",
    "TheoreticalPeak",
    "SpScorer",
    "SpScore",
    "XCorrScorer",
    "XCorrScore",
    "FDRCalculator",
    "PSM",
    "DatabaseType",
]
