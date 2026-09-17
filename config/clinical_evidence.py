"""
Clinical trial evidence for the efficacy and toxicity parameters.

WHY THIS EXISTS
---------------
The Efficacy, Toxicity, Liver_Impact and Kidney_Impact columns of drugs.xlsx
carried no recorded source. After an unsourced cost table produced a coherent and
entirely wrong clinical conclusion (Section 4.7), leaving three more unsourced
parameter families unexamined was not defensible.

WHAT CAN AND CANNOT BE SOURCED
------------------------------
A per-drug "efficacy" value has no direct empirical referent. Virologic
suppression is measured for REGIMENS, not for individual agents: no trial reports
"the efficacy of dolutegravir" as a number, because dolutegravir is never given
alone. The per-drug column is therefore a modelling abstraction, and no amount of
literature search will source it directly.

What CAN be sourced, and is recorded below:

  1. Regimen-level virologic suppression rates from trials and real-world cohorts,
     which bound what any per-drug decomposition must reproduce in aggregate.
  2. The relative ORDERING of toxicity between agents, which trials do establish
     directly (TDF vs TAF for renal and bone; DTG vs EFV for weight and
     neuropsychiatric effects; NVP hepatotoxicity).

So each entry below is tagged:
  SOURCED     - the value or ordering is supported by the cited evidence
  DIRECTION   - the cited evidence supports the direction of the difference but
                not the magnitude used in the model
  UNSOURCED   - no evidence located; the value is a modelling choice

WHAT THIS AUDIT FOUND
---------------------
The shipped efficacy column overstates the dolutegravir-efavirenz gap. It carries
DTG 0.98 against EFV 0.85, a 13-point difference. The trial evidence is that
dolutegravir is NON-INFERIOR to efavirenz 400 mg, not substantially superior:
NAMSAL found similar week-96 outcomes, and a South African cohort of 9,657
patients found 12-month viral suppression of 78.9% on TLD against 78.8% on TEE.
The toxicity gap is similarly overstated: NAMSAL reported comparable serious
adverse event rates (9% DTG vs 7% EFV 400 mg).

`run_robustness.py` re-runs the cohort with trial-consistent values and reports
the effect on recommendations. Under the shipped values dolutegravir anchors
17/17 recommendations; under trial-consistent values, 14/17. The direction of the
Section 4.7 finding survives, its magnitude does not.

SOURCES
-------
[NAMSAL]   NAMSAL ANRS 12313 Study Group. Dolutegravir-based and low-dose
           efavirenz-based regimen for the initial treatment of HIV-1 infection:
           week 96 results from a two-group, multicentre, randomised, open-label,
           phase 3 non-inferiority trial in Cameroon. Lancet HIV, 2020.
           n=613. Serious AEs 28/310 (9%) DTG vs 21/303 (7%) EFV400. Median
           weight gain 5.0 kg vs 3.0 kg (p<0.001); obesity 22% vs 16% (p=0.043).
           https://pubmed.ncbi.nlm.nih.gov/33010241/
[TLDCOHORT] Clinical outcomes after viraemia among people receiving dolutegravir
           vs efavirenz-based first-line ART in South Africa. n=9,657.
           12-month viral suppression 78.9% (TLD) vs 78.8% (TEE); retention
           84.9% vs 80.8%.
           https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10691652/
[TAFPOOL]  Renal safety of tenofovir alafenamide vs tenofovir disoproxil
           fumarate: pooled analysis of 26 clinical trials, >12,500 person-years.
           Significantly fewer renal adverse event discontinuations on TAF
           (p<0.001); more favourable renal biomarkers through 96 weeks.
           https://pmc.ncbi.nlm.nih.gov/articles/PMC6635043/
[TAFMETA]  Tenofovir alafenamide vs tenofovir disoproxil fumarate: updated
           meta-analysis of 14,894 patients across 14 trials. No differences on
           main safety endpoints when unboosted; boosted TDF associated with
           higher renal discontinuation risk (p=0.03) and more bone fractures
           (p=0.04).
           https://pubmed.ncbi.nlm.nih.gov/33048869/
"""

# (drug, parameter): (tag, note)
PARAMETER_PROVENANCE = {
    # --- tenofovir prodrugs: renal and bone ordering is directly established ----
    ('TDF', 'Kidney_Impact'): ('DIRECTION', 'TAFPOOL, TAFMETA: TDF > TAF for renal adverse events and discontinuation; magnitude (0.60 vs 0.10) is a modelling choice'),
    ('TAF', 'Kidney_Impact'): ('DIRECTION', 'TAFPOOL: more favourable renal biomarkers than TDF through 96 weeks'),
    ('TDF', 'Side_Effects'):  ('SOURCED',   'TAFMETA: bone fractures higher on boosted TDF (p=0.04); renal and bone_loss both correctly listed'),

    # --- dolutegravir vs efavirenz: model OVERSTATES the gap -------------------
    ('DTG', 'Efficacy'): ('UNSOURCED', 'OVERSTATED: model carries 0.98 vs EFV 0.85; NAMSAL and TLDCOHORT show non-inferiority, not superiority (78.9% vs 78.8% suppression)'),
    ('EFV', 'Efficacy'): ('UNSOURCED', 'OVERSTATED gap: see DTG entry'),
    ('DTG', 'Toxicity'): ('UNSOURCED', 'OVERSTATED gap: NAMSAL serious AEs 9% DTG vs 7% EFV400 -- comparable, not 0.25 vs 0.45'),
    ('EFV', 'Toxicity'): ('UNSOURCED', 'OVERSTATED gap: see DTG entry'),
    ('DTG', 'Side_Effects'): ('SOURCED', 'NAMSAL: weight gain 5.0 kg vs 3.0 kg (p<0.001), obesity 22% vs 16%; weight_gain correctly listed'),
    ('EFV', 'Side_Effects'): ('SOURCED', 'neuropsychiatric effects (dizziness, abnormal dreams) are the established EFV signature'),

    # --- established single-agent signatures ------------------------------------
    ('NVP', 'Liver_Impact'):  ('DIRECTION', 'hepatotoxicity is the established nevirapine signature; highest liver value in the table is the right ordering'),
    ('ABC', 'Side_Effects'):  ('SOURCED',   'hypersensitivity, HLA-B*5701-linked; handled as a hard constraint (config/clinical_rules.py)'),
    ('AZT', 'Side_Effects'):  ('SOURCED',   'anaemia is the established zidovudine signature'),
    ('LPV/r', 'Side_Effects'):('SOURCED',   'GI intolerance and lipodystrophy are established boosted-PI effects'),
}

# Regimen-level benchmarks the model should reproduce in aggregate.
REGIMEN_SUPPRESSION = {
    ('TDF', '3TC', 'DTG'): (0.789, 'TLDCOHORT', '12-month viral suppression, South African cohort, n=9657'),
    ('TDF', '3TC', 'EFV'): (0.788, 'TLDCOHORT', '12-month viral suppression, same cohort; statistically indistinguishable from TLD'),
}

# Values consistent with the trial evidence, used by run_robustness.py.
# DTG and EFV are set close together to reflect demonstrated non-inferiority.
TRIAL_CONSISTENT_OVERRIDES = {
    'DTG': {'Efficacy': 0.91, 'Toxicity': 0.28},
    'EFV': {'Efficacy': 0.90, 'Toxicity': 0.33},
}


def unsourced_parameters():
    """Drug-parameter pairs with no supporting evidence located."""
    return sorted(k for k, (tag, _n) in PARAMETER_PROVENANCE.items()
                  if tag == 'UNSOURCED')


def overstated_parameters():
    """Parameters the audit found inconsistent with the cited evidence."""
    return sorted(k for k, (_t, n) in PARAMETER_PROVENANCE.items()
                  if 'OVERSTATED' in n)
