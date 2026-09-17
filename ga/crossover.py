"""Crossover operators. AUDIT FIX: children are repaired back into the
shared valid space; previously crossover could emit redundant backbones.
"""
import random
from typing import Dict, Tuple
from config.clinical_rules import (enumerate_valid_regimens,
                                   enumerate_salvage_regimens,
                                   requires_salvage)


def _space(profile, drug_data):
    return (enumerate_salvage_regimens(profile, drug_data)
            if requires_salvage(profile, drug_data)
            else enumerate_valid_regimens(profile, drug_data))


def _repair(drugs, candidates):
    if not candidates:
        return None
    best = max(candidates, key=lambda c: len(set(c) & set(drugs)))
    return list(best)


def crossover_regimens(p1: Dict, p2: Dict, profile: Dict, drug_data: Dict) -> Tuple[Dict, Dict]:
    candidates = _space(profile, drug_data)
    if not candidates:
        return p1, p2
    a, b = p1.get("primary_regimen", []), p2.get("primary_regimen", [])
    pool = list(a) + list(b)
    random.shuffle(pool)
    c1 = _repair(pool[:3], candidates)
    c2 = _repair(pool[3:] or pool[:3], candidates)
    mk = lambda r: {"primary_regimen": list(r)}
    return mk(c1), mk(c2)
