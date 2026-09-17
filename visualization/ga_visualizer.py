# visualization/ga_visualizer.py
"""Genetic Algorithm visualization - tailored for HIVRegimenGA."""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Optional
from .base_visualizer import BaseVisualizer

class GAVisualizer(BaseVisualizer):
    """Visualize GA optimization progress for HIV regimen selection."""
    
    def plot_convergence(self, ga_instance, patient_id: str = "Patient"):
        """
        Plot fitness convergence using GA's tracked history.
        Works for both GA (Generations) and Brute Force (Iterations).
        """
        best_history = ga_instance.best_fitness_history
        avg_history = ga_instance.avg_fitness_history
        
        if not best_history:
            print(f"⚠ No history to plot for {patient_id}")
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        iterations = range(1, len(best_history) + 1)
        
        ax.plot(iterations, best_history, 'b-', linewidth=2.5, label='Best Fitness', marker='o', markersize=3)
        if avg_history and len(avg_history) == len(iterations) and any(
                v is not None for v in avg_history):
            ax.plot(iterations, avg_history, 'r--', linewidth=1.5,
                    label='Mean population fitness', alpha=0.8)
        
        # Updated label to be algorithm-agnostic
        ax.set_xlabel('Iteration / Generation', fontsize=11)
        # NOTE: best_fitness_history stores RAW fitness -- the GA selects on the
        # un-normalised objective (the logistic transform saturates and flattens
        # the landscape). Labelling this 1-100 would be wrong.
        ax.set_ylabel('Raw fitness (weighted objective)', fontsize=11)
        ax.set_title(f'Optimization Convergence - {patient_id}', fontsize=13, fontweight='bold', pad=15)
        ax.legend(loc='lower right', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle=':')
        
        # Add key metrics annotation
        if len(best_history) >= 2:
            improvement = best_history[-1] - best_history[0]
            try:
                max_idx = best_history.index(max(best_history))
                plateau = len(best_history) - max_idx
            except ValueError:
                plateau = 0
                
            ax.text(0.02, 0.98, 
                    f'Improvement: +{improvement:.1f}\nPlateau: {plateau} iters',
                   transform=ax.transAxes, fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.6),
                   verticalalignment='top')
        
        # Highlight WHO compliance threshold
        # The old y=80 reference line was calibrated against the normalised
        # 1-100 scale and has no meaning on the raw objective. Removed rather
        # than left in place mislabelled.
        
        plt.tight_layout()
        self.save_figure(fig, f'convergence_{patient_id}.png')
        return fig

    def plot_fitness_distribution(self, fitnesses: List[float], generation: int,
                                 patient_id: str = "Patient"):
        """Plot fitness distribution at a specific step."""
        if not fitnesses:
            return None
            
        fig, ax = plt.subplots(figsize=(9, 5))
        n, bins, patches = ax.hist(fitnesses, bins=20, edgecolor='black', 
                                   alpha=0.7, color='steelblue', density=False)
        
        mean_val = np.mean(fitnesses)
        median_val = np.median(fitnesses)
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
        ax.axvline(median_val, color='orange', linestyle=':', linewidth=2, label=f'Median: {median_val:.1f}')
        
        ax.set_xlabel('Fitness Score', fontsize=11)
        ax.set_ylabel('Frequency', fontsize=11)
        ax.set_title(f'Fitness Distribution - Step {generation} - {patient_id}',
                    fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        self.save_figure(fig, f'fitness_dist_step{generation}_{patient_id}.png')
        return fig