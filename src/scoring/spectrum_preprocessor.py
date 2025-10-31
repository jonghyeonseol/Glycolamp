"""
Spectrum Preprocessor Module

Implements SEQUEST-style spectrum preprocessing for MS/MS data:
1. Binning (0.5 Da bins, typically 0-2000 Da range)
2. Square root intensity transformation
3. Regional normalization (10 regions)
4. Noise filtering (remove low-intensity peaks)

This preprocessing improves XCorr scoring by:
- Reducing dynamic range of intensities
- Normalizing different spectral regions
- Removing noise peaks

Reference:
    Eng et al. (1994) "An approach to correlate tandem mass spectral data
    of peptides with amino acid sequences in a protein database"
    J Am Soc Mass Spectrom 5(11):976-89

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 3 (Week 3)
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ProcessedSpectrum:
    """
    Represents a preprocessed MS/MS spectrum

    Attributes
    ----------
    binned_intensities : np.ndarray
        Binned and normalized intensities
    bin_size : float
        Size of each bin (Da)
    min_mz : float
        Minimum m/z value
    max_mz : float
        Maximum m/z value
    num_bins : int
        Total number of bins
    num_peaks_original : int
        Number of peaks in original spectrum
    num_peaks_retained : int
        Number of peaks after filtering
    """
    binned_intensities: np.ndarray
    bin_size: float
    min_mz: float
    max_mz: float
    num_bins: int
    num_peaks_original: int
    num_peaks_retained: int

    def __repr__(self):
        return (
            f"ProcessedSpectrum(bins={self.num_bins}, "
            f"peaks={self.num_peaks_retained}/{self.num_peaks_original})"
        )


class SpectrumPreprocessor:
    """
    Preprocess MS/MS spectra using SEQUEST-style normalization

    Parameters
    ----------
    bin_size : float
        Size of m/z bins in Daltons (default: 1.0005)
        SEQUEST uses 1.0005 to avoid systematic binning errors
    min_mz : float
        Minimum m/z to bin (default: 0.0)
    max_mz : float
        Maximum m/z to bin (default: 2000.0)
    num_regions : int
        Number of regions for normalization (default: 10)
    noise_filter_percentile : float
        Percentile threshold for noise filtering (default: 5.0)
        Peaks below this percentile intensity are removed

    Examples
    --------
    >>> preprocessor = SpectrumPreprocessor()
    >>> mz = np.array([100.5, 200.3, 300.7, 400.2])
    >>> intensity = np.array([1000, 5000, 3000, 2000])
    >>> processed = preprocessor.process(mz, intensity)
    >>> print(processed.num_bins)
    """

    def __init__(
        self,
        bin_size: float = 1.0005,
        min_mz: float = 0.0,
        max_mz: float = 2000.0,
        num_regions: int = 10,
        noise_filter_percentile: float = 5.0
    ):
        """Initialize spectrum preprocessor"""
        self.bin_size = bin_size
        self.min_mz = min_mz
        self.max_mz = max_mz
        self.num_regions = num_regions
        self.noise_filter_percentile = noise_filter_percentile

        # Calculate number of bins
        self.num_bins = int((max_mz - min_mz) / bin_size) + 1

    def process(
        self,
        mz_array: np.ndarray,
        intensity_array: np.ndarray,
        precursor_mz: Optional[float] = None
    ) -> ProcessedSpectrum:
        """
        Process MS/MS spectrum with SEQUEST-style normalization

        Parameters
        ----------
        mz_array : np.ndarray
            m/z values of peaks
        intensity_array : np.ndarray
            Intensity values of peaks
        precursor_mz : float, optional
            Precursor m/z (to remove precursor peak if needed)

        Returns
        -------
        ProcessedSpectrum
            Preprocessed spectrum with binned and normalized intensities

        Raises
        ------
        ValueError
            If input arrays are invalid (empty, mismatched lengths, negative values)
        TypeError
            If inputs are not numpy arrays
        RuntimeError
            If preprocessing fails
        """
        # Input validation
        if not isinstance(mz_array, np.ndarray):
            raise TypeError(f"mz_array must be numpy array, got {type(mz_array)}")

        if not isinstance(intensity_array, np.ndarray):
            raise TypeError(f"intensity_array must be numpy array, got {type(intensity_array)}")

        if len(mz_array) == 0:
            raise ValueError("Empty m/z array provided")

        if len(intensity_array) == 0:
            raise ValueError("Empty intensity array provided")

        if len(mz_array) != len(intensity_array):
            raise ValueError(
                f"Array length mismatch: mz_array ({len(mz_array)}) "
                f"vs intensity_array ({len(intensity_array)})"
            )

        if np.any(mz_array < 0):
            raise ValueError("Negative m/z values detected")

        if np.any(intensity_array < 0):
            raise ValueError("Negative intensity values detected")

        if precursor_mz is not None and precursor_mz < 0:
            raise ValueError(f"Invalid precursor m/z: {precursor_mz}")

        num_peaks_original = len(mz_array)

        try:
            # Step 1: Remove precursor peak if specified
            if precursor_mz is not None:
                mz_array, intensity_array = self._remove_precursor(
                    mz_array, intensity_array, precursor_mz
                )

            # Step 2: Filter noise peaks
            mz_array, intensity_array = self._filter_noise(mz_array, intensity_array)
            num_peaks_retained = len(mz_array)

            if num_peaks_retained == 0:
                raise ValueError("All peaks were filtered out during noise removal")

            # Step 3: Square root transformation
            intensity_array = self._sqrt_transform(intensity_array)

            # Step 4: Binning
            binned = self._bin_spectrum(mz_array, intensity_array)

            # Step 5: Regional normalization
            binned = self._regional_normalization(binned)

            return ProcessedSpectrum(
                binned_intensities=binned,
                bin_size=self.bin_size,
                min_mz=self.min_mz,
                max_mz=self.max_mz,
                num_bins=self.num_bins,
                num_peaks_original=num_peaks_original,
                num_peaks_retained=num_peaks_retained
            )
        except (ValueError, TypeError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Spectrum preprocessing failed: {str(e)}") from e

    def _remove_precursor(
        self,
        mz_array: np.ndarray,
        intensity_array: np.ndarray,
        precursor_mz: float,
        tolerance_da: float = 15.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove precursor peak and isotopes

        Parameters
        ----------
        mz_array : np.ndarray
            m/z values
        intensity_array : np.ndarray
            Intensity values
        precursor_mz : float
            Precursor m/z
        tolerance_da : float
            Tolerance window around precursor (default: 15 Da)

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            Filtered m/z and intensity arrays
        """
        # Remove peaks within tolerance of precursor
        mask = np.abs(mz_array - precursor_mz) > tolerance_da
        return mz_array[mask], intensity_array[mask]

    def _filter_noise(
        self,
        mz_array: np.ndarray,
        intensity_array: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Filter noise peaks below percentile threshold

        Parameters
        ----------
        mz_array : np.ndarray
            m/z values
        intensity_array : np.ndarray
            Intensity values

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            Filtered arrays
        """
        if len(intensity_array) == 0:
            return mz_array, intensity_array

        # Calculate threshold
        threshold = np.percentile(intensity_array, self.noise_filter_percentile)

        # Keep peaks above threshold
        mask = intensity_array >= threshold
        return mz_array[mask], intensity_array[mask]

    def _sqrt_transform(self, intensity_array: np.ndarray) -> np.ndarray:
        """
        Apply square root transformation to intensities

        This reduces the dynamic range and makes low-intensity peaks
        more comparable to high-intensity peaks.

        Parameters
        ----------
        intensity_array : np.ndarray
            Original intensities

        Returns
        -------
        np.ndarray
            Square-root transformed intensities
        """
        return np.sqrt(intensity_array)

    def _bin_spectrum(
        self,
        mz_array: np.ndarray,
        intensity_array: np.ndarray
    ) -> np.ndarray:
        """
        Bin spectrum into fixed-size bins

        If multiple peaks fall in same bin, keep maximum intensity.

        Parameters
        ----------
        mz_array : np.ndarray
            m/z values
        intensity_array : np.ndarray
            Intensity values

        Returns
        -------
        np.ndarray
            Binned intensities (length = num_bins)
        """
        # Initialize binned array
        binned = np.zeros(self.num_bins)

        # Assign peaks to bins
        for mz, intensity in zip(mz_array, intensity_array):
            if self.min_mz <= mz <= self.max_mz:
                bin_idx = int((mz - self.min_mz) / self.bin_size)
                if 0 <= bin_idx < self.num_bins:
                    # Keep maximum intensity in bin
                    binned[bin_idx] = max(binned[bin_idx], intensity)

        return binned

    def _regional_normalization(self, binned: np.ndarray) -> np.ndarray:
        """
        Normalize spectrum by regions (SEQUEST-style)

        Divides spectrum into regions and normalizes each region
        to have mean = 0 and variance = 1 (z-score normalization).

        This ensures all spectral regions contribute equally to XCorr.

        Parameters
        ----------
        binned : np.ndarray
            Binned intensities

        Returns
        -------
        np.ndarray
            Regionally normalized intensities
        """
        normalized = np.zeros_like(binned)

        # Calculate region size
        region_size = self.num_bins // self.num_regions

        for i in range(self.num_regions):
            # Define region boundaries
            start = i * region_size
            end = start + region_size if i < self.num_regions - 1 else self.num_bins

            # Extract region
            region = binned[start:end]

            # Skip empty regions
            if len(region) == 0 or np.sum(region) == 0:
                continue

            # Z-score normalization
            mean = np.mean(region)
            std = np.std(region)

            if std > 0:
                normalized[start:end] = (region - mean) / std
            else:
                # If std = 0, just subtract mean
                normalized[start:end] = region - mean

        return normalized

    def get_bin_index(self, mz: float) -> int:
        """
        Get bin index for a given m/z value

        Parameters
        ----------
        mz : float
            m/z value

        Returns
        -------
        int
            Bin index (or -1 if out of range)
        """
        if mz < self.min_mz or mz > self.max_mz:
            return -1

        bin_idx = int((mz - self.min_mz) / self.bin_size)
        return min(bin_idx, self.num_bins - 1)

    def get_mz_from_bin(self, bin_idx: int) -> float:
        """
        Get center m/z value for a bin index

        Parameters
        ----------
        bin_idx : int
            Bin index

        Returns
        -------
        float
            m/z value at bin center
        """
        return self.min_mz + (bin_idx * self.bin_size) + (self.bin_size / 2)
