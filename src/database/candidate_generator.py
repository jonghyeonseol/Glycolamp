"""
Candidate Generator Module

Matches observed precursor m/z values to theoretical glycopeptide candidates
by combining peptides and glycans within mass tolerance.

Features:
- Precursor mass calculation from m/z and charge
- PPM error calculation
- Mass matching with tolerance
- Glycosylation site validation
- Candidate ranking

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 2 (Week 2)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from .fasta_parser import Peptide
from .glycan_database import Glycan


# Physical constants
PROTON_MASS = 1.007276  # Da


@dataclass
class GlycopeptideCandidate:
    """
    Represents a glycopeptide candidate match

    Attributes
    ----------
    peptide : Peptide
        Peptide component
    glycan : Glycan
        Glycan component
    theoretical_mass : float
        Theoretical neutral mass (Da)
    observed_mz : float
        Observed precursor m/z
    charge : int
        Precursor charge state
    ppm_error : float
        Mass accuracy (ppm)
    glycosylation_site : int
        Position of glycosylation in peptide (0-indexed)
    score : float
        Candidate score (for ranking)
    """
    peptide: Peptide
    glycan: Glycan
    theoretical_mass: float
    observed_mz: float
    charge: int
    ppm_error: float
    glycosylation_site: int = 0
    score: float = 0.0

    def __repr__(self):
        return (
            f"GlycopeptideCandidate(pep='{self.peptide.sequence}', "
            f"glycan='{self.glycan.composition}', "
            f"ppm={self.ppm_error:.2f})"
        )


class CandidateGenerator:
    """
    Generate glycopeptide candidates by mass matching

    Parameters
    ----------
    peptides : List[Peptide]
        Peptide library (from FASTA digestion)
    glycans : List[Glycan]
        Glycan library

    Examples
    --------
    >>> generator = CandidateGenerator(peptides, glycans)
    >>> candidates = generator.generate_candidates(
    ...     precursor_mz=1523.7245,
    ...     charge=2,
    ...     tolerance_ppm=10.0
    ... )
    >>> print(f"Found {len(candidates)} candidates")
    """

    def __init__(self, peptides: List[Peptide], glycans: List[Glycan]):
        """Initialize candidate generator"""
        self.peptides = peptides
        self.glycans = glycans

        # Pre-compute all possible glycopeptide masses for faster matching
        self._glycopeptide_masses: List[Tuple[float, Peptide, Glycan]] = []
        self._build_mass_index()

    def _build_mass_index(self):
        """
        Pre-compute all glycopeptide masses

        This creates an index for binary search during candidate generation.
        Only includes peptides with glycosylation sites.
        """
        self._glycopeptide_masses = []

        # Only consider peptides with glycosylation sites
        glyco_peptides = [p for p in self.peptides if p.has_glycosylation_site]

        for peptide in glyco_peptides:
            for glycan in self.glycans:
                total_mass = peptide.mass + glycan.mass
                self._glycopeptide_masses.append((total_mass, peptide, glycan))

        # Sort by mass for binary search
        self._glycopeptide_masses.sort(key=lambda x: x[0])

    def calculate_neutral_mass(self, precursor_mz: float, charge: int) -> float:
        """
        Calculate neutral mass from m/z and charge

        M = (m/z × z) - (z × proton_mass)

        Parameters
        ----------
        precursor_mz : float
            Observed m/z value
        charge : int
            Charge state

        Returns
        -------
        float
            Neutral mass (Da)
        """
        return (precursor_mz * charge) - (charge * PROTON_MASS)

    def calculate_ppm_error(self, theoretical_mass: float, observed_mass: float) -> float:
        """
        Calculate ppm error

        PPM = ((observed - theoretical) / theoretical) × 10^6

        Parameters
        ----------
        theoretical_mass : float
            Theoretical mass (Da)
        observed_mass : float
            Observed mass (Da)

        Returns
        -------
        float
            PPM error
        """
        return ((observed_mass - theoretical_mass) / theoretical_mass) * 1e6

    def generate_candidates(
        self,
        precursor_mz: float,
        charge: int,
        tolerance_ppm: float = 10.0,
        max_candidates: int = 5000
    ) -> List[GlycopeptideCandidate]:
        """
        Generate glycopeptide candidates for a precursor

        Parameters
        ----------
        precursor_mz : float
            Observed precursor m/z
        charge : int
            Precursor charge state
        tolerance_ppm : float
            Mass tolerance in ppm (default: 10.0)
        max_candidates : int
            Maximum number of candidates to return (default: 5000)

        Returns
        -------
        List[GlycopeptideCandidate]
            Matched candidates, sorted by ppm error
        """
        # Calculate neutral mass
        observed_mass = self.calculate_neutral_mass(precursor_mz, charge)

        # Calculate mass window
        mass_tolerance_da = (tolerance_ppm / 1e6) * observed_mass

        # Find candidates within tolerance
        candidates = []

        for theoretical_mass, peptide, glycan in self._glycopeptide_masses:
            # Check if within tolerance
            mass_diff = abs(theoretical_mass - observed_mass)
            if mass_diff <= mass_tolerance_da:
                # Calculate ppm error
                ppm_error = self.calculate_ppm_error(theoretical_mass, observed_mass)

                # Create candidate
                # Use first glycosylation site (could be extended to try all sites)
                glyco_site = peptide.glycosylation_sites[0] if peptide.glycosylation_sites else 0

                candidate = GlycopeptideCandidate(
                    peptide=peptide,
                    glycan=glycan,
                    theoretical_mass=theoretical_mass,
                    observed_mz=precursor_mz,
                    charge=charge,
                    ppm_error=ppm_error,
                    glycosylation_site=glyco_site,
                    score=abs(ppm_error)  # Lower is better
                )

                candidates.append(candidate)

        # Sort by ppm error (best matches first)
        candidates.sort(key=lambda c: abs(c.ppm_error))

        # Limit to max_candidates
        return candidates[:max_candidates]

    def filter_by_glycosylation_sites(
        self,
        candidates: List[GlycopeptideCandidate]
    ) -> List[GlycopeptideCandidate]:
        """
        Filter candidates to ensure glycosylation site is valid

        Parameters
        ----------
        candidates : List[GlycopeptideCandidate]
            Candidates to filter

        Returns
        -------
        List[GlycopeptideCandidate]
            Filtered candidates with valid glycosylation sites
        """
        return [c for c in candidates if c.peptide.has_glycosylation_site]

    def get_statistics(self, candidates: List[GlycopeptideCandidate]) -> Dict:
        """
        Get statistics about candidates

        Parameters
        ----------
        candidates : List[GlycopeptideCandidate]
            Candidates to analyze

        Returns
        -------
        dict
            Statistics
        """
        if not candidates:
            return {
                "total_candidates": 0,
                "unique_peptides": 0,
                "unique_glycans": 0,
                "ppm_error_range": (0, 0),
                "average_ppm_error": 0,
            }

        ppm_errors = [abs(c.ppm_error) for c in candidates]
        unique_peptides = set(c.peptide.sequence for c in candidates)
        unique_glycans = set(c.glycan.composition for c in candidates)

        return {
            "total_candidates": len(candidates),
            "unique_peptides": len(unique_peptides),
            "unique_glycans": len(unique_glycans),
            "ppm_error_range": (min(ppm_errors), max(ppm_errors)),
            "average_ppm_error": np.mean(ppm_errors),
            "median_ppm_error": np.median(ppm_errors),
        }

    def get_index_size(self) -> Dict:
        """
        Get size information about the mass index

        Returns
        -------
        dict
            Index statistics
        """
        return {
            "total_glycopeptides": len(self._glycopeptide_masses),
            "total_peptides": len(self.peptides),
            "glyco_peptides": sum(1 for p in self.peptides if p.has_glycosylation_site),
            "total_glycans": len(self.glycans),
            "memory_estimate_mb": len(self._glycopeptide_masses) * 32 / 1024 / 1024,  # Rough estimate
        }
