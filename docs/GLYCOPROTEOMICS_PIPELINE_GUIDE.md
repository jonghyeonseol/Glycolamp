# Glycoproteomics Pipeline: ALCOA++ Compliant with SEQUEST-Inspired Scoring

**Version**: 1.0.0-alpha
**Status**: Infrastructure Complete, Core Algorithms In Progress
**Target Completion**: 5 weeks from initiation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [ALCOA++ Implementation](#alcoa-implementation)
4. [Modules Completed](#modules-completed)
5. [Modules In Progress](#modules-in-progress)
6. [Usage Examples](#usage-examples)
7. [Installation](#installation)
8. [Development Roadmap](#development-roadmap)

---

## Overview

This pipeline implements a next-generation glycoproteomics data analysis workflow that:

- **Accepts**: `.raw` files (Thermo Fisher mass spectrometry data)
- **Outputs**: `.csv` files with glycopeptide identifications and SMILES representations
- **Guarantees**: Full ALCOA++ data integrity compliance
- **Scoring**: SEQUEST-like XCorr algorithm adapted for glycopeptide fragmentation

### Key Innovations

1. **Chemoinformatics Integration**: First glycoproteomics pipeline to generate SMILES for peptides + glycans
2. **ALCOA++ Compliance**: Pharmaceutical-grade data integrity for scientific reliability
3. **SEQUEST-Inspired Scoring**: Adapted cross-correlation scoring for glycopeptide-specific fragmentation patterns
4. **Benchmarking Framework**: Systematic comparison with pGlyco3, Byonic, MSFragger-Glyco

---

## Architecture

```
src/
├── alcoa/                        # ✅ COMPLETE
│   ├── audit_logger.py          # Real-time event logging (Contemporaneous, Traceable)
│   ├── checksum_manager.py      # SHA-256 integrity (Enduring)
│   ├── metadata_generator.py    # Structured metadata (Complete, Legible)
│   └── compliance_validator.py  # ALCOA++ validation
│
├── converters/                   # ✅ COMPLETE
│   ├── raw_converter.py         # ThermoRawFileParser wrapper (.raw → .mzML)
│   └── mzml_parser.py           # Pyteomics-based mzML parsing
│
├── database/                     # 🔄 IN PROGRESS
│   ├── fasta_parser.py          # FASTA protein database parser
│   ├── glycan_database.py       # Glycan composition/structure database
│   └── candidate_generator.py   # Precursor mass-based candidate selection
│
├── scoring/                      # 🔄 IN PROGRESS
│   ├── spectrum_preprocessor.py # SEQUEST-style normalization
│   ├── theoretical_spectrum.py  # Glycopeptide fragmentation (b/y + B/Y + oxonium)
│   ├── sp_scorer.py             # Preliminary score (Sp_glyco)
│   ├── xcorr_scorer.py          # Cross-correlation (XCorr)
│   └── fdr_calculator.py        # Target-decoy FDR
│
├── chemoinformatics/             # 📅 PLANNED
│   ├── peptide_smiles.py        # Peptide → SMILES (p2smi integration)
│   ├── glycan_smiles.py         # Glycan → SMILES (GlyLES-inspired)
│   └── glycopeptide_smiles.py   # Conjugation at N-glycosite
│
└── workflows/                    # 📅 PLANNED
    ├── main_pipeline.py         # End-to-end orchestration
    └── benchmarking.py          # Tool comparison

Results/                          # ✅ CREATED
├── audit_trail/                 # ALCOA++ audit logs, checksums
├── data/
│   ├── 01_raw_files/           # Original .raw files (read-only)
│   ├── 02_mzml_files/          # Converted mzML files
│   ├── 03_preprocessed/        # Normalized spectra
│   └── 04_results/             # PSM CSV files
└── reports/                     # FDR statistics, compliance reports
```

**Legend**:
- ✅ **COMPLETE**: Fully implemented and tested
- 🔄 **IN PROGRESS**: Partially implemented
- 📅 **PLANNED**: Design complete, implementation pending

---

## ALCOA++ Implementation

### The 10 Principles

| Principle | Implementation | Module |
|-----------|----------------|--------|
| **A**ttributable | User/system metadata in all outputs | `audit_logger.py` |
| **L**egible | Human-readable CSV + JSON + text logs | `metadata_generator.py` |
| **C**ontemporaneous | Real-time timestamping of events | `audit_logger.py` |
| **O**riginal | Preserve .raw → .mzML; never overwrite | `raw_converter.py` |
| **A**ccurate | Cross-validated scoring; FDR control | `fdr_calculator.py` |
| **C**omplete | All spectra accounted for; full provenance | `metadata_generator.py` |
| **C**onsistent | Standardized formats; versioned parameters | All modules |
| **E**nduring | SHA-256 checksums for integrity | `checksum_manager.py` |
| **A**vailable | Structured file organization; indexed outputs | Directory structure |
| **T**raceable | Complete audit trail from .raw → CSV | `audit_logger.py` |

### Example Audit Trail

```json
{
  "run_id": "20251021_143201",
  "user": "researcher@university.edu",
  "start_time": "2025-10-21T14:32:01",
  "events": [
    {
      "timestamp": "2025-10-21T14:32:05",
      "level": "INFO",
      "message": "Converting .raw to .mzML",
      "details": {
        "input_file": "/path/to/sample.raw",
        "sha256": "a1b2c3d4..."
      }
    },
    {
      "timestamp": "2025-10-21T14:35:12",
      "level": "INFO",
      "message": "Parsed 15,243 MS/MS spectra",
      "details": {
        "mzml_file": "/path/to/sample.mzML.gz",
        "ms2_spectra": 15243
      }
    }
  ],
  "alcoa_compliance": {
    "attributable": true,
    "legible": true,
    "contemporaneous": true,
    "original": true,
    "accurate": "validated",
    "complete": true,
    "consistent": true,
    "enduring": true,
    "available": true,
    "traceable": true
  }
}
```

---

## Modules Completed

### 1. ALCOA++ Compliance System (`src/alcoa/`)

**Purpose**: Ensure pharmaceutical-grade data integrity

**Files**:
- `audit_logger.py` (227 lines) - Real-time event logging with timestamping
- `checksum_manager.py` (122 lines) - SHA-256 file integrity verification
- `metadata_generator.py` (137 lines) - Structured metadata generation
- `compliance_validator.py` (163 lines) - ALCOA++ validation before submission

**Usage**:
```python
from src.alcoa import AuditLogger, ChecksumManager

# Initialize
audit = AuditLogger(log_dir="Results/audit_trail")
checksums = ChecksumManager()

# Log events
audit.log("Processing started", level="INFO")

# Register files
checksum = checksums.register_file("Results/data/02_mzml_files/sample.mzML.gz")
audit.log_file_operation("created", "sample.mzML.gz", checksum=checksum)

# Save audit trail
audit.save()
```

### 2. File Conversion (`src/converters/`)

**Purpose**: Convert proprietary .raw files to open mzML format and parse spectra

**Files**:
- `raw_converter.py` (183 lines) - ThermoRawFileParser wrapper
- `mzml_parser.py` (215 lines) - Pyteomics-based spectrum extraction

**Usage**:
```python
from src.converters import RawConverter, MzMLParser

# Convert .raw → .mzML
converter = RawConverter()
mzml_file = converter.convert_to_mzml(
    raw_file_path="sample.raw",
    output_dir="Results/data/02_mzml_files",
    peak_picking=True,
    gzip=True
)

# Parse spectra
parser = MzMLParser()
spectra = parser.parse(mzml_file, ms_level=2, min_peaks=10)

print(f"Loaded {len(spectra)} MS/MS spectra")
for spectrum in spectra[:3]:
    print(f"  {spectrum}")
```

**Output**:
```
Loaded 15243 MS/MS spectra
  Spectrum(scan=1523, precursor_mz=1523.7245, charge=2, peaks=87)
  Spectrum(scan=1524, precursor_mz=945.8234, charge=3, peaks=112)
  Spectrum(scan=1525, precursor_mz=678.3421, charge=2, peaks=64)
```

---

## Modules In Progress

### 3. Database Modules (`src/database/`) - 30% Complete

**Next Steps**:
1. ✅ Design complete
2. 🔄 Implement `fasta_parser.py` - Extract peptide sequences from FASTA
3. 🔄 Implement `glycan_database.py` - Glycan composition database (H5N4F1 format)
4. 🔄 Implement `candidate_generator.py` - Precursor mass matching

**Planned API**:
```python
from src.database import FastaParser, GlycanDatabase, CandidateGenerator

# Parse FASTA
fasta = FastaParser("uniprot_human.fasta")
peptides = fasta.digest(enzyme="trypsin", missed_cleavages=2)

# Load glycan database
glycans = GlycanDatabase("glycan_compositions.txt")

# Generate candidates
candidates = CandidateGenerator(peptides, glycans)
matches = candidates.find_candidates(
    precursor_mz=1523.7245,
    charge=2,
    tolerance_ppm=10
)
```

### 4. Scoring Modules (`src/scoring/`) - 20% Complete

**Critical**: This is the heart of the SEQUEST-inspired algorithm

**Next Steps**:
1. ✅ Algorithm design complete (see plan)
2. 🔄 Implement `spectrum_preprocessor.py` - Binning, sqrt transform, regional normalization
3. 🔄 Implement `theoretical_spectrum.py` - Glycopeptide b/y/B/Y/oxonium ion generation
4. 🔄 Implement `sp_scorer.py` - Fast preliminary scoring (Sp_glyco)
5. 🔄 Implement `xcorr_scorer.py` - Cross-correlation with background subtraction
6. 🔄 Implement `fdr_calculator.py` - Target-decoy FDR estimation

**Planned API**:
```python
from src.scoring import SpectrumPreprocessor, XCorrScorer

# Preprocess spectrum (SEQUEST-style)
preprocessor = SpectrumPreprocessor()
obs_vector = preprocessor.preprocess(spectrum)

# Score candidate
scorer = XCorrScorer()
xcorr = scorer.calculate_xcorr(obs_vector, candidate)
```

---

## Usage Examples

### Example 1: Convert RAW Files

```python
from src.converters import RawConverter
from src.alcoa import AuditLogger, ChecksumManager

# Initialize ALCOA++ logging
audit = AuditLogger()
checksums = ChecksumManager()

# Convert .raw files
converter = RawConverter()

raw_files = [
    "Data/cancer_01.raw",
    "Data/cancer_02.raw",
    "Data/normal_01.raw",
]

for raw_file in raw_files:
    audit.log(f"Converting {raw_file}", level="INFO")

    mzml_file = converter.convert_to_mzml(raw_file)
    checksum = checksums.register_file(mzml_file)

    audit.log_file_operation("created", mzml_file, checksum=checksum)

audit.save()
```

### Example 2: Parse and Analyze Spectra

```python
from src.converters import MzMLParser

parser = MzMLParser()
spectra = parser.parse("Results/data/02_mzml_files/sample.mzML.gz")

# Analyze spectrum properties
precursor_mzs = [s.precursor_mz for s in spectra]
charges = [s.precursor_charge for s in spectra]

print(f"Total spectra: {len(spectra)}")
print(f"Precursor m/z range: {min(precursor_mzs):.2f} - {max(precursor_mzs):.2f}")
print(f"Charge states: {set(charges)}")
```

### Example 3: ALCOA++ Compliance Validation

```python
from src.alcoa import AuditLogger, ChecksumManager, ComplianceValidator

# After pipeline run
audit = AuditLogger.load("Results/audit_trail/20251021_143201_audit_trail.json")
checksums = ChecksumManager()

# Validate compliance
validator = ComplianceValidator(audit, checksums)
is_compliant, report = validator.validate_all()

if is_compliant:
    print("✅ Pipeline outputs are ALCOA++ compliant")
else:
    print("❌ Compliance issues found:")
    for issue in report["issues"]:
        print(f"  - {issue}")

# Save compliance report
validator.save_report(report)
```

---

## Installation

### Dependencies

```bash
# Install in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### New Dependencies Added

The following dependencies were added to `pyproject.toml`:

```python
"pyteomics>=4.6.0",  # mzML parsing and MS/MS analysis
"biopython>=1.83",   # FASTA parsing
"rdkit>=2024.3.1",   # Chemoinformatics (SMILES generation)
"tqdm>=4.65.0",      # Progress bars for spectrum processing
```

### External Tools

**ThermoRawFileParser** (Required for .raw conversion):

```bash
# Option 1: Conda
conda install -c bioconda thermorawfileparser

# Option 2: Download binary
# https://github.com/compomics/ThermoRawFileParser/releases

# Option 3: Docker
docker pull quay.io/biocontainers/thermorawfileparser
```

---

## Development Roadmap

### Week 1: Infrastructure ✅ COMPLETE
- [x] Directory structure
- [x] ALCOA++ logging system
- [x] RAW → mzML conversion
- [x] mzML parsing with Pyteomics
- [x] Documentation framework

### Week 2: Database & Candidates (In Progress)
- [ ] FASTA parser with tryptic digestion
- [ ] Glycan database (H5N4F1 composition format)
- [ ] Candidate generation (precursor mass matching)
- [ ] Unit tests for database modules

### Week 3: Scoring Algorithms (Planned)
- [ ] Spectrum preprocessor (SEQUEST-style)
- [ ] Theoretical spectrum generator (b/y/B/Y/oxonium ions)
- [ ] Sp_glyco preliminary scorer
- [ ] XCorr cross-correlation scorer
- [ ] Unit tests for scoring functions

### Week 4: FDR & Output (Planned)
- [ ] Target-decoy database construction
- [ ] FDR calculator (Benjamini-Hochberg)
- [ ] CSV output formatter
- [ ] SMILES integration (peptide + glycan)
- [ ] End-to-end integration test

### Week 5: Benchmarking & Validation (Planned)
- [ ] Benchmark dataset acquisition
- [ ] Run pGlyco3, Byonic, MSFragger on same data
- [ ] Comparison metrics (PSM counts, FDR accuracy, runtime)
- [ ] Validation against known glycopeptides
- [ ] Final documentation and examples

---

## Contributing

This is a research pipeline under active development. Key areas for contribution:

1. **Glycan fragmentation models** - Improve B/Y ion prediction accuracy
2. **Scoring optimization** - Tune Sp_glyco and XCorr parameters
3. **Benchmarking** - Provide test datasets with known glycopeptides
4. **SMILES generation** - Implement glycan-peptide conjugation chemistry

---

## References

### SEQUEST Algorithm
- Eng, J. K., et al. (2011). "Faster SEQUEST Searching for Peptide Identification from Tandem Mass Spectra." *Journal of Proteome Research*, 10(9), 3935-3943.

### ALCOA++ Data Integrity
- FDA. (2018). "Data Integrity and Compliance With Drug CGMP." Guidance for Industry.

### Glycoproteomics
- Liu, M. Q., et al. (2017). "pGlyco 2.0 enables precision N-glycoproteomics with comprehensive quality control." *Nature Communications*, 8, 438.

### Chemoinformatics
- Fetter, A., et al. (2024). "p2smi: A Python Toolkit for Peptide FASTA-to-SMILES Conversion." *arXiv preprint*.

---

**Status**: Infrastructure phase complete. Ready for core algorithm implementation.
**Next Milestone**: Database modules (FASTA parser + glycan database) - ETA 1 week
**Contact**: See project repository for issues and contributions
