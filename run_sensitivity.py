"""
Weight-sensitivity analysis.

The fitness function linearly scalarises five objectives with fixed weights.
That choice is defensible only if the resulting recommendations are not
hostage to the exact weights chosen. This script measures how often the optimal
regimen changes when each weight is perturbed.

Method: for each weight, scale it by a factor over a sweep range while holding
the others at their nominal values, recompute the exhaustive-search optimum for
every patient, and record whether the recommended regimen differs from the
nominal one. Exhaustive search is used rather than the GA so that the measured
variation is attributable to the objective, not to stochastic search.

Outputs:
  reports/sensitivity.csv           per-weight, per-factor flip counts
  paper/figures/fig3_sensitivity.*  tornado plot of flip rates

Usage:  python run_sensitivity.py
"""
import logging, csv, os
logging.disable(logging.CRITICAL)

import config.constants as C
from data import load_drug_data, load_patient_profiles
from ga import HIVRegimenGA

# Weights swept. COST is a per-sensitivity-band multiplier dict, so it is scaled
# as a whole rather than replaced by a scalar.
WEIGHTS = ['EFFICACY_WEIGHT', 'TOXICITY_WEIGHT',
           'SIDE_EFFECT_BURDEN_WEIGHT', 'GUIDELINE_COMPLIANCE_BONUS',
           'COST_WEIGHT_MULTIPLIER']

FACTORS = [0.5, 0.75, 1.25, 1.5, 2.0]


def optima(dd, pts):
    """Exhaustive-search optimum per patient under current module constants."""
    out = {}
    for p in pts:
        g = HIVRegimenGA(profile=p, drug_data=dd, pop_size=1, generations=1, seed=9)
        reg, fit = g.run_exhaustive()
        out[p['Patient_ID']] = (tuple(sorted(reg['primary_regimen'])), fit)
    return out


def set_weight(name, factor, nominal):
    if name == 'COST_WEIGHT_MULTIPLIER':
        setattr(C, name, {k: v * factor for k, v in nominal.items()})
    else:
        setattr(C, name, nominal * factor)


def main():
    dd = load_drug_data()
    pts = load_patient_profiles()

    # The evaluator imports these names directly, so reload it after each change.
    import core.fitness_evaluator as FE
    import importlib

    nominal_vals = {w: getattr(C, w) for w in WEIGHTS}
    base = optima(dd, pts)

    rows = []
    for w in WEIGHTS:
        for f in FACTORS:
            set_weight(w, f, nominal_vals[w])
            importlib.reload(FE)
            importlib.reload(__import__('ga.genetic_algorithm', fromlist=['x']))
            import ga as _ga
            importlib.reload(_ga)
            from ga import HIVRegimenGA as _G

            flipped = []
            for p in pts:
                g = _G(profile=p, drug_data=dd, pop_size=1, generations=1, seed=9)
                reg, _ = g.run_exhaustive()
                if tuple(sorted(reg['primary_regimen'])) != base[p['Patient_ID']][0]:
                    flipped.append(p['Patient_ID'])

            rows.append(dict(weight=w, factor=f,
                             flipped=len(flipped),
                             pct=round(100 * len(flipped) / len(pts), 1),
                             patients=';'.join(flipped)))
            print(f"{w:<28}x{f:<5} {len(flipped):>2}/{len(pts)} regimens change "
                  f"({100*len(flipped)/len(pts):.0f}%)")

        # restore before moving to the next weight
        setattr(C, w, nominal_vals[w])
        importlib.reload(FE)

    os.makedirs('reports', exist_ok=True)
    with open('reports/sensitivity.csv', 'w', newline='') as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)

    print()
    print("Maximum flip rate per weight:")
    for w in WEIGHTS:
        m = max(r['pct'] for r in rows if r['weight'] == w)
        print(f"  {w:<30}{m:>6.1f}%")
    print("\nWritten: reports/sensitivity.csv")


if __name__ == '__main__':
    main()
