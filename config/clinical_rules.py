"""
Medical decision rules for HIV regimen safety and efficacy.

Design principles:
  1. Pure functions (no side effects) -> testable and reliable.
  2. Explicit clinical rationale in comments -> auditable by clinicians.
  3. Fail-safe defaults -> never recommend unsafe regimens.

Usage:
  - core/individual.py: During regimen generation
  - core/fitness_evaluator.py: In fitness calculation
  - ga/mutation.py: To validate mutated regimens
"""

from typing import Any, Dict, List, Set
from .constants import SIDE_EFFECT_ADHERENCE_IMPACT, PHARMACOGENETIC_MARKERS


# clinical safety thresholds
RENAL_FUNCTION_THRESHOLD = 0.3
HEPATIC_FUNCTION_THRESHOLD = 0.4
ORGAN_IMPACT_SAFETY_MARGIN = 0.8
WHO_REGIMEN_SIZE = 3
REQUIRED_NRTI_COUNT = 2


def _normalize_contraindications(contraindications: List[str]) -> Set[str]:
    """
    Normalize contraindication strings for case-insensitive matching.
    
    Args:
        contraindications: List of contraindication strings
    
    Returns:
        Set of normalized contraindication strings
    """
    return {c.strip().lower() for c in contraindications}


def _has_contraindication(drug_data: Dict[str, Any], contraindication_key: str) -> bool:
    """
    Check if drug has a specific contraindication.
    
    Args:
        drug_data: Drug properties dictionary
        contraindication_key: Contraindication key to check
    
    Returns:
        True if drug has the contraindication, False otherwise
    """
    contraindications = drug_data.get('Contraindications', [])
    normalized = _normalize_contraindications(contraindications)
    return contraindication_key.lower() in normalized


def is_drug_safe_for_patient(drug: str, profile: Dict[str, Any], drug_data: Dict[str, Any]) -> bool:
    """
    Check if a drug is clinically safe for a specific patient.
    
    Clinical rationale:
      - Pregnancy: EFV causes neural tube defects (WHO contraindication)
      - Renal impairment: TDF accumulates → Fanconi syndrome
      - Hepatic impairment: NVP causes hepatotoxicity
    
    Args:
        drug: Drug name (e.g., 'TDF')
        profile: Patient clinical profile with keys:
            - 'Allergies': List of drug allergies
            - 'Pregnancy': Boolean pregnancy status
            - 'Kidney_Function': Float (0.0-1.0) renal function
            - 'Liver_Function': Float (0.0-1.0) hepatic function
        drug_data: Drug properties dictionary with keys:
            - 'Contraindications': List of contraindication strings
            - 'Liver_Impact': Float impact on liver function
            - 'Kidney_Impact': Float impact on kidney function
    
    Returns:
        bool: True if drug passes all safety checks, False otherwise
    """
    drug_props = drug_data.get(drug, {})
    
    # Rule 1: Allergies (absolute contraindication)
    allergies = profile.get('Allergies', [])
    if drug in allergies:
        return False
    
    # Rule 2: Pregnancy status
    if profile.get('Pregnancy', False):
        if _has_contraindication(drug_props, 'pregnancy'):
            return False
    
    # Rule 3: Renal function (TDF caution)
    kidney_func = profile.get('Kidney_Function', 1.0)
    if (kidney_func < RENAL_FUNCTION_THRESHOLD and _has_contraindication(drug_props, 'severe_renal')):
        return False
    
    # Rule 4: Hepatic function (NVP/LPV caution)
    liver_func = profile.get('Liver_Function', 1.0)
    if (liver_func < HEPATIC_FUNCTION_THRESHOLD and _has_contraindication(drug_props, 'severe_hepatic')):
        return False
    
    # Rule 5: Pharmacogenetic contraindications (absolute).
    #
    # Abacavir hypersensitivity is strongly associated with the HLA-B*5701
    # allele; guidelines recommend screening before initiation and abacavir is
    # not prescribed to allele-positive patients. drugs.xlsx already listed
    # 'HLA-B*5701' as an ABC contraindication, but no rule consulted it and no
    # patient profile carried the status, so it could never fire. Patients whose
    # allele status is unknown are treated as eligible -- matching practice,
    # where screening precedes prescribing -- and flagged via
    # requires_hla_screening() so the requirement is visible rather than silent.
    for marker in PHARMACOGENETIC_MARKERS:
        if _has_contraindication(drug_props, marker.lower()):
            status = profile.get(marker)
            if status is True or (isinstance(status, str)
                                  and status.strip().lower() in ('positive', 'pos', 'yes')):
                return False

    # Rule 6: Organ impact safety margin (80% of function)
    liver_impact = drug_props.get('Liver_Impact', 0.0)
    kidney_impact = drug_props.get('Kidney_Impact', 0.0)
    
    if liver_impact > liver_func * ORGAN_IMPACT_SAFETY_MARGIN:
        return False

    if kidney_impact > kidney_func * ORGAN_IMPACT_SAFETY_MARGIN:
        return False
    
    return True


def is_regimen_who_compliant(regimen: List[str], drug_data: Dict[str, Any]) -> bool:
    """
    Check WHO 2024 guideline compliance.
    
    WHO recommendation (Module 5, Section 3.2.1):
      "Preferred first-line regimen: 2 NRTIs + DTG"
      "Alternative: 2 NRTIs + RPV (if VL <100,000) or EFV (if DTG unavailable)"
    
    Args:
        regimen: List of drug names (must be exactly 3)
        drug_data: Drug properties dictionary with 'Class' key for each drug
    
    Returns:
        bool: True if regimen matches WHO structure (2 NRTIs + 1 from INSTI/NNRTI/PI)
    """
    if len(regimen) != WHO_REGIMEN_SIZE:
        return False
    
    # Extract drug classes, ensuring all drugs have valid class Data
    classes = []
    for drug in regimen:
        drug_class = drug_data.get(drug, {}).get('Class')
        if not drug_class:
            return False
        classes.append(drug_class)
    
    # Must have exactly 2 NRTIs (backbone requirement)
    nrti_count = classes.count('NRTI')
    if nrti_count != REQUIRED_NRTI_COUNT:
        return False
    
    # Third drug must be from recommended classes
    non_nrti_classes = [cls for cls in classes if cls != 'NRTI']
    if len(non_nrti_classes) != 1:
        return False
    
    recommended_third_classes = {'INSTI', 'NNRTI', 'PI'}
    return non_nrti_classes[0] in recommended_third_classes


def get_efficacy_with_resistance(drug: str, profile: Dict[str, Any], drug_data: Dict[str, Any]) -> float:
    """
    Calculate drug efficacy adjusted for patient's resistance mutations.
    
    Clinical model:
      Adjusted_Efficacy = Base_Efficacy * (1 - SumOf(resistance_reductions))

    PROVENANCE WARNING. This docstring previously stated that the reduction
    values come from Stanford HIVDB. They do not. Stanford HIVdb assigns integer
    penalty scores per drug-mutation pair and maps their sum onto five
    susceptibility bands; the Resistance sheet holds fractional efficacy
    reductions, which is a different quantity. See config/resistance_scoring.py
    for the correctly structured model and for what still needs replacing with
    published scores.

    Base_Efficacy is likewise unsourced. Note that per-drug efficacy has no
    direct empirical referent -- virologic suppression is measured for regimens,
    not for individual agents -- so this column is a modelling abstraction, not a
    measurable quantity. Stanford genotypic susceptibility, which IS defined per
    drug, is the principled replacement.

    Example:
      Patient with M184V -> 3TC efficacy reduced by 90% -> 0.88 * 0.1 = 0.088
    
    Args:
        drug: Drug name
        profile: Patient profile dictionary with 'Mutations' key (list of strings)
        drug_data: Drug properties dictionary with keys:
            - 'Efficacy': Base efficacy (float, 0.0-1.0)
            - 'Resistance_Reduction': Dict mapping mutation names to reduction values
    
    Returns:
        float: Adjusted efficacy (0.0 to 1.0), clamped to prevent negative values
    """
    drug_props = drug_data.get(drug, {})
    base_efficacy = drug_props.get('Efficacy', 0.0)
    resistance_map = drug_props.get('Resistance_Reduction', {})
    
    # Calculate total resistance reduction from patient mutations
    mutations = profile.get('Mutations', [])
    total_reduction = sum(
        resistance_map[mutation]
        for mutation in mutations
        if mutation in resistance_map
    )
    
    # Clamp reduction to [0, 1] to prevent negative efficacy
    clamped_reduction = min(total_reduction, 1.0)
    adjusted_efficacy = base_efficacy * (1.0 - clamped_reduction)
    
    # Ensure efficacy is non-negative
    return max(0.0, adjusted_efficacy)


def calculate_side_effect_burden(regimen: List[str], profile: Dict[str, Any], drug_data: Dict[str, Any]) -> float:
    """
    Calculate adherence impact score from side effects.
    
    Clinical rationale:
      - Side effects directly impact medication adherence (Bangsberg et al., AIDS 2001)
      - Comorbidities amplify impact (e.g., insomnia worsens depression)
    
    Formula:
      Burden = SumOf(SE_weight x adherence_impact x comorbidity_multiplier)
      Where comorbidity_multiplier = 1.0 if comorbidity present, else 0.5
    
    Args:
        regimen: List of drug names
        profile: Patient profile dictionary with 'Comorbidities' key (list of strings)
        drug_data: Drug properties dictionary with 'Side_Effects' key (list of strings)
    
    Returns:
        float: Burden score (0.0 = no impact, 1.0 = high discontinuation risk)
    """
    burden = 0.0
    comorbidities = {
        comorbidity.lower()
        for comorbidity in profile.get('Comorbidities', [])
    }
    
    for drug in regimen:
        drug_props = drug_data.get(drug, {})
        side_effects = drug_props.get('Side_Effects', [])
        
        for side_effect in side_effects:
            se_key = side_effect.lower().strip()
            
            if se_key in SIDE_EFFECT_ADHERENCE_IMPACT:
                # Higher weight if comorbidity matches (1.0 vs 0.5)
                comorbidity_multiplier = (
                    1.0 if se_key in comorbidities else 0.5
                )
                adherence_impact = SIDE_EFFECT_ADHERENCE_IMPACT[se_key]
                burden += adherence_impact * comorbidity_multiplier
    
    # Cap at 1.0 for numerical stability
    return min(burden, 1.0)

# ---------------------------------------------------------------------------
# Added during pre-publication audit.
# Shared candidate enumeration + clinical redundancy checking.
# Both the GA and the exhaustive search MUST use these so that the two
# algorithms are compared over an identical candidate space.
# ---------------------------------------------------------------------------

from itertools import combinations as _combinations
from config.constants import REDUNDANT_NRTI_PAIRS as _REDUNDANT_NRTI_PAIRS


def is_backbone_redundant(nrti_pair, drug_data=None) -> bool:
    """
    True if the two NRTIs are clinically redundant and must not be co-prescribed.

    Rationale: WHO/DHHS treat 3TC and FTC as interchangeable cytidine analogues
    sharing the M184V pathway; combining them adds toxicity and cost with no
    virologic benefit. Same logic for the tenofovir prodrugs and the thymidine
    analogues.
    """
    return frozenset(nrti_pair) in _REDUNDANT_NRTI_PAIRS


def get_candidate_drugs(profile, drug_data):
    """
    Drugs available to this patient: clinically safe AND within access constraints.

    Access_Constraints was previously honoured by the GA (via RegimenIndividual)
    but ignored by the exhaustive search, so the two algorithms were searching
    different spaces. This is the single shared entry point.
    """
    access = profile.get('Access_Constraints')
    access_set = set(access) if access else set(drug_data.keys())
    return [
        d for d in drug_data
        if is_drug_safe_for_patient(d, profile, drug_data) and d in access_set
    ]


def enumerate_valid_regimens(profile, drug_data):
    """
    Every clinically valid 3-drug regimen for this patient.

    Unordered NRTI pairs (a regimen is a set, not a sequence), redundant
    backbones excluded. This is the ground-truth search space: the exhaustive
    search walks it directly, and the GA is constrained to it.
    """
    candidates = get_candidate_drugs(profile, drug_data)
    nrtis = [d for d in candidates if drug_data[d].get('Class') == 'NRTI']
    thirds = [d for d in candidates
              if drug_data[d].get('Class') in ('INSTI', 'NNRTI', 'PI')]
    out = []
    for pair in _combinations(sorted(nrtis), 2):
        if is_backbone_redundant(pair, drug_data):
            continue
        for third in thirds:
            if third in pair:
                continue
            out.append(list(pair) + [third])
    return out


def enumerate_salvage_regimens(profile, drug_data):
    """
    Salvage candidates for patients with no regimen meeting MIN_EFFICACY_THRESHOLD.

    Restricted to regimens anchored on a high-genetic-barrier third agent
    (boosted PI or INSTI), consistent with WHO third-line guidance, which
    recommends agents with minimal cross-resistance to those already used.
    NRTI activity is allowed to fall below the standard threshold; the fitness
    function penalises it rather than the constraint excluding it.
    """
    from config.constants import SALVAGE_ANCHOR_CLASSES
    candidates = get_candidate_drugs(profile, drug_data)
    nrtis = [d for d in candidates if drug_data[d].get('Class') == 'NRTI']
    anchors = [d for d in candidates
               if drug_data[d].get('Class') in SALVAGE_ANCHOR_CLASSES]
    out = []
    for pair in _combinations(sorted(nrtis), 2):
        if is_backbone_redundant(pair, drug_data):
            continue
        for anchor in anchors:
            if anchor in pair:
                continue
            out.append(list(pair) + [anchor])
    return out


def best_achievable_efficacy(profile, drug_data):
    """Highest mean resistance-adjusted efficacy over all valid regimens."""
    regs = enumerate_valid_regimens(profile, drug_data)
    if not regs:
        return 0.0
    return max(
        sum(get_efficacy_with_resistance(d, profile, drug_data) for d in r) / len(r)
        for r in regs
    )


def requires_salvage(profile, drug_data):
    """True if no available regimen reaches the standard efficacy threshold."""
    from config.constants import MIN_EFFICACY_THRESHOLD
    return best_achievable_efficacy(profile, drug_data) < MIN_EFFICACY_THRESHOLD


def requires_hla_screening(regimen, drug_data):
    """
    Pharmacogenetic markers that must be screened before this regimen starts.

    Returns a list of (drug, marker) pairs. A non-empty result means the regimen
    cannot be dispensed on the strength of the optimiser's output alone -- a
    laboratory result is a prerequisite. Reported alongside every recommendation
    so the requirement is explicit.
    """
    out = []
    for d in regimen:
        for marker in PHARMACOGENETIC_MARKERS:
            if _has_contraindication(drug_data.get(d, {}), marker.lower()):
                out.append((d, marker))
    return out
