# Glycoproteomics Pipeline - Example Scripts

This directory contains example scripts demonstrating the next-generation glycoproteomics pipeline functionality.

---

## 📂 Available Examples

### ✅ Phase 1: Infrastructure (Week 1)

| Script | Description | Status |
|--------|-------------|--------|
| `example_01_raw_conversion.py` | Convert .raw files to mzML with ALCOA++ compliance | ✅ Ready |
| `example_02_parse_spectra.py` | Parse mzML files and analyze MS/MS spectra | ✅ Ready |

### 📅 Future Examples (Weeks 2-5)

| Script | Description | Status |
|--------|-------------|--------|
| `example_03_database_search.py` | FASTA digestion and candidate generation | 📅 Week 2 |
| `example_04_spectrum_matching.py` | SEQUEST-like scoring (Sp + XCorr) | 📅 Week 3 |
| `example_05_fdr_calculation.py` | Target-decoy FDR estimation | 📅 Week 4 |
| `example_06_full_pipeline.py` | End-to-end .raw → .csv workflow | 📅 Week 5 |
| `example_07_benchmarking.py` | Compare with pGlyco3/Byonic/MSFragger | 📅 Week 5 |

---

## 🚀 Getting Started

### Prerequisites

```bash
# Install pipeline
cd /path/to/Glycopeptide-Automated-Data-Analysis
pip install -e .

# Install ThermoRawFileParser
conda install -c bioconda thermorawfileparser
```

### Running Examples

#### Example 1: Convert RAW Files

```bash
# 1. Edit the script and add your .raw file paths
nano examples/example_01_raw_conversion.py

# 2. Modify this section:
raw_files = [
    "path/to/sample1.raw",
    "path/to/sample2.raw",
]

# 3. Run the script
python examples/example_01_raw_conversion.py
```

**Output**:
- mzML files in `Results/data/02_mzml_files/`
- Audit trail in `Results/audit_trail/`
- Checksums in `Results/audit_trail/file_checksums.json`

#### Example 2: Parse and Analyze Spectra

```bash
# 1. Edit the script and specify mzML file
nano examples/example_02_parse_spectra.py

# 2. Modify this line:
mzml_file = "Results/data/02_mzml_files/sample.mzML.gz"

# 3. Run the script
python examples/example_02_parse_spectra.py
```

**Output**:
- Summary statistics printed to console
- Plots in `Results/reports/`
  - `spectral_summary.png`: 4-panel overview
  - `representative_spectrum.png`: Example MS/MS spectrum

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
        "sha256": "a1b2c3d4e5f6...",
        "source_file": "sample.raw"
      }
    }
  ],
  "alcoa_compliance": {
    "attributable": true,
    "legible": true,
    "contemporaneous": true,
    "traceable": true
  }
}
```

### Spectral Summary (Console)

```
📊 Spectral Data Summary:
  Total MS/MS Spectra: 15,243

  Precursor m/z:
    Range: 300.12 - 2000.45
    Mean: 876.34

  Charge States:
    2+: 8,421 (55.2%)
    3+: 5,234 (34.3%)
    4+: 1,588 (10.4%)

  Fragment Peaks:
    Average per spectrum: 87.3

  Retention Time:
    Range: 120.5 - 7200.8 sec
```

---

## 🔧 Customization

### Modify Conversion Parameters

```python
# In example_01_raw_conversion.py

mzml_file = converter.convert_to_mzml(
    raw_file_path=str(raw_file),
    output_dir="custom/output/dir",    # Change output location
    peak_picking=False,                # Disable centroiding (profile mode)
    gzip=False,                        # Disable compression
    metadata_format="txt"              # Use text metadata instead of JSON
)
```

### Modify Parsing Parameters

```python
# In example_02_parse_spectra.py

spectra = parser.parse(
    mzml_file_path=mzml_file,
    ms_level=1,        # Parse MS1 instead of MS/MS
    min_peaks=50       # Stricter quality filter
)
```

---

## 🐛 Troubleshooting

### ThermoRawFileParser Not Found

**Error**:
```
RuntimeError: ThermoRawFileParser not found. Please install it:
```

**Solution**:
```bash
conda install -c bioconda thermorawfileparser
```

### No mzML Files Found

**Error**:
```
⚠️  No input file specified!
```

**Solution**: Edit the script and add your file paths:
```python
mzml_file = "Results/data/02_mzml_files/your_file.mzML.gz"
```

### Pyteomics Import Error

**Error**:
```
ImportError: Pyteomics is required for mzML parsing.
```

**Solution**:
```bash
pip install pyteomics>=4.6.0
```

---

## 📚 Additional Resources

### Documentation
- **Quick Start Guide**: `../docs/PIPELINE_QUICKSTART.md`
- **Comprehensive Guide**: `../docs/GLYCOPROTEOMICS_PIPELINE_GUIDE.md`
- **Implementation Summary**: `../IMPLEMENTATION_SUMMARY.md`

### API Reference
- **AuditLogger**: `../src/alcoa/audit_logger.py`
- **RawConverter**: `../src/converters/raw_converter.py`
- **MzMLParser**: `../src/converters/mzml_parser.py`

---

## 🎓 Learning Path

1. **Start Here**: `example_01_raw_conversion.py`
   - Learn ALCOA++ audit logging
   - Understand file conversion workflow
   - Explore SHA-256 checksumming

2. **Next**: `example_02_parse_spectra.py`
   - Learn spectrum data structure
   - Understand MS/MS analysis
   - Explore visualization techniques

3. **Week 2**: Database examples (coming soon)
   - FASTA parsing and digestion
   - Glycan database construction
   - Candidate generation

4. **Week 3-5**: Scoring and benchmarking (coming soon)
   - SEQUEST-like algorithm
   - FDR calculation
   - Tool comparison

---

## 💡 Tips

1. **Start Small**: Test with 1-2 .raw files before batch processing
2. **Check Logs**: Review `Results/audit_trail/*_processing_log.txt` for detailed info
3. **Verify Checksums**: Use `ChecksumManager.verify_file()` to ensure data integrity
4. **Visualize Data**: Explore generated plots in `Results/reports/`

---

## 🤝 Contributing

Have an idea for a new example? Open an issue or submit a pull request!

**Example Ideas**:
- Batch processing with progress bars
- Quality control filtering
- Retention time alignment
- Multi-instrument comparison

---

**Questions?** See the main documentation in `docs/` or the implementation summary in `IMPLEMENTATION_SUMMARY.md`.
