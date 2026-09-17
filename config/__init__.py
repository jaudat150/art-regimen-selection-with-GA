"""
Clinical configuration module.
This is the "medical brain" of the system — reviewed by clinicians.
"""

from .constants import *
from .clinical_rules import *

__all__ = [
    # Constants
    'DRUG_CLASSES', 'REQUIRED_CLASSES', 
    'MIN_EFFICACY_THRESHOLD', 'COST_WEIGHT_MULTIPLIER',
    'SIDE_EFFECT_ADHERENCE_IMPACT',
    'EFFICACY_WEIGHT', 'TOXICITY_WEIGHT',
    'GUIDELINE_COMPLIANCE_BONUS',
    
    # Clinical rules
    'is_drug_safe_for_patient',
    'is_regimen_who_compliant',
    'get_efficacy_with_resistance',
    'calculate_side_effect_burden'
]