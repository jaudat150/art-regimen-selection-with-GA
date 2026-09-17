# visualization/statistical_plots.py
"""Statistical analysis visualizations."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict
from .base_visualizer import BaseVisualizer

class StatisticalPlots(BaseVisualizer):
    """Statistical analysis and comparison plots."""
    
    def plot_efficacy_vs_cost(self, regimens: List[Dict], drug_data: Dict,
                             fitness_scores: List[float]):
        """Scatter plot of regimen efficacy vs cost."""
        costs = []
        efficacies = []
        
        for i, regimen in enumerate(regimens):
            cost = sum(drug_data[d]['Monthly_Cost_USD'] 
                       for d in regimen['primary_regimen'])
            costs.append(cost)
            efficacies.append(fitness_scores[i])
        
        fig, ax = plt.subplots()
        scatter = ax.scatter(costs, efficacies, c=fitness_scores, 
                           cmap='RdYlGn', s=100, alpha=0.6, edgecolors='black')
        
        ax.set_xlabel('Monthly Cost (USD)', fontsize=12)
        ax.set_ylabel('Fitness Score', fontsize=12)
        ax.set_title('Regimen Cost vs Effectiveness', fontsize=14, fontweight='bold')
        
        plt.colorbar(scatter, label='Fitness Score')
        ax.grid(True, alpha=0.3)
        
        self.save_figure(fig, 'efficacy_vs_cost.png')
        return fig

    def plot_resistance_impact(self, profiles: List[Dict], drug_data: Dict):
        """Visualize impact of resistance mutations."""
        mutation_counts = {}
        for profile in profiles:
            for mutation in profile.get('Mutations', []):
                mutation_counts[mutation] = mutation_counts.get(mutation, 0) + 1
        
        if not mutation_counts:
            print("No mutations found in profiles")
            return None
        
        mutations = list(mutation_counts.keys())
        counts = [mutation_counts[m] for m in mutations]
        
        fig, ax = plt.subplots()
        ax.barh(mutations, counts, color='salmon')
        ax.set_xlabel('Number of Patients', fontsize=12)
        ax.set_ylabel('Mutation', fontsize=12)
        ax.set_title('Resistance Mutation Prevalence', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        self.save_figure(fig, 'resistance_mutations.png')
        return fig

    def plot_fitness_boxplot(self, all_fitnesses: List[List[float]], 
                            labels: List[str] = None):
        """Box plot of fitness distributions."""
        if labels is None:
            labels = [f'Run {i+1}' for i in range(len(all_fitnesses))]
        
        fig, ax = plt.subplots()
        bp = ax.boxplot(all_fitnesses, labels=labels, patch_artist=True)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(all_fitnesses)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        ax.set_ylabel('Fitness Score', fontsize=12)
        ax.set_title('Fitness Distribution Comparison', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        self.save_figure(fig, 'fitness_boxplot.png')
        return fig