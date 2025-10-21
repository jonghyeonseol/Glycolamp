"""
Chemoinformatics Module

Converts glycopeptides to SMILES format for machine learning applications.

Modules:
- peptide_smiles: Peptide sequence → SMILES
- glycan_smiles: Glycan composition → SMILES
- glycopeptide_smiles: Combined glycopeptide SMILES

Features:
- RDKit integration for structure validation
- Molecular weight calculation
- CSV export with SMILES columns
- Batch processing support

Phase: 4 (Week 4)
Status: Complete
"""

from .peptide_smiles import PeptideSMILESConverter, PeptideSMILES
from .glycan_smiles import GlycanSMILESConverter, GlycanSMILES
from .glycopeptide_smiles import GlycopeptideSMILESGenerator, GlycopeptideSMILES

__all__ = [
    "PeptideSMILESConverter",
    "PeptideSMILES",
    "GlycanSMILESConverter",
    "GlycanSMILES",
    "GlycopeptideSMILESGenerator",
    "GlycopeptideSMILES",
]
