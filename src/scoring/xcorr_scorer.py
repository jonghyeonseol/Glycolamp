"""
Cross-Correlation Scorer (XCorr) Module

Implements SEQUEST-style cross-correlation scoring using FFT.

XCorr measures the similarity between observed and theoretical spectra
by calculating the cross-correlation at different mass shifts (lags).

The final XCorr score is the correlation at lag 0 minus the average
correlation at other lags (background subtraction).

This is computationally expensive, so it's only applied to top candidates
after Sp filtering.

Reference:
    Eng et al. (1994) "An approach to correlate tandem mass spectral data"
    Uses FFT for efficient cross-correlation calculation

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 3 (Week 3)
"""

import numpy as np
from typing import List
from dataclasses import dataclass

from .spectrum_preprocessor import ProcessedSpectrum
from .theoretical_spectrum import TheoreticalPeak


@dataclass
class XCorrScore:
    """
    Cross-correlation score result

    Attributes
    ----------
    xcorr : float
        Final XCorr score (correlation at lag 0 minus background)
    raw_correlation : float
        Raw correlation at lag 0
    background : float
        Average correlation at non-zero lags
    matched_peaks : int
        Number of matched peaks
    """
    xcorr: float
    raw_correlation: float
    background: float
    matched_peaks: int

    def __repr__(self):
        return f"XCorrScore(xcorr={self.xcorr:.4f}, matched={self.matched_peaks})"


class XCorrScorer:
    """
    Calculate XCorr scores using FFT-based cross-correlation

    Parameters
    ----------
    lag_range : int
        Range of lags to exclude from background calculation (default: 75)
        SEQUEST uses ±75 bins around lag 0
    bin_size : float
        Bin size for spectra (default: 1.0005 Da)

    Examples
    --------
    >>> scorer = XCorrScorer()
    >>> xcorr = scorer.score(observed_spectrum, theoretical_peaks)
    >>> print(f"XCorr: {xcorr.xcorr:.4f}")
    """

    def __init__(
        self,
        lag_range: int = 75,
        bin_size: float = 1.0005
    ):
        """Initialize XCorr scorer"""
        self.lag_range = lag_range
        self.bin_size = bin_size

    def score(
        self,
        observed: ProcessedSpectrum,
        theoretical: List[TheoreticalPeak]
    ) -> XCorrScore:
        """
        Calculate XCorr score

        Parameters
        ----------
        observed : ProcessedSpectrum
            Preprocessed observed spectrum (already normalized)
        theoretical : List[TheoreticalPeak]
            Theoretical peaks for candidate

        Returns
        -------
        XCorrScore
            Cross-correlation score
        """
        if len(theoretical) == 0:
            return XCorrScore(
                xcorr=0.0,
                raw_correlation=0.0,
                background=0.0,
                matched_peaks=0
            )

        # Convert theoretical peaks to binned spectrum
        theoretical_binned = self._create_theoretical_binned(
            theoretical,
            observed.bin_size,
            observed.min_mz,
            observed.max_mz,
            observed.num_bins
        )

        # Calculate cross-correlation using FFT
        correlation = self._cross_correlate_fft(
            observed.binned_intensities,
            theoretical_binned
        )

        # Get correlation at lag 0 (center of correlation array)
        lag_0_idx = len(correlation) // 2
        raw_correlation = correlation[lag_0_idx]

        # Calculate background (average correlation excluding lag range)
        background = self._calculate_background(correlation, lag_0_idx)

        # Final XCorr = correlation at lag 0 - background
        xcorr = raw_correlation - background

        # Count matched peaks (non-zero overlap)
        matched_peaks = self._count_matched_peaks(
            observed.binned_intensities,
            theoretical_binned
        )

        return XCorrScore(
            xcorr=xcorr,
            raw_correlation=raw_correlation,
            background=background,
            matched_peaks=matched_peaks
        )

    def _create_theoretical_binned(
        self,
        theoretical: List[TheoreticalPeak],
        bin_size: float,
        min_mz: float,
        max_mz: float,
        num_bins: int
    ) -> np.ndarray:
        """
        Convert theoretical peaks to binned array

        Parameters
        ----------
        theoretical : List[TheoreticalPeak]
            Theoretical peaks
        bin_size : float
            Bin size (Da)
        min_mz : float
            Minimum m/z
        max_mz : float
            Maximum m/z
        num_bins : int
            Number of bins

        Returns
        -------
        np.ndarray
            Binned theoretical spectrum
        """
        binned = np.zeros(num_bins)

        for peak in theoretical:
            if min_mz <= peak.mz <= max_mz:
                bin_idx = int((peak.mz - min_mz) / bin_size)
                if 0 <= bin_idx < num_bins:
                    # Use theoretical intensity
                    binned[bin_idx] += peak.intensity

        return binned

    def _cross_correlate_fft(
        self,
        observed: np.ndarray,
        theoretical: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cross-correlation using FFT (fast)

        Cross-correlation in spatial domain = multiplication in frequency domain
        xcorr(x, y) = IFFT(FFT(x) * conj(FFT(y)))

        Parameters
        ----------
        observed : np.ndarray
            Observed spectrum (binned, normalized)
        theoretical : np.ndarray
            Theoretical spectrum (binned)

        Returns
        -------
        np.ndarray
            Cross-correlation at all lags
        """
        # Ensure same length
        assert len(observed) == len(theoretical), "Spectra must have same length"

        # FFT of both spectra
        obs_fft = np.fft.fft(observed)
        theo_fft = np.fft.fft(theoretical)

        # Cross-correlation in frequency domain
        # Multiply FFT(observed) by conjugate of FFT(theoretical)
        cross_fft = obs_fft * np.conj(theo_fft)

        # IFFT to get correlation in spatial domain
        correlation = np.fft.ifft(cross_fft).real

        # Shift to center (lag 0 at center)
        correlation = np.fft.fftshift(correlation)

        return correlation

    def _calculate_background(
        self,
        correlation: np.ndarray,
        lag_0_idx: int
    ) -> float:
        """
        Calculate background correlation (average excluding lag range)

        Parameters
        ----------
        correlation : np.ndarray
            Cross-correlation at all lags
        lag_0_idx : int
            Index of lag 0

        Returns
        -------
        float
            Background correlation
        """
        # Exclude ±lag_range bins around lag 0
        start_exclude = max(0, lag_0_idx - self.lag_range)
        end_exclude = min(len(correlation), lag_0_idx + self.lag_range + 1)

        # Create mask for background region
        mask = np.ones(len(correlation), dtype=bool)
        mask[start_exclude:end_exclude] = False

        # Calculate mean of background region
        if np.sum(mask) > 0:
            background = np.mean(correlation[mask])
        else:
            background = 0.0

        return background

    def _count_matched_peaks(
        self,
        observed: np.ndarray,
        theoretical: np.ndarray
    ) -> int:
        """
        Count number of matched peaks (both non-zero)

        Parameters
        ----------
        observed : np.ndarray
            Observed spectrum
        theoretical : np.ndarray
            Theoretical spectrum

        Returns
        -------
        int
            Number of matched peaks
        """
        # Both arrays must be non-zero
        matched = (observed != 0) & (theoretical != 0)
        return int(np.sum(matched))

    def rank_candidates(
        self,
        observed: ProcessedSpectrum,
        candidates_with_spectra: List[tuple],
        return_all: bool = False
    ) -> List[tuple]:
        """
        Score and rank candidates by XCorr

        Parameters
        ----------
        observed : ProcessedSpectrum
            Preprocessed observed spectrum
        candidates_with_spectra : List[tuple]
            List of (candidate, theoretical_peaks) or
            (candidate, theoretical_peaks, sp_score) tuples
        return_all : bool
            Return all candidates (default: False, returns only positive XCorr)

        Returns
        -------
        List[tuple]
            Candidates with XCorr scores, sorted by XCorr (descending)
        """
        scored_candidates = []

        for item in candidates_with_spectra:
            # Handle both (candidate, theoretical) and (candidate, theoretical, sp_score)
            if len(item) == 2:
                candidate, theoretical = item
                sp_score = None
            else:
                candidate, theoretical, sp_score = item[:3]

            xcorr_score = self.score(observed, theoretical)

            if sp_score is not None:
                scored_candidates.append((candidate, xcorr_score, sp_score))
            else:
                scored_candidates.append((candidate, xcorr_score))

        # Sort by XCorr (descending)
        scored_candidates.sort(
            key=lambda x: x[1].xcorr if isinstance(x[1], XCorrScore) else x[1],
            reverse=True
        )

        # Filter to positive XCorr unless return_all
        if not return_all:
            scored_candidates = [
                item for item in scored_candidates
                if (item[1].xcorr if isinstance(item[1], XCorrScore) else item[1]) > 0
            ]

        return scored_candidates
