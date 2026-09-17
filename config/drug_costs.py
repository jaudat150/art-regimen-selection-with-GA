"""
Antiretroviral cost data with per-figure provenance.

WHY THIS EXISTS
---------------
The original drugs.xlsx carried monthly costs with no recorded source. Checked
against published procurement prices they were roughly an order of magnitude too
high for the low- and middle-income public-sector setting this work models: the
table priced TDF + 3TC + DTG at US$546 per person-year, against a Global Fund
Pooled Procurement Mechanism reference of under US$45 for the same fixed-dose
combination. Dolutegravir was the most distorted entry, at US$420 per
person-year.

That mattered beyond tidiness. The cost term is the most influential weight in
the objective (Section 4.6), and the divergence from WHO first-line guidance
reported in Section 4.7 was driven substantially by dolutegravir's price
relative to efavirenz. A result that turns on an unsourced number is not a
result.

Every figure below is annotated with its source and year. Where no published
LMIC price was found, the entry is marked ESTIMATE and must be treated as such.

UNITS
-----
All prices are US dollars per person-year (PPPY), the unit in which
antiretroviral procurement is reported. The loader converts to monthly.

KNOWN LIMITATION — FIXED-DOSE COMBINATIONS ARE SUB-ADDITIVE
-----------------------------------------------------------
Antiretrovirals are largely procured as fixed-dose combinations, and FDC prices
are below the sum of their components: TDF, 3TC and DTG priced individually at
2016 global-lowest figures exceed the current TLD FDC price. This model costs
regimens additively from per-drug prices, which therefore OVERESTIMATES the true
procurement cost of any regimen available as an FDC — disproportionately the
WHO-preferred ones, since those are the combinations manufactured as FDCs.

For the three TLD components we allocate the published FDC ceiling price across
the components rather than using independent per-drug prices. This is an
allocation, not an observation, and is marked as such. A regimen-level cost
model would be the correct fix and is noted in the limitations.

SOURCES
-------
[GF2023]  The Global Fund. Global Fund agreements substantially reduce the price
          of first-line HIV treatment to below US$45 a year. 30 August 2023.
          https://www.theglobalfund.org/en/news/2023/2023-08-30-global-fund-agreements-substantially-reduce-price-first-line-hiv-treatment-below-usd45-a-year
[HILL2016] Hill A. et al. Antiretroviral price table, "Global lowest" column.
          J Virus Erad. https://pmc.ncbi.nlm.nih.gov/articles/PMC5075345/table/jve4-tbl-0001
[DEVEX2021] Pricing agreement brings HIV drug darunavir within reach of LMICs.
          Devex, 2021. DRV/r at US$210 PPPY for PEPFAR/Global Fund purchasers.
          https://www.devex.com/news/pricing-agreement-brings-hiv-drug-darunavir-within-reach-of-lmics-100478
"""

# drug: (PPPY_usd, source_tag, note)
ARV_PRICES_PPPY = {
    # --- TLD components: allocation of the GF2023 FDC ceiling of US$45 PPPY ---
    'TDF':   (15.0, 'GF2023',  'ALLOCATED from TLD FDC ceiling <$45 PPPY; not an independent per-drug price'),
    '3TC':   (10.0, 'GF2023',  'ALLOCATED from TLD FDC ceiling <$45 PPPY; not an independent per-drug price'),
    'DTG':   (20.0, 'GF2023',  'ALLOCATED from TLD FDC ceiling <$45 PPPY; not an independent per-drug price'),

    # --- published global-lowest generic prices --------------------------------
    'ABC':   (123.0, 'HILL2016', 'global lowest, 2016'),
    'AZT':   (46.0,  'HILL2016', 'listed as AZT/3TC combination; overestimates AZT alone'),
    'FTC':   (10.0,  'HILL2016', 'ESTIMATE: no standalone figure; priced as 3TC, its interchangeable analogue'),
    'EFV':   (38.0,  'HILL2016', 'global lowest, 2016'),
    'NVP':   (28.0,  'HILL2016', 'global lowest, 2016'),
    'RPV':   (40.0,  'HILL2016', 'global lowest, 2016'),
    'ATV/r': (219.0, 'HILL2016', 'global lowest, 2016'),
    'LPV/r': (243.0, 'HILL2016', 'global lowest, 2016'),
    'RAL':   (973.0, 'HILL2016', 'global lowest, 2016; pre-generic'),

    # --- later pricing agreement ----------------------------------------------
    'DRV/r': (210.0, 'DEVEX2021', 'PEPFAR/Global Fund pricing agreement, 2021'),

    # --- no published LMIC generic price located: ESTIMATES ---------------------
    'TAF':   (660.0, 'ESTIMATE', 'no LMIC generic price located; originator-tier placeholder'),
    'DOR':   (240.0, 'ESTIMATE', 'no LMIC generic price located; originator-tier placeholder'),
    'EVG':   (480.0, 'ESTIMATE', 'no LMIC generic price located; originator-tier placeholder'),
    'BIC':   (780.0, 'ESTIMATE', 'no LMIC generic price located; originator-tier placeholder'),
    'Maraviroc':  (1440.0, 'ESTIMATE', 'salvage agent; originator-tier placeholder'),
    'FTR':        (720.0,  'ESTIMATE', 'salvage agent; originator-tier placeholder'),
    'Ibalizumab': (24000.0, 'ESTIMATE', 'salvage agent; originator-tier placeholder'),
}


def monthly_cost(drug):
    """Monthly cost in USD, or None if the drug is not in the table."""
    entry = ARV_PRICES_PPPY.get(drug)
    return round(entry[0] / 12.0, 2) if entry else None


def unsourced_drugs():
    """Drugs whose price is an estimate rather than a published figure."""
    return sorted(d for d, (_, src, _n) in ARV_PRICES_PPPY.items() if src == 'ESTIMATE')


def provenance_table():
    """Rows of (drug, PPPY, monthly, source, note) for reporting in the paper."""
    return [
        (d, p, round(p / 12.0, 2), src, note)
        for d, (p, src, note) in sorted(ARV_PRICES_PPPY.items())
    ]
