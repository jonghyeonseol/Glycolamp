"""
FASTA Parser Module

Parses protein FASTA files and performs in-silico enzymatic digestion
for glycopeptide identification.

Features:
- FASTA file parsing with BioPython
- Enzymatic digestion (trypsin, chymotrypsin, etc.)
- N-glycosylation motif detection (N-X-S/T where X≠P)
- Peptide mass calculation
- Protein provenance tracking

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 2 (Week 2)
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass

try:
    from Bio import SeqIO
    from Bio.SeqUtils import molecular_weight
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False


# Amino acid monoisotopic masses (in Da)
AA_MASSES = {
    'A': 71.03711,  'C': 103.00919, 'D': 115.02694, 'E': 129.04259,
    'F': 147.06841, 'G': 57.02146,  'H': 137.05891, 'I': 113.08406,
    'K': 128.09496, 'L': 113.08406, 'M': 131.04049, 'N': 114.04293,
    'P': 97.05276,  'Q': 128.05858, 'R': 156.10111, 'S': 87.03203,
    'T': 101.04768, 'V': 99.06841,  'W': 186.07931, 'Y': 163.06333,
}

# Water mass (added to peptide mass)
WATER_MASS = 18.01056


@dataclass
class Protein:
    """
    Represents a protein from FASTA file

    Attributes
    ----------
    id : str
        Protein identifier (e.g., UniProt ID)
    description : str
        Protein description/name
    sequence : str
        Amino acid sequence
    """
    id: str
    description: str
    sequence: str

    def __repr__(self):
        return f"Protein(id='{self.id}', length={len(self.sequence)})"


@dataclass
class Peptide:
    """
    Represents a peptide from in-silico digestion

    Attributes
    ----------
    sequence : str
        Amino acid sequence
    protein_id : str
        Parent protein identifier
    start_position : int
        Start position in protein (1-indexed)
    end_position : int
        End position in protein (1-indexed)
    missed_cleavages : int
        Number of missed cleavage sites
    mass : float
        Monoisotopic mass (Da)
    has_glycosylation_site : bool
        Whether peptide contains N-glycosylation motif
    glycosylation_sites : List[int]
        Positions of N-glycosylation motifs (relative to peptide)
    """
    sequence: str
    protein_id: str
    start_position: int
    end_position: int
    missed_cleavages: int = 0
    mass: float = 0.0
    has_glycosylation_site: bool = False
    glycosylation_sites: List[int] = None

    def __post_init__(self):
        if self.glycosylation_sites is None:
            self.glycosylation_sites = []
        if self.mass == 0.0:
            self.mass = self.calculate_mass()

    def calculate_mass(self) -> float:
        """
        Calculate monoisotopic mass of peptide

        Returns
        -------
        float
            Monoisotopic mass in Daltons
        """
        mass = WATER_MASS  # N-terminus H + C-terminus OH

        for aa in self.sequence:
            if aa in AA_MASSES:
                mass += AA_MASSES[aa]
            else:
                # Unknown amino acid - use average mass
                mass += 110.0

        return mass

    def __repr__(self):
        return f"Peptide(seq='{self.sequence}', mass={self.mass:.2f}, glyco={self.has_glycosylation_site})"


class FastaParser:
    """
    Parse FASTA files and perform in-silico digestion

    Parameters
    ----------
    fasta_file_path : str
        Path to FASTA file

    Examples
    --------
    >>> parser = FastaParser("uniprot_human.fasta")
    >>> proteins = parser.parse()
    >>> peptides = parser.digest(enzyme='trypsin', missed_cleavages=2)
    >>> glyco_peptides = parser.filter_by_glycosylation_site(peptides)
    """

    # Enzyme cleavage rules (regular expressions)
    ENZYMES = {
        'trypsin': r'[KR](?!P)',              # Cleave after K or R, not before P
        'chymotrypsin': r'[FWY](?!P)',        # Cleave after F, W, or Y, not before P
        'pepsin': r'[FL]',                     # Cleave after F or L
        'lysc': r'K',                          # Cleave after K
        'argc': r'R',                          # Cleave after R
        'gluc': r'[ED]',                       # Cleave after E or D
    }

    # N-glycosylation motif: N-X-S/T where X ≠ P
    GLYCOSYLATION_MOTIF = r'N[^P][ST]'

    def __init__(self, fasta_file_path: str):
        """Initialize FASTA parser"""
        if not BIOPYTHON_AVAILABLE:
            raise ImportError(
                "BioPython is required for FASTA parsing.\n"
                "Install with: pip install biopython"
            )

        self.fasta_file_path = Path(fasta_file_path)
        if not self.fasta_file_path.exists():
            raise FileNotFoundError(f"FASTA file not found: {fasta_file_path}")

        self.proteins: List[Protein] = []

    def parse(self) -> List[Protein]:
        """
        Parse FASTA file and extract proteins

        Returns
        -------
        List[Protein]
            List of parsed proteins
        """
        self.proteins = []

        with open(self.fasta_file_path, 'r') as handle:
            for record in SeqIO.parse(handle, "fasta"):
                protein = Protein(
                    id=record.id,
                    description=record.description,
                    sequence=str(record.seq)
                )
                self.proteins.append(protein)

        return self.proteins

    def digest(
        self,
        enzyme: str = 'trypsin',
        missed_cleavages: int = 2,
        min_length: int = 6,
        max_length: int = 50
    ) -> List[Peptide]:
        """
        Perform in-silico enzymatic digestion

        Parameters
        ----------
        enzyme : str
            Enzyme name (default: 'trypsin')
            Options: trypsin, chymotrypsin, pepsin, lysc, argc, gluc
        missed_cleavages : int
            Maximum number of missed cleavages (default: 2)
        min_length : int
            Minimum peptide length (default: 6)
        max_length : int
            Maximum peptide length (default: 50)

        Returns
        -------
        List[Peptide]
            List of digested peptides
        """
        if not self.proteins:
            self.parse()

        if enzyme not in self.ENZYMES:
            raise ValueError(f"Unknown enzyme: {enzyme}. Options: {list(self.ENZYMES.keys())}")

        cleavage_pattern = self.ENZYMES[enzyme]
        all_peptides = []

        for protein in self.proteins:
            peptides = self._digest_protein(
                protein=protein,
                cleavage_pattern=cleavage_pattern,
                missed_cleavages=missed_cleavages,
                min_length=min_length,
                max_length=max_length
            )
            all_peptides.extend(peptides)

        return all_peptides

    def _digest_protein(
        self,
        protein: Protein,
        cleavage_pattern: str,
        missed_cleavages: int,
        min_length: int,
        max_length: int
    ) -> List[Peptide]:
        """
        Digest a single protein

        Parameters
        ----------
        protein : Protein
            Protein to digest
        cleavage_pattern : str
            Regular expression for cleavage sites
        missed_cleavages : int
            Maximum missed cleavages
        min_length : int
            Minimum peptide length
        max_length : int
            Maximum peptide length

        Returns
        -------
        List[Peptide]
            List of peptides from this protein
        """
        sequence = protein.sequence
        peptides = []

        # Find all cleavage sites
        cleavage_sites = [0]  # Start of sequence
        for match in re.finditer(cleavage_pattern, sequence):
            cleavage_sites.append(match.end())
        cleavage_sites.append(len(sequence))  # End of sequence

        # Generate peptides with missed cleavages
        for i in range(len(cleavage_sites) - 1):
            for j in range(i + 1, min(i + missed_cleavages + 2, len(cleavage_sites))):
                start = cleavage_sites[i]
                end = cleavage_sites[j]
                peptide_seq = sequence[start:end]

                # Apply length filters
                if len(peptide_seq) < min_length or len(peptide_seq) > max_length:
                    continue

                # Check for N-glycosylation motif
                has_glyco, glyco_sites = self._has_glycosylation_motif(peptide_seq)

                peptide = Peptide(
                    sequence=peptide_seq,
                    protein_id=protein.id,
                    start_position=start + 1,  # 1-indexed
                    end_position=end,
                    missed_cleavages=j - i - 1,
                    has_glycosylation_site=has_glyco,
                    glycosylation_sites=glyco_sites
                )

                peptides.append(peptide)

        return peptides

    def _has_glycosylation_motif(self, sequence: str) -> tuple:
        """
        Check if sequence contains N-glycosylation motif (N-X-S/T, X≠P)

        Parameters
        ----------
        sequence : str
            Peptide sequence

        Returns
        -------
        tuple
            (has_motif: bool, sites: List[int])
            Sites are 0-indexed positions of N in the motif
        """
        sites = []
        for match in re.finditer(self.GLYCOSYLATION_MOTIF, sequence):
            sites.append(match.start())  # Position of N

        return len(sites) > 0, sites

    def filter_by_glycosylation_site(
        self,
        peptides: Optional[List[Peptide]] = None
    ) -> List[Peptide]:
        """
        Filter peptides to only those with N-glycosylation sites

        Parameters
        ----------
        peptides : List[Peptide], optional
            Peptides to filter. If None, uses last digestion results

        Returns
        -------
        List[Peptide]
            Peptides containing N-glycosylation motifs
        """
        if peptides is None:
            raise ValueError("No peptides provided. Run digest() first.")

        return [p for p in peptides if p.has_glycosylation_site]

    def get_statistics(self, peptides: List[Peptide]) -> Dict:
        """
        Get statistics about digested peptides

        Parameters
        ----------
        peptides : List[Peptide]
            Peptides to analyze

        Returns
        -------
        dict
            Statistics including counts, mass range, etc.
        """
        if not peptides:
            return {
                "total_peptides": 0,
                "unique_sequences": 0,
                "with_glycosylation_sites": 0,
                "mass_range": (0, 0),
                "length_range": (0, 0),
            }

        sequences = set(p.sequence for p in peptides)
        glyco_peptides = [p for p in peptides if p.has_glycosylation_site]
        masses = [p.mass for p in peptides]
        lengths = [len(p.sequence) for p in peptides]

        return {
            "total_peptides": len(peptides),
            "unique_sequences": len(sequences),
            "with_glycosylation_sites": len(glyco_peptides),
            "glycosylation_percentage": (len(glyco_peptides) / len(peptides)) * 100,
            "mass_range": (min(masses), max(masses)),
            "length_range": (min(lengths), max(lengths)),
            "average_mass": sum(masses) / len(masses),
            "average_length": sum(lengths) / len(lengths),
        }
