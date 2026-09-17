"""
Test suite.

The claim the paper rests on is that exhaustive search really is exhaustive and
that the genetic algorithm searches exactly the same space. Neither is
self-evident from reading the code, so both are asserted here.

Run:  python -m pytest tests/ -q     (or: python tests/test_search.py)
"""
import os
import sys
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.disable(logging.CRITICAL)

from data import load_drug_data, load_patient_profiles
from ga import HIVRegimenGA
from core.fitness_evaluator import FitnessEvaluator
from config.clinical_rules import (
    enumerate_valid_regimens,
    enumerate_salvage_regimens,
    get_candidate_drugs,
    is_backbone_redundant,
    is_drug_safe_for_patient,
    is_regimen_who_compliant,
    requires_salvage,
)
from config.constants import REDUNDANT_NRTI_PAIRS, POPULATION_SIZE, GENERATIONS, SEED

DRUGS = load_drug_data()
PATIENTS = load_patient_profiles()

THIRD_CLASSES = ('INSTI', 'NNRTI', 'PI')


def _space(profile):
    return (enumerate_salvage_regimens(profile, DRUGS)
            if requires_salvage(profile, DRUGS)
            else enumerate_valid_regimens(profile, DRUGS))


# --- enumeration is genuinely exhaustive -------------------------------------

def test_enumeration_matches_independent_brute_force():
    """
    enumerate_valid_regimens() must equal a naive triple loop written
    independently of it. This is the assertion the paper's optimality claim
    depends on: if enumeration misses regimens, 'exhaustive search' is a
    misnomer and the GA comparison is meaningless.
    """
    for p in PATIENTS:
        cands = get_candidate_drugs(p, DRUGS)
        naive = set()
        for a, b, c in ((x, y, z) for x in cands for y in cands for z in cands):
            reg = [a, b, c]
            if len({a, b, c}) != 3:
                continue
            nrtis = [d for d in reg if DRUGS[d]['Class'] == 'NRTI']
            thirds = [d for d in reg if DRUGS[d]['Class'] in THIRD_CLASSES]
            if len(nrtis) != 2 or len(thirds) != 1:
                continue
            if is_backbone_redundant(nrtis, DRUGS):
                continue
            naive.add((tuple(sorted(nrtis)), thirds[0]))

        produced = {(tuple(sorted(r[:2])), r[2])
                    for r in enumerate_valid_regimens(p, DRUGS)}
        assert produced == naive, (
            f"{p['Patient_ID']}: enumeration disagrees with naive brute force "
            f"(missing {naive - produced}, extra {produced - naive})"
        )


def test_enumeration_has_no_duplicates():
    """Ordered NRTI pairs would double-count and inflate reported evaluations."""
    for p in PATIENTS:
        regs = [tuple(sorted(r[:2])) + (r[2],) for r in enumerate_valid_regimens(p, DRUGS)]
        assert len(regs) == len(set(regs)), f"{p['Patient_ID']}: duplicate regimens"


# --- clinical constraints hold -----------------------------------------------

def test_no_redundant_backbones_anywhere():
    for p in PATIENTS:
        for r in _space(p):
            assert not is_backbone_redundant(r[:2], DRUGS), \
                f"{p['Patient_ID']}: redundant backbone {r}"


def test_redundant_pairs_are_actually_rejected():
    """Guards against the constant being defined but never consulted."""
    for pair in REDUNDANT_NRTI_PAIRS:
        assert is_backbone_redundant(tuple(pair), DRUGS), f"{pair} not rejected"
    assert not is_backbone_redundant(('TDF', 'ABC'), DRUGS)


def test_every_candidate_is_safe_and_in_formulary():
    for p in PATIENTS:
        allowed = set(get_candidate_drugs(p, DRUGS))
        for r in _space(p):
            for d in r:
                assert d in allowed, f"{p['Patient_ID']}: {d} outside candidate set"
                assert is_drug_safe_for_patient(d, p, DRUGS), \
                    f"{p['Patient_ID']}: unsafe drug {d}"


def test_structure_is_two_nrtis_plus_one_third():
    for p in PATIENTS:
        for r in _space(p):
            assert len(r) == 3 and len(set(r)) == 3
            nrtis = [d for d in r if DRUGS[d]['Class'] == 'NRTI']
            thirds = [d for d in r if DRUGS[d]['Class'] in THIRD_CLASSES]
            assert len(nrtis) == 2 and len(thirds) == 1, f"{p['Patient_ID']}: {r}"


def test_non_salvage_regimens_are_who_compliant():
    for p in PATIENTS:
        if requires_salvage(p, DRUGS):
            continue
        for r in enumerate_valid_regimens(p, DRUGS):
            assert is_regimen_who_compliant(r, DRUGS), f"{p['Patient_ID']}: {r}"


# --- the two algorithms search the same space --------------------------------

def test_ga_output_is_always_inside_the_enumerated_space():
    """
    If the GA can emit a regimen exhaustive search would reject, the two are not
    searching the same set and the comparison is invalid.
    """
    for p in PATIENTS:
        space = {tuple(sorted(r)) for r in _space(p)}
        if not space:
            continue
        g = HIVRegimenGA(profile=p, drug_data=DRUGS, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=SEED)
        reg, _ = g.run()
        assert tuple(sorted(reg['primary_regimen'])) in space, \
            f"{p['Patient_ID']}: GA produced {reg['primary_regimen']} outside the space"


def test_ga_reaches_the_exhaustive_optimum():
    for p in PATIENTS:
        g = HIVRegimenGA(profile=p, drug_data=DRUGS, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=SEED)
        _, ga_fit = g.run()
        e = HIVRegimenGA(profile=p, drug_data=DRUGS, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=SEED)
        _, ex_fit = e.run_exhaustive()
        assert abs(ga_fit - ex_fit) < 1e-9, \
            f"{p['Patient_ID']}: GA {ga_fit:.4f} != exhaustive {ex_fit:.4f}"


def test_exhaustive_evaluates_every_candidate_exactly_once():
    for p in PATIENTS:
        e = HIVRegimenGA(profile=p, drug_data=DRUGS, pop_size=1,
                         generations=1, seed=SEED)
        e.run_exhaustive()
        assert e.evaluations == len(_space(p)), \
            f"{p['Patient_ID']}: {e.evaluations} evaluations for {len(_space(p))} candidates"


# --- determinism --------------------------------------------------------------

def test_same_seed_gives_same_result():
    p = PATIENTS[0]
    out = []
    for _ in range(3):
        g = HIVRegimenGA(profile=p, drug_data=DRUGS, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=SEED)
        reg, fit = g.run()
        out.append((tuple(reg['primary_regimen']), round(fit, 9)))
    assert len(set(out)) == 1, f"non-deterministic under a fixed seed: {out}"


def test_exhaustive_is_seed_independent():
    p = PATIENTS[0]
    res = set()
    for s in (1, 9, 42):
        e = HIVRegimenGA(profile=p, drug_data=DRUGS, pop_size=1, generations=1, seed=s)
        _, fit = e.run_exhaustive()
        res.add(round(fit, 9))
    assert len(res) == 1, f"exhaustive search varied with seed: {res}"


# --- fitness normalisation ----------------------------------------------------

def test_normalisation_is_monotone_and_bounded():
    prev = None
    for raw in range(-200, 201, 5):
        v = FitnessEvaluator._normalise(float(raw))
        assert 1.0 <= v <= 100.0, f"normalised {raw} -> {v} outside [1,100]"
        if prev is not None:
            assert v >= prev, f"normalisation not monotone at raw={raw}"
        prev = v
    assert FitnessEvaluator._normalise(float('-inf')) == 1.0


def test_salvage_patients_use_the_relaxed_threshold():
    """A salvage patient must have a non-empty space and a finite score."""
    for p in PATIENTS:
        if not requires_salvage(p, DRUGS):
            continue
        assert enumerate_salvage_regimens(p, DRUGS), \
            f"{p['Patient_ID']}: flagged salvage but no salvage candidates"
        g = HIVRegimenGA(profile=p, drug_data=DRUGS, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=SEED)
        assert g.salvage is True
        assert g.evaluator.salvage_mode is True, \
            f"{p['Patient_ID']}: salvage_mode not set on the evaluator"


if __name__ == '__main__':
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith('test_') and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL  {name}\n        {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
