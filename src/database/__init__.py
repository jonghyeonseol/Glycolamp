"""
Database Module

Handles protein/peptide database parsing and glycan composition management
for glycopeptide identification.

Modules:
- fasta_parser: Parse FASTA files and perform in-silico digestion
- glycan_database: Manage glycan composition library
- candidate_generator: Match precursor m/z to glycopeptide candidates

Phase: 2 (Week 2)
Status: In Development
"""

from .fasta_parser import FastaParser, Peptide, Protein
from .glycan_database import GlycanDatabase, Glycan, GlycanType
from .candidate_generator import CandidateGenerator, GlycopeptideCandidate

__all__ = [
    "FastaParser",
    "Peptide",
    "Protein",
    "GlycanDatabase",
    "Glycan",
    "GlycanType",
    "CandidateGenerator",
    "GlycopeptideCandidate",
]
