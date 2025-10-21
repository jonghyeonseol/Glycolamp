"""
Example 1: Convert RAW Files to mzML with ALCOA++ Compliance

This example demonstrates:
1. Converting Thermo .raw files to open mzML format
2. ALCOA++ compliant logging and checksumming
3. Basic quality control checks

Requirements:
- ThermoRawFileParser installed (conda install -c bioconda thermorawfileparser)
- Input: .raw file(s) from Thermo Fisher mass spectrometer
- Output: .mzML.gz file(s) with audit trail

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.converters import RawConverter
from src.alcoa import AuditLogger, ChecksumManager


def convert_raw_files(raw_file_paths, output_dir="Results/data/02_mzml_files"):
    """
    Convert .raw files to .mzML with full ALCOA++ compliance

    Parameters
    ----------
    raw_file_paths : list or str
        Path(s) to .raw file(s)
    output_dir : str
        Output directory for mzML files

    Returns
    -------
    list
        Paths to generated mzML files
    """
    # Ensure input is a list
    if isinstance(raw_file_paths, str):
        raw_file_paths = [raw_file_paths]

    # Initialize ALCOA++ logging
    print("📋 Initializing ALCOA++ audit system...")
    audit = AuditLogger(log_dir="Results/audit_trail")
    checksums = ChecksumManager()

    audit.log("Starting RAW file conversion pipeline", level="INFO", details={
        "input_files": [str(Path(f).name) for f in raw_file_paths],
        "output_directory": output_dir,
    })

    # Initialize converter
    converter = RawConverter()

    # Check if ThermoRawFileParser is available
    if not converter._is_thermo_parser_available():
        error_msg = (
            "ThermoRawFileParser not found!\n"
            "Install with: conda install -c bioconda thermorawfileparser\n"
            "Or download from: https://github.com/compomics/ThermoRawFileParser/releases"
        )
        audit.log(error_msg, level="ERROR")
        print(f"❌ {error_msg}")
        audit.save()
        return []

    # Convert files
    mzml_files = []
    successful = 0
    failed = 0

    for i, raw_file in enumerate(raw_file_paths, 1):
        raw_file = Path(raw_file)

        print(f"\n[{i}/{len(raw_file_paths)}] Converting: {raw_file.name}")
        audit.log(f"Converting file {i}/{len(raw_file_paths)}: {raw_file.name}", level="INFO")

        try:
            # Check if file exists
            if not raw_file.exists():
                raise FileNotFoundError(f"File not found: {raw_file}")

            # Convert
            mzml_file = converter.convert_to_mzml(
                raw_file_path=str(raw_file),
                output_dir=output_dir,
                peak_picking=True,   # Centroid mode (removes noise)
                gzip=True,           # Compress output
                metadata_format="json"
            )

            # Calculate checksum (ENDURING principle)
            checksum = checksums.register_file(mzml_file)

            # Log successful conversion (TRACEABLE principle)
            audit.log_file_operation(
                operation="created",
                file_path=mzml_file,
                checksum=checksum,
                metadata={
                    "source_file": str(raw_file),
                    "peak_picking": True,
                    "compression": "gzip"
                }
            )

            mzml_files.append(mzml_file)
            successful += 1

            print(f"   ✅ Success: {Path(mzml_file).name}")
            print(f"   📊 Size: {Path(mzml_file).stat().st_size / 1024 / 1024:.1f} MB")
            print(f"   🔒 SHA-256: {checksum[:16]}...")

        except Exception as e:
            failed += 1
            audit.log(f"Conversion failed for {raw_file.name}: {str(e)}", level="ERROR")
            print(f"   ❌ Failed: {e}")
            continue

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Conversion Summary:")
    print(f"   Total files: {len(raw_file_paths)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"{'='*60}")

    audit.log("Conversion pipeline completed", level="INFO", details={
        "total_files": len(raw_file_paths),
        "successful": successful,
        "failed": failed,
    })

    # Save audit trail (TRACEABLE, ENDURING principles)
    audit_file = audit.save()
    print(f"\n📋 Audit trail saved: {audit_file}")
    print(f"📋 Checksums saved: Results/audit_trail/file_checksums.json")

    # Print text log location
    print(f"📋 Human-readable log: {audit.text_log_path}")

    return mzml_files


if __name__ == "__main__":
    # Example usage
    print("="*60)
    print("  RAW to mzML Conversion (ALCOA++ Compliant)")
    print("="*60)

    # MODIFY THIS: Add your .raw file paths here
    raw_files = [
        # "path/to/sample1.raw",
        # "path/to/sample2.raw",
    ]

    if not raw_files:
        print("\n⚠️  No input files specified!")
        print("\nTo use this script:")
        print("1. Edit this file and add your .raw file paths to the 'raw_files' list")
        print("2. Run: python examples/example_01_raw_conversion.py")
        print("\nExample:")
        print("   raw_files = ['Data/cancer_01.raw', 'Data/normal_01.raw']")
        sys.exit(0)

    # Run conversion
    mzml_files = convert_raw_files(raw_files)

    if mzml_files:
        print(f"\n✅ Conversion complete! Generated {len(mzml_files)} mzML files.")
        print(f"\nNext steps:")
        print(f"  1. Parse spectra: python examples/example_02_parse_spectra.py")
        print(f"  2. Validate compliance: python examples/example_03_validate_compliance.py")
    else:
        print(f"\n❌ No files converted. Check the error messages above.")
