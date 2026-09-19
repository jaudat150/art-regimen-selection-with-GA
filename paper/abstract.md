# Abstract & framing

The previous abstract described the problem as "high-dimensional" and reported
"scalability." Section 4.1 measures the space at 2–130 regimens per patient and
shows it grows polynomially. Both claims had to go. What replaces them is a
sharper contribution than the original: not "our GA works" — which is
unfalsifiable without an exact baseline — but "here is where metaheuristics
begin to be warranted for this problem, and here are three ways the comparison
can be got wrong."

---

## Title

**Exhaustive search outperforms a genetic algorithm for formulary-constrained
antiretroviral regimen selection**

(States the finding and puts the formulary contribution in the title. The three
alternatives considered are kept below.)

## Abstract (draft, ~230 words)

Antiretroviral regimen selection requires balancing efficacy, toxicity, cost and
side-effect burden under patient-specific resistance and formulary constraints.
Genetic algorithms have been applied to this task in prior work, generally
without comparison against an exact baseline. We report such a comparison.

We formulate WHO-compliant regimen selection as constrained combinatorial
optimisation over a catalogue of 20 antiretrovirals, with drug availability
modelled through three formulary tiers derived from WHO guidance rather than
assumed universal. Evaluating a genetic algorithm and exhaustive search over a
provably identical feasible set across 17 patient profiles, we find the feasible
set contains 2–130 regimens per patient. The genetic algorithm recovers the
exact optimum for every patient across three random seeds, while requiring
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
Rebuilding the drug cost
table from published procurement figures — the original values were unsourced and
roughly an order of magnitude high — moves dolutegravir-anchored regimens from 3
of 17 recommendations to 17 of 17, reversing an apparent inversion of WHO
first-line guidance; under efficacy and toxicity values corrected against trial
evidence the figure is 14 of 17.

We conclude that metaheuristic search for this problem is warranted only under a
sequencing formulation, where the space grows as $O((n^2m)^L)$ across $L$ lines
of therapy and exhaustive enumeration becomes infeasible beyond the third line.

---

## A note on what changed late

Section 4.7 originally reported that the optimiser systematically diverged from
WHO first-line guidance, and attributed it to a structural limitation of
single-decision objectives. That was wrong. The divergence was an artefact of
unsourced cost data; with published procurement prices the model anchors on
dolutegravir for every patient. The section now reports the reversal instead,
which is the more useful finding: a single unsourced parameter produced a
coherent and completely wrong clinical conclusion in a model whose search logic
was already verified by an exact baseline and a passing test suite.

If you kept any of the old framing in your own drafts, it needs removing.

## Title alternatives considered

1. *When is evolutionary search warranted for antiretroviral regimen selection?
   An exact baseline and three comparison artefacts*
2. *Exhaustive search outperforms a genetic algorithm for WHO-compliant
   antiretroviral regimen selection: a complexity characterisation*
3. *Formulary-constrained antiretroviral regimen selection: search-space
   characterisation and the limits of metaheuristic optimisation*

(1) leads with the question and signals both contributions. (2) is the most
direct and the most likely to be read by exactly the right people. (3) is the
safest and the dullest.

---

## Keywords

combinatorial optimisation; exact algorithms; genetic algorithms; antiretroviral
therapy; clinical decision support; benchmarking; negative results

---

## Reframing Section 1 (Introduction)

Your existing introduction motivates the problem as complex and the GA as the
solution. The complexity claim is the part that needs to go; the clinical
motivation is fine and should stay.

Suggested arc:

1. **Clinical motivation** — keep as drafted. ART selection genuinely does trade
   off several objectives under patient-specific constraints, and in
   resource-constrained settings formulary availability is often binding rather
   than incidental. None of this depends on the problem being large.
2. **What prior work does** — metaheuristics have been applied to ART
   optimisation, typically reporting convergence behaviour and solution quality
   without an exact baseline. State this neutrally; it is an observation about
   evaluation practice, not an accusation.
3. **The gap** — without an exact baseline, "the GA found a good regimen" is
   not a claim that can be assessed. Whether it found *the* regimen, and at what
   cost relative to enumeration, is unanswered.
4. **What this paper does** — supplies the baseline, characterises the space,
   reports the comparison honestly, and identifies the formulation under which
   metaheuristics do become necessary.
5. **Contributions** — list four: the formulary-tier access model; the
   search-space characterisation; the head-to-head with an exact baseline; the
   three comparison artefacts.

Frame the negative result as the point from the first paragraph. Do not build to
it as a disappointment in Section 4.

---

## Reframing Section 2 (Related work)

Your ~780-word state-of-the-art section survives intact. What changes is the
question it is organised around.

Currently it surveys GA applications to HIV treatment optimisation and
implicitly argues *this approach is established, therefore we apply it*. Reorganise
it to ask *how has this work been evaluated?* — specifically, which studies
compare against an exact baseline, which report search-space size, and which
report weight sensitivity. That reframing converts a literature summary into
motivation for your contribution, and it costs you almost no rewriting.

Be scrupulous here. Do not characterise prior work as flawed. The honest claim
is that exact baselines are not routinely reported for this problem, which makes
cross-study comparison difficult — and that your own three artefacts show why
the baseline matters, since you introduced all three yourself and caught them
only because the baseline was there.

That framing also protects you. A reviewer who has published a GA paper without
an exact baseline is a plausible referee for this manuscript.

---

## Honest positioning

State plainly in the introduction that the cohort is largely synthetic and that
no clinical claim is made. The contributions that matter here — the complexity
characterisation and the comparison artefacts — do not depend on the patient
distribution, and saying so up front is stronger than letting a reviewer find it
in the limitations.
