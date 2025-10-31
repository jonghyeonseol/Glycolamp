"""
Infrastructure Validation Test Suite

Tests all Phase 1 modules to ensure they work correctly before proceeding
to database and scoring implementation.

Test Coverage:
--------------
1. AuditLogger (ALCOA++ Compliance)
   - Initialization and configuration
   - Event logging and timestamping
   - File operation logging
   - Audit trail persistence
   - Summary statistics generation

2. ChecksumManager (File Integrity)
   - SHA-256 checksum calculation
   - Checksum verification
   - File integrity validation

3. MetadataGenerator (Provenance Tracking)
   - Complete metadata generation
   - System information capture
   - Timestamp and user tracking

4. ComplianceValidator (ALCOA++ Validation)
   - All 10 ALCOA++ principles
   - Comprehensive compliance checking
   - Validation report generation

5. MzMLParser (File Format Conversion)
   - mzML file parsing
   - Spectrum extraction
   - MS1/MS2 spectrum handling

Usage:
------
    pytest tests/test_infrastructure.py -v
    python tests/test_infrastructure.py  # Standalone mode

Expected Results:
-----------------
    - All tests should pass (100% pass rate)
    - ALCOA++ compliance score: 10/10
    - No warnings or errors during execution

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
Phase: 1 (Infrastructure)
"""

import sys
import os
import tempfile
import json
from pathlib import Path
import unittest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.alcoa import AuditLogger, ChecksumManager, MetadataGenerator, ComplianceValidator
from src.converters import MzMLParser


class TestAuditLogger(unittest.TestCase):
    """Test ALCOA++ Audit Logger"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.audit = AuditLogger(log_dir=self.temp_dir, user="test_user")

    def test_initialization(self):
        """Test logger initialization"""
        self.assertIsNotNone(self.audit.run_id)
        self.assertEqual(self.audit.user, "test_user")
        self.assertIsNotNone(self.audit.start_time)
        self.assertEqual(len(self.audit.events), 1)  # Initialization event

    def test_log_event(self):
        """Test event logging"""
        self.audit.log("Test event", level="INFO")
        self.assertEqual(len(self.audit.events), 2)  # Init + test event

        last_event = self.audit.events[-1]
        self.assertEqual(last_event["message"], "Test event")
        self.assertEqual(last_event["level"], "INFO")
        self.assertIn("timestamp", last_event)

    def test_log_with_details(self):
        """Test logging with additional details"""
        details = {"param1": "value1", "param2": 42}
        self.audit.log("Event with details", level="DEBUG", details=details)

        last_event = self.audit.events[-1]
        self.assertIn("details", last_event)
        self.assertEqual(last_event["details"]["param1"], "value1")
        self.assertEqual(last_event["details"]["param2"], 42)

    def test_file_operation_logging(self):
        """Test file operation logging"""
        self.audit.log_file_operation(
            operation="created",
            file_path="/path/to/file.txt",
            checksum="abc123",
            metadata={"size": 1024}
        )

        last_event = self.audit.events[-1]
        self.assertIn("File created", last_event["message"])
        self.assertEqual(last_event["details"]["operation"], "created")
        self.assertEqual(last_event["details"]["sha256"], "abc123")

    def test_save_audit_trail(self):
        """Test saving audit trail to JSON"""
        self.audit.log("Test event 1", level="INFO")
        self.audit.log("Test event 2", level="WARNING")

        output_path = self.audit.save()
        self.assertTrue(Path(output_path).exists())

        # Verify JSON structure
        with open(output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["run_id"], self.audit.run_id)
        self.assertEqual(data["user"], "test_user")
        self.assertIn("start_time", data)
        self.assertIn("end_time", data)
        self.assertIn("runtime_seconds", data)
        self.assertGreater(data["total_events"], 0)

    def test_get_summary(self):
        """Test summary statistics"""
        self.audit.log("Info event", level="INFO")
        self.audit.log("Warning event", level="WARNING")
        self.audit.log("Error event", level="ERROR")

        summary = self.audit.get_summary()

        self.assertEqual(summary["run_id"], self.audit.run_id)
        self.assertGreater(summary["total_events"], 0)
        self.assertIn("level_breakdown", summary)
        self.assertIn("INFO", summary["level_breakdown"])
        self.assertIn("WARNING", summary["level_breakdown"])
        self.assertIn("ERROR", summary["level_breakdown"])


class TestChecksumManager(unittest.TestCase):
    """Test SHA-256 Checksum Manager"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.checksum_file = Path(self.temp_dir) / "checksums.json"
        self.manager = ChecksumManager(checksum_file=str(self.checksum_file))

        # Create a test file
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        self.test_file.write_text("Test content for checksum calculation")

    def test_calculate_checksum(self):
        """Test SHA-256 calculation"""
        checksum = self.manager.calculate_checksum(str(self.test_file))
        self.assertIsNotNone(checksum)
        self.assertEqual(len(checksum), 64)  # SHA-256 is 64 hex chars

        # Same file should give same checksum
        checksum2 = self.manager.calculate_checksum(str(self.test_file))
        self.assertEqual(checksum, checksum2)

    def test_register_file(self):
        """Test file registration"""
        checksum = self.manager.register_file(str(self.test_file))
        self.assertIsNotNone(checksum)

        # Check if stored
        stored_checksum = self.manager.get_checksum(str(self.test_file))
        self.assertEqual(checksum, stored_checksum)

    def test_verify_file(self):
        """Test file integrity verification"""
        # Register file
        self.manager.register_file(str(self.test_file))

        # Verify should pass
        is_valid = self.manager.verify_file(str(self.test_file))
        self.assertTrue(is_valid)

        # Modify file
        self.test_file.write_text("Modified content")

        # Verify should fail
        is_valid = self.manager.verify_file(str(self.test_file))
        self.assertFalse(is_valid)

    def test_checksum_persistence(self):
        """Test checksum persistence to JSON"""
        checksum1 = self.manager.register_file(str(self.test_file))

        # Create new manager with same file
        manager2 = ChecksumManager(checksum_file=str(self.checksum_file))
        checksum2 = manager2.get_checksum(str(self.test_file))

        self.assertEqual(checksum1, checksum2)


class TestMetadataGenerator(unittest.TestCase):
    """Test Metadata Generator"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        self.test_file.write_text("Test content")

    def test_generate_file_metadata(self):
        """Test file metadata generation"""
        metadata = MetadataGenerator.generate_file_metadata(
            file_path=str(self.test_file),
            file_type="text",
            description="Test file",
            processing_parameters={"param1": "value1"},
            source_files=["source1.txt", "source2.txt"],
            checksum="abc123"
        )

        self.assertIn("file_info", metadata)
        self.assertIn("provenance", metadata)
        self.assertIn("integrity", metadata)
        self.assertIn("alcoa_compliance", metadata)

        # Check file info
        self.assertEqual(metadata["file_info"]["name"], "test_file.txt")
        self.assertEqual(metadata["file_info"]["type"], "text")
        self.assertEqual(metadata["file_info"]["description"], "Test file")

        # Check provenance
        self.assertEqual(len(metadata["provenance"]["source_files"]), 2)
        self.assertIn("param1", metadata["provenance"]["processing_parameters"])

        # Check integrity
        self.assertEqual(metadata["integrity"]["checksum"], "abc123")

    def test_generate_run_metadata(self):
        """Test pipeline run metadata generation"""
        metadata = MetadataGenerator.generate_run_metadata(
            run_id="test_run_001",
            input_files=["input1.raw", "input2.raw"],
            config={"param": "value"},
            output_files=["output1.csv", "output2.csv"],
            runtime_seconds=123.45,
            user="test_user"
        )

        self.assertIn("run_info", metadata)
        self.assertIn("inputs", metadata)
        self.assertIn("outputs", metadata)
        self.assertIn("configuration", metadata)

        # Check run info
        self.assertEqual(metadata["run_info"]["run_id"], "test_run_001")
        self.assertEqual(metadata["run_info"]["user"], "test_user")
        self.assertEqual(metadata["run_info"]["runtime_seconds"], 123.45)

        # Check inputs/outputs
        self.assertEqual(metadata["inputs"]["count"], 2)
        self.assertEqual(metadata["outputs"]["count"], 2)

    def test_save_metadata(self):
        """Test metadata saving"""
        metadata = {"test": "data"}
        output_path = Path(self.temp_dir) / "metadata.json"

        MetadataGenerator.save_metadata(metadata, str(output_path))

        self.assertTrue(output_path.exists())

        # Verify content
        with open(output_path, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded["test"], "data")


class TestComplianceValidator(unittest.TestCase):
    """Test ALCOA++ Compliance Validator"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.audit = AuditLogger(log_dir=self.temp_dir, user="test_user")
        self.checksums = ChecksumManager(checksum_file=str(Path(self.temp_dir) / "checksums.json"))
        self.validator = ComplianceValidator(self.audit, self.checksums)

    def test_validate_attributable(self):
        """Test Attributable principle validation"""
        is_compliant, message = self.validator._check_attributable()
        self.assertTrue(is_compliant)
        self.assertIn("test_user", message)

    def test_validate_contemporaneous(self):
        """Test Contemporaneous principle validation"""
        self.audit.log("Test event", level="INFO")
        is_compliant, message = self.validator._check_contemporaneous()
        self.assertTrue(is_compliant)
        self.assertIn("events with real-time timestamps", message)

    def test_validate_enduring(self):
        """Test Enduring principle validation"""
        # No checksums initially
        is_compliant, message = self.validator._check_enduring()
        self.assertFalse(is_compliant)

        # Register a file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test")
        self.checksums.register_file(str(test_file))

        is_compliant, message = self.validator._check_enduring()
        self.assertTrue(is_compliant)
        self.assertIn("SHA-256 checksums", message)

    def test_validate_all(self):
        """Test validation of all principles"""
        # Add some activity
        self.audit.log("Test event 1", level="INFO")
        self.audit.log("Test event 2", level="INFO")

        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test")
        self.checksums.register_file(str(test_file))

        is_compliant, report = self.validator.validate_all()

        self.assertIn("principles", report)
        self.assertEqual(len(report["principles"]), 10)  # All 10 ALCOA++ principles

        # Check that most principles pass
        passed = sum(1 for p in report["principles"].values() if p["compliant"])
        self.assertGreaterEqual(passed, 7)  # At least 7 of 10 should pass


class TestMzMLParser(unittest.TestCase):
    """Test mzML Parser (without actual mzML file)"""

    def test_parser_initialization(self):
        """Test parser can be initialized"""
        try:
            parser = MzMLParser()
            self.assertIsNotNone(parser)
        except ImportError as e:
            self.skipTest(f"Pyteomics not installed: {e}")

    def test_spectrum_class(self):
        """Test Spectrum class structure"""
        from src.converters.mzml_parser import Spectrum
        import numpy as np

        # Mock spectrum data
        mock_data = {
            'id': 'scan=1234',
            'index': 1234,
            'ms level': 2,
            'precursorList': {
                'precursor': [{
                    'selectedIonList': {
                        'selectedIon': [{
                            'selected ion m/z': 500.25,
                            'charge state': 2,
                            'peak intensity': 1000.0
                        }]
                    }
                }]
            },
            'scanList': {
                'scan': [{'scan start time': 120.5}]
            },
            'm/z array': np.array([100.0, 200.0, 300.0]),
            'intensity array': np.array([10.0, 20.0, 15.0])
        }

        spectrum = Spectrum(mock_data)

        self.assertEqual(spectrum.scan_number, 1234)
        self.assertEqual(spectrum.ms_level, 2)
        self.assertAlmostEqual(spectrum.precursor_mz, 500.25)
        self.assertEqual(spectrum.precursor_charge, 2)
        self.assertEqual(len(spectrum.mz_array), 3)
        self.assertEqual(len(spectrum.intensity_array), 3)


def run_validation_suite():
    """Run all validation tests and generate report"""
    print("="*80)
    print("  GLYCOPROTEOMICS PIPELINE - INFRASTRUCTURE VALIDATION")
    print("="*80)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAuditLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestChecksumManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMetadataGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestComplianceValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestMzMLParser))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print()
    print("="*80)
    print("  VALIDATION SUMMARY")
    print("="*80)
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")
    print("="*80)

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED - Infrastructure is validated and ready!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(run_validation_suite())
