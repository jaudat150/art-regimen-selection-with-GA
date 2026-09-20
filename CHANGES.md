# Audit fixes applied

One project, one candidate-generation path, two search strategies.
`python run_comparison.py` reproduces every number below.

## What changed

**1. Clinical redundancy rule** — `config/constants.py`, `config/clinical_rules.py`
Added `REDUNDANT_NRTI_PAIRS` ({3TC,FTC}, {TDF,TAF}, {AZT,d4T}) and
`is_backbone_redundant()`. These pairs share an analogue class and resistance
pathway and are never co-prescribed. Previously 12 of 17 "optimal" regimens were
3TC+FTC; they are now excluded at enumeration time.

**2. Single shared candidate space** — `config/clinical_rules.py`
New `get_candidate_drugs()` and `enumerate_valid_regimens()`. Both algorithms
call these, which fixes three separate asymmetries:
- the GA honoured `Access_Constraints`, the old brute force ignored them
- the old brute force enumerated *ordered* NRTI pairs, scoring every regimen twice
- neither excluded redundant backbones

**3. GA population diversity** — `core/individual.py`, `ga/genetic_algorithm.py`
`RegimenIndividual.create()` was deterministic: sort NRTIs by efficacy, take top
2, take best INSTI. Sixty calls returned sixty identical individuals, so the GA
began every run with zero diversity and could only escape the greedy pick by
mutation. This is why it returned TDF/3TC/DTG for 9 of 17 patients.
Added `create_random()`, which samples uniformly from the valid space.
Also removed the `if fitness > 10` acceptance filter, which discarded most
candidates once the sigmoid was recalibrated.

**4. Fitness normalisation** — `config/constants.py`, `core/fitness_evaluator.py`
`scale = 10.0` squashed the observed raw-fitness IQR (23.8–35.3) into 92–97 — a
5-point band with almost no gradient. Measured the real distribution over all 140
feasible regimens (min −130.3, median 29.7, max 55.5) and recentred:
`FITNESS_SIGMOID_CENTER = 30.0`, `FITNESS_SIGMOID_SCALE = 8.0`.
Raw 24 → 32.8, raw 30 → 50.5, raw 35 → 65.5, raw 55 → 95.8.
Added `evaluate_raw()` so the scale can be recalibrated rather than guessed.

**5. Operators constrained** — `ga/mutation.py`, `ga/crossover.py`
Rewritten to resample and repair into the shared valid space, so the GA cannot
emit a regimen the exhaustive search would reject.

**6. Housekeeping**
`requirements.txt` re-encoded UTF-16 → UTF-8 (pip could not read it) and
matplotlib added. CRLF stripped from all sources. Stale figures deleted.

## Result

| | before | after |
|---|---|---|
| GA reaches true optimum | 1 / 17 | **15 / 15 feasible** |
| Redundant backbones in optima | 12 / 17 | **0** |
| Algorithms on same patient file | no | yes |
| Algorithms on same candidate space | no | yes |
| Exhaustive speed advantage | 50× | **1,378×** |

## The finding this exposes

With `Access_Constraints` and the redundancy rule both applied, the real
candidate space is:

| patients | valid regimens |
|---|---|
| 2 synthetic | 0 (no valid regimen exists) |
| 5 synthetic | 1 |
| 7 synthetic | 2 |
| 1 synthetic | 12 |
| 2 real | 50 and 72 |

**153 candidate regimens across the entire 17-patient cohort.** For most
synthetic patients there are one or two options — the answer is determined by the
constraints, not found by search. The GA now matches the optimum everywhere
because there is essentially nothing to search.

The `Access_Constraints` column lists 3–4 drugs per synthetic patient, which
collapses 9–20 clinically safe drugs down to 1–6. That is a dataset design
choice, not a code defect, and it is what removes the optimization problem.

## Still open

- Two patients (HIV-SY-007, HIV-SY-013) have no valid regimen at all. Either the
  access lists are unrealistically narrow or the safety filter is too strict.
- Several feasible patients still score ~1.0, meaning their only option falls
  below `MIN_EFFICACY_THRESHOLD`. Worth checking whether 0.75 is defensible.
- `backup_regimen` still never enters the fitness calculation.
- Weight-sensitivity sweep (from your `To add.txt`) not yet run.
- Figures not regenerated — do this after the above settle.


---

# Round 2 — formulary rebuild

## What changed

**`config/formulary.py`** (new) — replaces per-patient hand-picked
`Access_Constraints` lists with three nested service-delivery tiers, each
grounded in published guidance:

| tier | drugs | what it represents |
|---|---|---|
| `TIER_1_PUBLIC` | 10 | national-programme core: WHO-preferred first/second-line agents plus WHO second-line boosted PIs |
| `TIER_2_REGIONAL` | 14 | adds TAF (renal impairment / osteoporosis), DRV/r and RAL (WHO second-line alternatives), DOR |
| `TIER_3_FULL` | 20 | full catalogue incl. salvage agents requiring named-patient import |

Sources are cited inline in the module docstring: WHO consolidated ART
guidelines, WHO-CDS-HIV-18.51, WHO Model List of Essential Medicines 24th list
(2025), the WHO second-line regimen table, and the UNAIDS 2024 MENA regional
profile for the Global-Fund-supplied procurement context.

Cohort split 65 / 25 / 10 across the three tiers — an explicit modelling
assumption, stated as such, not data.

**`regenerate_patients.py`** (new) — rebuilds the cohort against those tiers.
Clinical fields (mutations, CD4, viral load, comorbidities) carry over
unchanged; only the access model is replaced. Writes `data/AllPatients_v2.xlsx`
with a `Formulary_Tier` column so tier can be reported as a covariate.

## Result

| | ad-hoc lists | tiered formulary |
|---|---|---|
| candidate space, whole cohort | 153 | **617** |
| per patient | 0–72 | **4–130** |
| patients with no valid regimen | 2 | **0** |
| GA reaches true optimum | 15/15 | **17/17** |
| exhaustive speed advantage | 1,378× | **750×** |

Every patient is now treatable, the access model is citeable, and tier is a
reportable covariate rather than an unexplained per-patient list.

## What this does not fix

Exhaustive search still wins by ~750×. A 4–130 candidate space is not large
enough to justify a GA, and it will not become large enough — the space grows as
O(n²·m) in catalogue size. Realistic data makes the study *valid*; it does not
make the GA *necessary*. The sequencing reframe is still required.

## Newly isolated

Two patients remain unsolvable, and the cause is now unambiguous — it is
resistance modelling, not access:

| patient | best achievable avg efficacy | mutations |
|---|---|---|
| HIV-SY-003 | 0.623 | M184V, K65R, L74V |
| HIV-SY-013 | 0.666 | Q151M, M184V |

Both fall below `MIN_EFFICACY_THRESHOLD = 0.75` even with a full 20-drug
formulary. Q151M is a genuine multi-NRTI resistance complex, so a poor score is
clinically realistic — but "no valid regimen exists" is not the right output.
Real practice would switch to a boosted-PI or INSTI-anchored salvage regimen and
accept reduced NRTI activity. Two options:

1. Lower the threshold and let the fitness function penalise rather than exclude.
2. Keep the threshold but treat these as a documented salvage subgroup — arguably
   the more interesting result, since it is exactly the population where
   sequencing decisions matter most.

Worth deciding deliberately: it is a modelling choice that a reviewer will ask
about either way.


---

# Round 3 — packaging and plotting fixes (from Windows test)

**`requirements.txt` rewritten.** The previous file pinned exact versions
transcribed from the original UTF-16 file, including `numpy==2.4.0` — a release
**yanked from PyPI for a backward-compatibility bug**. Installing it downgraded
numpy, pandas, matplotlib and tzdata, breaking scipy, ultralytics,
stable-baselines3 and nebula-ai in the test environment. Now minimum-version
bounds only, with `numpy<2.4` to keep pip away from the yanked release. Nothing
in this project is version-sensitive; exact pins bought nothing and cost a
working environment.

To repair an environment already downgraded by the old file, reinstall the
versions it replaced.

**seaborn removed.** `visualization/base_visualizer.py` imported seaborn for a
single cosmetic call, `sns.set_style('whitegrid')`. That pulled in the whole
seaborn → scipy chain, and the module failed outright on any scipy/numpy version
mismatch. Replaced with equivalent matplotlib `rcParams`. The visualisation
module now has no dependency beyond matplotlib, and `matplotlib.use('Agg')` is
set so it runs headless.

**Convergence plot corrected.** Three defects, all introduced when GA selection
moved to raw fitness:
- y-axis read "Fitness Score (1-100)" while the history stores the raw weighted
  objective. Relabelled.
- The mean-population series was computed with `np.mean` over a list containing
  `-inf` for infeasible individuals, so the whole series collapsed to `-inf` and
  never rendered — leaving a legend entry with no line. Now averaged over
  feasible individuals only.
- A `y=80` reference line labelled "WHO Recommended" was calibrated against the
  normalised 1–100 scale and is meaningless on the raw objective. Removed rather
  than left mislabelled.

## Verified

Clean virtualenv, only the four declared requirements (numpy 2.3.5, pandas 3.0.5,
matplotlib 3.11.1, openpyxl 3.1.5), no seaborn, no scipy. All four entry points
run; 17 regimen reports and 20 figures produced.


---

# Round 4 — code cleanup

**Test suite added** (`tests/test_search.py`, 14 tests, `python tests/test_search.py`).
The one that matters is `test_enumeration_matches_independent_brute_force`: it
rebuilds the feasible set with a naive triple loop written independently of
`enumerate_valid_regimens` and asserts the two agree, for every patient. Without
it, "exhaustive search" is an unverified claim and the whole comparison rests on
it. Also asserted: no duplicate regimens, no redundant backbones, every candidate
safe and in-formulary, GA output always inside the enumerated space, GA reaches
the exhaustive optimum, exhaustive evaluates each candidate exactly once,
determinism under a fixed seed, seed-independence of exhaustive search,
monotone bounded normalisation, and salvage-mode wiring.

**HLA-B\*5701 made reachable.** `drugs.xlsx` listed it as an abacavir
contraindication, but no rule consulted it and no patient profile carried the
status — the entry was inert. Added `PHARMACOGENETIC_MARKERS` and a rule that
excludes the drug when the profile records a positive status. Unknown status is
treated as eligible-pending-screening, matching practice, and surfaced by
`requires_hla_screening()`, which now populates a **Pre-Prescription** sheet in
every patient report. It fires on 14 of 17 recommendations.

**Backup regimen removed.** Nothing scored it: the fitness function reads
`primary_regimen` only and exhaustive search set backup = primary, so
"Yearly Savings" was structurally always zero. Removed from the individual
representation, the GA operators, `decode()`, the console output, and both
reporters, along with the dead `_select_backup_regimen` cost-aware selector.
Reintroduce only alongside an objective term that values it.

**Two figures dropped from the default run.** `plot_class_balance` is
tautological — every regimen is two NRTIs plus one third agent by construction,
so NRTI is always exactly 66.7%, and the pie chart reports the constraint rather
than a result. `plot_cost_efficacy_scatter` collapsed duplicate optima into
overlapping points. Both remain in `visualization/` if called explicitly.

**Also fixed earlier this round:** the patient report carried a column headed
"Available in Syria" reading Yes for every drug; `drugs.xlsx` has no availability
column, and the field was actually reading `Access_Constraints` (the formulary
tier). Relabelled "In Patient Formulary".

Verified after all changes: 14/14 tests pass, all five entry points run clean,
17 patient reports and 18 figures produced.


---

# Round 5 — drug cost provenance

**`config/drug_costs.py`** (new) — antiretroviral prices in US dollars per
person-year, every figure annotated with source and year, seven agents marked
ESTIMATE where no published LMIC generic price was located. Sources: Global Fund
Pooled Procurement (2023), Hill et al. global-lowest price table (2016), the 2021
darunavir pricing agreement.

**`apply_sourced_costs.py`** (new) — rewrites the cost column into
`data/drugs_sourced.xlsx` (all sheets preserved) and emits
`paper/tables/table1b_cost_provenance.csv` for the appendix.

**Why it mattered.** The original costs were unsourced and roughly 12x high for
this setting: TDF+3TC+DTG priced at $546 per person-year against a Global Fund
reference of under $45. Correcting it reverses the headline of Section 4.7:

| | unsourced | sourced |
|---|---|---|
| DTG-anchored | 3/17 | 17/17 |
| EFV-anchored | 5/17 | 0/17 |
| ABC appearances | 14/17 | 7/17 |
| TDF appearances | 1/17 | 7/17 |
| WHO-preferred structure | 0/17 | 7/17 |

The reported divergence from WHO guidance was a data artefact, not a property of
the objective. Section 4.7 rewritten; the earlier structural explanation was
withdrawn. Sensitivity ordering also changed — side-effect burden is now the most
influential weight (59%), cost second (41%).

Search results are unaffected: GA still matches the exhaustive optimum 17/17, and
14/14 tests pass.


---

# Round 6 — efficacy and toxicity provenance

**`config/clinical_evidence.py`** (new) — audits the efficacy, toxicity and
organ-impact columns against the trial literature. Each parameter is tagged
SOURCED, DIRECTION (evidence supports the ordering but not the magnitude) or
UNSOURCED. Sources: NAMSAL week-96, a 9,657-patient South African TLD/TEE cohort,
a 26-trial pooled TAF/TDF renal safety analysis, and a 14-trial TAF/TDF
meta-analysis.

**A per-drug efficacy value has no direct empirical referent.** Virologic
suppression is measured for regimens, not for individual agents, since no agent
is given alone. That column cannot be sourced directly at any level of effort;
what can be checked is whether it reproduces the orderings trials establish.

**It does not, in one respect.** The table carries DTG efficacy 0.98 against EFV
0.85 and toxicity 0.25 against 0.45. The evidence is non-inferiority, not
superiority: NAMSAL found comparable week-96 outcomes and similar serious adverse
event rates (9% vs 7%); the South African cohort found 12-month suppression of
78.9% vs 78.8%.

**`run_robustness.py`** (new) re-runs the cohort with trial-consistent values:

| | shipped | trial-consistent |
|---|---|---|
| DTG-anchored | 17/17 | 14/17 |
| EFV-anchored | 0/17 | 3/17 |
| recommendations changed | — | 3/17 |

The direction of the Section 4.7 finding survives; its magnitude does not. Both
figures are now reported in the paper rather than the more favourable one.

Title set: *Exhaustive search outperforms a genetic algorithm for
formulary-constrained antiretroviral regimen selection.*

`verify.py` now runs 30 checks including the robustness analysis. All pass.


---

# Round 7 — verified sources

**Neri 2007 verified from the author's manuscript, and one detail corrected.**
There are two companion 2007 papers, not one: the "intelligent mutation local
searchers" phrasing belongs to Neri, Toivanen & Makinen (Applied Intelligence
27(3):219-235), while the Adaptive Multimeme Algorithm is Neri, Toivanen,
Cascella & Ong (IEEE/ACM TCBB 4(2):264-278). Both are now cited. Their HIV model
is the Adams-Banks (2005) six-compartment ODE system, not Wodarz-Nowak, which
they cite only as prior art.

The verification also produced the strongest single fact in Section 2: Neri et al.
report a search space of approximately 7.7e318 schedules. That is the one study in
this literature that states its space size, and it makes the argument for us —
exhaustive enumeration there is physically impossible, while our feasible set is
613 regimens across the whole cohort. Both conclusions are right for their own
formulation.

**Section 2.2 added: resistance-guided regimen selection.** Cites Liu & Shafer
(2006) on genotype interpretation, Haupts et al. (2003, Swiss HIV Cohort) for
direct evidence that genotype-informed selection improved virologic response in
145 patients with virologic failure, Harrigan et al. (2005) on determinants of
emergent resistance in 1,191 naive adults, and the IAS-USA testing
recommendations and mutations panel. Earlier feedback had flagged the absence of
Harrigan and Gunthard.

**Resistance scoring: banding verified, penalties still derived — and two are
provably wrong.** The five-level banding and the GSS mapping are confirmed
against Stanford's own point-of-care document and an independent analysis.
Current algorithm is HIVdb 10.2 (2026-04-26). The per-drug integers could not be
retrieved from the mutation-score pages, which are JavaScript applications; the
machine-readable route is the ASI2 XML at github.com/hivdb/hivfacts.

Published v7.0 class-maximum scores are now recorded as an anchor, along with
`check_against_published()`, which flags derived penalties exceeding what
published values permit. It found two:

| pair | derived | published class max |
|---|---|---|
| E138K / RPV | 45 | 30 |
| L74V / ABC | 45 | 30 |

Both are now reported in the limitations. `check_provenance.py` runs the check.

`references.bib` now holds 27 entries.


# Round 8 — sensitivity is directionally asymmetric

Inspecting the full sweep (not just the per-weight maxima) shows the flips are
one-sided:

| weight | x0.5 | x0.75 | x1.25 | x1.5 | x2.0 |
|---|---|---|---|---|---|
| EFFICACY | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| TOXICITY | 5.9 | 0.0 | 0.0 | 0.0 | 11.8 |
| SIDE_EFFECT_BURDEN | 0.0 | 0.0 | 0.0 | 17.6 | 58.8 |
| GUIDELINE_COMPLIANCE_BONUS | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| COST_WEIGHT_MULTIPLIER | 41.2 | 11.8 | 0.0 | 0.0 | 0.0 |

Raising the cost weight changes nothing; halving it changes 41%. Lowering the
side-effect weight changes nothing; doubling it changes 59%. The nominal weights
sit at a boundary where, under sourced procurement prices, the cheapest feasible
regimens already win — so a larger cost penalty cannot reorder anything, and only
relaxing it lets the other objectives speak.

And efficacy is flat across the entire sweep. With the guideline bonus already
known to be inert, **two of the five objective terms do no work**: the scalarised
five-term objective behaves as a three-term one on this cohort. Section 4.6
updated.


# Round 9 — a stale number caught in the compiled paper

The paper claimed the optimum was already present in the random initial
population for **15 of 17** patients. Under the current parameters it is **14 of
17**, and the evolutionary operators contribute on three patients
(HIV-SY-005, HIV-SY-006, R-SECOND-HIV-002) rather than two — reaching the
optimum by generation 3 at the latest, within the first 180 of 6,000 evaluations.

The figure had been right all along, because `make_figures.py` computes the count
live; the prose had not been updated after the cost and formulary changes moved
it. `verify.py` did not test this number, which is why 31 checks passed with the
paper wrong. It does now.

Also corrected in the manuscript:
- figure cross-references were **crossed** — the initial-population discussion
  cited Figure 4 and the sensitivity discussion Figure 3, while LaTeX numbered
  them the other way round. All figure references now use `\ref{}`.
- `HLA-B\*5701` in the limitations rendered as `HLAB5701`, because `\*` is not a
  text-mode command.

`verify.py` now runs 31 checks. All pass.


# Round 10 — published

Paper published as a Zenodo preprint, 19 September 2026:
**10.5281/zenodo.22844540**

Authors: Jaudat Faisal Al-Husein, Omar Ali Al-Khayat, Yasser Almofaalani
(supervisor, third author). The code archive remains under the first two authors.

The paper record is linked to the code DOI (10.5281/zenodo.22809521) as
"is supplemented by", so the two resolve to each other.

Final state: 31 verification checks, 14 correctness tests, 11-page manuscript,
27 references, four figures, four tables. Every reported number reproduces from
`python verify.py`.

Known gaps, all declared in the paper's limitations: efficacy, toxicity and the
resistance penalties are unsourced; two derived resistance penalties exceed
published Stanford class maxima; the cohort is 15/17 synthetic. The sequencing
reformulation argued for in Section 5.2 is the follow-up work.


# Round 11 — an unstable headline number

An external audit of the published repository found three defects.

**Two markdown sections were never updated from 15 to 14.** `paper/results.md`
and `paper/introduction.md` still carried the superseded count, and results.md
still named two improving patients (HIV-SY-005, HIV-SY-007) where the corrected
figure is three (HIV-SY-005, HIV-SY-006, R-SECOND-HIV-002). The compiled PDF and
`main.tex` were already correct; the markdown had drifted.

**The headline speed figure was wall-clock, and wall-clock is not stable.** The
abstract claimed "approximately 1,400 times more computation" while Section 4.2
reported 1,550, and across the machines used in this project the ratio ranged
from about 1,400 to 2,000 — a spread of 40% in what was presented as a property
of the algorithms.

The stable quantity is the evaluation ratio: 102,000 genetic-algorithm
evaluations against 613 exhaustive ones, exactly **166**, independent of
hardware. The paper now leads with that and reports wall-clock separately,
explaining why it exceeds the evaluation ratio (per-generation overhead dominates
when a fitness evaluation is a few table lookups).

This is the fourth time in this project that a number looked authoritative and
was not. It is also the first one an outside reader found rather than a test.

**Also fixed:** the code DOI badge (the repository-ID badge URL returned 503;
switched to the DOI-form badge), the `@software` title in the README, and
CITATION.cff's citation type (`article` → `preprint`).

Version bumped to 1.1. The v1.0 Zenodo code archive predates the preprint and
still carries the superseded description; cutting a v1.1 release refreshes it.
