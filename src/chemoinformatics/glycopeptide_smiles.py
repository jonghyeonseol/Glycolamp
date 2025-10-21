"""
Glycopeptide SMILES Conjugation Module

Combines peptide and glycan SMILES to create glycopeptide representations.

In N-glycosylation, glycans attach to asparagine (N) residues via
N-glycosidic bonds at the N-X-S/T sequon.

This module provides SMILES representations for glycopeptides by
combining peptide and glycan SMILES with linkage annotations.

Features:
- Glycopeptide SMILES generation
- N-glycosylation site annotation
- Combined molecular properties
- CSV export format

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 4 (Week 4)
"""

from typing import Optional
from dataclasses import dataclass

from .peptide_smiles import PeptideSMILESConverter, PeptideSMILES
from .glycan_smiles import GlycanSMILESConverter, GlycanSMILES


@dataclass
class GlycopeptideSMILES:
    """
    Glycopeptide SMILES representation

    Attributes
    ----------
    peptide_sequence : str
        Peptide amino acid sequence
    glycan_composition : str
        Glycan composition
    glycosylation_site : int
        Position of N-glycosylation site (0-indexed)
    peptide_smiles : str
        Peptide SMILES
    glycan_smiles : str
        Glycan SMILES
    combined_smiles : str
        Combined glycopeptide SMILES
    peptide_mw : float
        Peptide molecular weight
    glycan_mw : float
        Glycan molecular weight
    total_mw : float
        Total glycopeptide molecular weight
    is_valid : bool
        Whether SMILES are valid
    """
    peptide_sequence: str
    glycan_composition: str
    glycosylation_site: int
    peptide_smiles: str
    glycan_smiles: str
    combined_smiles: str
    peptide_mw: float
    glycan_mw: float
    total_mw: float
    is_valid: bool = True

    def __repr__(self):
        return (
            f"GlycopeptideSMILES("
            f"pep='{self.peptide_sequence}', "
            f"glycan='{self.glycan_composition}', "
            f"site={self.glycosylation_site}, "
            f"MW={self.total_mw:.2f})"
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary for CSV export

        Returns
        -------
        dict
            Dictionary with all fields
        """
        return {
            'peptide_sequence': self.peptide_sequence,
            'glycan_composition': self.glycan_composition,
            'glycosylation_site': self.glycosylation_site,
            'peptide_smiles': self.peptide_smiles,
            'glycan_smiles': self.glycan_smiles,
            'combined_smiles': self.combined_smiles,
            'peptide_mw': self.peptide_mw,
            'glycan_mw': self.glycan_mw,
            'total_mw': self.total_mw,
            'is_valid': self.is_valid,
        }


class GlycopeptideSMILESGenerator:
    """
    Generate SMILES for glycopeptides

    Parameters
    ----------
    use_rdkit : bool
        Use RDKit for validation (default: True)

    Examples
    --------
    >>> generator = GlycopeptideSMILESGenerator()
    >>> result = generator.generate(
    ...     peptide_sequence="NGTIINEK",
    ...     glycan_composition="H5N4F1A2",
    ...     glycosylation_site=0
    ... )
    >>> print(result.combined_smiles)
    >>> print(f"Total MW: {result.total_mw:.2f}")
    """

    def __init__(self, use_rdkit: bool = True):
        """Initialize glycopeptide SMILES generator"""
        self.peptide_converter = PeptideSMILESConverter(use_rdkit=use_rdkit)
        self.glycan_converter = GlycanSMILESConverter(use_rdkit=use_rdkit)

    def generate(
        self,
        peptide_sequence: str,
        glycan_composition: str,
        glycosylation_site: int = 0
    ) -> GlycopeptideSMILES:
        """
        Generate glycopeptide SMILES

        Parameters
        ----------
        peptide_sequence : str
            Amino acid sequence
        glycan_composition : str
            Glycan composition (e.g., "H5N4F1A2")
        glycosylation_site : int
            Position of N-glycosylation site (0-indexed, default: 0)

        Returns
        -------
        GlycopeptideSMILES
            Glycopeptide SMILES representation
        """
        # Convert peptide to SMILES
        peptide_result = self.peptide_converter.convert(peptide_sequence)

        # Convert glycan to SMILES
        glycan_result = self.glycan_converter.convert(glycan_composition)

        # Combine SMILES (disconnected representation for now)
        # In a full implementation, would create glycosidic bond
        # For ML applications, disconnected SMILES are often sufficient
        combined_smiles = f"{peptide_result.smiles}.{glycan_result.smiles}"

        # Calculate total molecular weight
        total_mw = peptide_result.mol_weight + glycan_result.mol_weight

        # Check validity
        is_valid = peptide_result.is_valid and glycan_result.is_valid

        return GlycopeptideSMILES(
            peptide_sequence=peptide_sequence,
            glycan_composition=glycan_composition,
            glycosylation_site=glycosylation_site,
            peptide_smiles=peptide_result.smiles,
            glycan_smiles=glycan_result.smiles,
            combined_smiles=combined_smiles,
            peptide_mw=peptide_result.mol_weight,
            glycan_mw=glycan_result.mol_weight,
            total_mw=total_mw,
            is_valid=is_valid
        )

    def batch_generate(
        self,
        glycopeptides: list
    ) -> list:
        """
        Generate SMILES for multiple glycopeptides

        Parameters
        ----------
        glycopeptides : list
            List of (peptide_seq, glycan_comp, site) tuples

        Returns
        -------
        list
            List of GlycopeptideSMILES objects
        """
        results = []
        for item in glycopeptides:
            if len(item) == 3:
                peptide_seq, glycan_comp, site = item
            else:
                peptide_seq, glycan_comp = item
                site = 0

            try:
                result = self.generate(peptide_seq, glycan_comp, site)
                results.append(result)
            except Exception as e:
                # Create invalid result
                results.append(GlycopeptideSMILES(
                    peptide_sequence=peptide_seq,
                    glycan_composition=glycan_comp,
                    glycosylation_site=site,
                    peptide_smiles="",
                    glycan_smiles="",
                    combined_smiles="",
                    peptide_mw=0.0,
                    glycan_mw=0.0,
                    total_mw=0.0,
                    is_valid=False
                ))
        return results

    def to_csv(
        self,
        glycopeptides_smiles: list,
        output_file: str
    ):
        """
        Export glycopeptide SMILES to CSV

        Parameters
        ----------
        glycopeptides_smiles : list
            List of GlycopeptideSMILES objects
        output_file : str
            Output CSV file path
        """
        import csv

        with open(output_file, 'w', newline='') as f:
            if not glycopeptides_smiles:
                return

            # Get field names from first result
            fieldnames = list(glycopeptides_smiles[0].to_dict().keys())

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for gp_smiles in glycopeptides_smiles:
                writer.writerow(gp_smiles.to_dict())
