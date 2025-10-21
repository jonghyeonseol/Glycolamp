"""
Peptide to SMILES Converter Module

Converts peptide sequences to SMILES representation for chemoinformatics
and machine learning applications.

Uses RDKit to build peptide structures from amino acid SMILES building blocks,
connecting them via peptide bonds (amide linkages).

Features:
- Standard 20 amino acids
- Peptide bond formation
- N-terminus (NH2) and C-terminus (COOH)
- Structure validation with RDKit

Reference:
    Weininger (1988) "SMILES, a chemical language and information system"
    RDKit documentation: https://www.rdkit.org/

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 4 (Week 4)
"""

from typing import Optional, Dict
from dataclasses import dataclass

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


# Amino acid SMILES (with free N-terminus and C-terminus for bonding)
# Format: N-terminus (N), side chain, C-terminus (C(=O)O)
AMINO_ACID_SMILES = {
    'A': 'N[C@@H](C)C(=O)O',           # Alanine
    'C': 'N[C@@H](CS)C(=O)O',          # Cysteine
    'D': 'N[C@@H](CC(=O)O)C(=O)O',     # Aspartic acid
    'E': 'N[C@@H](CCC(=O)O)C(=O)O',    # Glutamic acid
    'F': 'N[C@@H](Cc1ccccc1)C(=O)O',   # Phenylalanine
    'G': 'NCC(=O)O',                    # Glycine
    'H': 'N[C@@H](Cc1c[nH]cn1)C(=O)O', # Histidine
    'I': 'N[C@@H]([C@H](C)CC)C(=O)O',  # Isoleucine
    'K': 'N[C@@H](CCCCN)C(=O)O',       # Lysine
    'L': 'N[C@@H](CC(C)C)C(=O)O',      # Leucine
    'M': 'N[C@@H](CCSC)C(=O)O',        # Methionine
    'N': 'N[C@@H](CC(=O)N)C(=O)O',     # Asparagine
    'P': 'N1[C@@H](CCC1)C(=O)O',       # Proline
    'Q': 'N[C@@H](CCC(=O)N)C(=O)O',    # Glutamine
    'R': 'N[C@@H](CCCNC(=N)N)C(=O)O',  # Arginine
    'S': 'N[C@@H](CO)C(=O)O',          # Serine
    'T': 'N[C@@H]([C@H](C)O)C(=O)O',   # Threonine
    'V': 'N[C@@H](C(C)C)C(=O)O',       # Valine
    'W': 'N[C@@H](Cc1c[nH]c2ccccc12)C(=O)O',  # Tryptophan
    'Y': 'N[C@@H](Cc1ccc(O)cc1)C(=O)O', # Tyrosine
}


@dataclass
class PeptideSMILES:
    """
    Peptide SMILES representation

    Attributes
    ----------
    sequence : str
        Amino acid sequence
    smiles : str
        SMILES representation
    canonical_smiles : str
        Canonical SMILES (if RDKit available)
    mol_weight : float
        Molecular weight
    formula : str
        Molecular formula
    is_valid : bool
        Whether SMILES is valid
    """
    sequence: str
    smiles: str
    canonical_smiles: str = ""
    mol_weight: float = 0.0
    formula: str = ""
    is_valid: bool = True

    def __repr__(self):
        return f"PeptideSMILES(seq='{self.sequence}', MW={self.mol_weight:.2f})"


class PeptideSMILESConverter:
    """
    Convert peptide sequences to SMILES

    Parameters
    ----------
    use_rdkit : bool
        Use RDKit for validation and canonicalization (default: True)

    Examples
    --------
    >>> converter = PeptideSMILESConverter()
    >>> result = converter.convert("NGTIINEK")
    >>> print(result.smiles)
    >>> print(f"Molecular weight: {result.mol_weight:.2f}")
    """

    def __init__(self, use_rdkit: bool = True):
        """Initialize peptide SMILES converter"""
        if use_rdkit and not RDKIT_AVAILABLE:
            raise ImportError(
                "RDKit is required for peptide SMILES conversion.\n"
                "Install with: conda install -c conda-forge rdkit\n"
                "or: pip install rdkit"
            )
        self.use_rdkit = use_rdkit and RDKIT_AVAILABLE

    def convert(self, sequence: str) -> PeptideSMILES:
        """
        Convert peptide sequence to SMILES

        Parameters
        ----------
        sequence : str
            Amino acid sequence (single-letter codes)

        Returns
        -------
        PeptideSMILES
            Peptide SMILES representation
        """
        # Validate sequence
        invalid_aa = [aa for aa in sequence if aa not in AMINO_ACID_SMILES]
        if invalid_aa:
            raise ValueError(
                f"Invalid amino acids in sequence: {', '.join(invalid_aa)}\n"
                f"Supported: {', '.join(sorted(AMINO_ACID_SMILES.keys()))}"
            )

        # Build peptide SMILES
        smiles = self._build_peptide_smiles(sequence)

        # Initialize result
        result = PeptideSMILES(
            sequence=sequence,
            smiles=smiles
        )

        # Use RDKit for validation and properties
        if self.use_rdkit:
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
            # Without RDKit, just return the constructed SMILES
            result.canonical_smiles = smiles
            result.mol_weight = self._estimate_molecular_weight(sequence)
            result.is_valid = True

        return result

    def _build_peptide_smiles(self, sequence: str) -> str:
        """
        Build peptide SMILES from amino acid sequence

        Connects amino acids via peptide bonds (amide linkages).
        Strategy: Build from N-terminus to C-terminus.

        Parameters
        ----------
        sequence : str
            Amino acid sequence

        Returns
        -------
        str
            Peptide SMILES
        """
        if len(sequence) == 0:
            return ""

        if len(sequence) == 1:
            # Single amino acid
            return AMINO_ACID_SMILES[sequence[0]]

        # For multiple amino acids, we'll use a simple approach:
        # Build the SMILES by concatenating and forming peptide bonds

        # Start with first amino acid (N-terminus)
        smiles_parts = []

        for i, aa in enumerate(sequence):
            aa_smiles = AMINO_ACID_SMILES[aa]

            if i == 0:
                # First amino acid: keep N-terminus, prepare for C-terminal bond
                # Remove OH from COOH for peptide bond
                smiles_parts.append(aa_smiles.replace('C(=O)O', 'C(=O)'))
            elif i == len(sequence) - 1:
                # Last amino acid: prepare for N-terminal bond, keep C-terminus
                # Remove H from NH2 for peptide bond
                smiles_parts.append(aa_smiles.replace('N', ''))
            else:
                # Middle amino acids: prepare for both bonds
                smiles_parts.append(aa_smiles.replace('N', '').replace('C(=O)O', 'C(=O)'))

        # Connect with peptide bonds (N-C(=O))
        # This is a simplified approach; for production, use RDKit reactions
        smiles = ''.join(smiles_parts) + 'O'  # Add back terminal OH

        return smiles

    def _estimate_molecular_weight(self, sequence: str) -> float:
        """
        Estimate molecular weight without RDKit

        Uses amino acid masses minus water for peptide bonds.

        Parameters
        ----------
        sequence : str
            Amino acid sequence

        Returns
        -------
        float
            Estimated molecular weight
        """
        # Amino acid monoisotopic masses (same as in fasta_parser)
        AA_MASSES = {
            'A': 71.03711,  'C': 103.00919, 'D': 115.02694, 'E': 129.04259,
            'F': 147.06841, 'G': 57.02146,  'H': 137.05891, 'I': 113.08406,
            'K': 128.09496, 'L': 113.08406, 'M': 131.04049, 'N': 114.04293,
            'P': 97.05276,  'Q': 128.05858, 'R': 156.10111, 'S': 87.03203,
            'T': 101.04768, 'V': 99.06841,  'W': 186.07931, 'Y': 163.06333,
        }

        mass = 18.01056  # Add water (N-terminus H + C-terminus OH)
        for aa in sequence:
            if aa in AA_MASSES:
                mass += AA_MASSES[aa]

        return mass

    def batch_convert(self, sequences: list) -> list:
        """
        Convert multiple peptide sequences to SMILES

        Parameters
        ----------
        sequences : list
            List of amino acid sequences

        Returns
        -------
        list
            List of PeptideSMILES objects
        """
        results = []
        for seq in sequences:
            try:
                result = self.convert(seq)
                results.append(result)
            except Exception as e:
                # Create invalid result
                results.append(PeptideSMILES(
                    sequence=seq,
                    smiles="",
                    is_valid=False
                ))
        return results
