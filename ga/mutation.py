"""Mutation operators. AUDIT FIX: mutation now resamples from the shared
enumerate_valid_regimens() space, so the GA can never emit a regimen the
exhaustive search would reject (redundant backbone / out of access list).
"""
import random
from typing import Dict
from config.clinical_rules import (enumerate_valid_regimens,
                                   enumerate_salvage_regimens,
                                   requires_salvage)


def _space(profile, drug_data):
    return (enumerate_salvage_regimens(profile, drug_data)
            if requires_salvage(profile, drug_data)
            else enumerate_valid_regimens(profile, drug_data))


def mutate_regimen(individual: Dict, profile: Dict, drug_data: Dict) -> Dict:
    candidates = _space(profile, drug_data)
    if not candidates:
        return individual
    cur = individual.get("primary_regimen", [])
    # prefer a neighbour sharing at least one drug; fall back to any candidate
    near = [c for c in candidates if len(set(c) & set(cur)) >= 2 and list(c) != list(cur)]
    pool = near or [c for c in candidates if list(c) != list(cur)] or candidates
    new = list(random.choice(pool))
    return {"primary_regimen": new}
