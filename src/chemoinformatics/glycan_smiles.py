"""
Glycan to SMILES Converter Module

Converts glycan compositions to SMILES representation.

Since full glycan structures require linkage information (α/β, 1-2/1-3/1-4/1-6),
this module generates linear SMILES representations based on composition
for common N-glycan core structures.

For machine learning applications, composition-based SMILES provides
a useful molecular fingerprint even without full structural information.

Features:
- Common N-glycan core structures
- Linear monosaccharide SMILES
- Composition-based approximation
- RDKit validation

Reference:
    Glycan notation: Symbol Nomenclature for Glycans (SNFG)
    IUPAC glycan nomenclature

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 4 (Week 4)
"""

from typing import Optional, Dict
from dataclasses import dataclass

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


# Monosaccharide SMILES (linear forms for simplicity)
# In reality, sugars exist as cyclic hemiacetals, but linear forms are simpler
MONOSACCHARIDE_SMILES = {
    'Hex': 'OCC(O)C(O)C(O)C(O)C=O',              # Hexose (Glucose/Mannose/Galactose)
    'HexNAc': 'CC(=O)NC(CO)C(O)C(O)C(O)C=O',    # N-Acetylhexosamine (GlcNAc/GalNAc)
    'Fuc': 'CC(O)C(O)C(O)C(O)C=O',               # Fucose (deoxyhexose)
    'NeuAc': 'CC(=O)NC(C(O)C(O)C(O)CO)C(=O)O',  # N-Acetylneuraminic acid (Sialic acid)
}

# Map composition codes to monosaccharide types
COMPOSITION_TO_MONO = {
    'H': 'Hex',
    'N': 'HexNAc',
    'F': 'Fuc',
    'A': 'NeuAc',
}


@dataclass
class GlycanSMILES:
    """
    Glycan SMILES representation

    Attributes
    ----------
    composition : str
        Glycan composition (e.g., "H5N4F1A2")
    smiles : str
        SMILES representation (linear approximation)
    canonical_smiles : str
        Canonical SMILES (if RDKit available)
    mol_weight : float
        Molecular weight
    formula : str
        Molecular formula
    is_valid : bool
        Whether SMILES is valid
    monosaccharide_counts : Dict[str, int]
        Counts of each monosaccharide type
    """
    composition: str
    smiles: str
    canonical_smiles: str = ""
    mol_weight: float = 0.0
    formula: str = ""
    is_valid: bool = True
    monosaccharide_counts: Dict[str, int] = None

    def __repr__(self):
        return f"GlycanSMILES(comp='{self.composition}', MW={self.mol_weight:.2f})"


class GlycanSMILESConverter:
    """
    Convert glycan compositions to SMILES

    Note: This generates linear SMILES approximations based on composition.
    Full structural SMILES would require linkage information.

    Parameters
    ----------
    use_rdkit : bool
        Use RDKit for validation and canonicalization (default: True)

    Examples
    --------
    >>> converter = GlycanSMILESConverter()
    >>> result = converter.convert("H5N4F1A2")
    >>> print(result.smiles)
    >>> print(f"Molecular weight: {result.mol_weight:.2f}")
    """

    def __init__(self, use_rdkit: bool = True):
        """Initialize glycan SMILES converter"""
        if use_rdkit and not RDKIT_AVAILABLE:
            print("Warning: RDKit not available. SMILES validation disabled.")
            use_rdkit = False
        self.use_rdkit = use_rdkit and RDKIT_AVAILABLE

    def convert(self, composition: str) -> GlycanSMILES:
        """
        Convert glycan composition to SMILES

        Parameters
        ----------
        composition : str
            Glycan composition (e.g., "H5N4F1A2")

        Returns
        -------
        GlycanSMILES
            Glycan SMILES representation
        """
        # Parse composition
        counts = self._parse_composition(composition)

        # Build linear SMILES (concatenate monosaccharides)
        smiles = self._build_glycan_smiles(counts)

        # Initialize result
        result = GlycanSMILES(
            composition=composition,
            smiles=smiles,
            monosaccharide_counts=counts
        )

        # Use RDKit for validation and properties
        if self.use_rdkit and smiles:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                result.is_valid = False
                return result

            # Canonicalize SMILES
            result.canonical_smiles = Chem.MolToSmiles(mol)

            # Calculate properties
            result.mol_weight = Descriptors.MolWt(mol)
            result.formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
            result.is_valid = True
        else:
            # Without RDKit, estimate properties
            result.canonical_smiles = smiles
            result.mol_weight = self._estimate_molecular_weight(counts)
            result.is_valid = bool(smiles)

        return result

    def _parse_composition(self, composition: str) -> Dict[str, int]:
        """
        Parse glycan composition string

        Parameters
        ----------
        composition : str
            Glycan composition (e.g., "H5N4F1A2")

        Returns
        -------
        Dict[str, int]
            Monosaccharide counts
        """
        import re
        counts = {}

        # Pattern: Letter followed by number
        pattern = r'([HNFA])(\d+)'
        for match in re.finditer(pattern, composition):
            mono_type = match.group(1)
            count = int(match.group(2))
            counts[mono_type] = count

        return counts

    def _build_glycan_smiles(self, counts: Dict[str, int]) -> str:
        """
        Build glycan SMILES from monosaccharide counts

        This creates a linear concatenation of monosaccharides.
        For a more realistic structure, would need linkage information.

        Parameters
        ----------
        counts : Dict[str, int]
            Monosaccharide counts

        Returns
        -------
        str
            Glycan SMILES (linear approximation)
        """
        if not counts:
            return ""

        # Build SMILES by concatenating monosaccharides
        # This is a simplified approach for composition-based representation
        smiles_parts = []

        # Add monosaccharides in order: H, N, F, A
        for code in ['H', 'N', 'F', 'A']:
            count = counts.get(code, 0)
            if count > 0:
                mono_type = COMPOSITION_TO_MONO[code]
                mono_smiles = MONOSACCHARIDE_SMILES[mono_type]
                # Add each monosaccharide
                for _ in range(count):
                    smiles_parts.append(mono_smiles)

        # Connect with '.' (disconnected components in SMILES)
        # This represents the monosaccharides as separate entities
        # In reality, they'd be connected via glycosidic bonds
        smiles = '.'.join(smiles_parts)

        return smiles

    def _estimate_molecular_weight(self, counts: Dict[str, int]) -> float:
        """
        Estimate molecular weight from composition

        Parameters
        ----------
        counts : Dict[str, int]
            Monosaccharide counts

        Returns
        -------
        float
            Estimated molecular weight
        """
        # Monosaccharide monoisotopic masses (same as in glycan_database)
        MONO_MASSES = {
            'H': 162.052823,  # Hexose
            'N': 203.079373,  # HexNAc
            'F': 146.057909,  # Fucose
            'A': 291.095417,  # NeuAc
        }

        mass = 0.0
        for code, count in counts.items():
            if code in MONO_MASSES:
                mass += MONO_MASSES[code] * count

        return mass

    def batch_convert(self, compositions: list) -> list:
        """
        Convert multiple glycan compositions to SMILES

        Parameters
        ----------
        compositions : list
            List of glycan compositions

        Returns
        -------
        list
            List of GlycanSMILES objects
        """
        results = []
        for comp in compositions:
            try:
                result = self.convert(comp)
                results.append(result)
            except Exception as e:
                # Create invalid result
                results.append(GlycanSMILES(
                    composition=comp,
                    smiles="",
                    is_valid=False
                ))
        return results
