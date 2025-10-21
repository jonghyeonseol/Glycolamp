"""
Example 2: Parse mzML Files and Analyze Spectra

This example demonstrates:
1. Parsing mzML files with Pyteomics
2. Extracting MS/MS spectrum information
3. Basic statistical analysis of spectral data
4. Visualization of representative spectra

Requirements:
- pyteomics installed (pip install pyteomics)
- matplotlib installed (pip install matplotlib)
- Input: .mzML or .mzML.gz file(s)

Author: Glycoproteomics Pipeline Team
Date: 2025-10-21
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.converters import MzMLParser


def analyze_spectra(mzml_file_path, output_dir="Results/reports"):
    """
    Parse and analyze MS/MS spectra from mzML file

    Parameters
    ----------
    mzml_file_path : str
        Path to mzML file (can be gzipped)
    output_dir : str
        Output directory for plots and reports

    Returns
    -------
    dict
        Summary statistics
    """
    print(f"📂 Loading: {Path(mzml_file_path).name}")

    # Parse mzML file
    parser = MzMLParser()
    spectra = parser.parse(
        mzml_file_path=mzml_file_path,
        ms_level=2,      # MS/MS spectra only
        min_peaks=10     # Filter out low-quality spectra
    )

    if len(spectra) == 0:
        print("❌ No MS/MS spectra found!")
        return None

    print(f"✅ Loaded {len(spectra)} MS/MS spectra\n")

    # Extract statistics
    precursor_mzs = [s.precursor_mz for s in spectra]
    charges = [s.precursor_charge for s in spectra]
    peak_counts = [len(s.mz_array) for s in spectra]
    retention_times = [s.retention_time for s in spectra]

    # Summary statistics
    stats = {
        "total_spectra": len(spectra),
        "precursor_mz_range": (min(precursor_mzs), max(precursor_mzs)),
        "precursor_mz_mean": np.mean(precursor_mzs),
        "charge_states": dict(zip(*np.unique(charges, return_counts=True))),
        "avg_peak_count": np.mean(peak_counts),
        "retention_time_range": (min(retention_times), max(retention_times)),
    }

    # Print summary
    print("="*60)
    print("📊 Spectral Data Summary:")
    print("="*60)
    print(f"  Total MS/MS Spectra: {stats['total_spectra']:,}")
    print(f"\n  Precursor m/z:")
    print(f"    Range: {stats['precursor_mz_range'][0]:.2f} - {stats['precursor_mz_range'][1]:.2f}")
    print(f"    Mean: {stats['precursor_mz_mean']:.2f}")
    print(f"\n  Charge States:")
    for charge, count in sorted(stats['charge_states'].items()):
        pct = (count / stats['total_spectra']) * 100
        print(f"    {charge}+: {count:,} ({pct:.1f}%)")
    print(f"\n  Fragment Peaks:")
    print(f"    Average per spectrum: {stats['avg_peak_count']:.1f}")
    print(f"\n  Retention Time:")
    print(f"    Range: {stats['retention_time_range'][0]:.1f} - {stats['retention_time_range'][1]:.1f} sec")
    print("="*60)

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Visualization
    print(f"\n📈 Generating visualizations...")

    # Plot 1: Precursor m/z distribution
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Precursor m/z histogram
    axes[0, 0].hist(precursor_mzs, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    axes[0, 0].set_xlabel('Precursor m/z')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Precursor m/z Distribution')
    axes[0, 0].grid(alpha=0.3)

    # Charge state distribution
    charge_values = list(stats['charge_states'].keys())
    charge_counts = list(stats['charge_states'].values())
    axes[0, 1].bar(charge_values, charge_counts, color='coral', edgecolor='black', alpha=0.7)
    axes[0, 1].set_xlabel('Charge State')
    axes[0, 1].set_ylabel('Count')
    axes[0, 1].set_title('Charge State Distribution')
    axes[0, 1].grid(alpha=0.3)

    # Peak count distribution
    axes[1, 0].hist(peak_counts, bins=30, color='mediumseagreen', edgecolor='black', alpha=0.7)
    axes[1, 0].set_xlabel('Number of Peaks')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Fragment Peak Count Distribution')
    axes[1, 0].grid(alpha=0.3)

    # Retention time profile
    axes[1, 1].scatter(retention_times, precursor_mzs, alpha=0.3, s=10, color='mediumpurple')
    axes[1, 1].set_xlabel('Retention Time (s)')
    axes[1, 1].set_ylabel('Precursor m/z')
    axes[1, 1].set_title('Precursor m/z vs Retention Time')
    axes[1, 1].grid(alpha=0.3)

    plt.tight_layout()
    summary_plot = output_dir / "spectral_summary.png"
    plt.savefig(summary_plot, dpi=300, bbox_inches='tight')
    print(f"   ✅ Summary plots: {summary_plot}")

    # Plot 2: Representative spectrum
    # Find spectrum with median peak count
    median_idx = np.argsort(peak_counts)[len(peak_counts) // 2]
    representative_spectrum = spectra[median_idx]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.vlines(
        representative_spectrum.mz_array,
        0,
        representative_spectrum.intensity_array,
        color='steelblue',
        linewidth=0.8
    )
    ax.set_xlabel('m/z', fontsize=12)
    ax.set_ylabel('Intensity', fontsize=12)
    ax.set_title(
        f'Representative MS/MS Spectrum (Scan {representative_spectrum.scan_number})\n'
        f'Precursor: {representative_spectrum.precursor_mz:.4f} m/z, '
        f'Charge: {representative_spectrum.precursor_charge}+, '
        f'Peaks: {len(representative_spectrum.mz_array)}',
        fontsize=13, fontweight='semibold'
    )
    ax.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    spectrum_plot = output_dir / "representative_spectrum.png"
    plt.savefig(spectrum_plot, dpi=300, bbox_inches='tight')
    print(f"   ✅ Representative spectrum: {spectrum_plot}")

    print(f"\n✅ Analysis complete!\n")

    return stats


if __name__ == "__main__":
    print("="*60)
    print("  mzML Spectrum Parsing and Analysis")
    print("="*60)

    # MODIFY THIS: Add your mzML file path here
    mzml_file = ""  # e.g., "Results/data/02_mzml_files/sample.mzML.gz"

    if not mzml_file:
        print("\n⚠️  No input file specified!")
        print("\nTo use this script:")
        print("1. Edit this file and set the 'mzml_file' variable")
        print("2. Run: python examples/example_02_parse_spectra.py")
        print("\nExample:")
        print("   mzml_file = 'Results/data/02_mzml_files/cancer_01.mzML.gz'")

        # Try to find mzML files automatically
        mzml_dir = Path("Results/data/02_mzml_files")
        if mzml_dir.exists():
            mzml_files = list(mzml_dir.glob("*.mzML*"))
            if mzml_files:
                print(f"\nFound {len(mzml_files)} mzML file(s) in {mzml_dir}:")
                for f in mzml_files[:5]:  # Show first 5
                    print(f"  - {f.name}")
                print(f"\nYou can use any of these files.")
        sys.exit(0)

    # Check if file exists
    if not Path(mzml_file).exists():
        print(f"\n❌ File not found: {mzml_file}")
        sys.exit(1)

    # Run analysis
    stats = analyze_spectra(mzml_file)

    if stats:
        print(f"Next steps:")
        print(f"  1. Examine the plots in Results/reports/")
        print(f"  2. Validate ALCOA++ compliance: python examples/example_03_validate_compliance.py")
        print(f"  3. Continue with database modules (Week 2)")
