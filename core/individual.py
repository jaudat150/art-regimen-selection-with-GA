"""
HIV regimen individual representation and generation.

Why this design?
  - A regimen is two NRTIs plus one third agent (WHO structure).

  REMOVED: this class previously also produced a 'backup_regimen'. Nothing ever
  scored it -- the fitness function reads primary_regimen only, and exhaustive
  search set backup = primary -- so it was a field every layer carried and no
  layer used. Reintroduce it only alongside an objective term that values it.
  - WHO mandates specific drug class combinations -> structure enforces this.
  - Real-world constraints (cost, access) must be baked into generation.

Key innovations:
  1. Backbone stability: Backup uses same NRTIs -> avoids cross-resistance.
  2. Cost-aware fallback: Only switches third drug if ≥20% cheaper AND efficacy >60%.
  3. Zero invalid regimens: Every create() call returns a clinically valid individual.

Where used:
  - ga/genetic_algorithm.py: Population initialization
  - ga/mutation.py: Validating mutated regimens
  - main.py: Manual regimen generation for testing
"""

from typing import Dict, List
from config.clinical_rules import (
    is_drug_safe_for_patient,
    is_regimen_who_compliant,
    get_efficacy_with_resistance
)
from config.constants import BACKUP_COST_REDUCTION_FACTOR, BACKUP_MIN_EFFICACY


class RegimenIndividual:
    """
    Represents an HIV treatment regimen as:
      {
        'primary_regimen': ['TDF', '3TC', 'DTG'],   # Optimal efficacy/safety
      }
    
    Clinical rationale for dual-regimen design:
      - Primary: For patients who can afford/access optimal therapy
      - Backup: For resource-limited settings or toxicity issues
      - Both must be clinically valid -> no post-hoc filtering needed
    """

    @staticmethod
    def create_random(profile: Dict, drug_data: Dict) -> Dict:
        """
        Sample a uniformly random clinically valid regimen.

        AUDIT FIX: create() below is fully deterministic -- it sorts NRTIs by
        efficacy and takes the top 2, then takes the highest-efficacy INSTI.
        Calling it N times returned N identical individuals, so the GA started
        every run with a zero-diversity population and could only escape the
        greedy pick by mutation. This is the diverse initialiser.
        """
        import random as _random
        from config.clinical_rules import (enumerate_valid_regimens,
                                            enumerate_salvage_regimens,
                                            requires_salvage)
        candidates = (enumerate_salvage_regimens(profile, drug_data)
                      if requires_salvage(profile, drug_data)
                      else enumerate_valid_regimens(profile, drug_data))
        if not candidates:
            raise ValueError(
                f"Patient {profile.get('Patient_ID')}: no clinically valid regimen "
                f"exists under current safety + access constraints"
            )
        primary = list(_random.choice(candidates))
        return {'primary_regimen': primary}

    @staticmethod
    def create(profile: Dict, drug_data: Dict) -> Dict:
        """
        Generate a clinically valid HIV regimen individual.
        
        Safety-first approach:
          1. Filter drugs safe for patient (contraindications, organ function, allergies)
          2. Ensure ≥2 safe NRTIs available (backbone requirement)
          3. Select optimal primary regimen (efficacy-first)
        
        Args:
            profile: Patient clinical profile
            drug_date: Drug properties dict
        
        Returns:
            dict: {'primary_regimen': [...]}
        
        Raises:
            ValueError: If no safe regimen can be generated
        """
        # Step 1: Determine access constraints (if empty -> all drugs available)
        access = profile.get('Access_Constraints')
        if access:
            access_set = set(access)
        else:
            access_set = set(drug_data.keys())

        # Step 1b: Get drugs safe for this patient (clinical safety + access)
        safe_drugs = [
            drug for drug in drug_data.keys()
            if is_drug_safe_for_patient(drug, profile, drug_data) and drug in access_set
        ]
        
        # Step 2: Verify NRTI backbone availability (WHO requirement)
        safe_nrtis = [d for d in safe_drugs if drug_data[d].get('Class') == 'NRTI']
        if len(safe_nrtis) < 2:
            available_nrtis = [d for d in drug_data.keys() if drug_data[d]['Class'] == 'NRTI']
            unsafe_nrtis = [d for d in available_nrtis if d not in safe_nrtis]
            reason = "No safe NRTIs available. Unsafe options: " + ", ".join(unsafe_nrtis) if unsafe_nrtis else "No NRTIs in access constraints."
            raise ValueError(f"Patient {profile['Patient_ID']}: {reason}")
        
        # Step 3: Select primary regimen (efficacy-optimized)
        primary = RegimenIndividual._select_primary_regimen(
            safe_nrtis, safe_drugs, profile, drug_data
        )
        
        return {'primary_regimen': primary}

    @staticmethod
    def _select_primary_regimen(nrtis: List[str], safe_drugs: List[str],profile: Dict, drug_data: Dict) -> List[str]:
        """
        Select optimal primary regimen (efficacy-first strategy).
        
        Clinical priority order for third drug:
          1. INSTI (DTG/BIC) -> highest barrier to resistance
          2. NNRTI (RPV) -> if VL < 100,000 and no resistance
          3. NNRTI (EFV) -> if DTG/RPV unavailable
          4. PI (LPV/r) -> last resort (toxicity, cost)
        
        Args:
            nrtis: List of safe NRTIs
            safe_drugs: All safe drugs for patient
            profile: Patient profile
            drug_ Drug properties
        
        Returns:
            List[str]: 3-drug regimen [NRTI, NRTI, third_drug]
        """
        # Select 2 NRTIs with highest resistance-adjusted efficacy
        nrti_scores = [(drug, get_efficacy_with_resistance(drug, profile, drug_data)) for drug in nrtis]
        # Sort by efficacy (descending), pick top 2
        nrti_scores.sort(key=lambda x: x[1], reverse=True)
        primary_nrtis = [drug for drug, _ in nrti_scores[:2]]
        
        # Select third drug: INSTI > NNRTI > PI priority (WHO 2024)
        third_drug = None
        for preferred_class in ['INSTI', 'NNRTI', 'PI']:
            candidates = [
                d for d in safe_drugs
                if drug_data[d]['Class'] == preferred_class
                and d not in primary_nrtis
            ]
            if candidates:
                # Pick candidate with highest resistance-adjusted efficacy
                best_candidate = max(
                    candidates,
                    key=lambda d: get_efficacy_with_resistance(d, profile, drug_data)
                )
                third_drug = best_candidate
                break
        
        # Fallback: Use any safe third drug (should rarely happen)
        if not third_drug:
            fallback_candidates = [d for d in safe_drugs if d not in primary_nrtis]
            if not fallback_candidates:
                raise ValueError("No third drug available after NRTI selection")
            third_drug = fallback_candidates[0]
        
        return primary_nrtis + [third_drug]

    @staticmethod
    def decode(regimen: Dict, drug_data: Dict) -> Dict:
        """
        Convert regimen to human-readable clinical summary.
        
        Output structure designed for clinician review:
          - Drug names and classes
          - Monthly cost (critical for LMICs)
          - WHO compliance status
          - Safety warnings
        
        Args:
            regimen: {'primary_regimen': [...]}
            drug_data: Drug properties dict
        
        Returns:
            dict: Structured summary for reports
        """
        def _summarize(drugs: List[str]) -> Dict:
            """Helper to summarize a regimen."""
            if not drugs:
                return {'drugs': [], 'classes': [], 'cost': 0.0, 'warnings': []}
            
            # Basic metrics
            classes = [drug_data[d]['Class'] for d in drugs if d in drug_data]
            cost = sum(drug_data[d]['Monthly_Cost_USD'] for d in drugs if d in drug_data)
            
            # Safety warnings
            warnings = []
            for drug in drugs:
                d = drug_data.get(drug, {})
                # Organ impact warnings
                if d.get('Liver_Impact', 0) > 0.7:
                    warnings.append(f"{drug}: High liver impact")
                if d.get('Kidney_Impact', 0) > 0.7:
                    warnings.append(f"{drug}: High kidney impact")
                # Side effect warnings
                for se in d.get('Side_Effects', []):
                    if se.lower() in ['insomnia', 'depression', 'rash']:
                        warnings.append(f"{drug}: {se} may affect adherence")
            
            return {
                'drugs': drugs,
                'classes': classes,
                'cost': round(cost, 1),
                'warnings': warnings
            }
        
        return {
            'primary': _summarize(regimen['primary_regimen']),
            'who_compliant': is_regimen_who_compliant(regimen['primary_regimen'], drug_data)
        }