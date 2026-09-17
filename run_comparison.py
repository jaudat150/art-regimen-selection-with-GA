"""
Reproducible GA vs exhaustive-search comparison.

Both algorithms are driven from the same HIVRegimenGA object and draw from the
same candidate space (config.clinical_rules.enumerate_valid_regimens), so the
only difference between them is the search strategy.

Usage:  python run_comparison.py
"""
import logging, time, csv
logging.disable(logging.CRITICAL)

from data import load_drug_data, load_patient_profiles
from ga import HIVRegimenGA
from config.clinical_rules import (enumerate_valid_regimens,
                                   enumerate_salvage_regimens,
                                   requires_salvage, best_achievable_efficacy)
from core.fitness_evaluator import FitnessEvaluator
from config.constants import POPULATION_SIZE, GENERATIONS, SEED


def main():
    dd = load_drug_data()
    pts = load_patient_profiles()
    rows, match, feasible = [], 0, 0
    ga_t = ex_t = 0.0

    for p in pts:
        salvage = requires_salvage(p, dd)
        space = len(enumerate_salvage_regimens(p, dd) if salvage
                    else enumerate_valid_regimens(p, dd))

        t = time.time()
        g = HIVRegimenGA(profile=p, drug_data=dd, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=SEED)
        g_reg, g_fit = g.run()
        ga_t += time.time() - t

        t = time.time()
        e = HIVRegimenGA(profile=p, drug_data=dd, pop_size=POPULATION_SIZE,
                         generations=GENERATIONS, seed=SEED)
        e_reg, e_fit = e.run_exhaustive()
        ex_t += time.time() - t

        if space > 0:
            feasible += 1
            if abs(g_fit - e_fit) < 1e-6:
                match += 1

        ev = FitnessEvaluator(p, dd)
        ev.salvage_mode = salvage
        raw = ev.evaluate_raw(e_reg)

        rows.append(dict(
            patient=p['Patient_ID'],
            tier=p.get('Formulary_Tier', ''),
            salvage=salvage,
            best_efficacy=round(best_achievable_efficacy(p, dd), 3),
            space=space,
            raw_fitness=round(raw, 2),
            ga_fitness=round(g_fit, 3), exhaustive_fitness=round(e_fit, 3),
            gap=round(g_fit - e_fit, 3),
            ga_regimen='/'.join(g_reg['primary_regimen']),
            exhaustive_regimen='/'.join(e_reg['primary_regimen']),
            ga_evaluations=POPULATION_SIZE * GENERATIONS,
            exhaustive_evaluations=space,
        ))

    with open('reports/comparison.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{'Patient':<18}{'tier':>16}{'space':>7}{'raw':>9}{'GA':>8}{'exh':>8}{'gap':>7}{'salv':>6}")
    for r in rows:
        print(f"{r['patient']:<18}{r['tier']:>16}{r['space']:>7}{r['raw_fitness']:>9.2f}"
              f"{r['ga_fitness']:>8.2f}{r['exhaustive_fitness']:>8.2f}{r['gap']:>7.2f}"
              f"{'yes' if r['salvage'] else '':>6}")
    print()
    print(f"GA matched the true optimum on {match}/{feasible} feasible patients")
    print(f"GA {ga_t:.2f}s ({POPULATION_SIZE * GENERATIONS} evals/patient)  |  "
          f"exhaustive {ex_t:.4f}s ({sum(r['space'] for r in rows)} evals total)")
    print(f"Speed ratio: exhaustive is {ga_t / max(ex_t, 1e-9):.0f}x faster")
    print("Written: reports/comparison.csv")


if __name__ == '__main__':
    main()
