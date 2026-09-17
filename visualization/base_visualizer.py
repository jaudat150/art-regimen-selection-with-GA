# visualization/base_visualizer.py
"""Base visualization utilities."""
import matplotlib
matplotlib.use('Agg')          # headless-safe: no display needed
import matplotlib.pyplot as plt
from pathlib import Path

class BaseVisualizer:
    """Base class with common visualization settings."""
    def __init__(self, output_dir: str = "visualization_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Style. Previously this called seaborn.set_style('whitegrid'), which
        # pulled in seaborn -> scipy for a single cosmetic line and made the
        # whole visualisation module fail on any scipy/numpy version mismatch.
        # Equivalent styling, matplotlib only.
        plt.rcParams.update({
            'figure.figsize': (10, 6),
            'font.size': 10,
            'axes.grid': True,
            'grid.color': 'white',
            'grid.linewidth': 1.0,
            'axes.facecolor': '#EAEAF2',
            'axes.edgecolor': 'white',
            'axes.axisbelow': True,
        })

    def save_figure(self, fig, filename: str):
        """Save figure to output directory."""
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filepath}")
        plt.close(fig)