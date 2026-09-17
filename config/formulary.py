"""
Access-constraint formulary tiers.

WHY THIS EXISTS
---------------
The original synthetic cohort assigned each patient an ad-hoc Access_Constraints
list of 3-4 drugs. That collapsed the candidate space to 0-2 valid regimens per
patient (153 across the whole 17-patient cohort), which removed the optimisation
problem entirely and made two patients untreatable. It was also unciteable: a
reviewer asking "why these four drugs?" had no answer.

This module replaces per-patient hand-picked lists with three service-delivery
tiers drawn from published guidance. Each tier is a claim you can defend and
cite, and the tier assignment -- not the drug list -- becomes the modelled
variable.

SOURCES
-------
[1] WHO. Consolidated guidelines on HIV prevention, testing, treatment, service
    delivery and monitoring: recommendations for a public health approach.
    First-, second- and third-line ART regimen tables for adults and adolescents.
    https://www.ncbi.nlm.nih.gov/books/NBK572730/
[2] WHO. Updated recommendations on first-line and second-line antiretroviral
    regimens (WHO-CDS-HIV-18.51). TDF + 3TC (or FTC) + DTG as preferred
    first-line; EFV as alternative.
    https://www.who.int/publications/i/item/WHO-CDS-HIV-18.51
[3] WHO. The selection and use of essential medicines, 2025: WHO Model List of
    Essential Medicines, 24th list. Antiretrovirals section.
    https://www.who.int/publications/i/item/B09474
[4] WHO second-line table: TDF-based first-line sequences to AZT + 3TC + DTG;
    PI-based first-line sequences to AZT + 3TC + DTG. DRV/r and RAL are listed
    alternatives to LPV/r.  https://tbksp.who.int/en/node/2778
[5] UNAIDS. Global AIDS Update 2024, Middle East and North Africa regional
    profile -- Global Fund support replenishes ARV stocks in conflict-affected
    states including the Syrian Arab Republic.
    https://www.unaids.org/sites/default/files/media_asset/2024-unaids-global-aids-update-mena_en.pdf

TIER RATIONALE
--------------
TIER_1_PUBLIC   National-programme core. WHO-preferred first- and second-line
                agents plus the boosted PIs that WHO lists for second-line [1,2,4].
                This is what a Global-Fund-supplied public ART clinic in a
                low-prevalence, resource-constrained setting can be expected to
                stock [5].

TIER_2_REGIONAL Adds WHO alternative and special-circumstance agents: TAF
                (recommended for adults with impaired renal function or
                established osteoporosis [2]), DRV/r and RAL (WHO second-line
                alternatives [4]), and DOR. A referral centre with a wider
                formulary.

TIER_3_FULL     Entire catalogue, including salvage agents (ibalizumab,
                fostemsavir, maraviroc) that in practice require named-patient
                import. Represents a well-resourced tertiary centre and gives
                the upper bound on search-space size.

Note that the tiers are nested: TIER_1 is a subset of TIER_2 is a subset of
TIER_3. This matters for the sequencing work -- a patient's tier bounds every
line of therapy available to them, not just the first.
"""

# WHO-preferred and WHO-alternative agents stocked by a national ART programme.
TIER_1_PUBLIC = [
    # NRTI backbone options -- WHO first- and second-line [1,2,4]
    'TDF', '3TC', 'FTC', 'AZT', 'ABC',
    # Third agents
    'DTG',              # WHO-preferred first- and second-line INSTI [2]
    'EFV', 'NVP',       # NNRTI alternatives [1,2]
    'LPV/r', 'ATV/r',   # boosted PIs, WHO second-line [4]
]

# Referral centre: adds WHO alternatives and special-circumstance agents.
TIER_2_REGIONAL = TIER_1_PUBLIC + [
    'TAF',              # renal impairment / osteoporosis [2]
    'DRV/r',            # WHO second-line PI alternative [4]
    'RAL',              # WHO second-line INSTI alternative [4]
    'DOR',              # newer NNRTI
]

# Tertiary / research centre: full catalogue including salvage agents.
TIER_3_FULL = TIER_2_REGIONAL + [
    'RPV', 'EVG', 'BIC',
    'Maraviroc', 'Ibalizumab', 'FTR',
]

FORMULARY_TIERS = {
    'TIER_1_PUBLIC': TIER_1_PUBLIC,
    'TIER_2_REGIONAL': TIER_2_REGIONAL,
    'TIER_3_FULL': TIER_3_FULL,
}

# Cohort composition. Most people in a resource-constrained national programme
# are managed at public clinics; a minority reach referral or tertiary centres.
# State this proportion explicitly in the paper -- it is an assumption, not data.
TIER_DISTRIBUTION = {
    'TIER_1_PUBLIC': 0.65,
    'TIER_2_REGIONAL': 0.25,
    'TIER_3_FULL': 0.10,
}


def get_formulary(tier_name):
    """Drug list for a named tier."""
    if tier_name not in FORMULARY_TIERS:
        raise ValueError(
            f"Unknown formulary tier {tier_name!r}. "
            f"Expected one of {sorted(FORMULARY_TIERS)}"
        )
    return list(FORMULARY_TIERS[tier_name])
