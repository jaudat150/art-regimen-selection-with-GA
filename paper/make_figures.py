"""Generate the figures that carry the paper's argument.

Run from the project root: python paper/make_figures.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv, os

os.makedirs('paper/figures', exist_ok=True)
plt.rcParams.update({'font.size': 9, 'font.family': 'serif',
                     'axes.grid': True, 'grid.alpha': 0.3, 'grid.linewidth': 0.5})

# --- Figure 1: search-space growth, selection vs sequencing --------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))

catalogue = [20, 29, 50, 100, 200, 500]
sizes = []
for n in catalogue:
    nrti, third = round(n * 0.30), round(n * 0.55)
    sizes.append(nrti * (nrti - 1) // 2 * third)

ax1.plot(catalogue, sizes, 'o-', color='#1f4e79', lw=1.5, ms=4)
ax1.set_xlabel('Antiretroviral catalogue size $n$')
ax1.set_ylabel('Distinct valid regimens')
ax1.set_title('(a) Single-regimen selection: $O(n^2m)$', fontsize=9)
ax1.set_yscale('log')
ax1.axhline(1e6, ls='--', lw=0.8, color='#c00')
ax1.text(22, 1.4e6, 'exhaustive search still <1 s', fontsize=7, color='#c00')
ax1.annotate('current\ncatalogue', xy=(20, sizes[0]), xytext=(45, 260),
             fontsize=7, arrowprops=dict(arrowstyle='->', lw=0.7))

lines = [1, 2, 3, 4, 5]
base = 165
seq = [base ** L for L in lines]
ax2.semilogy(lines, seq, 's-', color='#7b2d26', lw=1.5, ms=4)
ax2.set_xlabel('Lines of therapy $L$')
ax2.set_ylabel('Distinct treatment sequences')
ax2.set_title('(b) Sequencing: $O((n^2m)^L)$', fontsize=9)
ax2.set_xticks(lines)
ax2.axhline(1e6, ls='--', lw=0.8, color='#c00')
ax2.text(1.1, 1.6e6, 'exhaustive search infeasible', fontsize=7, color='#c00')

fig.tight_layout()
fig.savefig('paper/figures/fig1_search_space.png', dpi=300)
fig.savefig('paper/figures/fig1_search_space.pdf')
plt.close(fig)

# --- Figure 2: evaluations required, GA vs exhaustive -------------------------
rows = list(csv.DictReader(open('reports/comparison.csv')))
labels = [r['patient'].replace('HIV-SY-', 'S').replace('R-THIRD-HIV-', 'R')
                      .replace('R-SECOND-HIV-', 'R') for r in rows]
ex = [int(r['exhaustive_evaluations']) for r in rows]
ga = [int(r['ga_evaluations']) for r in rows]

fig, ax = plt.subplots(figsize=(7.0, 2.7))
x = range(len(rows))
ax.bar([i - 0.2 for i in x], ga, 0.4, label='Genetic algorithm', color='#7b2d26')
ax.bar([i + 0.2 for i in x], ex, 0.4, label='Exhaustive search', color='#1f4e79')
ax.set_yscale('log')
ax.set_ylabel('Fitness evaluations')
ax.set_xticks(list(x))
ax.set_xticklabels(labels, rotation=90, fontsize=6.5)
ax.legend(frameon=False, fontsize=8)
ax.set_title('Evaluations to reach the same optimum (all 17 patients)', fontsize=9)
fig.tight_layout()
fig.savefig('paper/figures/fig2_evaluations.png', dpi=300)
fig.savefig('paper/figures/fig2_evaluations.pdf')
plt.close(fig)

print('paper/figures/fig1_search_space.{png,pdf}')
print('paper/figures/fig2_evaluations.{png,pdf}')

# --- Figure 3: weight sensitivity ---------------------------------------------
import os
if os.path.exists('reports/sensitivity.csv'):
    srows = list(csv.DictReader(open('reports/sensitivity.csv')))
    weights = []
    for r in srows:
        if r['weight'] not in weights:
            weights.append(r['weight'])

    pretty = {
        'EFFICACY_WEIGHT': 'Efficacy',
        'TOXICITY_WEIGHT': 'Toxicity',
        'SIDE_EFFECT_BURDEN_WEIGHT': 'Side-effect burden',
        'GUIDELINE_COMPLIANCE_BONUS': 'Guideline bonus',
        'COST_WEIGHT_MULTIPLIER': 'Cost',
    }
    maxflip = {w: max(float(r['pct']) for r in srows if r['weight'] == w)
               for w in weights}
    order = sorted(weights, key=lambda w: maxflip[w])

    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    ax.barh([pretty.get(w, w) for w in order],
            [maxflip[w] for w in order],
            color=['#b0b0b0' if maxflip[w] == 0 else '#1f4e79' for w in order])
    ax.set_xlabel('Patients whose recommended regimen changes (%)')
    ax.set_xlim(0, 100)
    ax.set_title('Sensitivity to objective weights (0.5$\\times$–2$\\times$)',
                 fontsize=9)
    for i, w in enumerate(order):
        ax.text(maxflip[w] + 1.5, i, f'{maxflip[w]:.0f}%',
                va='center', fontsize=7.5)
    fig.tight_layout()
    fig.savefig('paper/figures/fig3_sensitivity.png', dpi=300)
    fig.savefig('paper/figures/fig3_sensitivity.pdf')
    plt.close(fig)
    print('paper/figures/fig3_sensitivity.{png,pdf}')

# --- Figure 4: where the GA's work actually happens ---------------------------
import logging as _lg
_lg.disable(_lg.CRITICAL)
from data import load_drug_data, load_patient_profiles
from ga import HIVRegimenGA
from config.clinical_rules import (enumerate_valid_regimens,
                                   enumerate_salvage_regimens, requires_salvage)
from config.constants import POPULATION_SIZE, GENERATIONS, SEED

_dd = load_drug_data()
_pts = load_patient_profiles()
spaces, gens, probs, labels = [], [], [], []
for _p in _pts:
    sp = len(enumerate_salvage_regimens(_p, _dd) if requires_salvage(_p, _dd)
             else enumerate_valid_regimens(_p, _dd))
    _g = HIVRegimenGA(profile=_p, drug_data=_dd, pop_size=POPULATION_SIZE,
                      generations=GENERATIONS, seed=SEED)
    _g.run()
    _h = _g.best_fitness_history
    _b = max(_h)
    spaces.append(sp)
    gens.append(next(i + 1 for i, v in enumerate(_h) if abs(v - _b) < 1e-9))
    probs.append(1 - (1 - 1 / sp) ** POPULATION_SIZE if sp else 0)
    labels.append(_p['Patient_ID'])

fig, ax = plt.subplots(figsize=(5.4, 3.0))
ax.scatter(spaces, [p * 100 for p in probs], s=26, color='#1f4e79',
           label='Predicted: optimum in initial population', zorder=3)
found1 = [s for s, g in zip(spaces, gens) if g == 1]
ax.scatter(found1, [100] * len(found1), marker='x', s=34, color='#7b2d26',
           label='Observed: optimum found in generation 1', zorder=4)
ax.set_xlabel('Feasible regimens for this patient')
ax.set_ylabel('Probability (%)')
ax.set_ylim(0, 108)
ax.set_title(f'The optimum is already in the random initial population\n'
             f'({len(found1)} of {len(_pts)} patients, population = {POPULATION_SIZE})',
             fontsize=9)
ax.legend(frameon=False, fontsize=7, loc='lower left')
fig.tight_layout()
fig.savefig('paper/figures/fig4_initial_population.png', dpi=300)
fig.savefig('paper/figures/fig4_initial_population.pdf')
plt.close(fig)
print('paper/figures/fig4_initial_population.{png,pdf}')
