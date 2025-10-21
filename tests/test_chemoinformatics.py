"""
Unit Tests for Chemoinformatics Modules

Tests SMILES conversion for peptides, glycans, and glycopeptides.

Usage:
    pytest tests/test_chemoinformatics.py -v
    python tests/test_chemoinformatics.py  # Standalone mode

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 4 (Week 4)
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chemoinformatics import (
    PeptideSMILESConverter, PeptideSMILES,
    GlycanSMILESConverter, GlycanSMILES,
    GlycopeptideSMILESGenerator, GlycopeptideSMILES
)


class TestPeptideSMILESConverter(unittest.TestCase):
    """Test PeptideSMILESConverter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.converter = PeptideSMILESConverter(use_rdkit=False)

    def test_single_amino_acid(self):
        """Test conversion of single amino acid"""
        result = self.converter.convert("A")
        self.assertEqual(result.sequence, "A")
        self.assertIsNotNone(result.smiles)
        self.assertTrue(result.is_valid)
        self.assertGreater(result.mol_weight, 0)

    def test_short_peptide(self):
        """Test conversion of short peptide"""
        result = self.converter.convert("NGT")
        self.assertEqual(result.sequence, "NGT")
        self.assertIsNotNone(result.smiles)
        self.assertTrue(result.is_valid)
        self.assertGreater(result.mol_weight, 200)

    def test_glycopeptide_sequence(self):
        """Test conversion of glycopeptide sequence"""
        result = self.converter.convert("NGTIINEK")
        self.assertEqual(result.sequence, "NGTIINEK")
        self.assertIsNotNone(result.smiles)
        self.assertTrue(result.is_valid)
        # Expected mass: 887.47 Da (from previous tests)
        self.assertAlmostEqual(result.mol_weight, 887.47, places=1)

    def test_all_amino_acids(self):
        """Test all 20 standard amino acids"""
        all_aa = "ACDEFGHIKLMNPQRSTVWY"
        result = self.converter.convert(all_aa)
        self.assertEqual(result.sequence, all_aa)
        self.assertTrue(result.is_valid)
        self.assertGreater(result.mol_weight, 2000)

    def test_invalid_amino_acid(self):
        """Test handling of invalid amino acid"""
        with self.assertRaises(ValueError):
            self.converter.convert("AXTYZ")

    def test_empty_sequence(self):
        """Test handling of empty sequence"""
        result = self.converter.convert("")
        self.assertEqual(result.smiles, "")

    def test_batch_conversion(self):
        """Test batch conversion of peptides"""
        sequences = ["A", "NG", "NGTIINEK"]
        results = self.converter.batch_convert(sequences)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.is_valid)


class TestGlycanSMILESConverter(unittest.TestCase):
    """Test GlycanSMILESConverter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.converter = GlycanSMILESConverter(use_rdkit=False)

    def test_high_mannose(self):
        """Test high-mannose glycan conversion"""
        result = self.converter.convert("H5N2")
        self.assertEqual(result.composition, "H5N2")
        self.assertIsNotNone(result.smiles)
        self.assertTrue(result.is_valid)
        # H5N2: 5*162.052823 + 2*203.079373 = 1216.422861
        self.assertAlmostEqual(result.mol_weight, 1216.42, places=1)

    def test_complex_glycan(self):
        """Test complex glycan conversion"""
        result = self.converter.convert("H5N4F1A2")
        self.assertEqual(result.composition, "H5N4F1A2")
        self.assertIsNotNone(result.smiles)
        self.assertTrue(result.is_valid)
        # Expected: 2350.83 Da
        self.assertAlmostEqual(result.mol_weight, 2350.83, places=1)

    def test_monosaccharide_counts(self):
        """Test monosaccharide count parsing"""
        result = self.converter.convert("H5N4F1A2")
        self.assertEqual(result.monosaccharide_counts['H'], 5)
        self.assertEqual(result.monosaccharide_counts['N'], 4)
        self.assertEqual(result.monosaccharide_counts['F'], 1)
        self.assertEqual(result.monosaccharide_counts['A'], 2)

    def test_fucosylated_glycan(self):
        """Test fucosylated glycan"""
        result = self.converter.convert("H3N4F1")
        self.assertEqual(result.composition, "H3N4F1")
        self.assertTrue(result.is_valid)
        # H3N4F1: 3*162.052823 + 4*203.079373 + 1*146.057909 = 1444.53
        self.assertAlmostEqual(result.mol_weight, 1444.53, places=1)

    def test_sialylated_glycan(self):
        """Test sialylated glycan"""
        result = self.converter.convert("H5N4A2")
        self.assertEqual(result.composition, "H5N4A2")
        self.assertTrue(result.is_valid)
        self.assertGreater(result.mol_weight, 2000)

    def test_empty_composition(self):
        """Test empty composition"""
        result = self.converter.convert("")
        self.assertEqual(result.smiles, "")

    def test_batch_conversion(self):
        """Test batch conversion of glycans"""
        compositions = ["H3N2", "H5N4F1", "H5N4A2"]
        results = self.converter.batch_convert(compositions)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.is_valid)


class TestGlycopeptideSMILESGenerator(unittest.TestCase):
    """Test GlycopeptideSMILESGenerator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = GlycopeptideSMILESGenerator(use_rdkit=False)

    def test_simple_glycopeptide(self):
        """Test simple glycopeptide generation"""
        result = self.generator.generate("NGT", "H3N2", 0)
        self.assertEqual(result.peptide_sequence, "NGT")
        self.assertEqual(result.glycan_composition, "H3N2")
        self.assertEqual(result.glycosylation_site, 0)
        self.assertIsNotNone(result.peptide_smiles)
        self.assertIsNotNone(result.glycan_smiles)
        self.assertIsNotNone(result.combined_smiles)
        self.assertTrue(result.is_valid)

    def test_complex_glycopeptide(self):
        """Test complex glycopeptide generation"""
        result = self.generator.generate("NGTIINEK", "H5N4F1A2", 0)
        self.assertEqual(result.peptide_sequence, "NGTIINEK")
        self.assertEqual(result.glycan_composition, "H5N4F1A2")
        # Peptide: 887.47, Glycan: 2350.83
        self.assertAlmostEqual(result.peptide_mw, 887.47, places=1)
        self.assertAlmostEqual(result.glycan_mw, 2350.83, places=1)
        self.assertAlmostEqual(result.total_mw, 3238.30, places=1)
        self.assertTrue(result.is_valid)

    def test_molecular_weight_sum(self):
        """Test that total MW equals peptide + glycan"""
        result = self.generator.generate("NGTIINEK", "H5N4F1A2", 0)
        self.assertAlmostEqual(
            result.total_mw,
            result.peptide_mw + result.glycan_mw,
            places=2
        )

    def test_glycosylation_site(self):
        """Test glycosylation site annotation"""
        result = self.generator.generate("NGTIINEK", "H5N2", 0)
        self.assertEqual(result.glycosylation_site, 0)

        result2 = self.generator.generate("AGFAGDDAPR", "H3N2", 5)
        self.assertEqual(result2.glycosylation_site, 5)

    def test_batch_generation(self):
        """Test batch glycopeptide generation"""
        glycopeptides = [
            ("NGT", "H3N2", 0),
            ("NGTIINEK", "H5N4F1A2", 0),
            ("AGFAGDDAPR", "H3N2", 0)
        ]
        results = self.generator.batch_generate(glycopeptides)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.is_valid)
            self.assertGreater(result.total_mw, 0)

    def test_to_dict(self):
        """Test conversion to dictionary"""
        result = self.generator.generate("NGT", "H3N2", 0)
        d = result.to_dict()
        self.assertIn('peptide_sequence', d)
        self.assertIn('glycan_composition', d)
        self.assertIn('combined_smiles', d)
        self.assertIn('total_mw', d)

    def test_csv_export(self):
        """Test CSV export functionality"""
        glycopeptides = [
            ("NGT", "H3N2", 0),
            ("NGTIINEK", "H5N4F1A2", 0)
        ]
        results = self.generator.batch_generate(glycopeptides)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_file = f.name

        try:
            # Export to CSV
            self.generator.to_csv(results, temp_file)

            # Read back and verify
            import csv
            with open(temp_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 2)
                self.assertIn('peptide_sequence', rows[0])
                self.assertIn('combined_smiles', rows[0])
        finally:
            os.unlink(temp_file)


def run_test_suite():
    """Run all chemoinformatics tests"""
    print("="*80)
    print("  CHEMOINFORMATICS MODULE UNIT TESTS")
    print("="*80)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPeptideSMILESConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestGlycanSMILESConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestGlycopeptideSMILESGenerator))

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
        print("\n✅ ALL TESTS PASSED - Chemoinformatics modules validated!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(run_test_suite())
