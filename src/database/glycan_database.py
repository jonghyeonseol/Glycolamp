"""
Glycan Database Module

Manages glycan composition library for glycopeptide identification.

Features:
- Parse glycan compositions (H5N4F1A2 format)
- Calculate monoisotopic masses
- Classify glycan types (HM, F, S, SF, C/H)
- Load custom glycan libraries
- Generate common N-glycan structures

Composition Format:
    H#N#F#A# where:
    - H = Hexose (e.g., Mannose, Galactose)
    - N = HexNAc (N-acetylhexosamine, e.g., GlcNAc)
    - F = Fucose (deoxyhexose)
    - A = NeuAc (Sialic acid, N-acetylneuraminic acid)

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 2 (Week 2)
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class GlycanType(Enum):
    """Glycan classification types"""
    HIGH_MANNOSE = "HM"      # H≥5, N=2, no F or A
    FUCOSYLATED = "F"        # Has F, no A
    SIALYLATED = "S"         # Has A, no F
    SIALOFUCOSYLATED = "SF"  # Has both F and A
    COMPLEX_HYBRID = "C/H"   # Everything else


# Monosaccharide monoisotopic masses (in Da)
MONOSACCHARIDE_MASSES = {
    'H': 162.052823,  # Hexose (Hex)
    'N': 203.079373,  # HexNAc (N-acetylhexosamine)
    'F': 146.057909,  # Fucose (dHex, deoxyhexose)
    'A': 291.095417,  # NeuAc (N-acetylneuraminic acid, sialic acid)
}


@dataclass
class Glycan:
    """
    Represents a glycan structure

    Attributes
    ----------
    composition : str
        Glycan composition (e.g., "H5N4F1A2")
    mass : float
        Monoisotopic mass (Da)
    glycan_type : GlycanType
        Classified glycan type
    counts : Dict[str, int]
        Monosaccharide counts {'H': 5, 'N': 4, 'F': 1, 'A': 2}
    """
    composition: str
    mass: float = 0.0
    glycan_type: GlycanType = None
    counts: Dict[str, int] = None

    def __post_init__(self):
        if self.counts is None:
            self.counts = self._parse_composition()
        if self.mass == 0.0:
            self.mass = self.calculate_mass()
        if self.glycan_type is None:
            self.glycan_type = self._classify_type()

    def _parse_composition(self) -> Dict[str, int]:
        """
        Parse composition string into monosaccharide counts

        Returns
        -------
        Dict[str, int]
            Monosaccharide counts
        """
        counts = {'H': 0, 'N': 0, 'F': 0, 'A': 0}

        # Pattern: Letter followed by number
        pattern = r'([HNFA])(\d+)'
        for match in re.finditer(pattern, self.composition):
            mono_type = match.group(1)
            count = int(match.group(2))
            if mono_type in counts:
                counts[mono_type] = count

        return counts

    def calculate_mass(self) -> float:
        """
        Calculate monoisotopic mass of glycan

        Returns
        -------
        float
            Monoisotopic mass in Daltons
        """
        mass = 0.0
        for mono_type, count in self.counts.items():
            if mono_type in MONOSACCHARIDE_MASSES:
                mass += MONOSACCHARIDE_MASSES[mono_type] * count
        return mass

    def _classify_type(self) -> GlycanType:
        """
        Classify glycan type based on composition

        Returns
        -------
        GlycanType
            Glycan classification
        """
        h = self.counts['H']
        n = self.counts['N']
        f = self.counts['F']
        a = self.counts['A']

        # High-mannose: H≥5, N=2, no F or A
        if h >= 5 and n == 2 and f == 0 and a == 0:
            return GlycanType.HIGH_MANNOSE

        # Sialofucosylated: has both A and F
        if f > 0 and a > 0:
            return GlycanType.SIALOFUCOSYLATED

        # Sialylated only: has A, no F
        if a > 0 and f == 0:
            return GlycanType.SIALYLATED

        # Fucosylated only: has F, no A
        if f > 0 and a == 0:
            return GlycanType.FUCOSYLATED

        # Complex/Hybrid: everything else
        return GlycanType.COMPLEX_HYBRID

    def __repr__(self):
        return f"Glycan(comp='{self.composition}', mass={self.mass:.2f}, type={self.glycan_type.value})"


class GlycanDatabase:
    """
    Manage glycan composition library

    Parameters
    ----------
    glycan_file_path : str, optional
        Path to custom glycan composition file

    Examples
    --------
    >>> db = GlycanDatabase()
    >>> glycans = db.generate_common_glycans()
    >>> glycan = db.get_glycan_by_composition("H5N4F1")
    >>> print(f"Mass: {glycan.mass:.2f} Da, Type: {glycan.glycan_type.value}")
    """

    def __init__(self, glycan_file_path: Optional[str] = None):
        """Initialize glycan database"""
        self.glycans: List[Glycan] = []
        self.composition_index: Dict[str, Glycan] = {}

        if glycan_file_path:
            self.load_from_composition_file(glycan_file_path)
        else:
            # Load default common glycans
            self.glycans = self.generate_common_glycans()
            self._build_index()

    def load_from_composition_file(self, file_path: str) -> List[Glycan]:
        """
        Load glycans from composition file

        File format (one composition per line):
            H5N2
            H6N2
            H5N4F1
            H5N4A2

        Parameters
        ----------
        file_path : str
            Path to composition file

        Returns
        -------
        List[Glycan]
            Loaded glycans
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Glycan file not found: {file_path}")

        self.glycans = []

        with open(file_path, 'r') as f:
            for line in f:
                composition = line.strip()
                if composition and not composition.startswith('#'):
                    try:
                        glycan = Glycan(composition=composition)
                        self.glycans.append(glycan)
                    except Exception as e:
                        print(f"Warning: Failed to parse '{composition}': {e}")

        self._build_index()
        return self.glycans

    def _build_index(self):
        """Build composition lookup index"""
        self.composition_index = {g.composition: g for g in self.glycans}

    def get_glycan_by_composition(self, composition: str) -> Optional[Glycan]:
        """
        Get glycan by composition string

        Parameters
        ----------
        composition : str
            Glycan composition (e.g., "H5N4F1")

        Returns
        -------
        Glycan or None
            Glycan object if found
        """
        return self.composition_index.get(composition)

    def calculate_mass(self, composition: str) -> float:
        """
        Calculate mass for a composition

        Parameters
        ----------
        composition : str
            Glycan composition

        Returns
        -------
        float
            Monoisotopic mass in Da
        """
        glycan = self.get_glycan_by_composition(composition)
        if glycan:
            return glycan.mass

        # Create temporary glycan for calculation
        temp_glycan = Glycan(composition=composition)
        return temp_glycan.mass

    def generate_common_glycans(self) -> List[Glycan]:
        """
        Generate library of common N-glycans

        Returns
        -------
        List[Glycan]
            Common N-glycan structures
        """
        common_compositions = [
            # High-mannose (HM)
            "H3N2", "H4N2", "H5N2", "H6N2", "H7N2", "H8N2", "H9N2",

            # Complex - non-fucosylated, non-sialylated
            "H3N3", "H3N4", "H4N4", "H5N4", "H6N4", "H3N5", "H4N5", "H5N5", "H6N5",

            # Fucosylated (F)
            "H3N3F1", "H3N4F1", "H4N4F1", "H5N4F1", "H6N4F1",
            "H3N5F1", "H4N5F1", "H5N5F1", "H6N5F1",
            "H3N4F2", "H4N4F2", "H5N4F2",

            # Sialylated (S)
            "H3N3A1", "H3N4A1", "H4N4A1", "H5N4A1", "H6N4A1",
            "H3N4A2", "H4N4A2", "H5N4A2", "H6N4A2",
            "H3N5A2", "H4N5A2", "H5N5A2", "H6N5A2",
            "H4N5A3", "H5N5A3", "H6N5A3",
            "H5N6A3", "H6N6A3",

            # Sialofucosylated (SF)
            "H3N4F1A1", "H4N4F1A1", "H5N4F1A1", "H6N4F1A1",
            "H3N4F1A2", "H4N4F1A2", "H5N4F1A2", "H6N4F1A2",
            "H3N5F1A2", "H4N5F1A2", "H5N5F1A2", "H6N5F1A2",
            "H4N5F1A3", "H5N5F1A3", "H6N5F1A3",
            "H5N6F1A3", "H6N6F1A3",
        ]

        glycans = []
        for composition in common_compositions:
            try:
                glycan = Glycan(composition=composition)
                glycans.append(glycan)
            except Exception as e:
                print(f"Warning: Failed to generate glycan '{composition}': {e}")

        return glycans

    def filter_by_type(self, glycan_type: GlycanType) -> List[Glycan]:
        """
        Filter glycans by type

        Parameters
        ----------
        glycan_type : GlycanType
            Glycan type to filter

        Returns
        -------
        List[Glycan]
            Glycans of specified type
        """
        return [g for g in self.glycans if g.glycan_type == glycan_type]

    def get_statistics(self) -> Dict:
        """
        Get database statistics

        Returns
        -------
        dict
            Statistics about glycan database
        """
        type_counts = {}
        for glycan_type in GlycanType:
            count = sum(1 for g in self.glycans if g.glycan_type == glycan_type)
            type_counts[glycan_type.value] = count

        masses = [g.mass for g in self.glycans]

        return {
            "total_glycans": len(self.glycans),
            "type_distribution": type_counts,
            "mass_range": (min(masses), max(masses)) if masses else (0, 0),
            "average_mass": sum(masses) / len(masses) if masses else 0,
        }
