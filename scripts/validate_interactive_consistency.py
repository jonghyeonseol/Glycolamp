"""
Validation Script for Interactive vs Static Plot Consistency

This script validates that interactive plots (Plotly) produce identical
statistical results to static plots (matplotlib) by comparing their trace data.

CRITICAL for publication: Ensures all supplementary materials match figures.

Author: pGlyco Auto Combine Pipeline
Created: 2025-10-20
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def validate_dataframes_equal(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    name1: str,
    name2: str,
    tolerance: float = 1e-10
) -> bool:
    """
    Validate that two DataFrames are identical within tolerance

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        name1: Name of first dataset (for error messages)
        name2: Name of second dataset
        tolerance: Numerical tolerance for floating point comparison

    Returns:
        True if DataFrames match, False otherwise
    """
    # Check shape
    if df1.shape != df2.shape:
        logger.error(f"❌ Shape mismatch: {name1} {df1.shape} vs {name2} {df2.shape}")
        return False

    # Check column names
    if set(df1.columns) != set(df2.columns):
        logger.error(f"❌ Column mismatch:")
        logger.error(f"   {name1} columns: {sorted(df1.columns)}")
        logger.error(f"   {name2} columns: {sorted(df2.columns)}")
        return False

    # Check numerical columns for consistency
    numeric_cols = df1.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Handle NaN values
        df1_col = df1[col].copy()
        df2_col = df2[col].copy()

        # Compare non-NaN values
        mask = ~(df1_col.isna() | df2_col.isna())
        if mask.sum() > 0:
            max_diff = (df1_col[mask] - df2_col[mask]).abs().max()
            if max_diff > tolerance:
                logger.error(f"❌ Numerical difference in column '{col}': max diff = {max_diff:.2e}")
                # Show examples
                diff_mask = (df1_col - df2_col).abs() > tolerance
                if diff_mask.sum() > 0:
                    examples = pd.DataFrame({
                        f'{name1}': df1_col[diff_mask].head(3),
                        f'{name2}': df2_col[diff_mask].head(3),
                        'Diff': (df1_col - df2_col)[diff_mask].head(3)
                    })
                    logger.error(f"   Examples:\n{examples}")
                return False

        # Check NaN counts match
        nan_count1 = df1_col.isna().sum()
        nan_count2 = df2_col.isna().sum()
        if nan_count1 != nan_count2:
            logger.error(f"❌ NaN count mismatch in '{col}': {name1}={nan_count1}, {name2}={nan_count2}")
            return False

    # Check string columns
    string_cols = df1.select_dtypes(include=['object']).columns
    for col in string_cols:
        if not df1[col].equals(df2[col]):
            logger.error(f"❌ String column '{col}' differs")
            return False

    logger.info(f"✅ {name1} and {name2} match perfectly")
    return True


def validate_volcano_plot(results_dir: Path) -> bool:
    """Validate volcano plot consistency"""
    logger.info("\n" + "="*80)
    logger.info("VALIDATING: Volcano Plot")
    logger.info("="*80)

    static_file = results_dir / "Trace" / "volcano_plot_data.csv"
    interactive_file = results_dir / "Trace" / "volcano_plot_interactive_data.csv"

    if not static_file.exists():
        logger.warning(f"⚠️  Static file not found: {static_file}")
        return False

    if not interactive_file.exists():
        logger.warning(f"⚠️  Interactive file not found: {interactive_file}")
        return False

    static_df = pd.read_csv(static_file)
    interactive_df = pd.read_csv(interactive_file)

    logger.info(f"Static file: {static_df.shape[0]} rows, {static_df.shape[1]} columns")
    logger.info(f"Interactive file: {interactive_df.shape[0]} rows, {interactive_df.shape[1]} columns")

    # Volcano plots may have different columns (interactive has fewer display columns)
    # Validate on common core columns only
    core_cols = ['Peptide', 'GlycanComposition', 'Log2FC', 'FDR', 'Regulation']
    common_cols = [col for col in core_cols if col in static_df.columns and col in interactive_df.columns]

    logger.info(f"Validating {len(common_cols)} core columns: {common_cols}")

    return validate_dataframes_equal(
        static_df[common_cols],
        interactive_df[common_cols],
        "Static volcano",
        "Interactive volcano"
    )


def validate_vip_plots(results_dir: Path) -> bool:
    """Validate VIP score plot consistency"""
    logger.info("\n" + "="*80)
    logger.info("VALIDATING: VIP Score Plots")
    logger.info("="*80)

    vip_types = ['glycopeptide', 'glycan_composition', 'peptide']
    all_valid = True

    for vip_type in vip_types:
        logger.info(f"\n--- VIP Plot: {vip_type} ---")

        # Static version uses different naming
        static_file = results_dir / "Trace" / f"vip_score_{vip_type}_data.csv"
        interactive_file = results_dir / "Trace" / f"vip_score_{vip_type}_interactive_data.csv"

        if not static_file.exists():
            logger.warning(f"⚠️  Static file not found: {static_file}")
            all_valid = False
            continue

        if not interactive_file.exists():
            logger.warning(f"⚠️  Interactive file not found: {interactive_file}")
            all_valid = False
            continue

        static_df = pd.read_csv(static_file)
        interactive_df = pd.read_csv(interactive_file)

        logger.info(f"Static file: {static_df.shape[0]} rows, {static_df.shape[1]} columns")
        logger.info(f"Interactive file: {interactive_df.shape[0]} rows, {interactive_df.shape[1]} columns")

        # VIP plots may show different numbers of features (top 10 vs top 20)
        # Validate that the overlapping top N rows match
        n_overlap = min(len(static_df), len(interactive_df))
        logger.info(f"Validating top {n_overlap} features (overlap)")

        # Compare common columns only (Feature and VIP_Score are core)
        core_cols = ['Feature', 'VIP_Score']
        common_cols = [col for col in core_cols if col in static_df.columns and col in interactive_df.columns]

        is_valid = validate_dataframes_equal(
            static_df[common_cols].head(n_overlap),
            interactive_df[common_cols].head(n_overlap),
            f"Static VIP ({vip_type})",
            f"Interactive VIP ({vip_type})"
        )

        all_valid = all_valid and is_valid

    return all_valid


def validate_pca_plot(results_dir: Path) -> bool:
    """Validate PCA plot consistency"""
    logger.info("\n" + "="*80)
    logger.info("VALIDATING: PCA Plot")
    logger.info("="*80)

    static_file = results_dir / "Trace" / "pca_plot_data.csv"
    interactive_file = results_dir / "Trace" / "pca_plot_interactive_data.csv"

    if not static_file.exists():
        logger.warning(f"⚠️  Static file not found: {static_file}")
        return False

    if not interactive_file.exists():
        logger.warning(f"⚠️  Interactive file not found: {interactive_file}")
        return False

    static_df = pd.read_csv(static_file)
    interactive_df = pd.read_csv(interactive_file)

    logger.info(f"Static file: {static_df.shape[0]} rows, {static_df.shape[1]} columns")
    logger.info(f"Interactive file: {interactive_df.shape[0]} rows, {interactive_df.shape[1]} columns")

    return validate_dataframes_equal(
        static_df,
        interactive_df,
        "Static PCA",
        "Interactive PCA"
    )


def main():
    """Main validation routine"""
    results_dir = Path("Results")

    if not results_dir.exists():
        logger.error(f"❌ Results directory not found: {results_dir}")
        logger.error("   Please run the pipeline first: python3 main.py")
        sys.exit(1)

    logger.info("=" * 80)
    logger.info("INTERACTIVE VS STATIC PLOT CONSISTENCY VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Results directory: {results_dir.absolute()}")

    # Run all validations
    volcano_valid = validate_volcano_plot(results_dir)
    vip_valid = validate_vip_plots(results_dir)
    pca_valid = validate_pca_plot(results_dir)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 80)

    results = {
        "Volcano Plot": volcano_valid,
        "VIP Score Plots": vip_valid,
        "PCA Plot": pca_valid
    }

    for name, valid in results.items():
        status = "✅ PASS" if valid else "❌ FAIL"
        logger.info(f"{status} - {name}")

    # Overall result
    all_valid = all(results.values())

    logger.info("=" * 80)
    if all_valid:
        logger.info("🎉 ALL VALIDATIONS PASSED")
        logger.info("   Interactive plots are consistent with static versions")
        logger.info("   Data integrity confirmed for publication")
        sys.exit(0)
    else:
        logger.error("❌ VALIDATION FAILED")
        logger.error("   Some interactive plots do not match static versions")
        logger.error("   Review errors above and fix before publication")
        sys.exit(1)


if __name__ == "__main__":
    main()
