# Ethics, Safety and Declarations

*Paste-ready. Addresses the reviewer comments on data governance, safety
validation, liability and regulatory pathway, plus the declarations journals
require. Section numbering assumes this follows Discussion.*

---

## 6. Ethics, safety and governance

A regimen optimiser is a clinical decision support system, and the question of
what happens when it is wrong is not separable from the question of whether it
works. This section sets out what the system does to constrain unsafe output,
what it cannot do, and what would be required before any deployment.

### 6.1 Data governance

No identifiable patient data was used in this study. Fifteen of seventeen
profiles are synthetic, generated to span clinically meaningful variation in
resistance, organ function and comorbidity. The remaining two are encoded from
case descriptions already published in the peer-reviewed literature, and contain
no information that could identify an individual.

Consequently no ethics committee approval, informed consent process or
data-protection impact assessment was required for the work as conducted. We
state this plainly because it is also a limitation: a study that requires no
governance is a study that has not touched real patients, and the results in
Sections 4.2–4.7 are correspondingly untested against real-world variation.

Any extension to real cohorts changes this entirely. It would require ethics
approval, a lawful basis for processing under the applicable regime — GDPR
Article 9 for special-category health data in European jurisdictions, HIPAA in
the United States, and the relevant national framework elsewhere — a data
protection impact assessment, and a data-sharing agreement with the holding
institution. Resistance genotypes are among the most sensitive categories of
health data, being simultaneously clinical information and, through the viral
sequence's linkage to transmission networks, potentially disclosive of
relationships. They warrant handling accordingly.

### 6.2 Safety validation

The question of how a search procedure is prevented from returning a harmful
combination has a specific answer in this architecture: harmful combinations are
never generated, rather than generated and then filtered.

All candidate regimens are produced by a single enumeration routine
(`enumerate_valid_regimens`) that applies, before any fitness is computed:

1. **Structural validity** — two NRTIs plus one third agent, per WHO guidance.
2. **Patient-specific contraindication** — drugs excluded by comorbidity,
   hepatic or renal function, pregnancy status or documented allergy.
3. **Backbone non-redundancy** — clinically redundant NRTI pairs excluded
   (Section 3.2).
4. **Pharmacogenetic prerequisite** — HLA-B\*5701-positive patients cannot
   receive abacavir; where status is unknown, the requirement is reported rather
   than silently ignored.
5. **Formulary availability** — drugs outside the patient's formulary tier.

The genetic algorithm's mutation and crossover operators are constrained to this
same enumerated set and repair any offspring back into it, so the search cannot
reach an invalid regimen even transiently. This is asserted by test —
`test_ga_output_is_always_inside_the_enumerated_space` — rather than assumed.

The enumeration itself is verified against an independently written exhaustive
triple loop for every patient (`test_enumeration_matches_independent_brute_force`),
so the claim that the constraint layer is complete does not rest on inspection of
the code that implements it. The full suite is fourteen tests; all pass, and a
single `verify.py` entry point reproduces every number reported in this paper.

We emphasise what this does *not* establish. The constraint layer is only as good
as the clinical rules encoded in it, and those rules are our transcription of
published guidance, not a validated implementation of it. A missing
contraindication is invisible to a test suite that checks the rules it was given.

### 6.3 Residual risk and the limits of the objective

Three residual risks are worth naming explicitly.

**Parameter provenance.** As reported in Section 4.7, an unsourced cost table
produced a coherent, plausible and entirely wrong clinical conclusion in a system
whose search logic was by then verified by both an exact baseline and a passing
test suite. Correctness of the optimiser is not correctness of the
recommendation. Efficacy, toxicity and resistance penalties remain unsourced
(Section 5.4); `check_provenance.py` reports their status.

**Weight dependence.** Section 4.6 shows that recommendations change for up to
59% of the cohort under modest reweighting. The weights encode a health-economic
judgement — how much toxicity is worth how much cost — that properly belongs to a
clinician or a national programme, not to the authors of an algorithm. Any
deployment should elicit weights from the responsible clinical authority and
report the sensitivity alongside each recommendation.

**Single decision point.** The model recommends one regimen and does not
represent switching on virologic failure or the forward cost of exhausting a drug
class (Section 5.2).

### 6.4 Human oversight and liability

We take the position that a system of this kind should not operate autonomously,
and our implementation does not support autonomous operation: it produces a
ranked recommendation with its constituent objective terms, constraint
justifications and screening prerequisites exposed, for a clinician to accept,
reject or modify. Prescribing authority and clinical responsibility remain with
the treating clinician throughout. The system's output is an input to a decision,
not a decision.

This is a design commitment rather than a claim of validation. We have not
conducted a human-factors study, and the well-documented risk of automation bias
— that a displayed recommendation anchors a clinician's judgement even when
wrong — applies here and is not mitigated by the interface as built. Given
Section 4.7, where a plausible-looking recommendation was wrong for a reason
invisible at the point of use, this risk should be taken seriously rather than
assumed away.

### 6.5 Regulatory pathway

Software intended to inform clinical treatment selection falls within Software as
a Medical Device as defined by the International Medical Device Regulators Forum,
and would be regulated as such in most jurisdictions — under the EU Medical
Device Regulation in Europe, and by FDA under the clinical-decision-support
provisions of the 21st Century Cures Act in the United States. Because the
recommendation concerns treatment selection and the clinician cannot in practice
independently reconstruct the weighted objective that produced it, we would not
expect this system to fall within the Cures Act exemption for decision support
whose basis is independently reviewable.

We make no claim that the present work constitutes a regulated device or is ready
for clinical use. It is a methodological study on largely synthetic data. A
deployment pathway would require, at minimum: sourced parameters throughout;
prospective validation against real cohorts with clinician-adjudicated outcomes;
a quality management system; and clinical evaluation under the applicable
framework. We state this to delimit the claim, not to gesture at future work.

---

## Declarations

**Ethics approval and consent to participate.** Not applicable. This study used
synthetic patient profiles and two profiles encoded from previously published,
de-identified case descriptions. No human participants, human data or human
tissue were involved.

**Consent for publication.** Not applicable.

**Availability of data and materials.** All code, data and analysis scripts are
available at https://github.com/Jaudat150/art-regimen-selection-with-GA. Every
figure, table and numerical result in this paper is reproduced by
`python verify.py`.

**Competing interests.** The authors declare that they have no competing
interests.

**Funding.** This research received no specific grant from any funding agency in
the public, commercial or not-for-profit sectors.

**Authors' contributions.** [ADJUST TO MATCH REALITY — e.g. JFA designed and
implemented the optimisation framework, conducted the experiments and drafted the
manuscript. OAK contributed to the clinical rule specification and manuscript
revision. Both authors read and approved the final manuscript.]

**Acknowledgements.** The authors thank Eng. Yasser Mafalani for his help with
this work.

---

## Notes for you

**On §6.4.** Your earlier draft claimed a human-in-the-loop design. The
implementation has no clinician interaction, so I have written this as a design
*position* with an explicit statement that it is not validated, and named
automation bias as an unmitigated risk. That is defensible. Claiming a
human-in-the-loop system you have not built is not, and a reviewer who opens the
repository will see the difference immediately.

**On §6.5.** I have described the regulatory landscape rather than asserting a
specific classification, because classification depends on jurisdiction and
intended-use statement, and neither of us is a regulatory specialist. Do not
sharpen this into a definite claim about what class the device would be.

**Still missing from your reference list.** Earlier feedback you received noted
that a tutorial website was cited for genetic-algorithm theory. Holland (1975)
and Goldberg (1989) are now in `references.bib` — use those. The same feedback
suggested Harrigan and Günthard on resistance-guided therapy; those would
strengthen Section 2 and I have not added them, since I have not read them and
will not cite on your behalf what I have not checked.

**`neri2007` remains unverified.** You did not send that PDF. Supply it or cut
the paragraph.
