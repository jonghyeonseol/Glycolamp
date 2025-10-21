"""
mzML Parser

Parses mzML files using Pyteomics to extract MS/MS spectra for glycopeptide identification.
Implements LEGIBLE and AVAILABLE ALCOA++ principles.
"""

from pathlib import Path
from typing import List, Dict, Optional, Iterator
import numpy as np

try:
    from pyteomics import mzml
    PYTEOMICS_AVAILABLE = True
except ImportError:
    PYTEOMICS_AVAILABLE = False


class Spectrum:
    """
    Represents a single MS/MS spectrum

    Attributes
    ----------
    id : str
        Spectrum identifier
    scan_number : int
        Scan number
    ms_level : int
        MS level (1 for MS1, 2 for MS/MS)
    precursor_mz : float
        Precursor m/z value
    precursor_charge : int
        Precursor charge state
    precursor_intensity : float
        Precursor intensity
    retention_time : float
        Retention time in seconds
    mz_array : np.ndarray
        Fragment ion m/z values
    intensity_array : np.ndarray
        Fragment ion intensities
    """

    def __init__(self, spectrum_dict: Dict):
        """
        Initialize spectrum from Pyteomics spectrum dictionary

        Parameters
        ----------
        spectrum_dict : dict
            Pyteomics spectrum dictionary
        """
        self.id = spectrum_dict.get('id', '')
        self.scan_number = spectrum_dict.get('index', 0)
        self.ms_level = spectrum_dict.get('ms level', 2)

        # Extract precursor information
        precursor_info = spectrum_dict.get('precursorList', {}).get('precursor', [{}])[0]
        selected_ion = precursor_info.get('selectedIonList', {}).get('selectedIon', [{}])[0]

        self.precursor_mz = selected_ion.get('selected ion m/z', 0.0)
        self.precursor_charge = selected_ion.get('charge state', 0)
        self.precursor_intensity = selected_ion.get('peak intensity', 0.0)

        # Retention time
        scan_list = spectrum_dict.get('scanList', {}).get('scan', [{}])[0]
        self.retention_time = scan_list.get('scan start time', 0.0)

        # Fragment ions
        self.mz_array = spectrum_dict.get('m/z array', np.array([]))
        self.intensity_array = spectrum_dict.get('intensity array', np.array([]))

    def __repr__(self):
        return (
            f"Spectrum(scan={self.scan_number}, "
            f"precursor_mz={self.precursor_mz:.4f}, "
            f"charge={self.precursor_charge}, "
            f"peaks={len(self.mz_array)})"
        )


class MzMLParser:
    """
    Parses mzML files to extract MS/MS spectra

    Uses Pyteomics library for robust mzML parsing
    """

    def __init__(self):
        """Initialize mzML parser"""
        if not PYTEOMICS_AVAILABLE:
            raise ImportError(
                "Pyteomics is required for mzML parsing.\n"
                "Install with: pip install pyteomics"
            )

    def parse(
        self,
        mzml_file_path: str,
        ms_level: int = 2,
        min_peaks: int = 10
    ) -> List[Spectrum]:
        """
        Parse mzML file and extract spectra

        Parameters
        ----------
        mzml_file_path : str
            Path to mzML file (can be gzipped)
        ms_level : int
            MS level to extract (default: 2 for MS/MS)
        min_peaks : int
            Minimum number of peaks required (default: 10)

        Returns
        -------
        list of Spectrum
            List of parsed spectra

        Raises
        ------
        FileNotFoundError
            If mzML file doesn't exist
        """
        mzml_file_path = Path(mzml_file_path)
        if not mzml_file_path.exists():
            raise FileNotFoundError(f"mzML file not found: {mzml_file_path}")

        spectra = []

        with mzml.read(str(mzml_file_path)) as reader:
            for spectrum_dict in reader:
                # Filter by MS level
                if spectrum_dict.get('ms level') != ms_level:
                    continue

                # Create Spectrum object
                spectrum = Spectrum(spectrum_dict)

                # Filter by minimum peaks
                if len(spectrum.mz_array) < min_peaks:
                    continue

                spectra.append(spectrum)

        return spectra

    def parse_iterator(
        self,
        mzml_file_path: str,
        ms_level: int = 2,
        min_peaks: int = 10
    ) -> Iterator[Spectrum]:
        """
        Parse mzML file and yield spectra one at a time (memory-efficient)

        Parameters
        ----------
        mzml_file_path : str
            Path to mzML file
        ms_level : int
            MS level to extract
        min_peaks : int
            Minimum number of peaks

        Yields
        ------
        Spectrum
            Parsed spectrum objects
        """
        mzml_file_path = Path(mzml_file_path)
        if not mzml_file_path.exists():
            raise FileNotFoundError(f"mzML file not found: {mzml_file_path}")

        with mzml.read(str(mzml_file_path)) as reader:
            for spectrum_dict in reader:
                if spectrum_dict.get('ms level') != ms_level:
                    continue

                spectrum = Spectrum(spectrum_dict)

                if len(spectrum.mz_array) < min_peaks:
                    continue

                yield spectrum

    def get_metadata(self, mzml_file_path: str) -> Dict:
        """
        Extract metadata from mzML file

        Parameters
        ----------
        mzml_file_path : str
            Path to mzML file

        Returns
        -------
        dict
            Metadata including instrument info, file description, etc.
        """
        mzml_file_path = Path(mzml_file_path)

        with mzml.read(str(mzml_file_path)) as reader:
            # Get file description
            metadata = {
                "file_path": str(mzml_file_path),
                "file_size_bytes": mzml_file_path.stat().st_size,
            }

            # Try to get instrument information
            try:
                # Read first spectrum to access file-level info
                first_spectrum = next(iter(reader))
                metadata["first_spectrum_id"] = first_spectrum.get('id', 'unknown')
            except StopIteration:
                metadata["first_spectrum_id"] = None

        return metadata
