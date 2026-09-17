"""
Data loading and management module.
Exports the main loading functions for external use.
"""

from .data_loader import load_drug_data, load_patient_profiles

__all__ = ['load_drug_data', 'load_patient_profiles']