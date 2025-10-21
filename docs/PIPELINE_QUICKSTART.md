# Glycoproteomics Pipeline - Quick Start Guide

## 🎯 What's Currently Available

This pipeline is under active development. Here's what you can do **right now**:

### ✅ Phase 1: Infrastructure Complete

1. **Convert .raw files to mzML** (ALCOA++ compliant)
2. **Parse mzML spectra** with Pyteomics
3. **Track all operations** with audit logging
4. **Verify file integrity** with SHA-256 checksums

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /path/to/Glycopeptide-Automated-Data-Analysis
pip install -e .
```

### 2. Install ThermoRawFileParser

```bash
# Option 1: Conda (easiest)
conda install -c bioconda thermorawfileparser

# Option 2: Download from GitHub
# https://github.com/compomics/ThermoRawFileParser/releases
```

### 3. Convert Your First RAW File

```python
from src.converters import RawConverter
from src.alcoa import AuditLogger, ChecksumManager

# Initialize ALCOA++ logging
audit = AuditLogger(log_dir="Results/audit_trail")
checksums = ChecksumManager()

# Convert .raw to .mzML
converter = RawConverter()

try:
    mzml_file = converter.convert_to_mzml(
        raw_file_path="path/to/your/sample.raw",
        output_dir="Results/data/02_mzml_files",
        peak_picking=True,  # Enable centroiding
        gzip=True           # Compress output
    )

    # Register file with checksum (ENDURING principle)
    checksum = checksums.register_file(mzml_file)

    # Log operation (TRACEABLE principle)
    audit.log_file_operation("created", mzml_file, checksum=checksum)

    print(f"✅ Conversion successful: {mzml_file}")
    print(f"   SHA-256: {checksum}")

except Exception as e:
    audit.log(f"Conversion failed: {e}", level="ERROR")
    print(f"❌ Error: {e}")

finally:
    # Save audit trail
    audit_file = audit.save()
    print(f"📋 Audit trail: {audit_file}")
```

### 4. Parse and Analyze Spectra

```python
from src.converters import MzMLParser
import matplotlib.pyplot as plt

# Parse mzML file
parser = MzMLParser()
spectra = parser.parse(
    mzml_file_path="Results/data/02_mzml_files/sample.mzML.gz",
    ms_level=2,      # MS/MS spectra only
    min_peaks=10     # Minimum peak count
)

print(f"📊 Loaded {len(spectra)} MS/MS spectra")

# Analyze first spectrum
spectrum = spectra[0]
print(f"\n🔬 Spectrum Details:")
print(f"   Scan Number: {spectrum.scan_number}")
print(f"   Precursor m/z: {spectrum.precursor_mz:.4f}")
print(f"   Charge: {spectrum.precursor_charge}+")
print(f"   Fragment Peaks: {len(spectrum.mz_array)}")
print(f"   RT: {spectrum.retention_time:.2f} seconds")

# Plot spectrum
plt.figure(figsize=(12, 4))
plt.vlines(spectrum.mz_array, 0, spectrum.intensity_array, color='steelblue')
plt.xlabel('m/z')
plt.ylabel('Intensity')
plt.title(f'MS/MS Spectrum: Scan {spectrum.scan_number} (Precursor: {spectrum.precursor_mz:.2f} m/z)')
plt.tight_layout()
plt.savefig('Results/example_spectrum.png', dpi=300)
print(f"\n📈 Spectrum plot saved to: Results/example_spectrum.png")
```

### 5. Validate ALCOA++ Compliance

```python
from src.alcoa import ComplianceValidator

# Validate compliance
validator = ComplianceValidator(audit, checksums)
is_compliant, report = validator.validate_all()

print(f"\n✅ ALCOA++ Compliance Check:")
for principle, details in report["principles"].items():
    status = "✅" if details["compliant"] else "❌"
    print(f"   {status} {principle}: {details['message']}")

# Save compliance report
report_path = validator.save_report(report)
print(f"\n📋 Compliance report: {report_path}")
```

---

## 📂 Output Structure

After running the examples above, you'll have:

```
Results/
├── audit_trail/
│   ├── 20251021_143201_audit_trail.json      # Complete operation log
│   ├── 20251021_143201_processing_log.txt    # Human-readable log
│   └── file_checksums.json                    # SHA-256 hashes
├── data/
│   └── 02_mzml_files/
│       └── sample.mzML.gz                     # Converted spectrum file
├── reports/
│   └── alcoa_compliance_report.json           # Compliance validation
└── example_spectrum.png                       # Visualization
```

---

## 📊 Example Output

### Audit Trail (JSON)
```json
{
  "run_id": "20251021_143201",
  "user": "researcher@university.edu",
  "start_time": "2025-10-21T14:32:01",
  "events": [
    {
      "timestamp": "2025-10-21T14:32:05",
      "level": "INFO",
      "message": "File created: sample.mzML.gz",
      "details": {
        "operation": "created",
        "file_path": "/path/to/sample.mzML.gz",
        "sha256": "a1b2c3d4e5f6..."
      }
    }
  ],
  "alcoa_compliance": {
    "attributable": true,
    "legible": true,
    "contemporaneous": true,
    "traceable": true,
    ...
  }
}
```

### Processing Log (Human-Readable)
```
2025-10-21 14:32:01 | INFO     | Audit logger initialized
2025-10-21 14:32:05 | INFO     | Converting sample.raw to mzML
2025-10-21 14:33:12 | INFO     | File created: sample.mzML.gz | Details: {"sha256": "a1b2c3d4..."}
2025-10-21 14:33:15 | INFO     | Audit trail saved to Results/audit_trail/20251021_143201_audit_trail.json
```

---

## 🔧 Troubleshooting

### ThermoRawFileParser Not Found

```
RuntimeError: ThermoRawFileParser not found. Please install it:
  - Download from: https://github.com/compomics/ThermoRawFileParser/releases
  - Or use conda: conda install -c bioconda thermorawfileparser
```

**Solution**:
```bash
# Install via Conda
conda install -c bioconda thermorawfileparser

# Or download manually and set path
converter = RawConverter(thermo_parser_path="/path/to/ThermoRawFileParser.exe")
```

### Pyteomics Import Error

```
ImportError: Pyteomics is required for mzML parsing.
Install with: pip install pyteomics
```

**Solution**:
```bash
pip install pyteomics>=4.6.0
```

### File Not Found

```
FileNotFoundError: RAW file not found: path/to/sample.raw
```

**Solution**: Verify the file path is correct:
```python
from pathlib import Path
raw_file = Path("path/to/sample.raw")
print(f"Exists: {raw_file.exists()}")
print(f"Absolute path: {raw_file.resolve()}")
```

---

## 🎓 Next Steps

Once you're comfortable with the current functionality:

1. **Week 2**: Database modules (FASTA parser, glycan database)
2. **Week 3**: Scoring algorithms (SEQUEST-style XCorr)
3. **Week 4**: FDR calculation and SMILES integration
4. **Week 5**: Benchmarking against pGlyco3, Byonic

See `docs/GLYCOPROTEOMICS_PIPELINE_GUIDE.md` for the complete roadmap.

---

## 📚 Further Reading

- **ALCOA++ Principles**: `docs/GLYCOPROTEOMICS_PIPELINE_GUIDE.md#alcoa-implementation`
- **SEQUEST Algorithm**: Eng et al. (2011), *J. Proteome Res.* 10(9), 3935-3943
- **ThermoRawFileParser**: https://github.com/compomics/ThermoRawFileParser
- **Pyteomics**: https://pyteomics.readthedocs.io/

---

**Questions?** Open an issue on the GitHub repository or consult the comprehensive guide.
