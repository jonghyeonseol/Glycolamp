#!/usr/bin/env python3
"""
Installation and Infrastructure Validation Script

Checks that all dependencies and modules are correctly installed
and functioning before proceeding with development.

Usage:
    python scripts/validate_installation.py

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
"""

import sys
import os
import platform
import subprocess
from pathlib import Path
from importlib import import_module


def print_header(text):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def print_status(check_name, passed, details=""):
    """Print check status with consistent formatting"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status:12} | {check_name}")
    if details:
        print(f"               {details}")


def check_python_version():
    """Check Python version"""
    print_header("PYTHON VERSION")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    required_major = 3
    required_minor = 9

    passed = version.major >= required_major and version.minor >= required_minor

    print_status(
        "Python Version",
        passed,
        f"Version: {version_str} (Required: >= {required_major}.{required_minor})"
    )

    print(f"\n  Platform: {platform.platform()}")
    print(f"  Python: {sys.executable}")

    return passed


def check_dependencies():
    """Check required Python packages"""
    print_header("PYTHON DEPENDENCIES")

    dependencies = {
        'pandas': '1.5.0',
        'numpy': '1.23.0',
        'matplotlib': '3.6.0',
        'scipy': '1.10.0',
        'scikit-learn': '1.2.0',
        'seaborn': '0.12.0',
        'pyyaml': '6.0',
        'pyteomics': '4.6.0',
        'biopython': '1.83',
        'tqdm': '4.65.0',
    }

    all_passed = True

    for package, min_version in dependencies.items():
        try:
            module = import_module(package.replace('-', '_'))

            # Get version
            version = getattr(module, '__version__', 'unknown')

            print_status(
                f"{package:20}",
                True,
                f"Version: {version}"
            )

        except ImportError:
            print_status(f"{package:20}", False, "Not installed")
            all_passed = False

    return all_passed


def check_rdkit():
    """Check RDKit installation (optional for Week 1)"""
    print_header("CHEMOINFORMATICS (Optional for Week 1)")

    try:
        from rdkit import Chem
        from rdkit import __version__
        print_status("RDKit", True, f"Version: {__version__}")
        return True
    except ImportError:
        print_status(
            "RDKit",
            False,
            "Not installed (Required for Week 4 - SMILES generation)"
        )
        return False


def check_thermo_parser():
    """Check ThermoRawFileParser installation"""
    print_header("EXTERNAL TOOLS")

    is_windows = platform.system() == "Windows"

    # Try to run ThermoRawFileParser
    try:
        if is_windows:
            cmd = ["ThermoRawFileParser", "--help"]
        else:
            cmd = ["ThermoRawFileParser", "--help"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=5,
            text=True
        )

        if result.returncode == 0 or "ThermoRawFileParser" in result.stdout + result.stderr:
            print_status("ThermoRawFileParser", True, "Installed and accessible")
            return True
        else:
            raise FileNotFoundError

    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        print_status(
            "ThermoRawFileParser",
            False,
            "Not found - Install: conda install -c bioconda thermorawfileparser"
        )
        return False


def check_pipeline_modules():
    """Check pipeline modules can be imported"""
    print_header("PIPELINE MODULES")

    modules = [
        ('src.alcoa', 'AuditLogger'),
        ('src.alcoa', 'ChecksumManager'),
        ('src.alcoa', 'MetadataGenerator'),
        ('src.alcoa', 'ComplianceValidator'),
        ('src.converters', 'RawConverter'),
        ('src.converters', 'MzMLParser'),
    ]

    all_passed = True

    for module_path, class_name in modules:
        try:
            module = import_module(module_path)
            cls = getattr(module, class_name)
            print_status(f"{module_path}.{class_name}", True, "Import successful")
        except Exception as e:
            print_status(f"{module_path}.{class_name}", False, f"Error: {e}")
            all_passed = False

    return all_passed


def check_directory_structure():
    """Check required directories exist"""
    print_header("DIRECTORY STRUCTURE")

    required_dirs = [
        "src/alcoa",
        "src/converters",
        "src/database",
        "src/scoring",
        "src/chemoinformatics",
        "src/workflows",
        "Results/audit_trail",
        "Results/data/01_raw_files",
        "Results/data/02_mzml_files",
        "Results/data/03_preprocessed",
        "Results/data/04_results",
        "Results/reports",
        "docs",
        "examples",
        "tests",
    ]

    all_passed = True

    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        status = "Created" if exists else "Missing"
        print_status(f"{dir_path:40}", exists, status)
        if not exists:
            all_passed = False

    return all_passed


def check_example_scripts():
    """Check example scripts exist"""
    print_header("EXAMPLE SCRIPTS")

    examples = [
        "examples/example_01_raw_conversion.py",
        "examples/example_02_parse_spectra.py",
        "examples/README.md",
    ]

    all_passed = True

    for example in examples:
        exists = Path(example).exists()
        print_status(f"{Path(example).name:40}", exists)
        if not exists:
            all_passed = False

    return all_passed


def check_documentation():
    """Check documentation files exist"""
    print_header("DOCUMENTATION")

    docs = [
        "CLAUDE.md",
        "docs/GLYCOPROTEOMICS_PIPELINE_GUIDE.md",
        "docs/PIPELINE_QUICKSTART.md",
        "IMPLEMENTATION_SUMMARY.md",
        "PROJECT_STATUS.md",
        "README.md",
    ]

    all_passed = True

    for doc in docs:
        exists = Path(doc).exists()
        if exists:
            size_kb = Path(doc).stat().st_size / 1024
            details = f"{size_kb:.1f} KB"
        else:
            details = "Missing"

        print_status(f"{Path(doc).name:45}", exists, details)
        if not exists:
            all_passed = False

    return all_passed


def run_unit_tests():
    """Run unit tests if available"""
    print_header("UNIT TESTS")

    test_file = Path("tests/test_infrastructure.py")

    if not test_file.exists():
        print_status("Unit tests", False, "test_infrastructure.py not found")
        return False

    try:
        # Try pytest first
        try:
            result = subprocess.run(
                ["pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print_status("Unit tests (pytest)", True, "All tests passed")
                return True
            else:
                print_status("Unit tests (pytest)", False, "Some tests failed")
                print(f"\n{result.stdout}")
                return False

        except FileNotFoundError:
            # Fallback to unittest
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print_status("Unit tests (unittest)", True, "All tests passed")
                return True
            else:
                print_status("Unit tests (unittest)", False, "Some tests failed")
                print(f"\n{result.stdout}")
                return False

    except subprocess.TimeoutExpired:
        print_status("Unit tests", False, "Tests timed out")
        return False
    except Exception as e:
        print_status("Unit tests", False, f"Error running tests: {e}")
        return False


def main():
    """Run all validation checks"""
    print("\n" + "="*80)
    print("  GLYCOPROTEOMICS PIPELINE - INFRASTRUCTURE VALIDATION")
    print("  Version: 4.0.0-alpha")
    print("  Phase: 1 (Infrastructure)")
    print("="*80)

    results = {}

    # Run checks
    results['python'] = check_python_version()
    results['dependencies'] = check_dependencies()
    results['rdkit'] = check_rdkit()  # Optional
    results['thermo_parser'] = check_thermo_parser()
    results['modules'] = check_pipeline_modules()
    results['directories'] = check_directory_structure()
    results['examples'] = check_example_scripts()
    results['documentation'] = check_documentation()
    results['tests'] = run_unit_tests()

    # Final summary
    print_header("VALIDATION SUMMARY")

    critical_checks = ['python', 'dependencies', 'modules', 'directories']
    optional_checks = ['rdkit', 'thermo_parser', 'examples', 'documentation', 'tests']

    critical_passed = all(results[check] for check in critical_checks)
    optional_passed = sum(results[check] for check in optional_checks)

    print(f"  Critical Checks: {sum(results[c] for c in critical_checks)}/{len(critical_checks)}")
    print(f"  Optional Checks: {optional_passed}/{len(optional_checks)}")

    print()

    if critical_passed:
        print("  ✅ INFRASTRUCTURE VALIDATED")
        print("  ➡️  Ready to proceed with Week 2 (Database modules)")
        print()

        if not results['thermo_parser']:
            print("  ⚠️  Note: ThermoRawFileParser not installed")
            print("     Install with: conda install -c bioconda thermorawfileparser")
            print()

        if not results['rdkit']:
            print("  ℹ️  RDKit not installed (required for Week 4)")
            print("     Install with: conda install -c conda-forge rdkit")
            print()

        return 0
    else:
        print("  ❌ CRITICAL ISSUES FOUND")
        print("  ➡️  Fix the issues above before proceeding")
        print()

        print("  Installation commands:")
        print("    pip install -e .")
        print("    conda install -c bioconda thermorawfileparser")
        print()

        return 1


if __name__ == "__main__":
    sys.exit(main())
