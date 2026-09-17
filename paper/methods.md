# Methods

*Paste-ready draft. Citation keys in `\cite{}` correspond to `paper/references.bib`.
Numbers are reproducible via `python run_comparison.py`.*

---

## 3. Methods

### 3.1 Problem formulation

We model first-line antiretroviral therapy (ART) selection as a constrained
combinatorial optimisation problem. Let $D$ be the catalogue of available
antiretroviral drugs, partitioned by class into nucleoside/nucleotide reverse
transcriptase inhibitors ($D_{\text{NRTI}}$), integrase strand transfer
inhibitors, non-nucleoside reverse transcriptase inhibitors, and boosted
protease inhibitors. Following WHO guidance, a valid regimen $r$ consists of two
NRTIs forming a backbone plus one third agent drawn from the remaining classes
\cite{who2021consolidated,who2018update}:

$$r = \{d_1, d_2, d_3\},\quad d_1, d_2 \in D_{\text{NRTI}},\ d_1 \neq d_2,\quad
d_3 \in D \setminus D_{\text{NRTI}}$$

A regimen is unordered: $\{d_1, d_2, d_3\}$ is a set, not a sequence. This
distinction matters for complexity analysis, as enumerating ordered NRTI pairs
inflates the apparent search space by a factor of two.

### 3.2 Clinical validity constraints

Three constraints restrict the feasible set.

**Patient safety.** A drug is excluded if it is contraindicated by the patient's
comorbidities, hepatic or renal function, or documented hypersensitivity.

**Backbone non-redundancy.** Class-level compliance is necessary but not
sufficient. Certain NRTI pairs share an analogue class and resistance pathway and
are never co-prescribed: lamivudine and emtricitabine are interchangeable
cytidine analogues sharing the M184V pathway; tenofovir disoproxil fumarate and
tenofovir alafenamide are both tenofovir prodrugs; zidovudine and stavudine are
thymidine analogues with additive mitochondrial toxicity. We therefore define a
redundancy relation $R \subset D_{\text{NRTI}} \times D_{\text{NRTI}}$ and
require $(d_1, d_2) \notin R$.

We note this explicitly because a purely class-structural validity check — two
NRTIs plus one third agent — admits all three of these pairs. In our cohort,
omitting the redundancy constraint caused 12 of 17 optimiser outputs to be
clinically inadmissible while passing structural validation.

**Formulary access.** Drug availability is modelled through service-delivery
tiers (Section 3.3) rather than assumed universal.

### 3.3 Formulary access model

Antiretroviral availability varies substantially by health-system context, and in
resource-constrained settings it is often the binding constraint on regimen
choice rather than a secondary consideration. Rather than assigning arbitrary
per-patient availability lists, we define three nested formulary tiers derived
from published guidance (Table 1).

**Tier 1 (national programme, $|D| = 10$)** comprises the WHO-preferred
first- and second-line agents together with the boosted protease inhibitors
listed for second-line use \cite{who2021consolidated,who2018update,who2025eml}.
This corresponds to the formulary of a public ART clinic supplied through pooled
procurement, the predominant delivery model in low-prevalence,
resource-constrained settings \cite{unaids2024mena}.

**Tier 2 (referral centre, $|D| = 14$)** adds WHO alternative and
special-circumstance agents: tenofovir alafenamide, indicated for adults with
impaired renal function or established osteoporosis; darunavir/ritonavir and
raltegravir, listed as second-line alternatives to lopinavir/ritonavir; and
doravirine \cite{who2018update}.

**Tier 3 (tertiary centre, $|D| = 20$)** comprises the full catalogue including
salvage agents that in practice require named-patient importation.

Tiers are nested, so a patient's tier bounds the options available at every line
of therapy, not only the first. We assign tiers across the cohort in a 65 / 25 /
10 ratio. This proportion is a modelling assumption reflecting the concentration
of care in public facilities; we report tier as a covariate so its effect can be
inspected directly.

### 3.4 Fitness function

We use a linear scalarisation of five objectives:

$$f(r) = w_e \bar{E}(r) - w_t T(r) - w_c C(r) - w_s S(r) + w_b B(r)$$

where $\bar{E}$ is mean resistance-adjusted efficacy, $T$ cumulative organ
toxicity, $C$ monthly cost, $S$ side-effect burden weighted by patient-specific
sensitivities, and $B$ a WHO-compliance bonus. Weights are patient-adjusted:
cost weight scales with reported cost sensitivity, and toxicity weight with
hepatic or renal impairment.

Linear scalarisation was chosen for three reasons: it yields a single scalar
directly usable as a genetic-algorithm fitness value; the weights are
individually interpretable and can be elicited from clinicians in the units of
each objective; and it permits the sensitivity analysis reported in Section 4.4.
Its principal limitation — that it cannot recover non-convex regions of the
Pareto front — is addressed in Section 5.

**Normalisation.** For reporting we map $f$ to $[1, 100]$ via a logistic
transform $\sigma(f) = 1 + 99 \, / \, (1 + e^{-(f - \mu)/s})$. The centre $\mu$
and scale $s$ are calibrated against the empirical distribution of $f$ over all
feasible regimens in the cohort ($\mu = 30$, $s = 8$; observed range
$[-143.6, 57.7]$). We report raw $f$ alongside $\sigma(f)$ throughout, since the
logistic transform saturates for the salvage subgroup and would otherwise
compress genuinely distinct outcomes onto the same value.

### 3.5 Salvage subgroup

Patients harbouring multi-NRTI resistance complexes may have no available
regimen reaching the standard mean-efficacy threshold $\tau = 0.75$. Declaring
such patients untreatable is clinically incorrect: practice anchors on a
high-genetic-barrier agent and accepts reduced NRTI activity, consistent with WHO
third-line guidance favouring agents with minimal cross-resistance to those
already used \cite{who2021consolidated}.

We therefore define a salvage mode. When
$\max_r \bar{E}(r) < \tau$, the feasible set is restricted to regimens anchored
on a boosted protease inhibitor or integrase inhibitor, and the efficacy
constraint is relaxed to $\tau_{\text{salv}} = 0.50$. Reduced efficacy is then
penalised by the fitness function rather than excluded by the constraint. Salvage
patients are flagged and reported as a distinct subgroup.

### 3.6 Search strategies

We compare two strategies over an identical feasible set. Both are driven from
the same candidate-generation routine, so the only difference between them is
search behaviour.

**Exhaustive search** enumerates every valid regimen and returns the maximiser.
It is guaranteed optimal and provides the ground truth against which the
metaheuristic is assessed.

**Genetic algorithm.** Individuals are regimens. The population is initialised by
uniform sampling from the feasible set; selection is tournament-based with
elitism; crossover pools parental drugs and repairs the child back into the
feasible set by maximal overlap; mutation resamples a feasible neighbour sharing
at least two drugs with the incumbent. Constraining every operator to the
feasible set guarantees the algorithm cannot emit a regimen that exhaustive
search would reject — a prerequisite for the comparison to be meaningful.
Parameters: population 60, generations 100, tournament size 3, crossover rate
0.8, mutation rate 0.15, elitism 2, fixed seed.

### 3.7 Cohort

The cohort comprises 17 patient profiles: 15 synthetic and 2 encoded from
published case reports. Synthetic profiles were generated to span clinically
meaningful variation in resistance mutations, CD4 count, viral load, hepatic and
renal function, comorbidities, and cost sensitivity.

We state plainly that synthetic data is a limitation. Individual-level ART
prescribing data was not obtainable for this study, and the synthetic cohort
cannot support claims about real-world clinical outcomes. It is adequate for the
purpose it serves here, which is characterising the structure and size of the
search space and comparing search strategies over it — quantities determined by
the drug catalogue and the constraint structure, not by the empirical
distribution of patients. Section 5 discusses what validation on real cohorts
would be required before clinical claims could be made.

---

## Table 1 — Formulary tiers

| Tier | $\|D\|$ | Composition | Source |
|---|---|---|---|
| Tier 1 — national programme | 10 | TDF, 3TC, FTC, AZT, ABC, DTG, EFV, NVP, LPV/r, ATV/r | WHO preferred first/second-line + second-line boosted PIs \cite{who2021consolidated,who2018update} |
| Tier 2 — referral centre | 14 | Tier 1 + TAF, DRV/r, RAL, DOR | WHO alternatives and special-circumstance agents \cite{who2018update} |
| Tier 3 — tertiary centre | 20 | Tier 2 + RPV, EVG, BIC, maraviroc, ibalizumab, FTR | Full catalogue incl. salvage agents |
