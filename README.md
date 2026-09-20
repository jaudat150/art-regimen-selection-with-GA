# Formulary-constrained antiretroviral regimen selection

[![Paper](https://zenodo.org/badge/DOI/10.5281/zenodo.22844539.svg)](https://doi.org/10.5281/zenodo.22844539)
[![Code](https://zenodo.org/badge/DOI/10.5281/zenodo.22809521.svg)](https://doi.org/10.5281/zenodo.22809521)

Code and data for *Exhaustive search outperforms a genetic algorithm for
formulary-constrained antiretroviral regimen selection*
([preprint](https://doi.org/10.5281/zenodo.22844539) ·
[PDF](paper/al-husein-2026-art-regimen-selection.pdf)).

We formulate WHO-compliant first-line HIV regimen selection as constrained
combinatorial optimisation, then compare a genetic algorithm against exhaustive
search over a provably identical feasible set.

**The genetic algorithm offers no advantage.** It reaches the exact optimum for
all 17 patients while performing 166× as many fitness evaluations — and for 14 of
them the optimum was
already in its random starting population, so evolution contributed nothing.

## Run it

```bash
pip install -r requirements.txt
python verify.py
```

`verify.py` runs everything and checks all 31 numbers reported in the paper.
Exit code 0 means the code and the paper agree. About 90 seconds.

| command | what it does |
|---|---|
| `run_comparison.py` | genetic algorithm vs exhaustive search |
| `run_sensitivity.py` | objective-weight sensitivity |
| `run_robustness.py` | re-run under trial-consistent parameters |
| `check_provenance.py` | which parameters are sourced, and which are not |
| `tests/test_search.py` | 14 correctness tests |
| `main.py --visualize` | patient reports and figures |

Python 3.9+, numpy, pandas, openpyxl, matplotlib. Nothing else.

## Results

| | |
|---|---|
| Feasible regimens per patient | 2–130 (613 across the cohort) |
| GA reaches the exact optimum | 17/17, seeds 1, 9, 42 |
| Evaluations: GA vs exhaustive | 102,000 vs 613 (166×) |
| Optimum already in the initial population | 14/17 |
| Recommendations changed by reweighting | up to 59% |

A regimen is a fixed three-slot object, so the space grows as O(n²m) — exhaustive
search stays sub-second at 25× today's drug catalogue. Sequencing across L lines
of therapy grows as O((n²m)^L) and breaks between the third and fourth line. That
is where evolutionary search for this problem belongs.

Both strategies live in `ga/genetic_algorithm.py` — `run()` and
`run_exhaustive()` — drawing candidates from the same enumeration, so the only
difference between them is search behaviour. Asserted by test, not assumed.

## Provenance

**The cohort is synthetic** (15 of 17 profiles; 2 from published case reports).
No real patient data, and no clinical claim is supported by this work.

**Not every parameter is sourced.** Costs are, from Global Fund procurement data.
Efficacy and toxicity are audited against trial evidence, with four values flagged
as overstated. Resistance penalties are derived, not taken from Stanford's
published tables, and two exceed published class maxima. Run
`check_provenance.py`.

This matters: an unsourced cost table produced a coherent and completely wrong
clinical conclusion here, in a system whose search logic was already verified by
an exact baseline and a passing test suite. `CHANGES.md` has the story.

**Not for clinical use.** A methodological study, not a medical device.

## Authors

- **Eng. Jaudat Faisal Al-Husein** — [@Jaudat150](https://github.com/Jaudat150)
- **Eng. Omar Ali Al-Khayat** — [@Alkhayat2003](https://github.com/Alkhayat2003)
- **Eng. Yasser Almofaalani** — supervisor, third author on the paper

Antioch Private University, Rural Damascus, Syria.
This repository is authored by the first two; all three are authors of the paper.

## Citation

Cite the paper:

```bibtex
@misc{alhusein2026art,
  title     = {Exhaustive Search Outperforms a Genetic Algorithm for
               Formulary-Constrained Antiretroviral Regimen Selection},
  author    = {Al-Husein, Jaudat Faisal and Al-Khayat, Omar Ali and
               Almofaalani, Yasser},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22844539},
  url       = {https://doi.org/10.5281/zenodo.22844539},
  note      = {Preprint}
}
```

Cite the code:

```bibtex
@software{alhusein2026artcode,
  title     = {Exhaustive Search Outperforms a Genetic Algorithm for
               Formulary-Constrained Antiretroviral Regimen Selection},
  author    = {Al-Husein, Jaudat Faisal and Al-Khayat, Omar Ali},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22809521},
  url       = {https://doi.org/10.5281/zenodo.22809521}
}
```

## License

MIT — see [LICENSE](LICENSE).
