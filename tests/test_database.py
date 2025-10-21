"""
Unit Tests for Database Modules

Tests FASTA parser, glycan database, and candidate generator modules.

Usage:
    pytest tests/test_database.py -v
    python tests/test_database.py  # Standalone mode

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


class TestGlycan(unittest.TestCase):
    """Test Glycan class"""

    def test_parse_composition(self):
        """Test composition parsing"""
        glycan = Glycan(composition="H5N4F1A2")
        self.assertEqual(glycan.counts['H'], 5)
        self.assertEqual(glycan.counts['N'], 4)
        self.assertEqual(glycan.counts['F'], 1)
        self.assertEqual(glycan.counts['A'], 2)

    def test_calculate_mass(self):
        """Test mass calculation"""
        glycan = Glycan(composition="H5N4F1A2")
        # H5: 5 * 162.052823 = 810.264115
        # N4: 4 * 203.079373 = 812.317492
        # F1: 1 * 146.057909 = 146.057909
        # A2: 2 * 291.095417 = 582.190834
        # Total: 2350.830350
        self.assertAlmostEqual(glycan.mass, 2350.83, places=1)

    def test_classify_high_mannose(self):
        """Test high-mannose classification"""
        glycan = Glycan(composition="H5N2")
        self.assertEqual(glycan.glycan_type, GlycanType.HIGH_MANNOSE)

    def test_classify_fucosylated(self):
        """Test fucosylated classification"""
        glycan = Glycan(composition="H5N4F1")
        self.assertEqual(glycan.glycan_type, GlycanType.FUCOSYLATED)

    def test_classify_sialylated(self):
        """Test sialylated classification"""
        glycan = Glycan(composition="H5N4A2")
        self.assertEqual(glycan.glycan_type, GlycanType.SIALYLATED)

    def test_classify_sialofucosylated(self):
        """Test sialofucosylated classification"""
        glycan = Glycan(composition="H5N4F1A2")
        self.assertEqual(glycan.glycan_type, GlycanType.SIALOFUCOSYLATED)

    def test_classify_complex(self):
        """Test complex/hybrid classification"""
        glycan = Glycan(composition="H3N4")
        self.assertEqual(glycan.glycan_type, GlycanType.COMPLEX_HYBRID)


class TestGlycanDatabase(unittest.TestCase):
    """Test GlycanDatabase class"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = GlycanDatabase()

    def test_generate_common_glycans(self):
        """Test common glycan generation"""
        self.assertGreater(len(self.db.glycans), 50)
        self.assertIn("H5N4F1", self.db.composition_index)

    def test_get_glycan_by_composition(self):
        """Test glycan retrieval"""
        glycan = self.db.get_glycan_by_composition("H5N4F1")
        self.assertIsNotNone(glycan)
        self.assertEqual(glycan.composition, "H5N4F1")

    def test_calculate_mass(self):
        """Test mass calculation via database"""
        mass = self.db.calculate_mass("H5N4F1")
        self.assertGreater(mass, 1700)
        self.assertLess(mass, 1800)

    def test_filter_by_type(self):
        """Test filtering by glycan type"""
        hm_glycans = self.db.filter_by_type(GlycanType.HIGH_MANNOSE)
        self.assertGreater(len(hm_glycans), 0)
        for glycan in hm_glycans:
            self.assertEqual(glycan.glycan_type, GlycanType.HIGH_MANNOSE)

    def test_get_statistics(self):
        """Test database statistics"""
        stats = self.db.get_statistics()
        self.assertIn("total_glycans", stats)
        self.assertIn("type_distribution", stats)
        self.assertGreater(stats["total_glycans"], 0)

    def test_load_from_file(self):
        """Test loading from custom file"""
        # Create temporary glycan file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("H5N2\n")
            f.write("H6N2\n")
            f.write("H5N4F1\n")
            temp_file = f.name

        try:
            db = GlycanDatabase(glycan_file_path=temp_file)
            self.assertEqual(len(db.glycans), 3)
        finally:
            os.unlink(temp_file)


class TestPeptide(unittest.TestCase):
    """Test Peptide class"""

    def test_calculate_mass(self):
        """Test peptide mass calculation"""
        peptide = Peptide(
            sequence="NGTIINEK",
            protein_id="TEST_PROTEIN",
            start_position=1,
            end_position=8
        )
        # N: 114.04293, G: 57.02146, T: 101.04768, I: 113.08406, I: 113.08406,
        # N: 114.04293, E: 129.04259, K: 128.09496
        # Total AA: 869.46067 + Water: 18.01056 = 887.47123
        self.assertAlmostEqual(peptide.mass, 887.47, places=1)

    def test_glycosylation_site_detection(self):
        """Test glycosylation site in peptide"""
        parser = FastaParser.__new__(FastaParser)
        has_glyco, sites = parser._has_glycosylation_motif("NGTIINEK")
        self.assertTrue(has_glyco)
        self.assertEqual(sites, [0])  # N at position 0


class TestFastaParser(unittest.TestCase):
    """Test FastaParser class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary FASTA file
        self.temp_fasta = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.fasta'
        )
        self.temp_fasta.write(">TEST_PROTEIN Test protein description\n")
        self.temp_fasta.write("NGTIINEKAGFAGDDAPRAVFPSIVGRPRHQGVMVGMGQK\n")
        self.temp_fasta.write(">TEST_PROTEIN2 Another test protein\n")
        self.temp_fasta.write("MKLNISFPATGCQKLIEVDDERRGYNAQEYYDRIPELR\n")
        self.temp_fasta.close()

    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_fasta.name)

    def test_parse_fasta(self):
        """Test FASTA parsing"""
        parser = FastaParser(self.temp_fasta.name)
        proteins = parser.parse()
        self.assertEqual(len(proteins), 2)
        self.assertEqual(proteins[0].id, "TEST_PROTEIN")

    def test_tryptic_digestion(self):
        """Test tryptic digestion"""
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()
        peptides = parser.digest(enzyme='trypsin', missed_cleavages=0)
        self.assertGreater(len(peptides), 0)

        # Check that peptides end with K or R (trypsin cleavage)
        for peptide in peptides:
            if len(peptide.sequence) > 0:
                last_aa = peptide.sequence[-1]
                # May not always be K/R due to protein terminus
                if peptide.end_position < len(parser.proteins[0].sequence):
                    self.assertIn(last_aa, ['K', 'R'])

    def test_missed_cleavages(self):
        """Test missed cleavage handling"""
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()

        peptides_0 = parser.digest(enzyme='trypsin', missed_cleavages=0)
        peptides_2 = parser.digest(enzyme='trypsin', missed_cleavages=2)

        # More peptides with missed cleavages
        self.assertGreater(len(peptides_2), len(peptides_0))

    def test_glycosylation_motif_detection(self):
        """Test N-glycosylation motif detection"""
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()
        peptides = parser.digest(enzyme='trypsin', missed_cleavages=2)

        # Filter for glycosylation sites
        glyco_peptides = parser.filter_by_glycosylation_site(peptides)
        self.assertGreater(len(glyco_peptides), 0)

        # All filtered peptides should have glycosylation sites
        for peptide in glyco_peptides:
            self.assertTrue(peptide.has_glycosylation_site)

    def test_length_filtering(self):
        """Test peptide length filtering"""
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()
        peptides = parser.digest(
            enzyme='trypsin',
            missed_cleavages=1,
            min_length=6,
            max_length=30
        )

        for peptide in peptides:
            self.assertGreaterEqual(len(peptide.sequence), 6)
            self.assertLessEqual(len(peptide.sequence), 30)

    def test_get_statistics(self):
        """Test peptide statistics"""
        parser = FastaParser(self.temp_fasta.name)
        parser.parse()
        peptides = parser.digest(enzyme='trypsin', missed_cleavages=2)

        stats = parser.get_statistics(peptides)
        self.assertIn("total_peptides", stats)
        self.assertIn("with_glycosylation_sites", stats)
        self.assertGreater(stats["total_peptides"], 0)


class TestCandidateGenerator(unittest.TestCase):
    """Test CandidateGenerator class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock peptides
        self.peptides = [
            Peptide(
                sequence="NGTIINEK",
                protein_id="TEST",
                start_position=1,
                end_position=8,
                has_glycosylation_site=True,
                glycosylation_sites=[0]
            ),
            Peptide(
                sequence="AGFAGDDAPR",
                protein_id="TEST",
                start_position=9,
                end_position=18,
                has_glycosylation_site=False,
                glycosylation_sites=[]
            ),
        ]

        # Create glycan database
        self.glycan_db = GlycanDatabase()
        self.glycans = self.glycan_db.glycans[:10]  # Use first 10 glycans

        # Create candidate generator
        self.generator = CandidateGenerator(self.peptides, self.glycans)

    def test_calculate_neutral_mass(self):
        """Test neutral mass calculation"""
        # m/z = 1000, z = 2
        # M = (1000 * 2) - (2 * 1.007276) = 2000 - 2.014552 = 1997.985448
        neutral_mass = self.generator.calculate_neutral_mass(1000.0, 2)
        self.assertAlmostEqual(neutral_mass, 1997.985, places=2)

    def test_calculate_ppm_error(self):
        """Test PPM error calculation"""
        # Theoretical: 1000, Observed: 1000.01
        # PPM = ((1000.01 - 1000) / 1000) * 1e6 = 10 ppm
        ppm_error = self.generator.calculate_ppm_error(1000.0, 1000.01)
        self.assertAlmostEqual(ppm_error, 10.0, places=1)

    def test_generate_candidates_basic(self):
        """Test candidate generation"""
        # NGTIINEK mass ≈ 887.47 Da
        # H5N2 mass ≈ 1234.45 Da (from glycan_database.py: 5*162.052823 + 2*203.079373 = 1216.422861)
        # Total ≈ 2103.89 Da
        # m/z for z=2: (2103.89 + 2*1.007276) / 2 ≈ 1052.95

        candidates = self.generator.generate_candidates(
            precursor_mz=1052.95,
            charge=2,
            tolerance_ppm=50.0  # Generous tolerance for testing
        )

        # Should find at least one candidate
        self.assertGreater(len(candidates), 0)

    def test_generate_candidates_with_tolerance(self):
        """Test tolerance filtering"""
        candidates_10ppm = self.generator.generate_candidates(
            precursor_mz=1000.0,
            charge=2,
            tolerance_ppm=10.0
        )

        candidates_100ppm = self.generator.generate_candidates(
            precursor_mz=1000.0,
            charge=2,
            tolerance_ppm=100.0
        )

        # More candidates with looser tolerance
        self.assertGreaterEqual(len(candidates_100ppm), len(candidates_10ppm))

    def test_filter_by_glycosylation_sites(self):
        """Test glycosylation site filtering"""
        # Generate some candidates
        candidates = self.generator.generate_candidates(
            precursor_mz=1500.0,
            charge=2,
            tolerance_ppm=100.0
        )

        # Filter by glycosylation sites
        filtered = self.generator.filter_by_glycosylation_sites(candidates)

        # All should have glycosylation sites
        for candidate in filtered:
            self.assertTrue(candidate.peptide.has_glycosylation_site)

    def test_get_statistics(self):
        """Test candidate statistics"""
        candidates = self.generator.generate_candidates(
            precursor_mz=1500.0,
            charge=2,
            tolerance_ppm=100.0
        )

        if len(candidates) > 0:
            stats = self.generator.get_statistics(candidates)
            self.assertIn("total_candidates", stats)
            self.assertIn("unique_peptides", stats)
            self.assertIn("ppm_error_range", stats)

    def test_get_index_size(self):
        """Test mass index information"""
        index_info = self.generator.get_index_size()
        self.assertIn("total_glycopeptides", index_info)
        self.assertGreater(index_info["glyco_peptides"], 0)


def run_test_suite():
    """Run all database tests"""
    print("="*80)
    print("  DATABASE MODULE UNIT TESTS")
    print("="*80)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGlycan))
    suite.addTests(loader.loadTestsFromTestCase(TestGlycanDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestPeptide))
    suite.addTests(loader.loadTestsFromTestCase(TestFastaParser))
    suite.addTests(loader.loadTestsFromTestCase(TestCandidateGenerator))

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
        print("\n✅ ALL TESTS PASSED - Database modules validated!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(run_test_suite())
