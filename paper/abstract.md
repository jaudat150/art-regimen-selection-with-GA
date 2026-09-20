# Exhaustive search outperforms a genetic algorithm for formulary-constrained antiretroviral regimen selection

**Jaudat Faisal Al-Husein**, **Omar Ali Al-Khayat** and **Yasser Almofaalani**

Antioch Private University, Rural Damascus, Syria

jaudatalhusein@gmail.com · omaralkhayat09@gmail.com · yasser.almofaalani@gmail.com

Corresponding author: Jaudat Faisal Al-Husein (jaudatalhusein@gmail.com)

---

## Abstract

Antiretroviral regimen selection requires balancing efficacy, toxicity, cost and
side-effect burden under patient-specific resistance and formulary constraints.
Genetic algorithms have been applied to this task in prior work, generally
without comparison against an exact baseline. We report such a comparison.

We formulate WHO-compliant regimen selection as constrained combinatorial
optimisation over a catalogue of 20 antiretrovirals, with drug availability
modelled through three formulary tiers derived from WHO guidance rather than
assumed universal. Evaluating a genetic algorithm and exhaustive search over a
provably identical feasible set across 17 patient profiles, we find the feasible
set contains 2–130 regimens per patient. The genetic algorithm recovers the exact
optimum for every patient across three random seeds, while requiring
approximately 1,400 times more computation. Because a regimen is a fixed
three-slot object, the space grows as $O(n^2m)$ in catalogue size: exhaustive
search remains sub-second at twenty-five times the present catalogue.

We report three implementation artefacts that inflate apparent metaheuristic
performance — deterministic population initialisation, asymmetric constraint
application between the compared methods, and fitness normalisation applied
inside the search loop — each of which we introduced and then detected only by
comparison against the exact baseline. For 14 of 17 patients the optimum is
already present in the randomly initialised population, so the metaheuristic's
remaining 5,940 evaluations perform no search at all. Sensitivity analysis shows
recommendations shift for up to 59% of patients under modest reweighting, and
that a guideline-compliance bonus duplicating a hard constraint is inert.
Rebuilding the drug cost table from published procurement figures — the original
values were unsourced and roughly an order of magnitude high — moves
dolutegravir-anchored regimens from 3 of 17 recommendations to 17 of 17,
reversing an apparent inversion of WHO first-line guidance; under efficacy and
toxicity values corrected against trial evidence the figure is 14 of 17.

We conclude that metaheuristic search for this problem is warranted only under a
sequencing formulation, where the space grows as $O((n^2m)^L)$ across $L$ lines
of therapy and exhaustive enumeration becomes infeasible beyond the third line.

## Keywords

combinatorial optimisation; exact algorithms; genetic algorithms; antiretroviral
therapy; clinical decision support; benchmarking; negative results
