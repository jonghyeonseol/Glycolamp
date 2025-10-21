"""
Example 03: Database Search for Glycopeptides

Demonstrates complete workflow:
1. Parse protein database (FASTA)
2. In-silico enzymatic digestion
3. Load glycan composition library
4. Generate glycopeptide candidates for observed precursors

This example shows how to use the database modules to create a search space
for glycopeptide identification from MS/MS data.

Usage:
    python examples/example_03_database_search.py

Requirements:
    - BioPython (pip install biopython)
    - Sample FASTA file (uses test data if not provided)

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 2 (Week 2)
"""

import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    FastaParser,
    GlycanDatabase, GlycanType,
    CandidateGenerator
)
from src.alcoa import AuditLogger


def create_sample_fasta():
    """Create sample FASTA file with glycoproteins"""
    temp_fasta = tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        suffix='.fasta'
    )

    # Sample glycoproteins
    temp_fasta.write(">sp|P02768|ALBU_HUMAN Serum albumin\n")
    temp_fasta.write("DAHKSEVAHRFKDLGEENFKALVLIAFAQYLQQCPFEDHVKLVNEVTEFAK\n")
    temp_fasta.write("TCVADESAENCDKSLHTLFGDKLCTVATLRETYGEMADCCAKQEPERNECF\n")
    temp_fasta.write("LQHKDDNPNLPRLVRPEVDVMCTAFHDNEETFLKKYLYEIARRHPYFYAPE\n")

    temp_fasta.write(">sp|P01857|IGHG1_HUMAN Immunoglobulin G1\n")
    temp_fasta.write("ASTKGPSVFPLAPSSKSTSGGTAALGCLVKDYFPEPVTVSWNSGALTSGV\n")
    temp_fasta.write("HTFPAVLQSSGLYSLSSVVTVPSSSLGTQTYICNVNHKPSNTKVDKKVEPK\n")

    temp_fasta.close()
    return temp_fasta.name


def main():
    """Run database search example"""

    # Initialize ALCOA++ audit logging
    logger = AuditLogger()
    logger.log("Starting database search example", level="INFO")

    print("="*80)
    print("  GLYCOPEPTIDE DATABASE SEARCH EXAMPLE")
    print("="*80)
    print()

    # ========================================================================
    # Step 1: Parse Protein Database
    # ========================================================================
    print("STEP 1: Parse Protein Database (FASTA)")
    print("-" * 80)

    # Create sample FASTA (or use your own)
    fasta_file = create_sample_fasta()
    print(f"Using FASTA file: {fasta_file}")

    parser = FastaParser(fasta_file)
    proteins = parser.parse()

    print(f"✓ Parsed {len(proteins)} proteins:")
    for protein in proteins:
        print(f"  - {protein.id}: {len(protein.sequence)} AA")

    logger.log(f"Parsed {len(proteins)} proteins from FASTA", level="INFO")
    print()

    # ========================================================================
    # Step 2: In-Silico Enzymatic Digestion
    # ========================================================================
    print("STEP 2: In-Silico Tryptic Digestion")
    print("-" * 80)

    # Digest with trypsin, allowing 2 missed cleavages
    peptides = parser.digest(
        enzyme='trypsin',
        missed_cleavages=2,
        min_length=6,
        max_length=30
    )

    print(f"✓ Generated {len(peptides)} peptides")

    # Filter for glycopeptides (N-X-S/T motif)
    glyco_peptides = parser.filter_by_glycosylation_site(peptides)
    print(f"✓ Found {len(glyco_peptides)} glycopeptides with N-X-S/T motif")

    # Show statistics
    stats = parser.get_statistics(peptides)
    print(f"\nStatistics:")
    print(f"  Total peptides: {stats['total_peptides']}")
    print(f"  With glyco sites: {stats['with_glycosylation_sites']} "
          f"({stats['glycosylation_percentage']:.1f}%)")
    print(f"  Mass range: {stats['mass_range'][0]:.2f} - {stats['mass_range'][1]:.2f} Da")

    # Show example glycopeptides
    print(f"\nExample glycopeptides:")
    for i, peptide in enumerate(glyco_peptides[:3], 1):
        print(f"  {i}. {peptide.sequence} (mass: {peptide.mass:.2f} Da)")
        print(f"     Sites: {peptide.glycosylation_sites}")

    logger.log(f"Generated {len(glyco_peptides)} glycopeptides", level="INFO")
    print()

    # ========================================================================
    # Step 3: Load Glycan Database
    # ========================================================================
    print("STEP 3: Load Glycan Composition Library")
    print("-" * 80)

    # Load default common N-glycans
    glycan_db = GlycanDatabase()

    print(f"✓ Loaded {len(glycan_db.glycans)} glycan structures")

    # Show statistics by type
    glycan_stats = glycan_db.get_statistics()
    print(f"\nGlycan type distribution:")
    for glycan_type, count in glycan_stats['type_distribution'].items():
        print(f"  {glycan_type}: {count}")

    # Show examples of each type
    print(f"\nExample glycans by type:")
    for glycan_type in GlycanType:
        type_glycans = glycan_db.filter_by_type(glycan_type)
        if type_glycans:
            example = type_glycans[0]
            print(f"  {glycan_type.value}: {example.composition} "
                  f"(mass: {example.mass:.2f} Da)")

    logger.log(f"Loaded {len(glycan_db.glycans)} glycans", level="INFO")
    print()

    # ========================================================================
    # Step 4: Build Candidate Generator
    # ========================================================================
    print("STEP 4: Build Glycopeptide Candidate Index")
    print("-" * 80)

    generator = CandidateGenerator(glyco_peptides, glycan_db.glycans)

    index_info = generator.get_index_size()
    print(f"✓ Indexed {index_info['total_glycopeptides']:,} glycopeptide combinations")
    print(f"  {index_info['glyco_peptides']} peptides × "
          f"{index_info['total_glycans']} glycans")
    print(f"  Memory estimate: {index_info['memory_estimate_mb']:.2f} MB")

    logger.log(f"Built index with {index_info['total_glycopeptides']} candidates", level="INFO")
    print()

    # ========================================================================
    # Step 5: Search for Precursors
    # ========================================================================
    print("STEP 5: Search for Glycopeptide Candidates")
    print("-" * 80)

    # Simulate observed precursor ions from MS data
    # These would come from actual mzML files in real workflow
    observed_precursors = [
        {"mz": 1234.5678, "charge": 2, "scan": 1001},
        {"mz": 1456.7890, "charge": 2, "scan": 1523},
        {"mz": 987.6543, "charge": 3, "scan": 2045},
    ]

    tolerance_ppm = 10.0  # Mass tolerance
    print(f"Searching with ±{tolerance_ppm} ppm tolerance\n")

    total_candidates = 0
    for precursor in observed_precursors:
        mz = precursor["mz"]
        charge = precursor["charge"]
        scan = precursor["scan"]

        # Generate candidates
        candidates = generator.generate_candidates(
            precursor_mz=mz,
            charge=charge,
            tolerance_ppm=tolerance_ppm
        )

        total_candidates += len(candidates)

        print(f"Scan {scan}: m/z {mz:.4f} (z={charge}+)")
        print(f"  Found {len(candidates)} candidates")

        # Show top 3 candidates
        for i, candidate in enumerate(candidates[:3], 1):
            print(f"  {i}. {candidate.peptide.sequence} + {candidate.glycan.composition}")
            print(f"     Theoretical mass: {candidate.theoretical_mass:.4f} Da")
            print(f"     PPM error: {candidate.ppm_error:+.2f}")
            print(f"     Glycan type: {candidate.glycan.glycan_type.value}")

        print()

    print(f"✓ Generated {total_candidates} total candidates across "
          f"{len(observed_precursors)} precursors")

    logger.log(f"Generated {total_candidates} candidates", level="INFO")
    print()

    # ========================================================================
    # Step 6: Filter by Glycan Type (Optional)
    # ========================================================================
    print("STEP 6: Filter by Glycan Type (Example)")
    print("-" * 80)

    # Search only for high-mannose glycopeptides
    hm_glycans = glycan_db.filter_by_type(GlycanType.HIGH_MANNOSE)
    print(f"Filtering for high-mannose glycans only ({len(hm_glycans)} structures)")

    hm_generator = CandidateGenerator(glyco_peptides, hm_glycans)

    # Search same precursor
    test_precursor = observed_precursors[0]
    hm_candidates = hm_generator.generate_candidates(
        precursor_mz=test_precursor["mz"],
        charge=test_precursor["charge"],
        tolerance_ppm=tolerance_ppm
    )

    print(f"✓ Found {len(hm_candidates)} high-mannose candidates")

    if hm_candidates:
        print(f"\nTop candidate:")
        top = hm_candidates[0]
        print(f"  {top.peptide.sequence} + {top.glycan.composition}")
        print(f"  PPM error: {top.ppm_error:+.2f}")

    print()

    # ========================================================================
    # Summary
    # ========================================================================
    print("="*80)
    print("  SUMMARY")
    print("="*80)
    print(f"✓ Parsed {len(proteins)} proteins")
    print(f"✓ Generated {len(peptides)} peptides ({len(glyco_peptides)} glycopeptides)")
    print(f"✓ Loaded {len(glycan_db.glycans)} glycan structures")
    print(f"✓ Indexed {index_info['total_glycopeptides']:,} glycopeptide combinations")
    print(f"✓ Searched {len(observed_precursors)} precursors")
    print(f"✓ Found {total_candidates} total candidates")
    print()
    print("Next steps:")
    print("  - Integrate with MS/MS spectrum parser (mzML)")
    print("  - Implement SEQUEST-inspired scoring (XCorr)")
    print("  - Generate fragment ions (b/y, B/Y, oxonium)")
    print("  - Rank candidates by spectral match quality")
    print("="*80)

    logger.log("Database search example completed successfully", level="INFO")

    # Clean up
    import os
    os.unlink(fasta_file)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
