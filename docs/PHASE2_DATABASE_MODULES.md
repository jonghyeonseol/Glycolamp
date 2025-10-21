# Phase 2: Database Modules Implementation

**Date**: 2025-10-21
**Status**: ✅ **COMPLETE**
**Phase**: Week 2 of 5-week development plan

---

## 📋 Overview

Phase 2 implements the complete database infrastructure for glycopeptide identification:

1. **FASTA Parser**: Protein database parsing with in-silico enzymatic digestion
2. **Glycan Database**: N-glycan composition library with classification system
3. **Candidate Generator**: Mass-based matching of precursors to glycopeptide candidates

All modules are fully implemented, tested (100% pass rate), and integrated with ALCOA++ compliance.

---

## 🎯 Objectives (All Achieved)

- [x] Parse FASTA files with BioPython
- [x] Implement in-silico enzymatic digestion (trypsin + 5 other enzymes)
- [x] Detect N-glycosylation motifs (N-X-S/T where X≠P)
- [x] Generate library of 63 common N-glycan structures
- [x] Classify glycans into 5 biological types
- [x] Calculate monoisotopic masses for peptides and glycans
- [x] Generate glycopeptide candidates from precursor m/z
- [x] Implement PPM-based mass tolerance filtering
- [x] Create comprehensive unit tests (28 tests, 100% pass rate)
- [x] Create integration tests (4 tests demonstrating full workflow)
- [x] Write example script demonstrating database search

---

## 📦 Modules Implemented

### 1. FASTA Parser (`src/database/fasta_parser.py`)

**Lines of Code**: 391
**Test Coverage**: 8 tests (all passing)

#### Features

- **BioPython Integration**: Parse FASTA files with robust error handling
- **Enzymatic Digestion**: Support for 6 enzymes
  - Trypsin (K, R cleavage)
  - Chymotrypsin (F, W, Y cleavage)
  - Pepsin (F, L cleavage)
  - Lys-C (K cleavage)
  - Arg-C (R cleavage)
  - Glu-C (E, D cleavage)
- **Missed Cleavages**: Configurable (0-3+ missed cleavages)
- **Length Filtering**: Min/max peptide length constraints
- **N-Glycosylation Detection**: Regex-based motif finding (N-X-S/T, X≠P)
- **Mass Calculation**: Monoisotopic mass with amino acid residue masses
- **Protein Provenance**: Track parent protein ID and peptide position

#### Key Classes

```python
@dataclass
class Protein:
    id: str                    # UniProt ID
    description: str           # Protein name/description
    sequence: str              # Amino acid sequence

@dataclass
class Peptide:
    sequence: str                        # Peptide sequence
    protein_id: str                      # Parent protein
    start_position: int                  # Start in protein (1-indexed)
    end_position: int                    # End in protein
    missed_cleavages: int                # Number of missed cleavages
    mass: float                          # Monoisotopic mass (Da)
    has_glycosylation_site: bool        # N-X-S/T motif present?
    glycosylation_sites: List[int]       # Positions of N in motifs
```

#### Usage Example

```python
from src.database import FastaParser

# Parse FASTA file
parser = FastaParser("uniprot_human.fasta")
proteins = parser.parse()

# Digest with trypsin
peptides = parser.digest(
    enzyme='trypsin',
    missed_cleavages=2,
    min_length=6,
    max_length=30
)

# Filter for glycopeptides
glyco_peptides = parser.filter_by_glycosylation_site(peptides)
print(f"Found {len(glyco_peptides)} glycopeptides")
```

---

### 2. Glycan Database (`src/database/glycan_database.py`)

**Lines of Code**: 346
**Test Coverage**: 13 tests (all passing)

#### Features

- **Common N-Glycans**: 63 pre-defined structures covering biological diversity
- **Composition Parsing**: Parse H#N#F#A# format into monosaccharide counts
- **Mass Calculation**: Monoisotopic mass from composition
- **Type Classification**: Automatic classification into 5 categories
- **Custom Loading**: Load glycan libraries from text files
- **Statistics**: Distribution analysis by glycan type

#### Glycan Classification System

| Type | Code | Criteria | Count | Example |
|------|------|----------|-------|---------|
| **High-Mannose** | HM | H≥5, N=2, no F or A | 5 | H5N2 |
| **Fucosylated** | F | Has F, no A | 12 | H5N4F1 |
| **Sialylated** | S | Has A, no F | 18 | H5N4A2 |
| **Sialofucosylated** | SF | Both F and A | 17 | H5N4F1A2 |
| **Complex/Hybrid** | C/H | Everything else | 11 | H3N4 |

**Total**: 63 glycan structures

#### Monosaccharide Masses

| Monosaccharide | Code | Mass (Da) | Full Name |
|----------------|------|-----------|-----------|
| Hexose | H | 162.052823 | Mannose, Galactose |
| HexNAc | N | 203.079373 | N-acetylglucosamine |
| Fucose | F | 146.057909 | Deoxyhexose |
| NeuAc | A | 291.095417 | Sialic acid |

#### Usage Example

```python
from src.database import GlycanDatabase, GlycanType

# Load default glycan library
glycan_db = GlycanDatabase()
print(f"Loaded {len(glycan_db.glycans)} glycans")

# Get specific glycan
glycan = glycan_db.get_glycan_by_composition("H5N4F1A2")
print(f"Mass: {glycan.mass:.2f} Da")
print(f"Type: {glycan.glycan_type.value}")

# Filter by type
hm_glycans = glycan_db.filter_by_type(GlycanType.HIGH_MANNOSE)
print(f"Found {len(hm_glycans)} high-mannose glycans")
```

---

### 3. Candidate Generator (`src/database/candidate_generator.py`)

**Lines of Code**: 299
**Test Coverage**: 7 tests (all passing)

#### Features

- **Pre-computed Index**: Binary search-optimized mass index
- **Mass Matching**: PPM-based tolerance filtering
- **Neutral Mass Calculation**: Convert m/z + charge → neutral mass
- **PPM Error Calculation**: Accurate mass deviation metrics
- **Candidate Ranking**: Sort by absolute PPM error
- **Glycosylation Validation**: Ensure candidates have valid N-glycosites
- **Performance Optimized**: <100ms search time for typical databases

#### Algorithm

1. **Indexing Phase** (one-time):
   ```
   For each peptide with N-glycosylation site:
       For each glycan:
           Calculate mass = peptide_mass + glycan_mass
           Store (mass, peptide, glycan) in sorted list
   ```

2. **Search Phase** (per precursor):
   ```
   Input: precursor m/z, charge, tolerance (ppm)

   1. Calculate neutral mass: M = (m/z × z) - (z × proton_mass)
   2. Calculate tolerance window: ±(tolerance_ppm / 1e6) × M
   3. Binary search sorted index for candidates in window
   4. Calculate PPM error for each candidate
   5. Rank by |PPM error|
   6. Return top N candidates
   ```

#### Usage Example

```python
from src.database import CandidateGenerator

# Create generator
generator = CandidateGenerator(glyco_peptides, glycans)

# Show index size
index_info = generator.get_index_size()
print(f"Indexed {index_info['total_glycopeptides']:,} combinations")

# Search for precursor
candidates = generator.generate_candidates(
    precursor_mz=1523.7245,
    charge=2,
    tolerance_ppm=10.0
)

print(f"Found {len(candidates)} candidates")
for candidate in candidates[:5]:
    print(f"{candidate.peptide.sequence} + {candidate.glycan.composition}")
    print(f"  PPM: {candidate.ppm_error:+.2f}")
```

---

## 🧪 Testing

### Unit Tests (`tests/test_database.py`)

**Total Tests**: 28
**Pass Rate**: 100%
**Execution Time**: ~30ms

#### Test Coverage by Module

| Module | Tests | Coverage |
|--------|-------|----------|
| Glycan | 7 | Composition parsing, mass calculation, type classification |
| GlycanDatabase | 6 | Generation, retrieval, filtering, statistics, file loading |
| Peptide | 2 | Mass calculation, glycosylation site detection |
| FastaParser | 6 | FASTA parsing, digestion, missed cleavages, motif detection, filtering |
| CandidateGenerator | 7 | Mass calculations, PPM error, candidate generation, tolerance filtering |

#### Running Unit Tests

```bash
# Option 1: Standalone mode
python tests/test_database.py

# Option 2: pytest (verbose)
pytest tests/test_database.py -v

# Option 3: pytest (coverage)
pytest tests/test_database.py --cov=src.database --cov-report=html
```

**Expected Output**:
```
================================================================================
  DATABASE MODULE UNIT TESTS
================================================================================

test_calculate_mass (TestGlycan) ... ok
test_classify_high_mannose (TestGlycan) ... ok
...
test_get_index_size (TestCandidateGenerator) ... ok

--------------------------------------------------------------------------------
Ran 28 tests in 0.036s

OK

✅ ALL TESTS PASSED - Database modules validated!
```

---

### Integration Tests (`tests/test_database_integration.py`)

**Total Tests**: 4
**Pass Rate**: 100%
**Execution Time**: ~30ms

#### Test Scenarios

1. **Full Workflow Test**: FASTA → Peptides → Glycans → Candidates
   - Validates end-to-end integration
   - Uses realistic glycoprotein sequences
   - Demonstrates complete pipeline

2. **Multiple Precursor Search**: Tests candidate generation for various m/z values

3. **Glycan Type Filtering**: Tests high-mannose-only search

4. **Performance Test**: Validates <100ms search time

#### Running Integration Tests

```bash
# Standalone mode
python tests/test_database_integration.py

# pytest
pytest tests/test_database_integration.py -v
```

**Sample Output**:
```
================================================================================
STEP 1: Parse FASTA File
================================================================================
✓ Parsed 2 proteins
  - sp|P02765|FETUA_HUMAN: 192 residues
  - sp|P01857|IGHG1_HUMAN: 97 residues

================================================================================
STEP 2: In-Silico Tryptic Digestion
================================================================================
✓ Generated 31 peptides
✓ Found 4 glycopeptides (with N-X-S/T motif)

Peptide Statistics:
  Total peptides: 31
  With glyco sites: 4 (12.9%)
  Mass range: 656.39 - 3368.54 Da

[... more steps ...]

✅ ALL INTEGRATION TESTS PASSED - Database pipeline validated!
```

---

## 📖 Usage Example

### Complete Workflow (`examples/example_03_database_search.py`)

This example demonstrates the full database search workflow:

```bash
python examples/example_03_database_search.py
```

#### Workflow Steps

1. **Parse FASTA** → Extract proteins from database
2. **Digest** → Generate peptides with missed cleavages
3. **Load Glycans** → Load N-glycan library
4. **Index** → Pre-compute glycopeptide masses
5. **Search** → Match precursors to candidates
6. **Filter** → Optional glycan type filtering

#### Expected Output

```
================================================================================
  GLYCOPEPTIDE DATABASE SEARCH EXAMPLE
================================================================================

STEP 1: Parse Protein Database (FASTA)
--------------------------------------------------------------------------------
✓ Parsed 2 proteins:
  - sp|P02765|FETUA_HUMAN: 192 AA
  - sp|P01857|IGHG1_HUMAN: 97 AA

STEP 2: In-Silico Tryptic Digestion
--------------------------------------------------------------------------------
✓ Generated 31 peptides
✓ Found 4 glycopeptides with N-X-S/T motif

[... steps 3-6 ...]

================================================================================
  SUMMARY
================================================================================
✓ Parsed 2 proteins
✓ Generated 31 peptides (4 glycopeptides)
✓ Loaded 63 glycan structures
✓ Indexed 252 glycopeptide combinations
✓ Searched 3 precursors
✓ Found candidates for matching

Next steps:
  - Integrate with MS/MS spectrum parser (mzML)
  - Implement SEQUEST-inspired scoring (XCorr)
  - Generate fragment ions (b/y, B/Y, oxonium)
  - Rank candidates by spectral match quality
```

---

## 🔗 Integration with ALCOA++

All database modules integrate with the ALCOA++ audit system:

### Audit Logging

```python
from src.alcoa import AuditLogger

logger = AuditLogger()
logger.log("Parsed 2 proteins from FASTA", level="INFO")
logger.log("Generated 31 peptides", level="INFO")
logger.log("Loaded 63 glycans", level="INFO")
```

### Compliance Features

- ✅ **Attributable**: User/system metadata in logs
- ✅ **Legible**: Human-readable CSV/JSON outputs
- ✅ **Contemporaneous**: Real-time event logging
- ✅ **Original**: Checksums for FASTA/glycan files
- ✅ **Accurate**: Validated mass calculations
- ✅ **Complete**: Full provenance tracking
- ✅ **Consistent**: Reproducible results
- ✅ **Enduring**: File integrity verification
- ✅ **Available**: Accessible data formats
- ✅ **Traceable**: Audit trail for all operations

---

## 📊 Performance Benchmarks

### Typical Performance (MacBook Pro M1)

| Operation | Size | Time | Throughput |
|-----------|------|------|------------|
| FASTA parsing | 2 proteins | <1ms | N/A |
| Tryptic digestion | 289 AA | ~1ms | ~300 AA/ms |
| Glycan loading | 63 structures | <1ms | N/A |
| Index building | 252 combinations | <0.1ms | N/A |
| Precursor search | 1 query | <0.03ms | >30,000 queries/s |

### Scalability Targets (for production)

| Scenario | Target | Notes |
|----------|--------|-------|
| Parse 20K proteins | <1s | Human proteome scale |
| Digest to 500K peptides | <10s | With missed cleavages |
| Index 5M glycopeptides | <1s | 500K peptides × 10 glycans |
| Search 10K precursors | <1s | Typical MS/MS run |

---

## 🚀 Next Steps (Phase 3: Scoring)

With database modules complete, Phase 3 will implement SEQUEST-inspired scoring:

### Week 3 Tasks

1. **Spectrum Preprocessor** (`spectrum_preprocessor.py`)
   - Binning (0.5 Da bins)
   - Square root intensity transformation
   - Regional normalization (10 regions)
   - Noise filtering

2. **Theoretical Spectrum Generator** (`theoretical_spectrum.py`)
   - b/y ions for peptide backbone
   - B/Y ions for glycan fragmentation
   - Oxonium diagnostic ions (m/z 204, 366, 657)
   - Multiple charge states

3. **Preliminary Scorer** (`sp_scorer.py`)
   - Shared peak count
   - Intensity weighting
   - Fast filtering before XCorr

4. **Cross-Correlation Scorer** (`xcorr_scorer.py`)
   - FFT-based cross-correlation
   - Lag normalization
   - Final PSM score

5. **FDR Calculator** (`fdr_calculator.py`)
   - Target-decoy approach
   - Benjamini-Hochberg correction
   - Q-value calculation

---

## 📚 References

### Scientific Literature

1. **SEQUEST Algorithm**: Eng et al. (1994) J Am Soc Mass Spectrom
2. **N-Glycosylation Motif**: Bause (1983) Biochem J
3. **Glycan Nomenclature**: Symbol Nomenclature for Glycans (SNFG)
4. **BioPython**: Cock et al. (2009) Bioinformatics

### Software Dependencies

- BioPython >= 1.83 (FASTA parsing)
- NumPy >= 1.24.0 (mass calculations)
- Python >= 3.9

---

## 📝 Phase 2 Completion Checklist

- [x] Implement FASTA parser with BioPython
- [x] Implement enzymatic digestion (6 enzymes)
- [x] Implement N-glycosylation motif detection
- [x] Implement glycan database (63 structures)
- [x] Implement glycan type classification (5 types)
- [x] Implement candidate generator with mass matching
- [x] Write 28 unit tests (100% pass rate)
- [x] Write 4 integration tests (100% pass rate)
- [x] Create example script
- [x] Update documentation
- [x] Integrate with ALCOA++ audit system
- [x] Performance validation (<100ms search time)

**Phase 2 Status**: ✅ **COMPLETE** (2025-10-21)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-21
**Next Review**: Phase 3 Kickoff
