# Paper package

| file | what it is |
|---|---|
| `abstract.md` | Rewritten abstract, title options, keywords, and reframing guidance for Sections 1 and 2. |
| `introduction.md` | Sections 1 and 2, paste-ready, built on your existing SOTA draft. |
| `methods.md` | Section 3, paste-ready. Problem formulation, constraints, formulary model, fitness function, salvage protocol, search strategies, cohort. Includes Table 1. |
| `ethics.md` | Section 6 plus journal declarations: data governance, safety validation, liability, regulatory pathway, COI/funding. |
| `results.md` | Sections 4–5, paste-ready. Results, negative-result framing, discussion, limitations, figure captions. |
| `references.bib` | The four WHO/UNAIDS sources cited in the above. |
| `figures/fig1_search_space.{png,pdf}` | Polynomial growth of selection vs exponential growth of sequencing. This figure carries the paper's central argument. |
| `figures/fig2_evaluations.{png,pdf}` | Per-patient evaluation counts, GA vs exhaustive, log scale. |
| `figures/fig3_sensitivity.{png,pdf}` | Tornado plot: proportion of cohort whose recommendation changes per weight. |
| `figures/fig4_initial_population.{png,pdf}` | Predicted vs observed probability the optimum is in the initial population. |
| `tables/table2_results.csv` | Full per-patient results: tier, salvage flag, best achievable efficacy, space size, raw and normalised fitness, both regimens, evaluation counts. |
| `make_figures.py` | Regenerates both figures from `reports/comparison.csv`. |

## Regenerating everything

```bash
pip install -r requirements.txt
python regenerate_patients.py     # rebuild cohort from formulary tiers
python run_comparison.py          # GA vs exhaustive -> reports/comparison.csv
python apply_sourced_costs.py    # sourced costs -> data/drugs_sourced.xlsx
python run_sensitivity.py         # weight sweep -> reports/sensitivity.csv
python run_robustness.py          # trial-consistent parameters -> reports/robustness.csv
python check_provenance.py        # which parameters are sourced
python verify.py                  # everything, 30 checks
python tests/test_search.py       # 14 correctness tests
python paper/make_figures.py      # all three figures from those CSVs
```

## Figures from `main.py --visualize`

Those 20 are diagnostic output, not paper figures. Two notes if you plan to use
any of them:

- `class_distribution.png` is tautological — every regimen is two NRTIs plus one
  third agent, so NRTI is always exactly 66.7%. The pie chart reports the
  constraint, not a result. Cut it.
- `cost_efficacy_tradeoff.png` shows only 10 distinct points for 17 patients
  (identical optima overlap), and the "Cost-Effective Zone" label floats outside
  the axes. Fixable, but Figure 3 makes the cost point better.

The convergence plots are worth keeping as an appendix: the flat best-fitness
traces with "Improvement: +0.0" are the visual form of Section 4.5.

## What still needs your hand

**Placeholders to fill:** repository URL and authors' contributions in
`ethics.md`; the title, from `abstract.md`.

**Parameter provenance.** Costs are sourced (`config/drug_costs.py`); efficacy
and toxicity are audited against trial evidence (`config/clinical_evidence.py`)
with four parameters flagged as overstated; resistance penalties are structurally
correct but unverified against the Stanford tables. `check_provenance.py` reports
the current state. The remaining task is replacing the resistance scores from
hivdb.stanford.edu, or declaring them derived in the limitations.

**The abstract** is drafted in `abstract.md` along with title options and
keywords. Read it against your existing draft and decide how much of the original
framing you want to keep.

**Author list and affiliations** — carried over from your existing drafts.

## Reviewer comments addressed

Earlier feedback on this project raised five gaps. Where they now stand:

| comment | status |
|---|---|
| No implementation details | Section 3 — full formulation, operators, parameters |
| No validation data | Sections 4.1–4.7, 14 tests, `verify.py` |
| Unsubstantiated claims (">97% optimal in seconds") | Replaced by measured results; the claim was false and is retracted |
| No ethics / data governance / safety / liability / regulatory | Section 6 (`ethics.md`) |
| No COI or funding statements | Declarations in `ethics.md` |
| Tutorial website cited for GA theory | Holland (1975), Goldberg (1989) in `references.bib` |
| Missing Harrigan / Günthard on resistance-guided therapy | Section 2.2, with Liu & Shafer, Haupts, and the IAS-USA panel |

## On venue

The negative result is the contribution: a complexity characterisation showing
when metaheuristics are and are not warranted for ART regimen selection, plus the
two comparison artefacts in Section 4.3 that inflate metaheuristic performance.
That is a methods contribution, not a clinical one, and should be pitched to
computational-optimisation or health-informatics venues rather than clinical HIV
journals. Workshop tracks on evolutionary computation in bioinformatics are a
reasonable first target; a preprint on arXiv (cs.NE) makes the work citable while
review proceeds.
