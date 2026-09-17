"""
Global clinical and algorithmic constants.
"""
import random


# Drug Classification (WHO Consolidated Guidelines 2024)
DRUG_CLASSES = [
    'NRTI', 'NNRTI', 'PI', 'INSTI', 'Entry_Inhibitor', 'Capsid_Inhibitor', 'PK_Enhancer'
]

# Core regimen structure: 2 NRTIs + 1 from preferred classes
REQUIRED_CLASSES = {
    'backbone': ['NRTI', 'NRTI'],
    'third_drug_options': ['INSTI', 'NNRTI', 'PI']
}

# Clinical Thresholds
MIN_EFFICACY_THRESHOLD = 0.75   
MAX_TOXICITY_MULTIPLIER = 2.0  
# Backup regimen selection defaults
# Fraction of current cost that an alternative must be <= to be considered (0.8 => 20% cheaper)
BACKUP_COST_REDUCTION_FACTOR = 0.8
# Retained for schema compatibility; unused since the backup-regimen feature was removed
BACKUP_MIN_EFFICACY = 0.6

# Cost Sensitivity Weighting
COST_WEIGHT_MULTIPLIER = {
    'High': 2.0,
    'Medium': 1.0,
    'Low': 0.3
}

# Side Effect → Adherence Impact
SIDE_EFFECT_ADHERENCE_IMPACT = {
    'insomnia': 0.4,        # DTG: leads to missed evening doses
    'dizziness': 0.3,       # EFV: affects daily functioning
    'depression': 0.5,      # Critical interaction with comorbid depression
    'renal': 0.4,           # TDF: requires monitoring; may discontinue
    'weight_gain': 0.2,     # INSTIs: long-term adherence impact
    'bone_loss': 0.15,      # TDF: cumulative effect
    'rash': 0.35,           # NVP: early discontinuation risk
    'nausea': 0.25          # Common but often transient
}

# Pharmacogenetic markers requiring a laboratory result before prescribing.
# A drug listing one of these in its Contraindications column is only excluded
# when the patient profile records a positive status for that marker; unknown
# status is treated as eligible-pending-screening, and surfaced by
# clinical_rules.requires_hla_screening().
PHARMACOGENETIC_MARKERS = ['HLA-B*5701']

# Salvage therapy.
# When no available regimen reaches MIN_EFFICACY_THRESHOLD -- typically in the
# presence of multi-NRTI resistance complexes such as Q151M or K65R+M184V+L74V --
# clinical practice does not declare the patient untreatable. It anchors on a
# high-genetic-barrier agent (boosted PI or INSTI) and accepts reduced NRTI
# activity. These patients are scored, flagged, and reported as a subgroup rather
# than excluded.
SALVAGE_EFFICACY_THRESHOLD = 0.50
SALVAGE_ANCHOR_CLASSES = ('PI', 'INSTI')

# Clinically redundant NRTI pairs.
# These share an analogue class / resistance pathway and are never co-prescribed:
#   3TC + FTC  -> both cytidine analogues, identical M184V pathway (interchangeable, not combinable)
#   TDF + TAF  -> both tenofovir prodrugs
#   AZT + d4T  -> both thymidine analogues, additive mitochondrial toxicity
REDUNDANT_NRTI_PAIRS = [
    frozenset({'3TC', 'FTC'}),
    frozenset({'TDF', 'TAF'}),
    frozenset({'AZT', 'D4T'}),
    frozenset({'AZT', 'd4T'}),
]

# Fitness normalisation: sigmoid scale.
# scale=10 saturated the landscape: the observed raw fitness IQR is 23.8-35.3,
# which sigmoid(raw/10) squashed into 92-97 -- a 5-point band, leaving the GA
# almost no gradient to climb. Recentred on the observed median with a scale of
# roughly IQR/2 so feasible regimens spread across the reportable range.
# Measured over all 140 feasible regimens: min -130.3, median 29.7, max 55.5.
FITNESS_SIGMOID_CENTER = 30.0
FITNESS_SIGMOID_SCALE = 8.0

# Multi-Objective Fitness Weights
EFFICACY_WEIGHT = 50.0
TOXICITY_WEIGHT = 30.0
SIDE_EFFECT_BURDEN_WEIGHT = 20.0
GUIDELINE_COMPLIANCE_BONUS = 50.0

# # Genetic Algorithm Parameters
POPULATION_SIZE = 60 #60
GENERATIONS = 100 #100

SEED = 9 #random.randint(1, 10000)
CROSSOVER_PROB = 0.7
MUTATION_PROB = 0.3
ELITISM_RATE = 0.1