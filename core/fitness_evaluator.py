# core/fitness_evaluator.py
"""
Multi-objective clinical fitness evaluation for HIV regimens.

Why multi-objective?
  - HIV treatment balances: efficacy, toxicity, cost, adherence
  - Single-score fitness enables GA optimization
  - Weights reflect clinical priorities (efficacy > toxicity > cost)

Clinical validation:
  - Fitness > 80: WHO-recommended regimen (e.g., TDF/3TC/DTG)
  - Fitness 60-80: Acceptable alternative (e.g., TDF/3TC/EFV)
  - Fitness < 40: Suboptimal (high resistance risk or toxicity)

Where used:
  - ga/genetic_algorithm.py: Evaluating population fitness
  - main.py: Reporting best regimen scores
"""

from typing import Dict, List
import math
from config.clinical_rules import (
    get_efficacy_with_resistance,
    calculate_side_effect_burden,
    is_regimen_who_compliant
)
from config.constants import (
    EFFICACY_WEIGHT,
    TOXICITY_WEIGHT,
    COST_WEIGHT_MULTIPLIER,
    SIDE_EFFECT_BURDEN_WEIGHT,
    GUIDELINE_COMPLIANCE_BONUS,
    MIN_EFFICACY_THRESHOLD,
    FITNESS_SIGMOID_SCALE,
    FITNESS_SIGMOID_CENTER,
    SALVAGE_EFFICACY_THRESHOLD,
    MAX_TOXICITY_MULTIPLIER,
    REQUIRED_CLASSES
)


class FitnessEvaluator:
    """
    evaluates HIV regimen fitness using clinically weighted objectives.
    
    Scoring methodology:
      - Efficacy is primary (virologic success is non-negotiable)
      - Toxicity and adherence impact treatment continuity
      - Cost is weighted by patient context (critical in LMICs)
      - WHO compliance gets strong bonus (ensures guideline adherence)
    """
    
    def __init__(self, profile: Dict, drug_data: Dict):
        """
        Initialize fitness evaluator for a specific patient.
        
        Args:
            profile: Patient clinical profile
            drug_data: Drug properties dict
        """
        self.profile = profile or {}
        self.drug_data = drug_data or {}

    def evaluate_raw(self, regimen: Dict) -> float:
        """Un-normalised fitness, for calibrating the sigmoid scale."""
        return self._score(regimen)[0]

    def evaluate(self, regimen: Dict) -> float:
        """
        Compute clinical fitness score for an HIV regimen.
        
        Formula:
          Fitness = 
            (Avg_Efficacy x efficacy_weight) 
            - (Toxicity_Sum x toxicity_weight) 
            - (Cost x cost_weight) 
            - (SideEffectBurden x side_effect_weight)
            + (GUIDELINE_COMPLIANCE_BONUS if WHO-compliant)
        
        Weights are adjusted based on patient profile for personalization.
        
        Args:
            regimen: {'primary_regimen': [...]}
        
        Returns:
            float: Fitness score (normalized 1-100)
        """
        fitness, _ = self._score(regimen)
        return self._normalise(fitness)

    def _score(self, regimen: Dict):
        primary = regimen.get('primary_regimen', [])
        
        # === Adjust weights based on patient profile ===
        base_efficacy_weight = EFFICACY_WEIGHT
        base_toxicity_weight = TOXICITY_WEIGHT
        base_side_effect_weight = SIDE_EFFECT_BURDEN_WEIGHT
        
        # If patient has low organ function, increase toxicity weight
        liver_func = self.profile.get('Liver_Function', 1.0)
        kidney_func = self.profile.get('Kidney_Function', 1.0)
        if liver_func < 0.8 or kidney_func < 0.8:
            base_toxicity_weight *= 1.5  # Increase toxicity concern
        
        # If patient has comorbidities, increase side effect weight
        comorbidities = self.profile.get('Comorbidities', [])
        if comorbidities:
            base_side_effect_weight *= 1.2
        
        # If patient has many mutations, increase efficacy weight
        mutations = self.profile.get('Mutations', [])
        if len(mutations) > 2:
            base_efficacy_weight *= 1.2
        
        # === 1. Efficacy: Average resistance-adjusted efficacy ===
        # Clinical rationale: Regimen succeeds if overall suppression is achieved
        efficacy_sum = 0.0
        for drug in primary:
            efficacy_sum += get_efficacy_with_resistance(drug, self.profile, self.drug_data)
        avg_efficacy = (efficacy_sum / len(primary)) if primary else 0.0
        
        # Critical penalty: If efficacy < threshold, reject regimen
        threshold = (SALVAGE_EFFICACY_THRESHOLD if getattr(self, 'salvage_mode', False)
                     else MIN_EFFICACY_THRESHOLD)
        if avg_efficacy < threshold:
            return float('-inf'), False
        
        # === 2. Toxicity: Sum with organ function amplification ===
        # Clinical rationale: Toxicity multiplies when organ function is impaired
        toxicity_sum = 0.0
        for drug in primary:
            d = self.drug_data.get(drug, {})
            base_toxicity = d.get('Toxicity', 0.0)

            # Amplify if organ impact exceeds function capacity
            liver_mult = (
                MAX_TOXICITY_MULTIPLIER
                if d.get('Liver_Impact', 0) > self.profile.get('Liver_Function', 1.0)
                else 1.0
            )

            kidney_mult = (
                MAX_TOXICITY_MULTIPLIER
                if d.get('Kidney_Impact', 0) > self.profile.get('Kidney_Function', 1.0)
                else 1.0
            )

            toxicity_sum += base_toxicity * liver_mult * kidney_mult
        
        # === 3. Cost: Monthly cost weighted by patient sensitivity ===
        cost = sum(
            self.drug_data.get(d, {}).get('Monthly_Cost_USD', 0.0)
            for d in primary
        )
        cost_sensitivity = self.profile.get('Cost_Sensitivity', 'Medium')
        cost_weight = COST_WEIGHT_MULTIPLIER.get(cost_sensitivity, 1.0)
        
        # === 4. Side effect burden: Adherence impact ===
        side_effect_burden = calculate_side_effect_burden(primary, self.profile, self.drug_data)
        
        # === 5. Guideline compliance bonus ===
        guideline_bonus = GUIDELINE_COMPLIANCE_BONUS if is_regimen_who_compliant(
            primary, self.drug_data
        ) else 0.0
        
        # === Final fitness calculation ===
        fitness = (
            avg_efficacy * base_efficacy_weight
            - toxicity_sum * base_toxicity_weight
            - cost * cost_weight
            - side_effect_burden * base_side_effect_weight
            + guideline_bonus
        )
        
        # Extreme penalty: Invalid regimen structure (safety net)
        required_total = len(REQUIRED_CLASSES.get('backbone', [])) + 1
        if len(primary) != required_total or not self._has_required_classes(primary):
            fitness -= 2000.0
        
        return fitness, True

    @staticmethod
    def _normalise(fitness: float) -> float:
        if fitness == float('-inf'):
            return 1.0
        scale = FITNESS_SIGMOID_SCALE
        try:
            sigmoid = 1 / (1 + math.exp(-(fitness - FITNESS_SIGMOID_CENTER) / scale))
        except OverflowError:
            sigmoid = 0.0 if fitness < 0 else 1.0
        return 1 + 99 * sigmoid

    def _has_required_classes(self, regimen: List[str]) -> bool:
        """
        Check if regimen has required WHO class structure.
        
        Returns:
            bool: True if 2 NRTIs + 1 from {INSTI, NNRTI, PI}
        """
        backbone_required = REQUIRED_CLASSES.get('backbone', [])
        third_options = REQUIRED_CLASSES.get('third_drug_options', [])

        if len(regimen) != len(backbone_required) + 1:
            return False

        classes = [self.drug_data.get(d, {}).get('Class') for d in regimen]
        nrti_count = classes.count('NRTI')
        third_classes = [c for c in classes if c != 'NRTI']

        return nrti_count == len([c for c in backbone_required if c == 'NRTI']) and len(third_classes) == 1 and third_classes[0] in third_options