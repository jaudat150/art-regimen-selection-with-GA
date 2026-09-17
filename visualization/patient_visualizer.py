# visualization/patient_visualizer.py
"""Patient-specific visualizations."""
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
from .base_visualizer import BaseVisualizer

class PatientVisualizer(BaseVisualizer):
    """Visualize patient-specific data and outcomes."""
    
    def plot_patient_profile(self, profile: Dict, drug_data: Dict):
        """Visualize patient clinical profile."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        axes[0, 0].bar(['Liver Function', 'Kidney Function'],
                      [profile['Liver_Function'], profile['Kidney_Function']],
                      color=['lightcoral', 'lightblue'], alpha=0.7)
        axes[0, 0].set_ylim(0, 1)
        axes[0, 0].set_title('Organ Function', fontweight='bold')
        
        mutations = profile.get('Mutations', [])
        if mutations:
            axes[0, 1].barh(range(len(mutations)), [1]*len(mutations))
            axes[0, 1].set_yticks(range(len(mutations)))
            axes[0, 1].set_yticklabels(mutations)
            axes[0, 1].set_title('Resistance Mutations', fontweight='bold')
        else:
            axes[0, 1].text(0.5, 0.5, 'No Mutations', ha='center', va='center')
            axes[0, 1].set_title('Resistance Mutations', fontweight='bold')
        
        cost_sens = profile.get('Cost_Sensitivity', 'Medium')
        colors = {'High': 'red', 'Medium': 'orange', 'Low': 'green'}
        axes[1, 0].bar(['Cost Sensitivity'], [1], color=colors.get(cost_sens, 'gray'))
        axes[1, 0].set_title(f'Cost Sensitivity: {cost_sens}', fontweight='bold')
        
        axes[1, 1].axis('off')
        info_text = f"""
        Patient ID: {profile['Patient_ID']}
        Viral Load: {profile.get('Viral_Load', 'N/A')}
        CD4 Count: {profile.get('CD4', 'N/A')}
        Subtype: {profile.get('Subtype', 'N/A')} 
        Pregnancy: {'Yes' if profile.get('Pregnancy') else 'No'}
        Comorbidities: {', '.join(profile.get('Comorbidities', [])) or 'None'}
        """
        axes[1, 1].text(0.1, 0.5, info_text, fontsize=10, verticalalignment='center',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle(f'Patient Profile - {profile["Patient_ID"]}', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        self.save_figure(fig, f'patient_profile_{profile["Patient_ID"]}.png')
        return fig

    def compare_patients(self, profiles: List[Dict], metric: str = 'CD4'):
        """Compare multiple patients on a specific metric."""
        patient_ids = [p['Patient_ID'] for p in profiles]
        values = [p.get(metric, 0) for p in profiles]
        
        fig, ax = plt.subplots()
        bars = ax.bar(patient_ids, values, color=plt.cm.Set3(range(len(profiles))))
        
        ax.set_xlabel('Patient ID', fontsize=12)
        ax.set_ylabel(metric, fontsize=12)
        ax.set_title(f'Patient Comparison - {metric}', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        self.save_figure(fig, f'compare_patients_{metric}.png')
        return fig