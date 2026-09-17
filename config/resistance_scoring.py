"""
Genotypic susceptibility scoring, aligned to the Stanford HIVdb algorithm.

WHY THIS EXISTS
---------------
`get_efficacy_with_resistance()` documented its resistance values as coming
"from Stanford HIVDB". They do not. The Resistance sheet holds fractional
efficacy reductions (M184V -> 0.90 against 3TC), whereas Stanford HIVdb assigns
integer PENALTY SCORES per drug-mutation pair, sums them across a sequence, and
maps the total onto five susceptibility bands. The two are different quantities
and the source attribution was wrong.

That matters more than the arithmetic: an unsourced cost table already produced a
coherent and completely wrong clinical conclusion in this project (Section 4.7).
A resistance model carrying a false attribution is the same failure waiting to
happen, and harder to catch because the citation makes it look checked.

THE STANDARD  (VERIFIED)
------------------------
Stanford HIVdb sums penalty scores for all resistance mutations present, then
maps the total to a resistance category. The banding below is confirmed by
Stanford's own point-of-care document [POC] and independently by Beauparlant et
al. [BEAUPARLANT]; the corresponding genotypic susceptibility scores are the
mapping specified in the GEMINI-1 and GEMINI-2 statistical analysis plans
[GEMINI]. Current algorithm version at time of writing: HIVdb 10.2, released
2026-04-26.

    resistance estimate    GSS     interpretation
    0  - 9                 1.00    susceptible
    10 - 14                0.75    potential low-level resistance
    15 - 29                0.50    low-level resistance
    30 - 59                0.25    intermediate resistance
    >= 60                  0.00    high-level resistance

Published per-mutation penalty scores live at:
    NRTI   https://hivdb.stanford.edu/dr-summary/mut-scores/NRTI/
    NNRTI  https://hivdb.stanford.edu/dr-summary/mut-scores/NNRTI/
    PI     https://hivdb.stanford.edu/dr-summary/mut-scores/PI/
    INSTI  https://hivdb.stanford.edu/dr-summary/mut-scores/INSTI/

STATUS OF THE SCORES IN THIS FILE  ***READ THIS***
--------------------------------------------------
The band mapping above is VERIFIED. The per-mutation penalty scores are NOT.

The four mutation-score pages are JavaScript applications and do not serve their
tables to a plain HTTP fetch, so the current per-drug integers could not be
retrieved that way. The machine-readable source is the ASI2 algorithm XML in
Stanford's own repository:

    https://github.com/hivdb/hivfacts   ->   data/algorithms/HIVDB_10.2.xml

Each <DRUG> element carries per-mutation `SCORE FROM(...)` rules, and
<COMMENT_DEFINITIONS> carries the level cutoffs. The same XML is mirrored in
PoonLab/sierra-local under sierralocal/data/. Either gives exact, citable,
per-drug integers for the current version.

PUBLISHED ANCHOR VALUES (verified, but NOT per-drug and NOT current)
--------------------------------------------------------------------
CLASS_MAXIMUM_SCORES_V7 below is taken from Stanford's point-of-care document
[POC], Tables 1-3. Two limitations make these an anchor rather than a
substitute:

  1. They are HIVdb version 7.0, not the current 10.2.
  2. Each is the HIGHEST penalty for that mutation ACROSS THE DRUGS IN ITS CLASS,
     not the per-drug value. M184V scoring 60 means 60 against the worst-affected
     drug in the NRTI class (3TC/FTC), not 60 against every NRTI.

They are recorded because they let you check that any table you build is
consistent with published values at the class level, and because the POC
document contains no INSTI table at all -- so dolutegravir, raltegravir,
elvitegravir and bictegravir have no anchor here and must come from the XML.

The values actually used by the model remain DERIVED from the project's
pre-existing fractional reductions, by inverting the band table. That makes the
model structurally correct and every value checkable, but it does not make the
values sourced. `unverified_mutations()` lists everything still tagged DERIVED.

SOURCES
-------
[GEMINI] Statistical analysis plan, GEMINI-1/GEMINI-2 (NCT02831673, NCT02831764).
         Stanford Genotypic Susceptibility Score banding.
         https://cdn.clinicaltrials.gov/large-docs/64/NCT02831764/SAP_002.pdf
[HIVDB]  Liu TF, Shafer RW. Web resources for HIV type 1 genotypic-resistance
         test interpretation. Clin Infect Dis 2006;42:1608-1618.
         doi:10.1086/503914. The canonical citation for the algorithm.
[POC]    Rhee SY et al. (Shafer group). HIV-1 Drug Resistance Mutations:
         Potential Applications for Point-of-Care Genotypic Resistance Testing,
         Tables 1-3. Scores are HIVdb v7.0 class maxima.
         https://hivdb.stanford.edu/download/POC/POC_DRMs.pdf
[BEAUPARLANT] Beauparlant et al. Impact of changes over time in the Stanford
         University genotypic resistance interpretation algorithm.
         https://pmc.ncbi.nlm.nih.gov/articles/PMC6241513/
[HIVFACTS] Stanford HIVdb ASI2 algorithm XML, data/algorithms/.
         https://github.com/hivdb/hivfacts
"""

# Verified from [POC], HIVdb v7.0. CLASS MAXIMA, not per-drug. No INSTI table
# exists in that document, so INSTI mutations are absent by necessity.
CLASS_MAXIMUM_SCORES_V7 = {
    'NRTI':  {'M184V': 60, 'K65R': 60, 'Q151M': 60, 'T215Y': 45,
              'K70R': 30, 'L74V': 30, 'M41L': 15, 'D67N': 15},
    'NNRTI': {'K103N': 60, 'Y181C': 60, 'G190A': 60, 'V106M': 60,
              'Y188L': 60, 'E138K': 30},
    'PI':    {'I84V': 60, 'I47A': 60, 'I50V': 30, 'V82A': 30, 'L76V': 30,
              'L90M': 25, 'M46I': 15, 'I54V': 15},
}

HIVDB_VERSION = '10.2'
HIVDB_VERSION_DATE = '2026-04-26'
HIVDB_XML_SOURCE = ('https://github.com/hivdb/hivfacts '
                    '-> data/algorithms/HIVDB_10.2.xml')

# Sourced: GEMINI SAP banding. (upper_bound_inclusive, gss, label)
GSS_BANDS = [
    (9,             1.00, 'susceptible'),
    (14,            0.75, 'potential low-level resistance'),
    (29,            0.50, 'low-level resistance'),
    (59,            0.25, 'intermediate resistance'),
    (float('inf'),  0.00, 'high-level resistance'),
]

# Representative penalty score for each band, used when deriving scores from
# legacy fractional reductions. Midpoints, except the open-ended top band.
_BAND_REPRESENTATIVE = {1.00: 0, 0.75: 12, 0.50: 22, 0.25: 45, 0.00: 60}


def gss_from_score(total_penalty):
    """Map a summed Stanford penalty score to (gss, label). Sourced: [GEMINI]."""
    for upper, gss, label in GSS_BANDS:
        if total_penalty <= upper:
            return gss, label
    return 0.0, 'high-level resistance'


def _score_from_legacy_reduction(reduction):
    """
    Invert a legacy fractional efficacy reduction into a representative penalty
    score. DERIVED, not sourced -- see the module docstring.
    """
    if reduction >= 0.85:
        return _BAND_REPRESENTATIVE[0.00]
    if reduction >= 0.55:
        return _BAND_REPRESENTATIVE[0.25]
    if reduction >= 0.25:
        return _BAND_REPRESENTATIVE[0.50]
    if reduction > 0.0:
        return _BAND_REPRESENTATIVE[0.75]
    return 0


def build_penalty_table(resistance_rows):
    """
    Build {(mutation, drug): (penalty, provenance_tag)} from the Resistance sheet.

    Every entry is tagged DERIVED until replaced with a published Stanford score.
    """
    table = {}
    for mutation, drug, reduction in resistance_rows:
        table[(mutation, drug)] = (_score_from_legacy_reduction(float(reduction)),
                                   'DERIVED')
    return table


def susceptibility(drug, mutations, penalty_table):
    """
    Genotypic susceptibility score for one drug given a patient's mutations.

    Penalties are summed across mutations and mapped through the sourced band
    table, following the HIVdb algorithm. Returns (gss, label, total_penalty).
    """
    total = sum(penalty_table.get((m, drug), (0, None))[0] for m in mutations)
    gss, label = gss_from_score(total)
    return gss, label, total


def unverified_mutations(penalty_table):
    """Drug-mutation pairs whose penalty is derived rather than published."""
    return sorted(k for k, (_s, tag) in penalty_table.items() if tag == 'DERIVED')


def class_maximum(mutation):
    """
    Published HIVdb v7.0 class-maximum penalty for a mutation, or None.

    Verified from [POC]. Use to sanity-check a per-drug table against published
    values: no per-drug score should exceed its class maximum.
    """
    for scores in CLASS_MAXIMUM_SCORES_V7.values():
        if mutation in scores:
            return scores[mutation]
    return None


def check_against_published(penalty_table):
    """
    Flag derived scores that exceed the published class maximum for their
    mutation. A non-empty result means the derived table is inconsistent with
    published HIVdb values and should not be used.
    """
    bad = []
    for (mutation, drug), (score, _tag) in penalty_table.items():
        cap = class_maximum(mutation)
        if cap is not None and score > cap:
            bad.append((mutation, drug, score, cap))
    return sorted(bad)
