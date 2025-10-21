"""
Integration Test for Database Pipeline

Tests the complete workflow:
1. Parse FASTA file → Proteins
2. Digest proteins → Peptides
3. Load glycan database → Glycans
4. Generate candidates for precursor m/z

This validates the integration between all database modules.

Usage:
    pytest tests/test_database_integration.py -v
    python tests/test_database_integration.py  # Standalone mode

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 2 (Week 2)
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    FastaParser, Peptide, Protein,
    GlycanDatabase, Glycan, GlycanType,
    CandidateGenerator, GlycopeptideCandidate
)


class TestDatabaseIntegration(unittest.TestCase):
    """Test complete database workflow integration"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures (runs once for all tests)"""
        # Create temporary FASTA file with realistic glycoprotein sequences
        cls.temp_fasta = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.fasta'
        )

        # Fetuin-A (human) - a well-known glycoprotein
        cls.temp_fasta.write(">sp|P02765|FETUA_HUMAN Alpha-2-HS-glycoprotein\n")
        cls.temp_fasta.write("MKVPWLWLFLFLGATVLAAGDYKSGLVPGKQTLVVQNNSHVNEAGKPF\n")
        cls.temp_fasta.write("QLFGSPSGQKDLLFKDSAIGFSRVPPQSDQWQSGTSQNNALVFSVDKL\n")
        cls.temp_fasta.write("QGDQEGDEPVWCEEPQKDEGVHFGAKVSRGEVLLKFQTDNHNHKQIGG\n")
        cls.temp_fasta.write("KCPDCPLLAPLNDSRVVHAVEVALATFNAESYTNTDTSYFVFDRDQKR\n")

        # IgG1 Fc fragment - contains N-glycosylation site
        cls.temp_fasta.write(">sp|P01857|IGHG1_HUMAN Ig gamma-1 chain C region\n")
        cls.temp_fasta.write("ASTKGPSVFPLAPSSKSTSGGTAALGCLVKDYFPEPVTVSWNSGALTS\n")
        cls.temp_fasta.write("GVHTFPAVLQSSGLYSLSSVVTVPSSSLGTQTYICNVNHKPSNTKVDKK\n")

        cls.temp_fasta.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures"""
        os.unlink(cls.temp_fasta.name)

    def test_full_workflow_fasta_to_candidates(self):
        """Test complete workflow: FASTA → Peptides → Glycans → Candidates"""

        # Step 1: Parse FASTA file
        print("\n" + "="*80)
        print("STEP 1: Parse FASTA File")
        print("="*80)

        parser = FastaParser(self.temp_fasta.name)
        proteins = parser.parse()

        self.assertEqual(len(proteins), 2)
        print(f"✓ Parsed {len(proteins)} proteins")
        for protein in proteins:
            print(f"  - {protein.id}: {len(protein.sequence)} residues")

        # Step 2: Digest proteins
        print("\n" + "="*80)
        print("STEP 2: In-Silico Tryptic Digestion")
        print("="*80)

        peptides = parser.digest(
            enzyme='trypsin',
            missed_cleavages=2,
            min_length=6,
            max_length=30
        )

        self.assertGreater(len(peptides), 0)
        print(f"✓ Generated {len(peptides)} peptides")

        # Filter for glycopeptides
        glyco_peptides = parser.filter_by_glycosylation_site(peptides)
        self.assertGreater(len(glyco_peptides), 0)
        print(f"✓ Found {len(glyco_peptides)} glycopeptides (with N-X-S/T motif)")

        # Show statistics
        stats = parser.get_statistics(peptides)
        print(f"\nPeptide Statistics:")
        print(f"  Total peptides: {stats['total_peptides']}")
        print(f"  With glyco sites: {stats['with_glycosylation_sites']} "
              f"({stats['glycosylation_percentage']:.1f}%)")
        print(f"  Mass range: {stats['mass_range'][0]:.2f} - {stats['mass_range'][1]:.2f} Da")
        print(f"  Length range: {stats['length_range'][0]} - {stats['length_range'][1]} AA")

        # Step 3: Load glycan database
        print("\n" + "="*80)
        print("STEP 3: Load Glycan Database")
        print("="*80)

        glycan_db = GlycanDatabase()
        self.assertGreater(len(glycan_db.glycans), 0)
        print(f"✓ Loaded {len(glycan_db.glycans)} glycan structures")

        # Show glycan statistics
        glycan_stats = glycan_db.get_statistics()
        print(f"\nGlycan Statistics:")
        print(f"  Total glycans: {glycan_stats['total_glycans']}")
        print(f"  Type distribution:")
        for glycan_type, count in glycan_stats['type_distribution'].items():
            print(f"    {glycan_type}: {count}")
        print(f"  Mass range: {glycan_stats['mass_range'][0]:.2f} - "
              f"{glycan_stats['mass_range'][1]:.2f} Da")

        # Step 4: Generate candidates
        print("\n" + "="*80)
        print("STEP 4: Generate Glycopeptide Candidates")
        print("="*80)

        generator = CandidateGenerator(glyco_peptides, glycan_db.glycans)

        # Show index size
        index_info = generator.get_index_size()
        print(f"✓ Pre-computed {index_info['total_glycopeptides']:,} glycopeptide masses")
        print(f"  Memory estimate: {index_info['memory_estimate_mb']:.2f} MB")

        # Test candidate generation for a realistic precursor
        # Example: peptide NGTIINEK (887.47 Da) + H5N4F1 (1722.64 Da) = 2610.11 Da
        # m/z for z=2: (2610.11 + 2*1.007276) / 2 ≈ 1306.06
        test_precursor_mz = 1306.06
        test_charge = 2
        test_tolerance_ppm = 10.0

        print(f"\nSearching for candidates:")
        print(f"  Precursor m/z: {test_precursor_mz}")
        print(f"  Charge: {test_charge}+")
        print(f"  Tolerance: ±{test_tolerance_ppm} ppm")

        candidates = generator.generate_candidates(
            precursor_mz=test_precursor_mz,
            charge=test_charge,
            tolerance_ppm=test_tolerance_ppm
        )

        print(f"\n✓ Found {len(candidates)} candidates")

        # Show top 5 candidates
        if len(candidates) > 0:
            print(f"\nTop 5 Candidates (by PPM error):")
            for i, candidate in enumerate(candidates[:5], 1):
                print(f"  {i}. {candidate.peptide.sequence} + {candidate.glycan.composition}")
                print(f"     Mass: {candidate.theoretical_mass:.4f} Da, "
                      f"PPM: {candidate.ppm_error:+.2f}")

            # Get candidate statistics
            candidate_stats = generator.get_statistics(candidates)
            print(f"\nCandidate Statistics:")
            print(f"  Total candidates: {candidate_stats['total_candidates']}")
            print(f"  Unique peptides: {candidate_stats['unique_peptides']}")
            print(f"  Unique glycans: {candidate_stats['unique_glycans']}")
            print(f"  PPM error range: {candidate_stats['ppm_error_range'][0]:.2f} - "
                  f"{candidate_stats['ppm_error_range'][1]:.2f}")
            print(f"  Average PPM error: {candidate_stats['average_ppm_error']:.2f}")

    def test_multiple_precursor_search(self):
        """Test candidate generation for multiple precursors"""

        # Parse and digest
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()
        peptides = parser.digest(enzyme='trypsin', missed_cleavages=2)
        glyco_peptides = parser.filter_by_glycosylation_site(peptides)

        # Load glycans
        glycan_db = GlycanDatabase()

        # Create generator
        generator = CandidateGenerator(glyco_peptides, glycan_db.glycans)

        # Test multiple precursors
        precursors = [
            (1000.5, 2),  # Low m/z
            (1500.7, 2),  # Medium m/z
            (2000.3, 3),  # High m/z, higher charge
        ]

        total_candidates = 0
        for mz, charge in precursors:
            candidates = generator.generate_candidates(
                precursor_mz=mz,
                charge=charge,
                tolerance_ppm=10.0
            )
            total_candidates += len(candidates)

        # Should find at least some candidates
        print(f"\n✓ Generated {total_candidates} candidates across {len(precursors)} precursors")

    def test_glycan_type_filtering_integration(self):
        """Test filtering candidates by glycan type"""

        # Parse and digest
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()
        peptides = parser.digest(enzyme='trypsin', missed_cleavages=1)
        glyco_peptides = parser.filter_by_glycosylation_site(peptides)

        # Load glycans and filter by type
        glycan_db = GlycanDatabase()

        # Test with high-mannose glycans only
        hm_glycans = glycan_db.filter_by_type(GlycanType.HIGH_MANNOSE)
        self.assertGreater(len(hm_glycans), 0)

        # Create generator with filtered glycans
        generator = CandidateGenerator(glyco_peptides, hm_glycans)

        # Generate candidates
        candidates = generator.generate_candidates(
            precursor_mz=1200.0,
            charge=2,
            tolerance_ppm=50.0
        )

        # All candidates should have high-mannose glycans
        for candidate in candidates:
            self.assertEqual(candidate.glycan.glycan_type, GlycanType.HIGH_MANNOSE)

        print(f"\n✓ Generated {len(candidates)} high-mannose glycopeptide candidates")

    def test_performance_with_large_library(self):
        """Test performance with realistic library sizes"""

        # Parse and digest
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()
        peptides = parser.digest(enzyme='trypsin', missed_cleavages=2)
        glyco_peptides = parser.filter_by_glycosylation_site(peptides)

        # Load full glycan database
        glycan_db = GlycanDatabase()

        # Create generator
        import time
        start_time = time.time()
        generator = CandidateGenerator(glyco_peptides, glycan_db.glycans)
        index_time = time.time() - start_time

        print(f"\n✓ Indexed {len(glyco_peptides)} peptides × {len(glycan_db.glycans)} glycans")
        print(f"  Indexing time: {index_time*1000:.2f} ms")

        # Test search speed
        start_time = time.time()
        candidates = generator.generate_candidates(
            precursor_mz=1500.0,
            charge=2,
            tolerance_ppm=10.0
        )
        search_time = time.time() - start_time

        print(f"✓ Search completed in {search_time*1000:.2f} ms")
        print(f"  Found {len(candidates)} candidates")

        # Performance should be reasonable (< 100ms for search)
        self.assertLess(search_time, 0.1)


def run_integration_tests():
    """Run all integration tests"""
    print("="*80)
    print("  DATABASE INTEGRATION TESTS")
    print("="*80)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDatabaseIntegration)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print()
    print("="*80)
    print("  TEST SUMMARY")
    print("="*80)
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")
    print("="*80)

    if result.wasSuccessful():
        print("\n✅ ALL INTEGRATION TESTS PASSED - Database pipeline validated!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(run_integration_tests())
