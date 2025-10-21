# Scripts Directory

Utility scripts for data analysis and visualization.

## Available Scripts

### 1. generate_protein_glycan_matrix.py

Generates protein-glycan composition matrix visualization showing Cancer vs Normal Log2FC for top proteins and glycans.

**Usage:**
```bash
# From repository root
python3 scripts/generate_protein_glycan_matrix.py
```

**Requirements:**
- Must run AFTER `python3 main.py` (requires `Results/integrated_filtered.csv`)
- Outputs: `Results/protein_glycan_composition_matrix_v1_green_black_red.png`

**Features:**
- Green-Black-Red diverging colormap (Green=Normal enriched, Red=Cancer enriched)
- Glycan types color-coded (HM, C/H, F, S, SF)
- Statistical filtering: |Log2FC| ≥ 1.0, p-value ≤ 0.05
- Top 25 proteins, top 10 glycans per type

### 2. validate_interactive_consistency.py

Validates consistency between static PNG and interactive HTML visualizations.

**Usage:**
```bash
python3 scripts/validate_interactive_consistency.py
```

### 3. verify_trace_data.py

Verifies trace CSV data integrity and completeness.

**Usage:**
```bash
python3 scripts/verify_trace_data.py
```

## Notes

- All scripts should be run from the repository root directory
- Scripts assume the standard directory structure (Dataset/, Results/, etc.)
- See main README.md for full pipeline documentation
