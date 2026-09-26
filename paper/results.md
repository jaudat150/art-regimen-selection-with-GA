## 4. Results

### 4.1 Search space characterisation

Across the 17-patient cohort the feasible set contains 613 regimens in total,
ranging from 2 to 130 per patient (median 30). Search-space size is driven
primarily by formulary tier: Tier 1 patients have a median of 27 feasible
regimens, Tier 2 a median of 40, Tier 3 a median of 80.

The governing observation is structural. Because a regimen is a fixed three-slot
object — two NRTIs plus one third agent — the number of distinct valid regimens
for a catalogue of $n$ drugs containing $n_{\text{NRTI}}$ NRTIs and $m$ eligible
third agents is

$$|\mathcal{R}| = \binom{n_{\text{NRTI}}}{2} \cdot m = O(n^2 m)$$

This is polynomial, not exponential. Figure 1(a) plots the growth: at the current
catalogue of roughly 20 approved agents the space contains 165 regimens; at 100
agents it contains approximately 24,000; at 500 agents — twenty-five times the
present catalogue, and well beyond any credible projection — approximately
3.07 million, which exhaustive search evaluates in under one minute on a single
core.

### 4.2 Genetic algorithm versus exhaustive search

The genetic algorithm recovered the exhaustive-search optimum for all 17
patients, and this held across three independent random seeds (1, 9, 42). No instance was found in which the metaheuristic located a better
solution, which is expected: exhaustive search is optimal by construction.

The cost asymmetry is substantial. The genetic algorithm performs
$60 \times 100 = 6{,}000$ fitness evaluations per patient regardless of instance
size — 102,000 across the cohort — while exhaustive search performs one
evaluation per feasible regimen, 613 in total. The evaluation ratio is therefore
166, and this figure is exact and independent of hardware. Figure 2 shows the
per-patient counts on a logarithmic scale.

Wall-clock time is the less useful comparison. On
one core the genetic algorithm took 10.3 s against 0.0067 s for exhaustive
search, a factor near 1,550; across machines we observed this ratio between
roughly 1,400 and 2,000. It exceeds the evaluation ratio because the genetic
algorithm's per-generation overhead — selection, crossover, mutation and repair
into the feasible set — dominates when each fitness evaluation is only a few
table lookups. We report the evaluation ratio as the primary figure for that
reason.

**We report this as a negative result.** For single-regimen ART selection at
realistic catalogue sizes, a genetic algorithm offers no advantage over
exhaustive search on either solution quality or computational cost. The search
space is small enough that guaranteed-optimal enumeration is not merely feasible
but strictly preferable.

### 4.3 Three failure modes recovered by correcting the comparison

Three implementation defects, each of which inflated the apparent case for the
metaheuristic, are worth reporting because they are easy to introduce and hard to
detect from aggregate results.

First, deterministic population initialisation. Our initial implementation
constructed individuals by a greedy rule — rank NRTIs by resistance-adjusted
efficacy, take the top two, take the highest-efficacy integrase inhibitor. This
returns an identical individual on every call, so the population began each run
with zero diversity and could escape the greedy solution only through mutation.
Before correction the algorithm returned the same regimen for 9 of 17 patients
irrespective of profile and matched the optimum for only 1.

Second, asymmetric constraint application. The metaheuristic honoured formulary
access constraints while the exhaustive baseline did not, so the two searched
different spaces; the baseline could reach drugs the metaheuristic was
structurally forbidden from selecting. Any comparison drawn from that
configuration is uninterpretable.

A third arose from normalisation placement: the logistic transform of
Section 3.4 saturates at both ends, so for the salvage subgroup every candidate
mapped to the same reported value and the search loop had no gradient to follow.
Selection must operate on raw fitness, with normalisation applied once at the
reporting boundary.

All three were corrected by routing candidate generation, mutation, and
crossover repair through a single shared enumeration routine and moving
normalisation outside the search loop. We report them because a
comparison between an exact method and a metaheuristic is only meaningful when
both operate over a provably identical feasible set, and this is easier to
violate than it appears.

### 4.4 Salvage subgroup

Two patients (11.8%) had no available regimen reaching the standard mean-efficacy
threshold. Both harboured multi-NRTI resistance complexes: M184V + K65R + L74V
(best achievable mean efficacy 0.623) and Q151M + M184V (0.666). Under the
salvage protocol of Section 3.5 both received anchored regimens — AZT + 3TC + DTG
and TAF + 3TC + DTG respectively — with substantially reduced raw fitness
($-55.1$ and $-143.6$ against a cohort median of $36.6$).

This subgroup is where sequencing decisions carry the greatest weight, since the
choice of first-line agent directly determines what remains available after
virologic failure. It is also where the single-regimen formulation is least
adequate, as it cannot represent the forward cost of exhausting a drug class.

### 4.5 The genetic algorithm's search contributes nothing

Inspecting the convergence traces makes the mechanism explicit. For 14 of 17
patients the best regimen found across the entire run is already present in the
**randomly initialised generation-1 population**; the reported improvement from
generation 1 to generation 100 is exactly zero. The evolutionary operators
contribute on three patients only (HIV-SY-005, HIV-SY-006 and R-SECOND-HIV-002),
and there the optimum is reached by generation 3 at the latest — within the
first 180 of 6,000 evaluations.

This is predictable rather than accidental. With a population of 60 sampled
uniformly from a feasible set of size $|\mathcal{R}|$, the probability that the
optimum appears at initialisation is
$1 - (1 - 1/|\mathcal{R}|)^{60}$, which for the observed range of
$|\mathcal{R}|$ is 37–100% (Figure 4).

The genetic algorithm is therefore not performing directed search on this
problem. It is performing random sampling, and then spending a further 5,940
evaluations confirming what its first 60 draws already found. Reporting
convergence curves without an exact baseline would show a rapid rise to a stable
plateau — a trace easily read as fast convergence, when the correct reading is
that the search never began.

### 4.6 Sensitivity to objective weights

Linear scalarisation is only defensible if the resulting recommendations are not
hostage to the particular weights chosen. We perturbed each weight over
$0.5\times$ to $2\times$ its nominal value, holding the others fixed, and
recomputed the exhaustive optimum for every patient. Exhaustive search rather
than the genetic algorithm was used so that observed variation is attributable
to the objective and not to stochastic search. Figure 3 reports the maximum
proportion of patients whose recommended regimen changes.

Recommendations are **not robust to weighting**, and the pattern is asymmetric.
Side-effect burden is the most influential term under sourced costs, changing the
recommended regimen for 10 of 17 patients (59%) when doubled; the cost weight
changes 7 of 17 (41%) when halved, and toxicity 2 of 17 (12%).

The direction matters. Raising the cost weight above its nominal value changes
nothing, while halving it changes 41% of recommendations; conversely, lowering
the side-effect weight changes nothing, while doubling it changes 59%. The
nominal weights therefore sit at a boundary at which the cost term already
dominates: under sourced procurement prices the cheapest feasible regimens
already win, so increasing the penalty on cost cannot change the ranking, and
only relaxing it allows the other objectives to express a preference.

**Two of the five objective terms do no work at all.** Efficacy changes no
recommendation anywhere in the $0.5\times$–$2\times$ range, and the
guideline-compliance bonus changes none either, for the structural reason given
below. Efficacy is inert here for a different and more contingent reason: within
each patient's feasible set the surviving candidates have already passed the
efficacy threshold of Section 3.5, and their residual differences are small
relative to the cost and side-effect spreads. A scalarised objective with five
terms is, in this instance, effectively a three-term objective.

This has a direct implication for deployment. A regimen recommendation from this
system is a statement about the weights as much as about the patient, and those
weights encode a health-economic judgement — how much toxicity is worth how many
dollars — that properly belongs to a clinician or a national programme, not to
the algorithm's authors. We report the sensitivity rather than tuning it away.

**The guideline-compliance bonus is inert.** Perturbing it across the full sweep
range changed no recommendation for any patient. This follows from the
constraint structure: the candidate enumeration of Section 3.2 admits only
WHO-compliant regimens, so the bonus is applied uniformly across the entire
feasible set, shifts every fitness value equally, and cannot alter the ranking.
It is a term in the objective that does no work. We note this because a bonus
term that duplicates a hard constraint is easy to introduce and produces no
visible symptom — the fitness values it inflates look entirely reasonable.

The dominance of the cost term also explains two patients (HIV-SY-007,
HIV-SY-011) whose recommendations score near the reporting floor despite meeting
the efficacy threshold: the cost penalty, scaled by their reported cost
sensitivity, outweighs their attainable efficacy.

### 4.7 Recommendations under sourced versus unsourced cost data

The drug table inherited from the original implementation carried monthly costs
with no recorded provenance. Checked against published procurement figures they
were roughly an order of magnitude high for the setting modelled here: the table
priced TDF + 3TC + DTG at US$546 per person-year, against a Global Fund Pooled
Procurement Mechanism reference of under US$45 for the same fixed-dose
combination \cite{globalfund2023}. Dolutegravir was the most distorted entry.

We rebuilt the cost table from published sources, annotating every figure with
its origin and year and marking as estimates the seven agents for which no
published low- and middle-income generic price was located; the full table, with
per-figure sources, is in the repository. The
effect on recommendations is not marginal.

| | unsourced costs | sourced costs |
|---|---|---|
| DTG-anchored regimens | 3 / 17 | **17 / 17** |
| EFV-anchored regimens | 5 / 17 | 0 / 17 |
| ABC appearances | 14 / 17 | 7 / 17 |
| TDF appearances | 1 / 17 | 7 / 17 |
| WHO-preferred structure (tenofovir + XTC + DTG) | 0 / 17 | 7 / 17 |

Under the original figures the optimiser systematically preferred
efavirenz-anchored regimens over dolutegravir, inverting WHO first-line guidance
\cite{who2018update,who2021consolidated}. Under sourced figures it anchors on
dolutegravir for every patient in the cohort, and selects the full WHO-preferred
structure wherever a tenofovir prodrug is not excluded by renal constraints. The
apparent divergence from guidelines was an artefact of the cost data, not a
property of the objective.

We report this because the direction of the error is instructive. An unsourced
parameter did not produce noise; it produced a coherent, defensible-looking, and
completely wrong clinical conclusion, in a model whose search and constraint
logic were by then verified by an exact baseline and a test suite. Correctness of
the optimiser is not correctness of the recommendation.

### Robustness to trial-consistent parameter values

Having found the cost column unsourced, we audited the remaining parameter
families against the clinical literature. Per-drug efficacy has no direct
empirical referent — virologic suppression is measured for regimens, not for
individual agents, since no agent is given alone — so that column cannot be
sourced directly at any level of effort. What can be checked is whether the
per-drug values reproduce the relative orderings that trials do establish.

They do not, in one respect that matters. The inherited table carries
dolutegravir efficacy at 0.98 against efavirenz at 0.85, and toxicity at 0.25
against 0.45. The trial evidence is of non-inferiority rather than superiority:
NAMSAL reported comparable week-96 outcomes and similar serious adverse event
rates (9% against 7%) for dolutegravir versus efavirenz 400 mg
\cite{namsal2020}, and a South African cohort of 9,657 patients found 12-month
viral suppression of 78.9% on tenofovir/lamivudine/dolutegravir against 78.8% on
the efavirenz-based regimen \cite{tldcohort}.

Re-running the cohort with values reflecting that non-inferiority (efficacy 0.91
against 0.90, toxicity 0.28 against 0.33) changes the recommendation for 3 of 17
patients, all from a dolutegravir anchor to an efavirenz anchor. Dolutegravir
anchors 14 of 17 recommendations rather than 17 of 17.

The direction of the Section 4.7 finding therefore survives — sourced costs move
the model decisively toward guideline-concordant recommendations — but its
magnitude does not. We report both figures rather than the more favourable one.
`run_robustness.py` reproduces this analysis.

**A caveat on fixed-dose combinations.** Antiretrovirals are largely procured as
fixed-dose combinations priced below the sum of their components. Our model costs
regimens additively from per-drug prices, which overestimates the procurement
cost of any regimen available as an FDC — disproportionately the WHO-preferred
ones, since those are the combinations manufactured as FDCs. For the three TLD
components we allocate the published FDC ceiling across the components rather
than using independent per-drug prices, and mark this as an allocation. A
regimen-level cost model is the correct fix.

**Pharmacogenetic prerequisite.** Abacavir hypersensitivity is strongly
associated with the HLA-B*5701 allele; screening before initiation is
recommended and abacavir is contraindicated in allele-positive patients
\cite{dhhs_hlab5701}. We implement this as a hard exclusion when allele status
is recorded and otherwise report it as a pre-prescription screening requirement,
which it is for the abacavir-containing recommendations in the cohort. No profile
in this cohort records allele status, so the exclusion never binds here; the
requirement is surfaced rather than enforced.

---

## 5. Discussion

### 5.1 When is a metaheuristic warranted?

Our results delimit the conditions under which evolutionary search is
appropriate for antiretroviral optimisation. A genetic algorithm earns its cost
when at least one of three conditions holds: the search space grows
super-polynomially; fitness evaluation is expensive, as with simulation-based
objectives; or a set of trade-off solutions is required rather than a single
scalarised optimum.

Single-regimen selection under a fixed three-slot structure satisfies none of
these. Fitness evaluation is a weighted sum over a handful of table lookups, the
space grows as $O(n^2m)$, and linear scalarisation returns one point.

This is not an argument against metaheuristics in HIV therapy optimisation. It
is an argument that the problem must be formulated at a scale where they are
warranted, and that reporting a metaheuristic's success on a tractable instance
without an exact baseline risks presenting as an achievement what exhaustive
enumeration would deliver faster and with a guarantee.

### 5.2 Sequencing as the appropriate formulation

HIV therapy is not a single decision. Patients begin on first-line therapy,
experience virologic failure, accumulate resistance, and switch — and the
first-line choice constrains what remains viable at second and third line. This
is a sequential decision problem under evolving constraints.

Formulated as a sequence of $L$ lines drawn from a feasible set of size
$|\mathcal{R}|$, and accounting for resistance accumulation between lines, the
space is $O(|\mathcal{R}|^L)$. Figure 1(b) plots the growth for
$|\mathcal{R}| = 165$: 27,225 sequences at $L = 2$, $4.49 \times 10^6$ at
$L = 3$, $7.41 \times 10^8$ at $L = 4$. Exhaustive search becomes infeasible
between the third and fourth line — precisely the horizon over which HIV therapy
is actually planned, and precisely the regime in which the salvage subgroup of
Section 4.4 lives.

This is the formulation under which the present work should be extended, and it
requires modelling components the current implementation lacks: virologic failure
probability as a function of regimen and adherence, resistance mutation
accumulation conditioned on the failing regimen, and cross-resistance between
classes.

### 5.3 Multi-objective alternative

A second direction retains the single-regimen formulation but replaces linear
scalarisation with a Pareto-based method such as NSDA-II. The contribution would
then be the trade-off surface itself — presenting a clinician with the efficacy /
toxicity / cost frontier rather than one point determined by weights fixed in
advance. This is a weaker contribution than the sequencing reformulation but
requires substantially less additional modelling, and it addresses the
non-convexity limitation noted in Section 3.4.

### 5.4 Limitations

**Synthetic cohort.** Fifteen of seventeen profiles are synthetic. No claim about
real-world clinical outcomes is supported by this work. The search-space
characterisation in Section 4.1 is determined by catalogue and constraint
structure and does not depend on the patient distribution; the results in
Sections 4.2–4.4 do, and require replication on a real cohort.

**Tier proportions.** The 65 / 25 / 10 tier distribution is an assumption, not an
observation. Tier is reported as a covariate so its influence can be assessed.

**Pharmacogenetic constraints.** Abacavir carries an HLA-B\*5701 prerequisite,
implemented as a hard exclusion when allele status is recorded positive and
otherwise reported as a pre-prescription screening requirement — which it is for
14 of 17 recommendations. No cohort profile records allele status, so the
exclusion never binds here; the requirement is surfaced rather than enforced.
Real deployment would need the screening result before dispensing.

**Unsourced model parameters.** Per-drug efficacy, toxicity, organ-impact and
side-effect values carry no recorded source. The resistance model is structurally
aligned to the Stanford HIVdb algorithm \cite{liu2006}: penalties are summed
across mutations and mapped through the published five-level banding (0--9
susceptible, 10--14 potential low-level, 15--29 low-level, 30--59 intermediate,
$\geq$60 high-level), with genotypic susceptibility scores of 1.0, 0.75, 0.5,
0.25 and 0. The banding is verified; the per-mutation penalties are not. They are
derived from the project's legacy fractional reductions rather than taken from
the published Stanford tables, and are marked as such in
`config/resistance_scoring.py`. Checked against the published version-7.0
class-maximum scores, two derived penalties exceed what the published values
permit (E138K against rilpivirine, and L74V against abacavir, both derived at 45
against a published class maximum of 30). Exact per-drug penalties for the
current algorithm version (HIVdb 10.2) are available as machine-readable ASI2
XML from Stanford's `hivfacts` repository and should replace the derived values
before any clinical claim is made. Note
also that per-drug efficacy has no direct empirical referent — virologic
suppression is measured for regimens, not individual agents — so that column is a
modelling abstraction rather than a measurable quantity. Seven agents have no
published low- and middle-income generic price and carry estimates. Given
Section 4.7, no conclusion resting on the specific magnitude of these parameters
should be treated as established. `check_provenance.py` reports the current
status of every parameter.

**Static resistance model.** Resistance is treated as a fixed patient attribute.
Real resistance evolves under selective pressure from the administered regimen —
the central mechanism the sequencing reformulation of Section 5.2 would capture.

**Weight elicitation.** Section 4.6 shows recommendations shift substantially
under modest reweighting, and the nominal weights were not elicited from
clinicians. Any deployment would require weights set by the responsible clinical
authority, with the sensitivity reported alongside the recommendation.

**Single decision point.** The model recommends one regimen. It does not
represent a fallback, a switch on failure, or any later line — the limitation the
sequencing reformulation of Section 5.2 addresses.

---

## Figure captions

**Figure 1.** Search-space growth under two problem formulations. (a) Single
regimen selection with a fixed two-NRTI-plus-third-agent structure grows as
$O(n^2m)$ in catalogue size $n$; exhaustive search remains sub-second across the
entire plotted range, including catalogue sizes twenty-five times the present
one. (b) Sequencing over $L$ lines of therapy grows as $O(|\mathcal{R}|^L)$ and
crosses the tractability boundary between the third and fourth line.

**Figure 4.** Probability that the optimum appears in the randomly initialised
population, $1-(1-1/|\mathcal{R}|)^{60}$, plotted against feasible-set size,
with the patients whose optimum was in fact found in generation 1 marked. For 15
of 17 patients the genetic algorithm's remaining 5,940 evaluations produced no
improvement over its initial random sample.

**Figure 3.** Sensitivity of recommended regimens to objective weights. Each
bar gives the maximum proportion of the cohort whose recommended regimen changes
when that weight is scaled between $0.5\times$ and $2\times$ its nominal value,
all others held fixed. The guideline-compliance bonus is applied uniformly across
the feasible set — which by construction contains only compliant regimens — and
therefore cannot alter any ranking.

**Figure 2.** Fitness evaluations required to reach the same optimum, per
patient, logarithmic scale. The genetic algorithm performs a fixed 6,000
evaluations per patient irrespective of instance size; exhaustive search performs
one per feasible regimen (2–130). Both returned identical optima for all 17
patients.
