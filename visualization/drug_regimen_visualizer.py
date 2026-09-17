# visualization/drug_regimen_visualizer.py
"""Drug regimen visualization - tailored for your drug_data structure."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict
from collections import Counter, defaultdict
from .base_visualizer import BaseVisualizer

class DrugRegimenVisualizer(BaseVisualizer):
    """Visualize drug selection patterns and regimen characteristics."""
    
    def plot_drug_frequency(self, regimens: List[Dict], drug_data: Dict,
                           patient_ids: List[str] = None,
                           title: str = "Drug Selection Frequency"):
        """Plot frequency of drugs in optimal primary regimens."""
        drug_counter = Counter()
        for i, regimen in enumerate(regimens):
            for drug in regimen.get('primary_regimen', []):
                drug_counter[drug] += 1
        
        if not drug_counter:
            print("⚠ No drugs to visualize")
            return None
        
        drugs = np.array(list(drug_counter.keys()))
        frequencies = np.array([drug_counter[d] for d in drugs])
        sorted_idx = np.argsort(frequencies)[::-1]
        
        drugs = drugs[sorted_idx]
        frequencies = frequencies[sorted_idx]
        
        classes = [drug_data.get(d, {}).get('Class', 'Unknown') for d in drugs]
        class_colors = {'NRTI': '#4E79A7', 'NNRTI': '#F28E2B', 'INSTI': '#E15759', 
                       'PI': '#76B7B2', 'Entry_Inhibitor': '#59A14F', 'Capsid_Inhibitor': '#EDC948'}
        colors = [class_colors.get(c, '#B0B0B0') for c in classes]
        
        fig, ax = plt.subplots(figsize=(10, max(5, len(drugs)*0.4)))
        bars = ax.barh(drugs, frequencies, color=colors, edgecolor='black', alpha=0.8)
        
        ax.set_xlabel('Frequency in Optimal Regimens', fontsize=11)
        ax.set_ylabel('Drug', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.invert_yaxis()
        
        for bar, freq in zip(bars, frequencies):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                  str(int(freq)), va='center', fontsize=9, fontweight='bold')
        
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, label=cls) for cls, color in class_colors.items() 
                          if cls in classes]
        if legend_elements:
            ax.legend(handles=legend_elements, title='Drug Class', loc='lower right', fontsize=9)
        
        plt.tight_layout()
        self.save_figure(fig, 'drug_frequency.png')
        return fig

    def plot_cost_efficacy_scatter(self, regimens: List[Dict], drug_data: Dict,
                                   fitness_scores: List[float],
                                    patient_ids: List[str] = None):
        """Scatter plot: Cost vs Efficacy, colored by fitness."""
        costs = []
        efficacies = []
        
        for i, regimen in enumerate(regimens):
            primary = regimen.get('primary_regimen', [])
            cost = sum(drug_data.get(d, {}).get('Monthly_Cost_USD', 0) for d in primary)
            costs.append(cost)
            
            efficacy_sum = 0
            for drug in primary:
                base_efficacy = drug_data.get(drug, {}).get('Efficacy', 0.5)
                efficacy_sum += base_efficacy
            avg_efficacy = efficacy_sum / len(primary) if primary else 0
            efficacies.append(avg_efficacy)
        
        if not costs:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 7))
        scatter = ax.scatter(costs, efficacies, c=fitness_scores, 
                           cmap='RdYlGn', s=120, alpha=0.7, 
                           edgecolors='black', linewidth=0.5)
        
        ax.set_xlabel('Monthly Cost (USD)', fontsize=11)
        ax.set_ylabel('Average Efficacy', fontsize=11)
        ax.set_title('Regimen Cost vs Efficacy\n(Color = Fitness Score)', 
                    fontsize=13, fontweight='bold')
        
        cbar = plt.colorbar(scatter, ax=ax, label='Fitness Score')
        cbar.ax.tick_params(labelsize=9)
        
        ax.axvline(x=50, color='gray', linestyle=':', alpha=0.5)
        ax.text(52, 0.95, 'Cost-Effective\nZone ( <$50/mo)', fontsize=9, 
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
        
        ax.grid(True, alpha=0.3, linestyle=':')
        plt.tight_layout()
        
        self.save_figure(fig, 'cost_efficacy_tradeoff.png')
        return fig

    def plot_class_balance(self, regimens: List[Dict], drug_data: Dict):
        """Show drug class composition in selected regimens."""
        class_counts = Counter()
        
        for regimen in regimens:
            for drug in regimen.get('primary_regimen', []):
                drug_class = drug_data.get(drug, {}).get('Class', 'Unknown')
                class_counts[drug_class] += 1
        
        if not class_counts:
            return None
        
        labels = list(class_counts.keys())
        sizes = list(class_counts.values())
        colors = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948', '#B0B0B0']
        
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                         colors=colors[:len(labels)],
                                         startangle=90, textprops={'fontsize': 10})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Drug Class Distribution in Optimal Regimens', 
                    fontsize=13, fontweight='bold', pad=20)
        
        plt.tight_layout()
        self.save_figure(fig, 'class_distribution.png')
        return fig