"""
Generate 5 different design versions of protein-glycan composition matrix
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

# Design configurations
DESIGNS = {
    'v1_green_black_red': {
        'name': 'Green-Black-Red Diverging Scale',
        'bg_color': 'white',
        'text_color': 'black',
        'grid_color': '#CCCCCC',
        'cmap_name': 'custom_green_black_red',
        'nan_color': 'black',
        'grid_width': 0.8,
        'colorbar_orientation': 'vertical',
        'colorbar_location': 'right',
        'show_glycan_bar': True,
        'edge_color': 'black',
        'spine_width': 2.0,
        'glycan_bar_text_color': 'white',
        'glycan_bar_text_weight': 'bold',
        'glycan_bar_border_color': 'black',
        'glycan_bar_border_width': 2.0,
        'figsize': (20, 14),
        'dpi': 300,
    }
}

GLYCAN_COLORS = {
    'HM': '#00FF00',
    'C/H': '#0000FF',
    'F': '#FFA500',
    'S': '#FF69B4',
    'SF': '#9932CC'
}

def prepare_matrix_data(df, log2fc_threshold=1.0, p_value_threshold=0.05, top_n_proteins=25, max_glycans_per_type=10):
    """Prepare the matrix data (shared across all design versions)"""

    print("Preparing matrix data...")

    # Get sample columns
    cancer_samples = [col for col in df.columns if col.startswith('C') and col[1:].isdigit()]
    normal_samples = [col for col in df.columns if col.startswith('N') and col[1:].isdigit()]

    # Calculate statistics
    stats_results = []

    for idx, row in df.iterrows():
        cancer_values = pd.to_numeric(row[cancer_samples], errors='coerce').dropna()
        normal_values = pd.to_numeric(row[normal_samples], errors='coerce').dropna()

        if len(cancer_values) < 5 or len(normal_values) < 5:
            continue

        cancer_mean = cancer_values.mean()
        normal_mean = normal_values.mean()
        log2fc = np.log2((cancer_mean + 1) / (normal_mean + 1))

        try:
            _, p_value = stats.mannwhitneyu(cancer_values, normal_values, alternative='two-sided')
        except:
            p_value = 1.0

        stats_results.append({
            'Peptide': row['Peptide'],
            'GlycanComposition': row['GlycanComposition'],
            'ProteinID': row['ProteinID'],
            'GlycanTypeCategory': row.get('GlycanTypeCategory', 'Unknown'),
            'Log2FC': log2fc,
            'P_Value': p_value
        })

    stats_df = pd.DataFrame(stats_results)

    # Filter for significance
    significant_mask = (
        (np.abs(stats_df['Log2FC']) >= log2fc_threshold) &
        (stats_df['P_Value'] <= p_value_threshold)
    )
    sig_df = stats_df[significant_mask].copy()

    print(f"Found {len(sig_df)} significant glycopeptides from {sig_df['ProteinID'].nunique()} proteins")

    # Select top proteins
    protein_counts = sig_df['ProteinID'].value_counts()
    top_proteins = protein_counts.head(top_n_proteins).index.tolist()
    plot_df = sig_df[sig_df['ProteinID'].isin(top_proteins)].copy()

    # Group glycans by type
    glycan_order = []
    glycan_type_positions = {}
    current_pos = 0

    for glycan_type in ['HM', 'C/H', 'F', 'S', 'SF']:
        type_glycans = plot_df[plot_df['GlycanTypeCategory'] == glycan_type]['GlycanComposition'].value_counts()
        selected_glycans = type_glycans.head(max_glycans_per_type).index.tolist()

        # Sort glycans properly - extract numbers for comparison
        def glycan_sort_key(glycan_str):
            """Extract numbers from glycan composition for proper sorting"""
            import re
            # Extract all numbers from the string
            numbers = re.findall(r'\d+', glycan_str)
            # Convert to integers for proper numeric comparison
            return [int(n) for n in numbers] if numbers else [0]

        selected_glycans = sorted(selected_glycans, key=glycan_sort_key)

        if selected_glycans:
            glycan_type_positions[glycan_type] = (current_pos, current_pos + len(selected_glycans))
            glycan_order.extend(selected_glycans)
            current_pos += len(selected_glycans)

    # Create matrix
    matrix_data = []
    protein_order = []

    for protein in top_proteins:
        protein_data = plot_df[plot_df['ProteinID'] == protein]
        row_values = []

        for glycan in glycan_order:
            glycan_data = protein_data[protein_data['GlycanComposition'] == glycan]
            if len(glycan_data) > 0:
                row_values.append(glycan_data['Log2FC'].mean())
            else:
                row_values.append(np.nan)

        matrix_data.append(row_values)
        protein_order.append(f"{protein}\n(n={len(protein_data)})")

    matrix = pd.DataFrame(matrix_data, index=protein_order, columns=glycan_order)

    return matrix, glycan_type_positions, glycan_order


def plot_matrix_design(matrix, glycan_type_positions, glycan_order, design_config, output_path):
    """Generate a single design version"""

    print(f"  Generating: {design_config['name']}")

    # Create figure with improved dimensions
    figsize = design_config.get('figsize', (28, 16))
    dpi = design_config.get('dpi', 300)
    fig = plt.figure(figsize=figsize, dpi=dpi, facecolor=design_config['bg_color'])

    # Determine grid layout based on design with improved spacing
    if design_config['show_glycan_bar'] and design_config['colorbar_location'] == 'right':
        # Glycan bar on top, heatmap in center, colorbar on right
        # Adjusted margins: top for title, bottom for x-labels, left/right for spacing
        gs = fig.add_gridspec(2, 2, height_ratios=[0.8, 20], width_ratios=[20, 1.5],
                              hspace=0.15, wspace=0.10,
                              top=0.90, bottom=0.15, left=0.10, right=0.94)
        ax_glycan_bar = fig.add_subplot(gs[0, 0], facecolor=design_config['bg_color'])
        ax = fig.add_subplot(gs[1, 0], facecolor=design_config['bg_color'])
        ax_cbar = fig.add_subplot(gs[1, 1], facecolor=design_config['bg_color'])
    elif design_config['show_glycan_bar'] and design_config['colorbar_location'] == 'bottom':
        # Glycan bar on top, heatmap in center, colorbar on bottom
        gs = fig.add_gridspec(3, 1, height_ratios=[1, 20, 1],
                              hspace=0.15)
        ax_glycan_bar = fig.add_subplot(gs[0, 0], facecolor=design_config['bg_color'])
        ax = fig.add_subplot(gs[1, 0], facecolor=design_config['bg_color'])
        ax_cbar = fig.add_subplot(gs[2, 0], facecolor=design_config['bg_color'])
    elif not design_config['show_glycan_bar'] and design_config['colorbar_location'] == 'right':
        # No glycan bar, heatmap on left, colorbar on right
        gs = fig.add_gridspec(1, 2, width_ratios=[20, 1], wspace=0.05)
        ax = fig.add_subplot(gs[0, 0], facecolor=design_config['bg_color'])
        ax_cbar = fig.add_subplot(gs[0, 1], facecolor=design_config['bg_color'])
        ax_glycan_bar = None
    else:
        # No glycan bar, heatmap on top, colorbar on bottom
        gs = fig.add_gridspec(2, 1, height_ratios=[20, 1], hspace=0.15)
        ax = fig.add_subplot(gs[0, 0], facecolor=design_config['bg_color'])
        ax_cbar = fig.add_subplot(gs[1, 0], facecolor=design_config['bg_color'])
        ax_glycan_bar = None

    # Prepare colormap
    vmax = max(abs(matrix.min().min()), abs(matrix.max().max()))

    # Create custom Green-Black-Red colormap with steeper gradient
    if design_config['cmap_name'] == 'custom_green_black_red':
        from matplotlib.colors import LinearSegmentedColormap
        import numpy as np

        # Create non-linear positions to make gradient steeper near center (black)
        # This makes colors transition more quickly from black, creating higher contrast
        positions = np.array([0.0, 0.4, 0.5, 0.6, 1.0])
        colors_with_positions = [
            (0.0, '#00FF00'),    # Far negative: fluorescent bright green
            (0.4, '#00AA00'),    # Near negative: medium green (steeper transition)
            (0.5, 'black'),      # Zero: black
            (0.6, 'darkred'),    # Near positive: dark red (steeper transition)
            (1.0, 'red')         # Far positive: full red
        ]

        # Extract positions and colors
        positions = [p for p, c in colors_with_positions]
        colors = [c for p, c in colors_with_positions]

        n_bins = 256
        cmap = LinearSegmentedColormap.from_list('green_black_red',
                                                 list(zip(positions, colors)),
                                                 N=n_bins)
    else:
        cmap = plt.cm.get_cmap(design_config['cmap_name']).copy()

    cmap.set_bad(color=design_config['nan_color'])

    # Plot heatmap
    if design_config['colorbar_location'] in ['right', 'left']:
        cbar_orientation = 'vertical'
        cbar_label_rotation = 270 if design_config['colorbar_location'] == 'right' else 90
        cbar_labelpad = 20
    else:
        cbar_orientation = 'horizontal'
        cbar_label_rotation = 0
        cbar_labelpad = 10

    sns.heatmap(
        matrix,
        cmap=cmap,
        center=0,
        vmin=-vmax,
        vmax=vmax,
        annot=False,
        cbar_ax=ax_cbar,
        cbar_kws={'label': 'Log2 FC (Cancer/Normal)', 'orientation': cbar_orientation},
        linewidths=design_config['grid_width'],
        linecolor=design_config['grid_color'],
        ax=ax,
        square=True  # Make each cell square-shaped
    )

    # Format colorbar
    if cbar_orientation == 'vertical':
        ax_cbar.yaxis.set_label_position('right' if design_config['colorbar_location'] == 'right' else 'left')
        cbar_label = ax_cbar.get_ylabel()
        ax_cbar.set_ylabel(cbar_label, fontsize=12, fontweight='bold',
                          color=design_config['text_color'], rotation=cbar_label_rotation, labelpad=cbar_labelpad)
    else:
        ax_cbar.xaxis.set_label_position('bottom' if design_config['colorbar_location'] == 'bottom' else 'top')
        cbar_label = ax_cbar.get_xlabel()
        ax_cbar.set_xlabel(cbar_label, fontsize=12, fontweight='bold',
                          color=design_config['text_color'], rotation=cbar_label_rotation, labelpad=cbar_labelpad)

    ax_cbar.tick_params(colors=design_config['text_color'], labelsize=9)
    for spine in ax_cbar.spines.values():
        spine.set_edgecolor(design_config['edge_color'])
        spine.set_linewidth(design_config['spine_width'])

    # Add glycan type bar if enabled
    if design_config['show_glycan_bar'] and ax_glycan_bar is not None:
        glycan_type_array = np.zeros(len(glycan_order))
        glycan_type_colors_map = {'HM': 0, 'C/H': 1, 'F': 2, 'S': 3, 'SF': 4}

        for i, glycan in enumerate(glycan_order):
            for glycan_type, (start, end) in glycan_type_positions.items():
                if start <= i < end:
                    glycan_type_array[i] = glycan_type_colors_map.get(glycan_type, 0)
                    break

        glycan_type_cmap = plt.matplotlib.colors.ListedColormap([
            GLYCAN_COLORS['HM'], GLYCAN_COLORS['C/H'], GLYCAN_COLORS['F'],
            GLYCAN_COLORS['S'], GLYCAN_COLORS['SF']
        ])

        ax_glycan_bar.imshow(glycan_type_array.reshape(1, -1), cmap=glycan_type_cmap,
                            aspect='auto', interpolation='nearest')

        # Add labels with improved styling
        glycan_bar_label_size = design_config.get('glycan_bar_label_size', 13)
        glycan_bar_text_color = design_config.get('glycan_bar_text_color', 'white')
        glycan_bar_text_weight = design_config.get('glycan_bar_text_weight', 'bold')
        glycan_bar_border_width = design_config.get('glycan_bar_border_width', 2.0)

        for glycan_type, (start, end) in glycan_type_positions.items():
            mid_pos = (start + end) / 2
            # Add text with shadow effect for better readability
            ax_glycan_bar.text(mid_pos, 0, glycan_type, ha='center', va='center',
                              fontsize=glycan_bar_label_size,
                              fontweight=glycan_bar_text_weight,
                              color=glycan_bar_text_color,
                              bbox=dict(boxstyle='round,pad=0.3',
                                       facecolor='black',
                                       edgecolor='none',
                                       alpha=0.3))
            if end < len(glycan_order):
                ax_glycan_bar.axvline(x=end - 0.5,
                                     color=design_config.get('glycan_bar_border_color', 'black'),
                                     linewidth=glycan_bar_border_width)

        ax_glycan_bar.set_xlim(-0.5, len(glycan_order) - 0.5)
        ax_glycan_bar.set_ylim(-0.5, 0.5)
        ax_glycan_bar.set_xticks([])
        ax_glycan_bar.set_yticks([])
        # Remove ylabel so bar sits flush above heatmap
        # ax_glycan_bar.set_ylabel('Glycan Type', fontsize=12, fontweight='bold',
        #                          color=design_config['text_color'])

        for spine in ax_glycan_bar.spines.values():
            spine.set_edgecolor(design_config['edge_color'])
            spine.set_linewidth(design_config['spine_width'])

    # Format main heatmap
    ax.set_xlabel('Glycan Composition (grouped by type)', fontsize=14,
                 fontweight='bold', color=design_config['text_color'])
    ax.set_ylabel('Protein (UniProt ID)', fontsize=14,
                 fontweight='bold', color=design_config['text_color'])

    # Set title on the figure instead of the axis for better positioning
    fig.suptitle(f'Protein-Glycan Composition Matrix\n{design_config["name"]}',
                fontsize=18, fontweight='bold', color=design_config['text_color'], y=0.98)

    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='center',
                      fontsize=8, color=design_config['text_color'])
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0,
                      fontsize=9, color=design_config['text_color'])
    ax.tick_params(colors=design_config['text_color'], which='both')

    for spine in ax.spines.values():
        spine.set_edgecolor(design_config['edge_color'])
        spine.set_linewidth(design_config['spine_width'])

    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
               facecolor=design_config['bg_color'], edgecolor=design_config['edge_color'])
    plt.close()

    print(f"    Saved to: {output_path}")


def main():
    """Generate protein-glycan matrix with Green-Black-Red colormap"""

    print("="*60)
    print("Generating Protein-Glycan Matrix")
    print("Green (Low/Normal) - Black (Zero) - Red (High/Cancer)")
    print("="*60)

    # Load data
    print("\nLoading data...")
    # Find the header line (starts with "Peptide")
    with open('Results/integrated_filtered.csv', 'r') as f:
        for i, line in enumerate(lines := f.readlines()):
            if line.startswith('Peptide'):
                skiprows = i
                break

    df = pd.read_csv('Results/integrated_filtered.csv', skiprows=range(skiprows))
    print(f"Loaded {len(df)} rows with {len(df.columns)} columns")

    # Prepare matrix data (shared)
    matrix, glycan_type_positions, glycan_order = prepare_matrix_data(df)

    # Generate design
    print("\nGenerating matrix...")
    output_dir = Path('Results')

    for design_key, design_config in DESIGNS.items():
        output_path = output_dir / f'protein_glycan_composition_matrix_{design_key}.png'
        plot_matrix_design(matrix, glycan_type_positions, glycan_order, design_config, output_path)

    print("\n" + "="*60)
    print("✨ Matrix generated successfully!")
    print("="*60)
    print("\nGenerated file:")
    print(f"  Results/protein_glycan_composition_matrix_v1_green_black_red.png")


if __name__ == '__main__':
    main()
