"""
Robustness of the Section 4.7 finding to trial-consistent parameter values.

The shipped efficacy and toxicity columns overstate the dolutegravir-efavirenz
gap relative to the trial evidence (see config/clinical_evidence.py). This script
re-runs the cohort with values consistent with demonstrated non-inferiority and
reports the effect on recommendations.

Usage:  python run_robustness.py
"""
import logging, csv
logging.disable(logging.CRITICAL)
from collections import Counter

from data import load_drug_data, load_patient_profiles
from ga import HIVRegimenGA
from config.clinical_evidence import TRIAL_CONSISTENT_OVERRIDES

dd = load_drug_data()
pts = load_patient_profiles()


def optima(drug_data):
    counts, regs = Counter(), {}
    for p in pts:
        g = HIVRegimenGA(profile=p, drug_data=drug_data,
                         pop_size=1, generations=1, seed=9)
        r, f = g.run_exhaustive()
        counts.update(r['primary_regimen'])
        regs[p['Patient_ID']] = ('/'.join(r['primary_regimen']), round(f, 2))
    return counts, regs


base_c, base_r = optima(dd)

alt = {k: dict(v) for k, v in dd.items()}
for drug, params in TRIAL_CONSISTENT_OVERRIDES.items():
    if drug in alt:
        alt[drug].update(params)
alt_c, alt_r = optima(alt)

changed = [p for p in base_r if base_r[p][0] != alt_r[p][0]]

print(f"{'Drug':<8}{'shipped':>9}{'trial-consistent':>19}")
for d in ('DTG', 'EFV', 'TDF', 'TAF', 'ABC', '3TC', 'FTC'):
    print(f'{d:<8}{base_c[d]:>9}{alt_c[d]:>19}')
print()
print(f'Recommendations that change: {len(changed)}/{len(pts)}')
for p in changed:
    print(f'  {p:<18}{base_r[p][0]:<20} -> {alt_r[p][0]}')
print()
print(f'DTG-anchored: {base_c["DTG"]}/{len(pts)} shipped, '
      f'{alt_c["DTG"]}/{len(pts)} trial-consistent')

with open('reports/robustness.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['patient', 'shipped_regimen', 'shipped_fitness',
                'trial_consistent_regimen', 'trial_consistent_fitness', 'changed'])
    for p in base_r:
        w.writerow([p, base_r[p][0], base_r[p][1],
                    alt_r[p][0], alt_r[p][1], p in changed])
print('Written: reports/robustness.csv')
