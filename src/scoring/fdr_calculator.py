"""
FDR Calculator Module

Implements False Discovery Rate calculation using target-decoy approach.

The target-decoy strategy estimates FDR by searching against both:
- Target database (real sequences)
- Decoy database (reversed/shuffled sequences)

FDR = (# decoy hits) / (# target hits) at a given score threshold

Includes:
- Target-decoy FDR estimation
- Q-value calculation (minimum FDR at which PSM is accepted)
- Decoy sequence generation (peptide reversal)
- Benjamini-Hochberg FDR correction

Reference:
    Elias & Gygi (2007) "Target-decoy search strategy for increased
    confidence in large-scale protein identifications by mass spectrometry"

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 3 (Week 3)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DatabaseType(Enum):
    """Database type for PSMs"""
    TARGET = "target"
    DECOY = "decoy"


@dataclass
class PSM:
    """
    Peptide-Spectrum Match

    Attributes
    ----------
    spectrum_id : str
        Spectrum identifier (scan number)
    peptide_sequence : str
        Peptide sequence
    glycan_composition : str
        Glycan composition
    protein_id : str
        Protein identifier
    xcorr : float
        XCorr score
    sp_score : float
        Sp score
    ppm_error : float
        Precursor mass error (ppm)
    charge : int
        Precursor charge
    database_type : DatabaseType
        Target or decoy
    rank : int
        Rank within spectrum (1 = best)
    fdr : float
        False discovery rate at this score threshold
    q_value : float
        Minimum FDR at which PSM is accepted
    """
    spectrum_id: str
    peptide_sequence: str
    glycan_composition: str
    protein_id: str
    xcorr: float
    sp_score: float = 0.0
    ppm_error: float = 0.0
    charge: int = 2
    database_type: DatabaseType = DatabaseType.TARGET
    rank: int = 1
    fdr: float = 1.0
    q_value: float = 1.0

    def __repr__(self):
        return (
            f"PSM({self.peptide_sequence}+{self.glycan_composition}, "
            f"XCorr={self.xcorr:.4f}, FDR={self.fdr:.4f})"
        )


class FDRCalculator:
    """
    Calculate FDR using target-decoy approach

    Parameters
    ----------
    fdr_threshold : float
        FDR threshold for accepting PSMs (default: 0.01 = 1%)
    decoy_prefix : str
        Prefix for decoy protein IDs (default: "DECOY_")

    Examples
    --------
    >>> calculator = FDRCalculator(fdr_threshold=0.01)
    >>> decoy_peptide = calculator.generate_decoy_sequence("NGTIINEK")
    >>> print(decoy_peptide)  # "KEENITN" (reversed, keep N/C termini)
    >>>
    >>> psms_with_fdr = calculator.calculate_fdr(all_psms)
    >>> accepted = calculator.filter_by_fdr(psms_with_fdr, fdr_threshold=0.01)
    """

    def __init__(
        self,
        fdr_threshold: float = 0.01,
        decoy_prefix: str = "DECOY_"
    ):
        """Initialize FDR calculator"""
        self.fdr_threshold = fdr_threshold
        self.decoy_prefix = decoy_prefix

    def generate_decoy_sequence(
        self,
        sequence: str,
        method: str = "reverse"
    ) -> str:
        """
        Generate decoy peptide sequence

        Parameters
        ----------
        sequence : str
            Target peptide sequence
        method : str
            Decoy generation method (default: "reverse")
            Options: "reverse", "shuffle"

        Returns
        -------
        str
            Decoy sequence

        Notes
        -----
        SEQUEST-style reversal: reverse sequence but keep N-terminal
        and C-terminal residues in place to preserve tryptic properties.
        """
        if len(sequence) <= 2:
            return sequence[::-1]

        if method == "reverse":
            # Reverse middle, keep termini
            # This preserves tryptic cleavage properties
            decoy = sequence[0] + sequence[-2:0:-1] + sequence[-1]
        elif method == "shuffle":
            # Shuffle middle
            import random
            middle = list(sequence[1:-1])
            random.shuffle(middle)
            decoy = sequence[0] + ''.join(middle) + sequence[-1]
        else:
            # Simple reversal
            decoy = sequence[::-1]

        return decoy

    def calculate_fdr(
        self,
        psms: List[PSM],
        score_field: str = "xcorr"
    ) -> List[PSM]:
        """
        Calculate FDR for PSMs using target-decoy approach

        Parameters
        ----------
        psms : List[PSM]
            All PSMs (target and decoy)
        score_field : str
            Score field to use for ranking (default: "xcorr")

        Returns
        -------
        List[PSM]
            PSMs with FDR and Q-values calculated
        """
        if len(psms) == 0:
            return psms

        # Sort by score (descending)
        psms_sorted = sorted(
            psms,
            key=lambda x: getattr(x, score_field),
            reverse=True
        )

        # Calculate cumulative target and decoy counts
        n_target_cumulative = 0
        n_decoy_cumulative = 0

        # Calculate FDR at each PSM
        for i, psm in enumerate(psms_sorted):
            # Update counts
            if psm.database_type == DatabaseType.TARGET:
                n_target_cumulative += 1
            else:
                n_decoy_cumulative += 1

            # Calculate FDR
            if n_target_cumulative > 0:
                # FDR = decoys / targets
                fdr = n_decoy_cumulative / n_target_cumulative
            else:
                fdr = 1.0

            # Ensure FDR doesn't exceed 1.0
            fdr = min(fdr, 1.0)

            psm.fdr = fdr

        # Calculate Q-values (minimum FDR from this point forward)
        self._calculate_qvalues(psms_sorted)

        return psms_sorted

    def _calculate_qvalues(self, psms_sorted: List[PSM]):
        """
        Calculate Q-values (minimum FDR at which PSM would be accepted)

        Q-value is the minimum FDR threshold at which a PSM would be accepted.
        It's calculated as the minimum FDR from the current PSM to the end.

        Parameters
        ----------
        psms_sorted : List[PSM]
            PSMs sorted by score (descending)
        """
        # Start from the end (worst scores)
        min_fdr = 1.0

        for psm in reversed(psms_sorted):
            min_fdr = min(min_fdr, psm.fdr)
            psm.q_value = min_fdr

    def filter_by_fdr(
        self,
        psms: List[PSM],
        fdr_threshold: Optional[float] = None
    ) -> List[PSM]:
        """
        Filter PSMs by FDR threshold

        Parameters
        ----------
        psms : List[PSM]
            PSMs with FDR calculated
        fdr_threshold : float, optional
            FDR threshold (default: use self.fdr_threshold)

        Returns
        -------
        List[PSM]
            Accepted PSMs (target only, below FDR threshold)
        """
        if fdr_threshold is None:
            fdr_threshold = self.fdr_threshold

        accepted = [
            psm for psm in psms
            if psm.database_type == DatabaseType.TARGET
            and psm.q_value <= fdr_threshold
        ]

        return accepted

    def get_statistics(self, psms: List[PSM]) -> Dict:
        """
        Get FDR statistics

        Parameters
        ----------
        psms : List[PSM]
            All PSMs with FDR calculated

        Returns
        -------
        dict
            Statistics including counts at various FDR thresholds
        """
        target_psms = [p for p in psms if p.database_type == DatabaseType.TARGET]
        decoy_psms = [p for p in psms if p.database_type == DatabaseType.DECOY]

        # Count PSMs at different FDR thresholds
        fdr_thresholds = [0.001, 0.01, 0.05, 0.10]
        counts_at_fdr = {}

        for threshold in fdr_thresholds:
            accepted = self.filter_by_fdr(psms, fdr_threshold=threshold)
            counts_at_fdr[f"fdr_{threshold}"] = len(accepted)

        stats = {
            "total_psms": len(psms),
            "target_psms": len(target_psms),
            "decoy_psms": len(decoy_psms),
            "target_decoy_ratio": len(target_psms) / len(decoy_psms) if decoy_psms else 0,
            "counts_at_fdr": counts_at_fdr,
        }

        # XCorr statistics
        if target_psms:
            target_xcorrs = [p.xcorr for p in target_psms]
            stats["target_xcorr_mean"] = np.mean(target_xcorrs)
            stats["target_xcorr_median"] = np.median(target_xcorrs)

        if decoy_psms:
            decoy_xcorrs = [p.xcorr for p in decoy_psms]
            stats["decoy_xcorr_mean"] = np.mean(decoy_xcorrs)
            stats["decoy_xcorr_median"] = np.median(decoy_xcorrs)

        return stats

    def estimate_fdr_at_score(
        self,
        psms: List[PSM],
        score_threshold: float,
        score_field: str = "xcorr"
    ) -> float:
        """
        Estimate FDR at a given score threshold

        Parameters
        ----------
        psms : List[PSM]
            All PSMs
        score_threshold : float
            Score threshold
        score_field : str
            Score field (default: "xcorr")

        Returns
        -------
        float
            Estimated FDR
        """
        # Count targets and decoys above threshold
        targets_above = sum(
            1 for p in psms
            if p.database_type == DatabaseType.TARGET
            and getattr(p, score_field) >= score_threshold
        )

        decoys_above = sum(
            1 for p in psms
            if p.database_type == DatabaseType.DECOY
            and getattr(p, score_field) >= score_threshold
        )

        # Calculate FDR
        if targets_above > 0:
            fdr = decoys_above / targets_above
        else:
            fdr = 1.0

        return min(fdr, 1.0)
