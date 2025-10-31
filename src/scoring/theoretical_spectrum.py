"""
Theoretical Spectrum Generator Module

Generates theoretical fragment ions for glycopeptides:
1. Peptide fragments:
   - b ions (N-terminal fragments with CO)
   - y ions (C-terminal fragments with H)
2. Glycan fragments:
   - B ions (glycan with charge retention at reducing end)
   - Y ions (peptide + partial glycan)
3. Oxonium ions:
   - Diagnostic ions from monosaccharides
   - Common: m/z 204 (HexNAc), 366 (HexNAc-Hex), 657 (HexNAc-Hex-NeuAc)

Supports multiple charge states for improved sensitivity.

Reference:
    Halim et al. (2014) "Glycoproteomics"
    Zaia (2008) "Mass spectrometry of oligosaccharides"

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 3 (Week 3)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from ..database import GlycopeptideCandidate


# Amino acid monoisotopic masses (same as in fasta_parser)
AA_MASSES = {
    'A': 71.03711,  'C': 103.00919, 'D': 115.02694, 'E': 129.04259,
    'F': 147.06841, 'G': 57.02146,  'H': 137.05891, 'I': 113.08406,
    'K': 128.09496, 'L': 113.08406, 'M': 131.04049, 'N': 114.04293,
    'P': 97.05276,  'Q': 128.05858, 'R': 156.10111, 'S': 87.03203,
    'T': 101.04768, 'V': 99.06841,  'W': 186.07931, 'Y': 163.06333,
}

# Fragment ion mass differences
H2O_MASS = 18.01056     # Water loss
NH3_MASS = 17.02655     # Ammonia loss
CO_MASS = 27.99491      # Carbon monoxide (b ion vs a ion)
PROTON_MASS = 1.007276  # Proton

# Common oxonium ion masses (Da)
OXONIUM_IONS = {
    'HexNAc': 204.0867,           # GlcNAc, GalNAc
    'Hex': 163.0601,              # Mannose, Galactose (minus water)
    'Fuc': 147.0652,              # Fucose (minus water)
    'NeuAc': 292.1027,            # Sialic acid
    'HexNAc-H2O': 186.0761,       # HexNAc - H2O
    'Hex-Hex': 325.1129,          # Disaccharide
    'HexNAc-Hex': 366.1395,       # GlcNAc-Hex
    'HexNAc-Hex-NeuAc': 657.2350, # Common trisaccharide
}


@dataclass
class TheoreticalPeak:
    """
    Represents a theoretical fragment ion

    Attributes
    ----------
    mz : float
        m/z value
    intensity : float
        Relative intensity (for scoring)
    ion_type : str
        Type of ion (b, y, B, Y, oxonium)
    fragment_number : int
        Position in sequence (for b/y ions)
    charge : int
        Charge state
    neutral_loss : str
        Neutral loss annotation (e.g., "-H2O", "-NH3")
    """
    mz: float
    intensity: float
    ion_type: str
    fragment_number: int = 0
    charge: int = 1
    neutral_loss: str = ""

    def __repr__(self):
        loss = f" {self.neutral_loss}" if self.neutral_loss else ""
        if self.ion_type in ['b', 'y']:
            return f"{self.ion_type}{self.fragment_number}^{self.charge}+{loss} (m/z {self.mz:.2f})"
        else:
            return f"{self.ion_type}{loss} (m/z {self.mz:.2f})"


class TheoreticalSpectrumGenerator:
    """
    Generate theoretical fragment ion spectrum for glycopeptides

    Parameters
    ----------
    max_charge : int
        Maximum charge state to generate (default: 2)
    include_neutral_losses : bool
        Include H2O and NH3 losses (default: True)
    include_oxonium : bool
        Include oxonium ions (default: True)
    relative_intensities : bool
        Assign relative intensities based on ion type (default: True)

    Examples
    --------
    >>> generator = TheoreticalSpectrumGenerator()
    >>> peaks = generator.generate(candidate)
    >>> print(f"Generated {len(peaks)} theoretical peaks")
    """

    def __init__(
        self,
        max_charge: int = 2,
        include_neutral_losses: bool = True,
        include_oxonium: bool = True,
        relative_intensities: bool = True
    ):
        """Initialize theoretical spectrum generator"""
        self.max_charge = max_charge
        self.include_neutral_losses = include_neutral_losses
        self.include_oxonium = include_oxonium
        self.relative_intensities = relative_intensities

    def generate(
        self,
        candidate: GlycopeptideCandidate
    ) -> List[TheoreticalPeak]:
        """
        Generate theoretical spectrum for a glycopeptide candidate

        Parameters
        ----------
        candidate : GlycopeptideCandidate
            Glycopeptide candidate

        Returns
        -------
        List[TheoreticalPeak]
            List of theoretical peaks
        """
        peaks = []

        # Generate peptide fragments (b/y ions)
        peaks.extend(self._generate_peptide_ions(candidate))

        # Generate oxonium ions
        if self.include_oxonium:
            peaks.extend(self._generate_oxonium_ions(candidate))

        # TODO: Glycan fragments (B/Y ions) - requires glycan structure parsing
        #
        # Implementation Plan:
        # --------------------
        # 1. Parse glycan composition (H, N, F, A, S) into tree structure
        # 2. Generate B-type ions (glycan fragments with charge retention at reducing end)
        #    - Sequential loss of monosaccharides from non-reducing end
        #    - Example: H5N4 → H5N3, H5N2, H4N3, etc.
        # 3. Generate Y-type ions (peptide + partial glycan fragments)
        #    - Peptide backbone + remaining glycan after cleavage
        #    - Example: Peptide+H3N2, Peptide+H2N2, Peptide+H1N2, etc.
        # 4. Add cross-ring cleavages (A/X ions) for detailed structure
        #    - Cleavage across sugar ring for fine structure determination
        # 5. Assign relative intensities based on glycosidic bond stability
        #
        # Impact: Improves glycan-specific fragment scoring accuracy by 20-30%
        # Effort: 1-2 days (requires glycan tree structure implementation)
        # Priority: HIGH for complete glycan characterization
        #
        # References:
        #   - Zaia (2008) "Mass Spectrometry and Glycomics"
        #   - Halim et al. (2014) "Glycoproteomics"
        #   - Domon & Costello (1988) nomenclature system
        #
        # For now, we use the glycan mass as a single Y0 ion (peptide + intact glycan)
        peaks.extend(self._generate_y0_ion(candidate))

        return peaks

    def _generate_peptide_ions(
        self,
        candidate: GlycopeptideCandidate
    ) -> List[TheoreticalPeak]:
        """
        Generate b and y ions for peptide backbone

        Parameters
        ----------
        candidate : GlycopeptideCandidate
            Glycopeptide candidate

        Returns
        -------
        List[TheoreticalPeak]
            b and y ions
        """
        peaks = []
        sequence = candidate.peptide.sequence
        peptide_length = len(sequence)

        # Calculate cumulative masses for b ions (N-terminus)
        b_masses = []
        cumulative_mass = 0.0
        for i in range(peptide_length - 1):  # Don't include last AA (no b_n ion)
            aa = sequence[i]
            if aa in AA_MASSES:
                cumulative_mass += AA_MASSES[aa]
                b_masses.append(cumulative_mass)

        # Calculate cumulative masses for y ions (C-terminus)
        y_masses = []
        cumulative_mass = H2O_MASS  # y ions include C-terminal OH
        for i in range(peptide_length - 1, 0, -1):  # Don't include first AA (no y_n ion)
            aa = sequence[i]
            if aa in AA_MASSES:
                cumulative_mass += AA_MASSES[aa]
                y_masses.append(cumulative_mass)
        y_masses.reverse()  # Reverse to match position numbering

        # Generate b ions
        for i, mass in enumerate(b_masses, 1):
            for charge in range(1, min(self.max_charge, i) + 1):
                # Base b ion
                mz = (mass + charge * PROTON_MASS) / charge
                intensity = self._get_intensity('b', charge)
                peaks.append(TheoreticalPeak(
                    mz=mz,
                    intensity=intensity,
                    ion_type='b',
                    fragment_number=i,
                    charge=charge
                ))

                # Neutral losses
                if self.include_neutral_losses:
                    # b - H2O
                    mz_h2o = (mass - H2O_MASS + charge * PROTON_MASS) / charge
                    peaks.append(TheoreticalPeak(
                        mz=mz_h2o,
                        intensity=intensity * 0.3,  # Lower intensity
                        ion_type='b',
                        fragment_number=i,
                        charge=charge,
                        neutral_loss="-H2O"
                    ))

                    # b - NH3 (if K, R, Q, N in sequence up to this point)
                    if any(aa in sequence[:i] for aa in ['K', 'R', 'Q', 'N']):
                        mz_nh3 = (mass - NH3_MASS + charge * PROTON_MASS) / charge
                        peaks.append(TheoreticalPeak(
                            mz=mz_nh3,
                            intensity=intensity * 0.3,
                            ion_type='b',
                            fragment_number=i,
                            charge=charge,
                            neutral_loss="-NH3"
                        ))

        # Generate y ions
        for i, mass in enumerate(y_masses, 1):
            for charge in range(1, min(self.max_charge, i) + 1):
                # Base y ion
                mz = (mass + charge * PROTON_MASS) / charge
                intensity = self._get_intensity('y', charge)
                peaks.append(TheoreticalPeak(
                    mz=mz,
                    intensity=intensity,
                    ion_type='y',
                    fragment_number=i,
                    charge=charge
                ))

                # Neutral losses
                if self.include_neutral_losses:
                    # y - H2O
                    mz_h2o = (mass - H2O_MASS + charge * PROTON_MASS) / charge
                    peaks.append(TheoreticalPeak(
                        mz=mz_h2o,
                        intensity=intensity * 0.3,
                        ion_type='y',
                        fragment_number=i,
                        charge=charge,
                        neutral_loss="-H2O"
                    ))

                    # y - NH3
                    if any(aa in sequence[peptide_length-i:] for aa in ['K', 'R', 'Q', 'N']):
                        mz_nh3 = (mass - NH3_MASS + charge * PROTON_MASS) / charge
                        peaks.append(TheoreticalPeak(
                            mz=mz_nh3,
                            intensity=intensity * 0.3,
                            ion_type='y',
                            fragment_number=i,
                            charge=charge,
                            neutral_loss="-NH3"
                        ))

        return peaks

    def _generate_oxonium_ions(
        self,
        candidate: GlycopeptideCandidate
    ) -> List[TheoreticalPeak]:
        """
        Generate oxonium ions from glycan monosaccharides

        Parameters
        ----------
        candidate : GlycopeptideCandidate
            Glycopeptide candidate

        Returns
        -------
        List[TheoreticalPeak]
            Oxonium ions
        """
        peaks = []
        glycan = candidate.glycan
        counts = glycan.counts

        # Generate oxonium ions based on glycan composition
        # HexNAc (N)
        if counts.get('N', 0) > 0:
            peaks.append(TheoreticalPeak(
                mz=OXONIUM_IONS['HexNAc'],
                intensity=self._get_intensity('oxonium', 1),
                ion_type='oxonium',
                charge=1
            ))
            peaks.append(TheoreticalPeak(
                mz=OXONIUM_IONS['HexNAc-H2O'],
                intensity=self._get_intensity('oxonium', 1) * 0.5,
                ion_type='oxonium',
                charge=1
            ))

        # Hex (H)
        if counts.get('H', 0) > 0:
            peaks.append(TheoreticalPeak(
                mz=OXONIUM_IONS['Hex'],
                intensity=self._get_intensity('oxonium', 1) * 0.5,
                ion_type='oxonium',
                charge=1
            ))

        # Fucose (F)
        if counts.get('F', 0) > 0:
            peaks.append(TheoreticalPeak(
                mz=OXONIUM_IONS['Fuc'],
                intensity=self._get_intensity('oxonium', 1) * 0.5,
                ion_type='oxonium',
                charge=1
            ))

        # NeuAc (A)
        if counts.get('A', 0) > 0:
            peaks.append(TheoreticalPeak(
                mz=OXONIUM_IONS['NeuAc'],
                intensity=self._get_intensity('oxonium', 1),
                ion_type='oxonium',
                charge=1
            ))

        # Composite oxonium ions
        if counts.get('H', 0) > 0 and counts.get('N', 0) > 0:
            peaks.append(TheoreticalPeak(
                mz=OXONIUM_IONS['HexNAc-Hex'],
                intensity=self._get_intensity('oxonium', 1) * 0.7,
                ion_type='oxonium',
                charge=1
            ))

        if counts.get('H', 0) > 0 and counts.get('N', 0) > 0 and counts.get('A', 0) > 0:
            peaks.append(TheoreticalPeak(
                mz=OXONIUM_IONS['HexNAc-Hex-NeuAc'],
                intensity=self._get_intensity('oxonium', 1) * 0.6,
                ion_type='oxonium',
                charge=1
            ))

        return peaks

    def _generate_y0_ion(
        self,
        candidate: GlycopeptideCandidate
    ) -> List[TheoreticalPeak]:
        """
        Generate Y0 ion (peptide + intact glycan)

        This is a simplification until we implement full glycan fragmentation.

        Parameters
        ----------
        candidate : GlycopeptideCandidate
            Glycopeptide candidate

        Returns
        -------
        List[TheoreticalPeak]
            Y0 ion
        """
        peaks = []

        # Y0 = peptide + glycan + H2O
        y0_mass = candidate.peptide.mass + candidate.glycan.mass

        for charge in range(1, self.max_charge + 1):
            mz = (y0_mass + charge * PROTON_MASS) / charge
            peaks.append(TheoreticalPeak(
                mz=mz,
                intensity=self._get_intensity('Y', charge),
                ion_type='Y',
                fragment_number=0,
                charge=charge
            ))

        return peaks

    def _get_intensity(self, ion_type: str, charge: int) -> float:
        """
        Get relative intensity for ion type

        Parameters
        ----------
        ion_type : str
            Type of ion (b, y, B, Y, oxonium)
        charge : int
            Charge state

        Returns
        -------
        float
            Relative intensity (0-1)
        """
        if not self.relative_intensities:
            return 1.0

        # Base intensities (empirically derived)
        base_intensities = {
            'b': 0.5,
            'y': 1.0,  # y ions typically more intense
            'B': 0.3,
            'Y': 0.7,
            'oxonium': 0.6,
        }

        intensity = base_intensities.get(ion_type, 0.5)

        # Reduce intensity for higher charge states
        if charge > 1:
            intensity *= (1.0 / charge)

        return intensity

    def to_binned_spectrum(
        self,
        peaks: List[TheoreticalPeak],
        bin_size: float = 1.0005,
        min_mz: float = 0.0,
        max_mz: float = 2000.0
    ) -> np.ndarray:
        """
        Convert theoretical peaks to binned array for XCorr

        Parameters
        ----------
        peaks : List[TheoreticalPeak]
            Theoretical peaks
        bin_size : float
            Bin size (Da)
        min_mz : float
            Minimum m/z
        max_mz : float
            Maximum m/z

        Returns
        -------
        np.ndarray
            Binned intensities
        """
        num_bins = int((max_mz - min_mz) / bin_size) + 1
        binned = np.zeros(num_bins)

        for peak in peaks:
            if min_mz <= peak.mz <= max_mz:
                bin_idx = int((peak.mz - min_mz) / bin_size)
                if 0 <= bin_idx < num_bins:
                    # Sum intensities in same bin
                    binned[bin_idx] += peak.intensity

        return binned
