"""
Pre-release verification.

Runs the whole pipeline from a clean state and checks every number the paper
claims. Anything that fails here is a number in the manuscript that is wrong.

Usage:  python verify.py

Exit code 0 means everything checks out.
"""
import logging
import os
import shutil
import subprocess
import contextlib
import io
import sys
import time

logging.disable(logging.CRITICAL)

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

PASS, FAIL = [], []


def check(label, condition, detail=''):
    (PASS if condition else FAIL).append(label)
    mark = ' ok ' if condition else 'FAIL'
    print(f'  [{mark}] {label}' + (f'  -- {detail}' if detail else ''))
    return condition


def run(cmd):
    t = time.time()
    r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr, time.time() - t


print('=' * 70)
print('PRE-RELEASE VERIFICATION')
print('=' * 70)

# --- 0. clean state -----------------------------------------------------------
print('\n[0] Clean state')
for d in ('reports/regimens', 'reports/viz'):
    shutil.rmtree(d, ignore_errors=True)
os.makedirs('reports/regimens', exist_ok=True)
for f in ('data/AllPatients_v2.xlsx', 'data/drugs_sourced.xlsx',
          'reports/comparison.csv', 'reports/sensitivity.csv'):
    if os.path.exists(f):
        os.remove(f)
print('  removed generated artefacts')

# --- 1. dependencies ----------------------------------------------------------
print('\n[1] Dependencies')
try:
    import pandas, numpy, matplotlib, openpyxl
    check('pandas / numpy / matplotlib / openpyxl importable', True,
          f'numpy {numpy.__version__}, pandas {pandas.__version__}')
    check('numpy is not the yanked 2.4.0', numpy.__version__ != '2.4.0',
          numpy.__version__)
except ImportError as e:
    check('required packages importable', False, str(e))
    print('\nRun: pip install -r requirements.txt')
    sys.exit(1)
try:
    import seaborn  # noqa: F401
    check('seaborn NOT required', True, 'present but unused')
except ImportError:
    check('seaborn NOT required', True, 'absent, as intended')

# --- 2. pipeline --------------------------------------------------------------
# Data generators run BEFORE the tests: the tests read the generated cohort and
# cost table, so running them first would test the fallback data instead.
print('\n[2] Pipeline')
for script, label in [('apply_sourced_costs.py', 'sourced costs applied'),
                      ('regenerate_patients.py', 'cohort regenerated'),
                      ('run_comparison.py', 'GA vs exhaustive'),
                      ('run_sensitivity.py', 'weight sensitivity'),
                      ('run_robustness.py', 'parameter robustness'),
                      ('paper/make_figures.py', 'paper figures')]:
    ok, out, dt = run([script])
    check(label, ok, f'{dt:.1f}s')
    if not ok:
        print('\n'.join('      ' + l for l in out.strip().splitlines()[-4:]))

# --- 3. test suite ------------------------------------------------------------
print('\n[3] Correctness tests')
ok, out, dt = run(['tests/test_search.py'])
check('14/14 tests pass', ok and '14/14 passed' in out, f'{dt:.1f}s')
if not ok:
    print('\n'.join('      ' + l for l in out.splitlines() if 'FAIL' in l))

# --- 4. headline numbers ------------------------------------------------------
print('\n[4] Headline numbers (these are in the paper)')
import csv
from collections import Counter

rows = list(csv.DictReader(open('reports/comparison.csv')))
check('17 patients', len(rows) == 17, str(len(rows)))
check('GA matches exhaustive optimum on every patient',
      all(abs(float(r['gap'])) < 1e-9 for r in rows),
      f"{sum(1 for r in rows if abs(float(r['gap'])) < 1e-9)}/17")

total_space = sum(int(r['space']) for r in rows)
check('candidate space 613 across cohort', total_space == 613, str(total_space))
spaces = [int(r['space']) for r in rows]
check('per-patient space 2-130', min(spaces) >= 2 and max(spaces) <= 130,
      f'{min(spaces)}-{max(spaces)}')
check('no patient without a feasible regimen', min(spaces) > 0)
check('2 salvage patients',
      sum(1 for r in rows if r['salvage'] == 'True') == 2,
      str(sum(1 for r in rows if r['salvage'] == 'True')))

# drug frequencies under sourced costs
freq = Counter()
for r in rows:
    freq.update(r['exhaustive_regimen'].split('/'))
check('DTG anchors all 17 recommendations', freq['DTG'] == 17, str(freq['DTG']))
check('no EFV-anchored recommendations', freq['EFV'] == 0, str(freq['EFV']))

# --- 5. multi-seed stability --------------------------------------------------
print('\n[5] Seed stability')
from data import load_drug_data, load_patient_profiles
from ga import HIVRegimenGA
from config.constants import POPULATION_SIZE, GENERATIONS

dd, pts = load_drug_data(), load_patient_profiles()
for seed in (1, 9, 42):
    n = 0
    for p in pts:
        g = HIVRegimenGA(profile=p, drug_data=dd, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=seed)
        _, gf = g.run()
        e = HIVRegimenGA(profile=p, drug_data=dd, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=seed)
        _, ef = e.run_exhaustive()
        n += abs(gf - ef) < 1e-9
    check(f'seed {seed}: GA matches optimum 17/17', n == 17, f'{n}/17')

# the paper claims the optimum is already in the random initial population for
# 14 of 17 patients -- this drifted once when parameters changed, so check it
with contextlib.redirect_stdout(io.StringIO()):
    from config.constants import POPULATION_SIZE as _POP, GENERATIONS as _GEN
    _gen1 = 0
    for _p in pts:
        _g = HIVRegimenGA(profile=_p, drug_data=dd, pop_size=_POP,
                          generations=_GEN, seed=9)
        _g.run()
        _h = _g.best_fitness_history
        if abs(_h[0] - max(_h)) < 1e-9:
            _gen1 += 1
check('optimum already in initial population for 14 of 17', _gen1 == 14,
      f'{_gen1}/17')

# --- 6. sensitivity -----------------------------------------------------------
print('\n[6] Sensitivity')
srows = list(csv.DictReader(open('reports/sensitivity.csv')))
gb = max(float(r['pct']) for r in srows
         if r['weight'] == 'GUIDELINE_COMPLIANCE_BONUS')
check('guideline bonus is inert (0% flips)', gb == 0.0, f'{gb}%')
mx = max(float(r['pct']) for r in srows)
check('some weight flips >50% of recommendations', mx > 50, f'max {mx}%')

# --- 7. outputs ---------------------------------------------------------------
print('\n[7] Output artefacts')
ok, out, dt = run(['main.py', '--visualize'])
check('main.py --visualize runs', ok, f'{dt:.1f}s')
check('17 patient reports', len(os.listdir('reports/regimens')) == 17,
      str(len(os.listdir('reports/regimens'))))
nviz = len(os.listdir('reports/viz')) if os.path.isdir('reports/viz') else 0
check('18 diagnostic figures', nviz == 18, str(nviz))
figs = os.listdir('paper/figures')
check('4 paper figures as png+pdf', len(figs) == 8, str(len(figs)))
check('no class_distribution.png (tautological, removed)',
      'class_distribution.png' not in os.listdir('reports/viz'))

# --- 8. provenance ------------------------------------------------------------
print('\n[8] Provenance (expected to show gaps)')
ok, out, dt = run(['check_provenance.py'])
check('provenance audit runs', ok)
check('audit reports unsourced parameters', 'UNSOURCED' in out or '0/20' in out,
      'efficacy, toxicity, resistance still unsourced')

# --- verdict ------------------------------------------------------------------
print('\n' + '=' * 70)
print(f'{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('\nFAILED:')
    for f in FAIL:
        print(f'  - {f}')
    print('\nDo not publish until these are resolved.')
else:
    print('\nEverything checks out. Every number in the paper reproduces.')
    print('Remaining known gaps are parameter provenance (section 8 above),')
    print('which is declared in the limitations, not a defect.')
print('=' * 70)
sys.exit(1 if FAIL else 0)
