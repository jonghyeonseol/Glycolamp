"""
Preliminary Scorer (Sp) Module

Implements SEQUEST-style preliminary scoring for fast candidate filtering.

The Sp score is a simple shared-peak count with intensity weighting,
used to quickly filter candidates before the more expensive XCorr calculation.

Sp = Sum of (matched peak intensities)

This provides a fast first-pass filter to reduce the candidate pool
from thousands to hundreds before XCorr scoring.

Reference:
    Eng et al. (1994) "An approach to correlate tandem mass spectral data"
    SEQUEST uses Sp to rank top 500 candidates before XCorr

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 3 (Week 3)
"""

import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

from .spectrum_preprocessor import ProcessedSpectrum
from .theoretical_spectrum import TheoreticalPeak


@dataclass
class SpScore:
    """
    Preliminary score result

    Attributes
    ----------
    score : float
        Sp score (sum of matched intensities)
    matched_peaks : int
        Number of matched peaks
    total_theoretical_peaks : int
        Total theoretical peaks
    matched_intensity_fraction : float
        Fraction of total intensity matched
    """
    score: float
    matched_peaks: int
    total_theoretical_peaks: int
    matched_intensity_fraction: float

    def __repr__(self):
        return (
            f"SpScore(score={self.score:.2f}, "
            f"matched={self.matched_peaks}/{self.total_theoretical_peaks})"
        )


class SpScorer:
    """
    Calculate preliminary scores (Sp) for rapid candidate filtering

    Parameters
    ----------
    tolerance_da : float
        Mass tolerance in Daltons for peak matching (default: 0.5)
        This should match the bin size used in preprocessing
    intensity_weight : bool
        Weight matches by intensity (default: True)

    Examples
    --------
    >>> scorer = SpScorer(tolerance_da=0.5)
    >>> sp_score = scorer.score(observed_spectrum, theoretical_peaks)
    >>> print(f"Sp score: {sp_score.score:.2f}")
    """

    def __init__(
        self,
        tolerance_da: float = 0.5,
        intensity_weight: bool = True
    ):
        """Initialize Sp scorer"""
        self.tolerance_da = tolerance_da
        self.intensity_weight = intensity_weight

    def score(
        self,
        observed: ProcessedSpectrum,
        theoretical: List[TheoreticalPeak]
    ) -> SpScore:
        """
        Calculate Sp score

        Parameters
        ----------
        observed : ProcessedSpectrum
            Preprocessed observed spectrum
        theoretical : List[TheoreticalPeak]
            Theoretical peaks for candidate

        Returns
        -------
        SpScore
            Preliminary score

        Raises
        ------
        ValueError
            If observed spectrum is invalid or empty
        TypeError
            If inputs are not of expected types
        """
        # Input validation
        if not isinstance(observed, ProcessedSpectrum):
            raise TypeError(f"Expected ProcessedSpectrum, got {type(observed)}")

        if not isinstance(theoretical, list):
            raise TypeError(f"Expected list of TheoreticalPeak, got {type(theoretical)}")

        if observed.binned_intensities is None or len(observed.binned_intensities) == 0:
            raise ValueError("Observed spectrum has no binned intensities")

        if observed.num_bins <= 0:
            raise ValueError(f"Invalid number of bins: {observed.num_bins}")

        if len(theoretical) == 0:
            return SpScore(
                score=0.0,
                matched_peaks=0,
                total_theoretical_peaks=0,
                matched_intensity_fraction=0.0
            )

        try:
            # Match peaks
            matches, total_obs_intensity = self._match_peaks(observed, theoretical)
        except Exception as e:
            raise RuntimeError(f"Failed to match peaks: {str(e)}") from e

        # Calculate score
        try:
            if self.intensity_weight:
                # Sum of matched intensities from observed spectrum
                score = sum(intensity for _, intensity in matches)
            else:
                # Simple peak count
                score = float(len(matches))

            # Calculate matched intensity fraction
            matched_intensity_fraction = 0.0
            if total_obs_intensity > 0:
                matched_intensity = sum(intensity for _, intensity in matches)
                matched_intensity_fraction = matched_intensity / total_obs_intensity

            # Validate score is not negative
            if score < 0:
                raise ValueError(f"Calculated negative Sp score: {score}")

            return SpScore(
                score=score,
                matched_peaks=len(matches),
                total_theoretical_peaks=len(theoretical),
                matched_intensity_fraction=matched_intensity_fraction
            )
        except (ZeroDivisionError, ValueError) as e:
            raise RuntimeError(f"Failed to calculate Sp score: {str(e)}") from e

    def _match_peaks(
        self,
        observed: ProcessedSpectrum,
        theoretical: List[TheoreticalPeak]
    ) -> Tuple[List[Tuple[float, float]], float]:
        """
        Match theoretical peaks to observed spectrum

        Parameters
        ----------
        observed : ProcessedSpectrum
            Preprocessed spectrum
        theoretical : List[TheoreticalPeak]
            Theoretical peaks

        Returns
        -------
        Tuple[List[Tuple[float, float]], float]
            List of (mz, intensity) matches and total observed intensity
        """
        matches = []
        matched_bins = set()  # Track which bins have been matched

        # Calculate total observed intensity (for normalization)
        total_obs_intensity = np.sum(np.abs(observed.binned_intensities))

        for theo_peak in theoretical:
            # Get bin index for theoretical peak
            bin_idx = self._get_bin_index(theo_peak.mz, observed)

            if bin_idx < 0 or bin_idx >= observed.num_bins:
                continue

            # Skip if this bin was already matched
            if bin_idx in matched_bins:
                continue

            # Check for match within tolerance
            obs_intensity = observed.binned_intensities[bin_idx]

            if obs_intensity > 0:  # Peak present in observed spectrum
                matches.append((theo_peak.mz, obs_intensity))
                matched_bins.add(bin_idx)

        return matches, total_obs_intensity

    def _get_bin_index(self, mz: float, observed: ProcessedSpectrum) -> int:
        """
        Get bin index for m/z value

        Parameters
        ----------
        mz : float
            m/z value
        observed : ProcessedSpectrum
            Observed spectrum with binning info

        Returns
        -------
        int
            Bin index
        """
        if mz < observed.min_mz or mz > observed.max_mz:
            return -1

        bin_idx = int((mz - observed.min_mz) / observed.bin_size)
        return min(bin_idx, observed.num_bins - 1)

    def rank_candidates(
        self,
        observed: ProcessedSpectrum,
        candidates_with_spectra: List[Tuple[any, List[TheoreticalPeak]]],
        top_n: int = 500
    ) -> List[Tuple[any, SpScore]]:
        """
        Score and rank multiple candidates, returning top N

        This is the primary use case for Sp - rapid filtering of candidates.

        Parameters
        ----------
        observed : ProcessedSpectrum
            Preprocessed observed spectrum
        candidates_with_spectra : List[Tuple[any, List[TheoreticalPeak]]]
            List of (candidate, theoretical_peaks) tuples
        top_n : int
            Number of top candidates to return (default: 500)

        Returns
        -------
        List[Tuple[any, SpScore]]
            Top N candidates with their Sp scores, sorted by score (descending)
        """
        scored_candidates = []

        for candidate, theoretical in candidates_with_spectra:
            sp_score = self.score(observed, theoretical)
            scored_candidates.append((candidate, sp_score))

        # Sort by Sp score (descending)
        scored_candidates.sort(key=lambda x: x[1].score, reverse=True)

        # Return top N
        return scored_candidates[:top_n]
