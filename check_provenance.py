"""
Provenance audit: report every model parameter and whether it is sourced.

Run before submission. Anything listed UNSOURCED must either be sourced or
declared in the paper's limitations.

Usage:  python check_provenance.py
"""
import logging
logging.disable(logging.CRITICAL)
import pandas as pd

from config.drug_costs import ARV_PRICES_PPPY, unsourced_drugs
from config.resistance_scoring import build_penalty_table, unverified_mutations

print('=' * 68)
print('PARAMETER PROVENANCE AUDIT')
print('=' * 68)

# --- costs -----------------------------------------------------------------
sourced = [d for d, (_p, s, _n) in ARV_PRICES_PPPY.items() if s != 'ESTIMATE']
est = unsourced_drugs()
print(f'\nCOSTS  {len(sourced)}/{len(ARV_PRICES_PPPY)} sourced')
print(f'  sourced   : {", ".join(sorted(sourced))}')
print(f'  ESTIMATE  : {", ".join(est)}')
alloc = [d for d, (_p, _s, n) in ARV_PRICES_PPPY.items() if n.startswith('ALLOCATED')]
print(f'  allocated from an FDC price (not independent): {", ".join(sorted(alloc))}')

# --- resistance --------------------------------------------------------------
res = pd.read_excel('data/drugs.xlsx', sheet_name='Resistance')
tbl = build_penalty_table(res[['Mutation', 'Drug', 'Efficacy_Reduction']].values)
unver = unverified_mutations(tbl)
print(f'\nRESISTANCE  0/{len(tbl)} sourced')
print(f'  band mapping : SOURCED (GEMINI SAP)')
print(f'  penalty scores: {len(unver)} DERIVED from legacy values, none verified')
from config.resistance_scoring import (check_against_published, HIVDB_VERSION,
                                       HIVDB_VERSION_DATE, HIVDB_XML_SOURCE)
print(f'  current algo : HIVdb {HIVDB_VERSION} ({HIVDB_VERSION_DATE})')
print(f'  replace from : {HIVDB_XML_SOURCE}')
bad = check_against_published(tbl)
if bad:
    print(f'  INCONSISTENT with published v7.0 class maxima: {len(bad)} pair(s)')
    for m, d, sc, cap in bad:
        print(f'    {m}/{d}: derived {sc} exceeds published class max {cap}')
else:
    print('  derived scores are within published class maxima')

# --- efficacy / toxicity ------------------------------------------------------
drugs = pd.read_excel('data/drugs.xlsx', sheet_name='Drugs')
from config.clinical_evidence import (PARAMETER_PROVENANCE, unsourced_parameters,
                                      overstated_parameters, REGIMEN_SUPPRESSION)
tags = {}
for _k, (t, _n) in PARAMETER_PROVENANCE.items():
    tags[t] = tags.get(t, 0) + 1
print(f'\nEFFICACY / TOXICITY  (config/clinical_evidence.py)')
print('  Per-drug efficacy has no direct empirical referent: virologic')
print('  suppression is measured for regimens, not individual agents, so this')
print('  column cannot be sourced directly at any level of effort.')
print(f'  Audited parameters: ' + ', '.join(f'{v} {k}' for k, v in sorted(tags.items())))
print(f'  Regimen-level benchmarks sourced: {len(REGIMEN_SUPPRESSION)}')
ov = overstated_parameters()
if ov:
    print(f'  OVERSTATED vs evidence: ' + ', '.join(f'{d}.{p}' for d, p in ov))
    print('  -> see run_robustness.py; DTG anchors 17/17 shipped, 14/17 corrected')

print(f'\nPATIENTS')
print('  15 of 17 profiles synthetic; 2 encoded from published case reports.')

print('\n' + '=' * 68)
print('VERDICT: costs partly sourced; resistance structurally correct but')
print('unverified; efficacy and toxicity unsourced. Declare all of the above')
print('in the limitations section before submission.')
print('=' * 68)
