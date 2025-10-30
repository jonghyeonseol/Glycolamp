# Quick Start: Glycolamp Analysis

**Your Dataset:**
- **mzML**: `20250106_mouse_18plex_F01.mzML` (524 MB, 62,701 scans)
- **FASTA**: `uniprotkb_mouse_AND_reviewed_true_AND_m_2025_10_22.fasta` (17 MB, 25,659 proteins)
- **Location**: `/Users/seoljonghyeon/Documents/GitHub/`

---

## ✅ Quick Start: Run Complete Analysis

### Option 1: Run Full Benchmark (Recommended)

This will benchmark Glycolamp performance AND identify proteins:

```bash
cd /Users/seoljonghyeon/Documents/GitHub/Glycolamp

python scripts/benchmark_glycolamp.py \
  --mzml /Users/seoljonghyeon/Documents/GitHub/20250106_mouse_18plex_F01.mzML \
  --fasta /Users/seoljonghyeon/Documents/GitHub/uniprotkb_mouse_AND_reviewed_true_AND_m_2025_10_22.fasta \
  --output benchmark_results/glycolamp_full \
  --fdr 0.01 \
  --ppm 10.0
```

**Expected output:**
```
[1/8] Parsing mzML file...
  ✓ Parsed 62,701 spectra
[2/8] Parsing FASTA database...
  ✓ Parsed 25,659 proteins
  Generated XX,XXX glycopeptides
[3/8] Loading glycan database...
  ✓ Loaded 63 glycan structures
[4/8] Generating glycopeptide candidates...
  ✓ Generated XX,XXX candidates
...

Total runtime: XX minutes
Peak memory: XX MB
PSMs identified: XXX (1% FDR)
```

**Results saved to:**
- `benchmark_results/glycolamp_full/benchmark_results.json`
- `benchmark_results/glycolamp_full/benchmark_summary.csv`
- `benchmark_results/glycolamp_full/psms.csv` (identified proteins/peptides)

---

### Option 2: Quick Test (First 1,000 Spectra)

For testing/debugging:

```bash
python scripts/benchmark_glycolamp.py \
  --mzml /Users/seoljonghyeon/Documents/GitHub/20250106_mouse_18plex_F01.mzML \
  --fasta /Users/seoljonghyeon/Documents/GitHub/uniprotkb_mouse_AND_reviewed_true_AND_m_2025_10_22.fasta \
  --output benchmark_results/glycolamp_test \
  --max-spectra 1000 \
  --fdr 0.01 \
  --ppm 10.0
```

**Expected runtime:** ~2-5 minutes

---

### Option 3: Manual Step-by-Step

If you want to run each module separately:

```python
cd /Users/seoljonghyeon/Documents/GitHub/Glycolamp
python3

# In Python interpreter:
from src.converters import MzMLParser
from src.database import FastaParser, GlycanDatabase, CandidateGenerator
from src.scoring import XCorrScorer, FDRCalculator

# 1. Parse mzML
parser = MzMLParser()
spectra = parser.parse("/Users/seoljonghyeon/Documents/GitHub/20250106_mouse_18plex_F01.mzML")
print(f"Loaded {len(spectra)} spectra")

# 2. Parse FASTA
fasta = FastaParser("/Users/seoljonghyeon/Documents/GitHub/uniprotkb_mouse_AND_reviewed_true_AND_m_2025_10_22.fasta")
proteins = fasta.parse()
peptides = fasta.digest(enzyme='trypsin', missed_cleavages=2)
glyco_peptides = fasta.filter_by_glycosylation_site(peptides)
print(f"Generated {len(glyco_peptides)} glycopeptides")

# 3. Load glycans
glycan_db = GlycanDatabase()
print(f"Loaded {len(glycan_db.glycans)} glycans")

# 4. Generate candidates
generator = CandidateGenerator(glyco_peptides, glycan_db.glycans)

# Search first MS/MS spectrum
ms2_spectrum = [s for s in spectra if s.ms_level == 2][0]
candidates = generator.generate_candidates(
    precursor_mz=ms2_spectrum.precursor_mz,
    charge=ms2_spectrum.precursor_charge,
    tolerance_ppm=10.0
)
print(f"Found {len(candidates)} candidates for first spectrum")

# ... continue with scoring, FDR, etc.
```

---

## 📊 Expected Results

### Performance (Predicted)

| Metric | Expected Range |
|--------|---------------|
| **Runtime** | 38-70 minutes (full dataset) |
| **Memory** | 2-4 GB peak |
| **Throughput** | ~1,000-2,000 spectra/minute |

### Identification (Predicted)

| Metric | Expected Range |
|--------|---------------|
| **PSMs (1% FDR)** | 5,000-15,000 |
| **Unique glycopeptides** | 1,500-5,000 |
| **Glycoproteins** | 200-800 |

### Output Files

```
benchmark_results/glycolamp_full/
├── benchmark_results.json          # Performance metrics
├── benchmark_summary.csv           # Summary table
├── psms.csv                        # Peptide-spectrum matches
├── glycopeptides.csv              # Unique glycopeptides
├── proteins.csv                    # Identified proteins
└── smiles.csv                      # SMILES for ML
```

---

## 🔬 What You'll Get

### 1. Protein Identifications

**Example PSM result:**

| Protein | Peptide | Glycan | Score | FDR | Site |
|---------|---------|--------|-------|-----|------|
| P01027 | NGTIINEK | H5N4F1A2 | 2.45 | 0.005 | N0 |
| Q8BMS1 | SLVNKTR | H6N5F1 | 1.89 | 0.008 | N4 |

### 2. Performance Metrics

**Example benchmark result:**

```json
{
  "timing": {
    "total_time_min": 45.2,
    "candidate_gen_sec": 145.8,
    "xcorr_score_sec": 892.3
  },
  "memory": {
    "peak_mb": 3247.5
  },
  "counts": {
    "total_spectra": 62701,
    "total_psms": 8934,
    "total_glycopeptides": 2847
  }
}
```

### 3. SMILES for ML

**Example SMILES output:**

```csv
peptide,glycan,peptide_smiles,glycan_smiles,combined_smiles,mw
NGTIINEK,H5N4F1A2,NCC(=O)O...,OC1C(O)C(O)...,NCC(=O)O.OC1...,2847.32
```

---

## 🚀 Next Steps After Analysis

### 1. Compare with FragPipe

```bash
# Run FragPipe on same data
# See docs/BENCHMARKING_PROTOCOL.md

# Compare results
python scripts/compare_results.py \
  --glycolamp benchmark_results/glycolamp_full/psms.csv \
  --fragpipe fragpipe_results/psm.tsv \
  --output comparison/
```

### 2. ML Model Training

```python
import pandas as pd

# Load SMILES
smiles_df = pd.read_csv('benchmark_results/glycolamp_full/smiles.csv')

# Train ML model
from sklearn.ensemble import RandomForestClassifier

X = smiles_df['combined_smiles']  # Features
y = smiles_df['glycan_type']      # Labels

# ... ML pipeline ...
```

### 3. Generate Publication Figures

```python
import matplotlib.pyplot as plt
import pandas as pd

results = pd.read_csv('benchmark_results/glycolamp_full/psms.csv')

# Score distribution
plt.hist(results['xcorr'], bins=50)
plt.xlabel('XCorr Score')
plt.ylabel('Count')
plt.title('Glycopeptide Identification Scores')
plt.savefig('figures/score_distribution.png', dpi=300)
```

---

## 📝 Summary

**You now have:**
- ✅ mzML file (62,701 spectra)
- ✅ FASTA database (25,659 mouse proteins)
- ✅ Glycolamp pipeline (ready to run)
- ✅ Benchmark script (performance profiling)

**To identify proteins, run:**
```bash
python scripts/benchmark_glycolamp.py \
  --mzml /Users/seoljonghyeon/Documents/GitHub/20250106_mouse_18plex_F01.mzML \
  --fasta /Users/seoljonghyeon/Documents/GitHub/uniprotkb_mouse_AND_reviewed_true_AND_m_2025_10_22.fasta \
  --output benchmark_results/glycolamp_full
```

**Expected time:** ~40-70 minutes
**Expected memory:** ~2-4 GB
**Expected output:** Thousands of glycopeptide identifications!

---

**Ready to run?** 🚀

Just execute the command above and Glycolamp will:
1. Parse your spectra
2. Digest the proteome
3. Generate candidates
4. Score matches
5. Calculate FDR
6. Output protein identifications!
