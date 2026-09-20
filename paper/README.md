# Paper

*Exhaustive Search Outperforms a Genetic Algorithm for Formulary-Constrained
Antiretroviral Regimen Selection*

Jaudat Faisal Al-Husein · Omar Ali Al-Khayat · Yasser Almofaalani
Antioch Private University, Rural Damascus, Syria

Published as a preprint —
[10.5281/zenodo.22844539](https://doi.org/10.5281/zenodo.22844539)
(concept DOI; always resolves to the latest version)

> **Note.** The PDF in this folder reports the cost comparison as the evaluation
> ratio (166×, exact and hardware-independent) rather than wall-clock time, which
> varied between roughly 1,400× and 2,000× across machines. See `CHANGES.md`,
> Round 11. Zenodo versions v1 and v2 predate this correction; cite the concept
> DOI above, which resolves to the current version.

## Contents

| | |
|---|---|
| `al-husein-2026-art-regimen-selection.pdf` | The published preprint. |
| `main.tex` | LaTeX source (IEEEtran, conference format). Compiles with `references.bib` and the four PDFs in `figures/`. |
| `references.bib` | 27 references. |
| `figures/` | Four figures, PDF for LaTeX and PNG for slides or the web. |
| `tables/` | Four result tables as CSV, written by the analysis scripts. |
| `abstract.md` `introduction.md` `methods.md` `results.md` `ethics.md` | The same manuscript as markdown, one file per section. |

## Compiling

From this directory, with a TeX distribution installed:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Or upload `main.tex`, `references.bib` and `figures/*.pdf` to Overleaf.

## Reproducing the numbers

Every figure, table and numerical result in the paper is regenerated from the
code in this repository. From the repository root:

```bash
python verify.py
```

31 checks. Exit code 0 means the manuscript and the code agree.

To regenerate the paper's figures specifically:

```bash
python paper/make_figures.py
```

which reads `reports/comparison.csv` and `reports/sensitivity.csv` and writes all
four figures to `paper/figures/` as both PNG and PDF.

## Sections

1. **Introduction** — the problem, and why an exact baseline is missing from the
   literature.
2. **Related Work** — simulation-coupled evolutionary therapy design
   (Castiglione, Golpayegani, Neri), resistance-guided regimen selection (Liu &
   Shafer, Haupts, Harrigan, IAS-USA), and how prior work has been evaluated.
3. **Methods** — problem formulation, clinical constraints, the formulary tier
   model, the fitness function, the salvage protocol, and both search strategies.
4. **Results** — search-space characterisation, the genetic algorithm against
   exhaustive search, four failure modes, the salvage subgroup, weight
   sensitivity, and the effect of sourced versus unsourced cost data.
5. **Discussion** — when a metaheuristic is warranted, sequencing as the
   appropriate formulation, and limitations.
6. **Ethics, safety and governance** — data governance, safety validation,
   residual risk, human oversight, and the regulatory pathway.

## Known limitations

Stated in full in Section 5.4 of the paper. In summary: the cohort is 15/17
synthetic; per-drug efficacy, toxicity and the resistance penalties are
unsourced; two derived resistance penalties exceed published Stanford class
maxima; and the model represents a single decision rather than a sequence of
therapy lines.

`python check_provenance.py` reports the current status of every model parameter.
