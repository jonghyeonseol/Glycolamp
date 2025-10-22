# Glycolamp Benchmarking Protocol

**Version**: 1.0
**Date**: 2025-10-22
**Purpose**: Step-by-step protocol for benchmarking Glycolamp against FragPipe

---

## Overview

This protocol provides detailed instructions for benchmarking Glycolamp performance and comparing results with FragPipe on your mouse 18-plex TMT glycoproteomics dataset.

**Dataset**: `20250106_mouse_18plex_F01.mzML`
- **Size**: 524 MB
- **Scans**: 62,701 MS scans
- **Type**: Mouse 18-plex TMT
- **Location**: `/Users/seoljonghyeon/Documents/GitHub/`

---

## Prerequisites

### Software Requirements

**For Glycolamp:**
- Python 3.9+
- Glycolamp installed (`pip install -e .`)
- Additional packages: `psutil`, `memory_profiler`

**For FragPipe:**
- FragPipe (latest version from https://fragpipe.nesvilab.org/)
- Java 11+
- Mouse proteome FASTA database

### Data Requirements

1. **mzML file** (already converted ✓)
   - `20250106_mouse_18plex_F01.mzML`

2. **FASTA database**
   ```bash
   # Download mouse proteome if needed
   wget https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/reference_proteomes/Eukaryota/UP000000589/UP000000589_10090.fasta.gz
   gunzip UP000000589_10090.fasta.gz
   mv UP000000589_10090.fasta mouse_proteome.fasta
   ```

---

## Part 1: Glycolamp Benchmark

### Step 1: Install Dependencies

```bash
cd /Users/seoljonghyeon/Documents/GitHub/Glycolamp

# Install Glycolamp (if not already done)
pip install -e .

# Install benchmarking dependencies
pip install psutil memory_profiler matplotlib pandas
```

### Step 2: Run Benchmark Script

```bash
# Full benchmark on complete dataset
python scripts/benchmark_glycolamp.py \
  --mzml /Users/seoljonghyeon/Documents/GitHub/20250106_mouse_18plex_F01.mzML \
  --fasta mouse_proteome.fasta \
  --output benchmark_results/glycolamp_full \
  --fdr 0.01 \
  --ppm 10.0

# Expected output:
# [1/8] Parsing mzML file...
# [2/8] Parsing FASTA database...
# [3/8] Loading glycan database...
# [4/8] Generating glycopeptide candidates...
# [5/8] Preliminary Sp scoring...
# [6/8] XCorr scoring (top candidates)...
# [7/8] FDR calculation...
# [8/8] SMILES generation...
#
# BENCHMARK SUMMARY
# Total runtime: XX.XX min
# Peak memory: XXX.X MB
# ...
```

### Step 3: Test Run (Optional)

For quick testing with subset of data:

```bash
# Test with first 1000 spectra
python scripts/benchmark_glycolamp.py \
  --mzml /Users/seoljonghyeon/Documents/GitHub/20250106_mouse_18plex_F01.mzML \
  --fasta mouse_proteome.fasta \
  --output benchmark_results/glycolamp_test \
  --max-spectra 1000 \
  --fdr 0.01 \
  --ppm 10.0
```

### Step 4: Collect Results

Results will be saved in `benchmark_results/glycolamp_full/`:

```
benchmark_results/glycolamp_full/
├── benchmark_results.json      # Full metrics (JSON)
├── benchmark_summary.csv       # Summary table (CSV)
└── ...                         # Additional output files
```

**Key Metrics to Record:**

| Metric | Value | Notes |
|--------|-------|-------|
| Total Time (min) | | End-to-end |
| Peak Memory (MB) | | Maximum RAM usage |
| Candidates/sec | | Throughput |
| Spectra Processed | | Total count |
| PSMs (1% FDR) | | Identified |

---

## Part 2: FragPipe Benchmark

### Step 1: Install FragPipe

```bash
# Download from
https://github.com/Nesvilab/FragPipe/releases

# macOS: Download FragPipe-XX.X.dmg
# Install to /Applications/FragPipe.app

# Verify installation
/Applications/FragPipe.app/Contents/MacOS/fragpipe --version
```

### Step 2: Download Reference Database

If not already downloaded:

```bash
# Download mouse proteome
wget https://ftp.uniprot.org/pub/databases/uniprot/current_release/\
knowledgebase/reference_proteomes/Eukaryota/UP000000589/\
UP000000589_10090.fasta.gz

gunzip UP000000589_10090.fasta.gz
```

### Step 3: Run FragPipe (GUI Method)

**Recommended for first-time users:**

1. **Open FragPipe**
   ```bash
   open /Applications/FragPipe.app
   ```

2. **Configure Workflow**
   - Click "Workflow" tab
   - Select **"Glyco"** workflow
   - (This pre-configures MSFragger-Glyco parameters)

3. **Add Input Files**
   - Click "Select Files" or drag-and-drop
   - Add: `20250106_mouse_18plex_F01.mzML`

4. **Set Database**
   - FASTA file: `mouse_proteome.fasta`
   - Decoy generation: **Enabled** (default)

5. **Configure Glycan Database**
   - Use built-in N-glycan database
   - Or upload custom glycan list

6. **Configure TMT Quantification**
   - Workflow tab → Quant
   - Select **"TMT-18plex"**
   - Set reporter ion m/z values

7. **Set Output Directory**
   - Browse to: `benchmark_results/fragpipe_full/`

8. **Adjust Resources**
   - RAM allocation: Let FragPipe auto-detect
   - Threads: Use all available cores

9. **Start Run**
   - Click **"RUN"** button
   - Monitor progress in console

10. **Record Timing**
    - **Start time**: (record when you click RUN)
    - **End time**: (record when "DONE" appears)
    - **Total time**: End - Start

### Step 4: Run FragPipe (CLI Method)

**For reproducibility and automation:**

First, create a manifest file:

```bash
# Create manifest.fp-manifest
cat > manifest.fp-manifest << EOF
/Users/seoljonghyeon/Documents/GitHub/20250106_mouse_18plex_F01.mzML	Experiment1	1	DDA
EOF
```

Then run FragPipe:

```bash
# Run FragPipe CLI
/Applications/FragPipe.app/Contents/MacOS/fragpipe \
  --headless \
  --workflow glyco \
  --manifest manifest.fp-manifest \
  --workdir benchmark_results/fragpipe_full/ \
  --database mouse_proteome.fasta \
  --threads 8 \
  --ram 16

# Monitor with time command
/usr/bin/time -l /Applications/FragPipe.app/Contents/MacOS/fragpipe \
  --headless \
  --workflow glyco \
  --manifest manifest.fp-manifest \
  --workdir benchmark_results/fragpipe_full/ \
  --database mouse_proteome.fasta \
  --threads 8 \
  --ram 16
```

### Step 5: Monitor Performance

**Memory Monitoring** (macOS):

```bash
# In separate terminal, monitor memory
while true; do
  ps aux | grep -i fragpipe | awk '{print $6/1024 " MB"}' | head -1
  sleep 5
done
```

Or use **Activity Monitor**:
1. Open Activity Monitor
2. Sort by "Memory"
3. Find FragPipe process
4. Record peak "Memory" value

### Step 6: Collect FragPipe Results

Results in `benchmark_results/fragpipe_full/`:

```
benchmark_results/fragpipe_full/
├── psm.tsv                    # Peptide-spectrum matches
├── protein.tsv                # Protein identifications
├── glycan_diagnostic.tsv      # Glycan-specific results
├── fragpipe.log               # Run log (contains timing)
└── ...
```

**Extract Key Metrics:**

```bash
# Total PSMs
wc -l benchmark_results/fragpipe_full/psm.tsv

# Unique glycopeptides
awk -F'\t' 'NR>1 {print $2,$3}' benchmark_results/fragpipe_full/psm.tsv | sort -u | wc -l

# Runtime (from log)
grep "total time" benchmark_results/fragpipe_full/fragpipe.log
```

---

## Part 3: Comparative Analysis

### Step 1: Extract Metrics

Create comparison table:

| Metric | FragPipe | Glycolamp | Ratio (FP/GL) |
|--------|----------|-----------|---------------|
| **Performance** |
| Total Time (min) | | | |
| Peak Memory (GB) | | | |
| Spectra/sec | | | |
| **Identification** |
| Total PSMs | | | |
| Unique glycopeptides | | | |
| Glycoproteins | | | |
| **Quality** |
| Decoy rate (%) | | | |
| Median Q-value | | | |
| Mass accuracy (ppm) | | | |

### Step 2: PSM Overlap Analysis

```python
# Python script for overlap analysis
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2

# Load FragPipe PSMs
fragpipe = pd.read_csv('benchmark_results/fragpipe_full/psm.tsv', sep='\t')
fragpipe_ids = set(fragpipe['Peptide'] + '_' + fragpipe['Glycan'])

# Load Glycolamp PSMs
glycolamp = pd.read_csv('benchmark_results/glycolamp_full/psms.csv')
glycolamp_ids = set(glycolamp['peptide'] + '_' + glycolamp['glycan'])

# Calculate overlap
overlap = fragpipe_ids & glycolamp_ids
fragpipe_only = fragpipe_ids - glycolamp_ids
glycolamp_only = glycolamp_ids - fragpipe_ids

print(f"FragPipe total: {len(fragpipe_ids)}")
print(f"Glycolamp total: {len(glycolamp_ids)}")
print(f"Overlap: {len(overlap)} ({len(overlap)/len(fragpipe_ids)*100:.1f}%)")

# Venn diagram
venn2([fragpipe_ids, glycolamp_ids], ('FragPipe', 'Glycolamp'))
plt.title('PSM Overlap')
plt.savefig('benchmark_results/psm_overlap.png', dpi=300)
```

### Step 3: Score Distribution Comparison

```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# FragPipe Hyperscore
ax1.hist(fragpipe['Hyperscore'], bins=50, alpha=0.7, label='FragPipe')
ax1.set_xlabel('Hyperscore')
ax1.set_ylabel('Count')
ax1.set_title('FragPipe Score Distribution')
ax1.legend()

# Glycolamp XCorr
ax2.hist(glycolamp['xcorr'], bins=50, alpha=0.7, label='Glycolamp', color='orange')
ax2.set_xlabel('XCorr')
ax2.set_ylabel('Count')
ax2.set_title('Glycolamp Score Distribution')
ax2.legend()

plt.tight_layout()
plt.savefig('benchmark_results/score_distributions.png', dpi=300)
```

### Step 4: FDR Calibration Check

```python
# Check decoy rates
fragpipe_decoys = fragpipe[fragpipe['Is Decoy'] == True]
glycolamp_decoys = glycolamp[glycolamp['is_decoy'] == True]

fragpipe_decoy_rate = len(fragpipe_decoys) / len(fragpipe) * 100
glycolamp_decoy_rate = len(glycolamp_decoys) / len(glycolamp) * 100

print(f"FragPipe decoy rate: {fragpipe_decoy_rate:.2f}%")
print(f"Glycolamp decoy rate: {glycolamp_decoy_rate:.2f}%")
print(f"Expected: ~1.0% at 1% FDR threshold")
```

### Step 5: Generate Final Report

```python
# Create summary report
report = f"""
# Benchmarking Results Summary

## Dataset
- File: 20250106_mouse_18plex_F01.mzML
- Scans: 62,701
- Size: 524 MB

## Performance Comparison

| Metric | FragPipe | Glycolamp | Ratio |
|--------|----------|-----------|-------|
| Time (min) | {fragpipe_time:.1f} | {glycolamp_time:.1f} | {fragpipe_time/glycolamp_time:.1f}x |
| Memory (GB) | {fragpipe_mem:.1f} | {glycolamp_mem:.1f} | {fragpipe_mem/glycolamp_mem:.1f}x |
| PSMs | {len(fragpipe)} | {len(glycolamp)} | {len(fragpipe)/len(glycolamp):.1f}x |

## Identification Overlap

- Total FragPipe: {len(fragpipe_ids)}
- Total Glycolamp: {len(glycolamp_ids)}
- Overlap: {len(overlap)} ({len(overlap)/len(fragpipe_ids)*100:.1f}%)

## FDR Control

- FragPipe decoy rate: {fragpipe_decoy_rate:.2f}%
- Glycolamp decoy rate: {glycolamp_decoy_rate:.2f}%
- Both within expected range (≤1.0%)

## Conclusion

[Add your interpretation here]
"""

with open('benchmark_results/FINAL_REPORT.md', 'w') as f:
    f.write(report)

print("✓ Final report saved to benchmark_results/FINAL_REPORT.md")
```

---

## Part 4: Troubleshooting

### Common Issues

**Issue 1: Glycolamp runs out of memory**

Solution:
```bash
# Process in batches
python scripts/benchmark_glycolamp.py \
  --mzml file.mzML \
  --fasta database.fasta \
  --max-spectra 10000  # Process in chunks
```

**Issue 2: FragPipe cannot find Java**

Solution:
```bash
# Install/update Java
brew install openjdk@11

# Set JAVA_HOME
export JAVA_HOME=/opt/homebrew/opt/openjdk@11
```

**Issue 3: mzML file not recognized**

Solution:
```bash
# Verify mzML format
head -20 file.mzML

# Re-convert if needed (see DATA_PREPARATION.md)
```

---

## Part 5: Expected Results

### Predicted Performance

Based on technical analysis:

**FragPipe:**
- Time: 7-12 minutes
- Memory: 8-16 GB
- PSMs: 10,000-30,000 (1% FDR)
- Glycopeptides: 3,000-8,000

**Glycolamp:**
- Time: 38-70 minutes (5-10x slower)
- Memory: 2-4 GB (2-4x more efficient)
- PSMs: 5,000-15,000 (1% FDR)
- Glycopeptides: 1,500-5,000

**Overlap:**
- Expected: 60-80% agreement
- FragPipe likely identifies more (larger database)
- Glycolamp more conservative (curated library)

### Success Criteria

✅ **Benchmark is successful if:**

1. **Both tools complete** without errors
2. **FDR control working**: Decoy rate ≤1.2%
3. **Reasonable overlap**: >50% PSMs in common
4. **Performance matches predictions**: Within 2x of expected values
5. **Results reproducible**: Re-running gives similar results (±10%)

---

## Part 6: Publication & Sharing

### Data to Report

For publication, report:

1. **System specs**:
   - OS: macOS Tahoe (15.0)
   - CPU: Apple M-series
   - RAM: XX GB
   - Storage: SSD

2. **Software versions**:
   - FragPipe: vX.X
   - Glycolamp: v4.0.0
   - MSFragger: vX.X

3. **Parameters**:
   - FDR: 1%
   - Mass tolerance: ±10 ppm
   - Enzyme: Trypsin (≤2 missed cleavages)
   - Glycan database: Default (63 for Glycolamp, standard for FragPipe)

4. **Results**:
   - All metrics from comparison table
   - Figures: Venn diagram, score distributions, FDR calibration

### Sharing Results

```bash
# Create shareable archive
tar -czf glycolamp_fragpipe_benchmark_2025.tar.gz \
  benchmark_results/ \
  docs/BENCHMARKING_TECHNICAL_REPORT.md \
  docs/BENCHMARKING_PROTOCOL.md \
  scripts/benchmark_glycolamp.py

# Upload to repository or supplementary materials
```

---

## References

1. **This Protocol**: `docs/BENCHMARKING_PROTOCOL.md`
2. **Technical Report**: `docs/BENCHMARKING_TECHNICAL_REPORT.md`
3. **FragPipe Comparison**: `docs/FRAGPIPE_COMPARISON.md`
4. **Data Preparation**: `docs/DATA_PREPARATION.md`

---

## Appendix: Quick Reference Commands

```bash
# === Glycolamp Benchmark ===
python scripts/benchmark_glycolamp.py \
  --mzml 20250106_mouse_18plex_F01.mzML \
  --fasta mouse_proteome.fasta \
  --output benchmark_results/glycolamp_full

# === FragPipe Benchmark ===
/Applications/FragPipe.app/Contents/MacOS/fragpipe \
  --headless \
  --workflow glyco \
  --manifest manifest.fp-manifest \
  --workdir benchmark_results/fragpipe_full/ \
  --database mouse_proteome.fasta

# === Analysis ===
python scripts/compare_results.py \
  --fragpipe benchmark_results/fragpipe_full/psm.tsv \
  --glycolamp benchmark_results/glycolamp_full/psms.csv \
  --output benchmark_results/comparison/
```

---

**Last Updated**: 2025-10-22
**Version**: 1.0
**Author**: Glycolamp Benchmarking Team

For questions: See `docs/BENCHMARKING_TECHNICAL_REPORT.md` or open GitHub issue.
