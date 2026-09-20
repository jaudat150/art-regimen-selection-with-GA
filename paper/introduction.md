## 1. Introduction

Antiretroviral therapy has turned HIV infection into a manageable chronic
condition, but choosing a regimen for an individual patient remains a decision
under several competing constraints. A regimen must suppress the virus given
whatever resistance mutations the patient carries, avoid drugs contraindicated by
their hepatic, renal or pregnancy status, keep toxicity and side-effect burden
low enough to sustain lifelong adherence, and cost little enough to be
dispensable by the health system treating them. In resource-constrained settings
the last of these is frequently the binding constraint rather than a secondary
consideration: what a clinic stocks determines what can be prescribed, before
any clinical reasoning begins.

This has made antiretroviral regimen design an attractive target for
computational optimisation, and evolutionary algorithms in particular have been
applied to it for over fifteen years. The appeal is understandable. The problem
has several objectives that trade against one another, hard clinical
constraints, and — in the formulations most often studied — an expensive fitness
evaluation. Metaheuristics are the standard tool for exactly that combination.

What the literature does not generally report is how these methods compare
against exact search. Studies present convergence behaviour, final solution
quality, and improvements over prior evolutionary variants, but rarely the size
of the space being searched or the result an exhaustive enumeration would return.
Without those, "the algorithm found a good regimen" is difficult to assess:
whether it found *the* regimen, and at what cost relative to simply checking
every option, is left open.

This paper supplies that baseline. We formulate WHO-compliant first-line regimen
selection as constrained combinatorial optimisation over a catalogue of twenty
antiretrovirals, with availability modelled through formulary tiers drawn from
published guidance rather than assumed universal, and we run a genetic algorithm
and exhaustive search over a provably identical feasible set.

The result is negative, and we report it as the contribution. The feasible set
holds between two and 130 regimens per patient. Exhaustive search returns the
optimum in milliseconds; the genetic algorithm matches it on every patient while
performing roughly 1,400 times more computation, and for 15 of 17 patients the
optimum is already present in its randomly initialised population, so its
evolutionary operators do no work at all. Because a regimen is a fixed
three-slot object, the space grows as $O(n^2m)$ in catalogue size and stays
tractable far beyond any plausible expansion of the drug catalogue.

We report three implementation artefacts encountered along the way — deterministic
population initialisation, asymmetric constraint application between the compared
methods, and fitness normalisation applied inside the search loop — each of which
inflated apparent metaheuristic performance, each of which we introduced
ourselves, and none of which we would have detected without the exact baseline to
check against. We also report a fourth failure of a different kind: an unsourced
drug cost table produced a coherent, plausible, and entirely wrong clinical
conclusion in a model whose search logic was by then verified by both an exact
baseline and a passing test suite.

Two caveats belong here rather than buried in the limitations. Fifteen of our
seventeen patient profiles are synthetic, and no claim about real-world clinical
outcomes is supported by this work; the search-space characterisation does not
depend on the patient distribution, but the empirical results do. And several
model parameters — per-drug efficacy, toxicity, and the resistance penalties —
remain unsourced; we report which, and treat conclusions resting on them
accordingly.

---

## 2. Related Work

Evolutionary algorithms have been applied to antiretroviral therapy optimisation
for more than fifteen years. We review that work below, organised around a
question the field does not usually foreground: **how have these methods been
evaluated, and against what?**

### 2.1 Simulation-coupled evolutionary therapy design

The earliest sustained line of work couples a genetic algorithm to a biological
simulator. Castiglione et al. combined a genetic algorithm with the C-ImmSim
agent-based immune simulator to optimise highly active antiretroviral therapy
schedules \cite{castiglione2007}. A chromosome was a 24-bit binary string, one
bit per week of a six-month therapeutic horizon, indicating whether antiretroviral
drugs were administered that week. Selection was by tournament, reproduction by
uniform crossover, with elitism on the two fittest individuals. The fitness
function summed three terms — normalised HIV load, a CD4 recovery ratio, and the
fraction of active therapy days — and was minimised. The optimal schedule
achieved survival close to continuous therapy (30.5% against 34.11% in simulated
opportunistic-infection challenge) while administering therapy for 15 weeks
rather than 25, roughly 40% less drug.

The computational cost is the salient detail for our purposes. The authors ran a
population of 32 schedules evaluated across 16 virtual patients each, over 60
generations: 30,720 simulations in total, each requiring around 30 minutes,
necessitating a 128-machine cluster — on the order of 15,000 CPU-hours for a
single optimisation. The formulation also addressed dosage timing rather than
selection among agents, and modelled only two drug classes, reverse
transcriptase inhibitors and protease inhibitors, administered together.

Golpayegani et al. pursued a similar formulation with a two-dimensional
cellular-automata model of HIV infection in the peripheral bloodstream
\cite{golpayegani2017}. Their chromosome was a 32-bit string, one bit per week
over 32 weeks, with a population of 320 evolved for 50 generations under
tournament selection, scattered crossover at 0.8, uniform mutation at 0.01 and
an elite count of 2. The cost function summed normalised healthy-cell
concentration, viral load and drug dosage; fitness was its reciprocal. The
optimised schedule reduced drug dosage by 47% relative to continuous therapy
while leaving steady-state healthy CD4⁺ concentration only 3.9% lower.

As in the preceding work, therapy was represented by class-level effectiveness
parameters for reverse transcriptase and protease inhibitors rather than by drug
identity, so the search could not distinguish between agents within a class or
their differing toxicities. Optimisation was therefore over schedules rather than
over clinically realistic regimens, and the cellular-automata fitness again
imposed substantial computational cost.

Neri and colleagues extended the approach methodologically in two companion 2007
papers: an adaptive evolutionary algorithm with intelligent mutation local
searchers \cite{neri2007appl}, and an Adaptive Multimeme Algorithm coordinating
three local searchers — localised random search, a steepest-descent explorer and
simulated annealing — under a fitness-diversity index \cite{neri2007tcbb}. Both
optimise reverse transcriptase and protease inhibitor administration schedules
against a six-compartment ordinary differential equation model of HIV–immune
dynamics including an immune-effector compartment \cite{adams2005}, with an
objective steering effectors toward a healthy steady state while penalising
cumulative drug exposure. The multimeme algorithm outperformed a genetic
algorithm, an evolution strategy and standalone simulated annealing under an
equal budget of 85,000 fitness evaluations.

This work is directly instructive for the present question, because it is the one
study in this literature that reports the size of its search space. Under its
period representation — integer vectors encoding successive on/off durations over
a 750-day horizon — the decision space contains approximately
$7.7 \times 10^{318}$ schedules \cite{neri2007tcbb}. Exhaustive enumeration is
not merely impractical there but physically impossible, and the authors do not
attempt it. Each fitness evaluation required roughly 0.2 seconds of numerical
integration, so a single run consumed around five hours of computation.

Treatment representation nonetheless remained centred on temporal scheduling
rather than drug identity: agents enter only as class-level efficacy parameters,
so toxicity differentiation, resistance profiles and guideline constraints were
not incorporated into the search.

### 2.2 Resistance-guided regimen selection

A parallel and much larger literature addresses the clinical problem our
formulation targets: using genotypic resistance information to select a regimen
for an individual patient. Liu and Shafer review the principles by which a
genotype is translated into drug-level resistance interpretations and survey the
web-based systems that implement this, noting that prospective controlled studies
have found patients whose physicians have access to genotypic resistance data
respond better to therapy than controls \cite{liu2006}. Haupts et al., in the
Swiss HIV Cohort, provide direct evidence from 145 adults with virologic failure
that lower resistance scores predicted improved virologic response to a new
regimen, and that treatment choices informed by genotype plus decision-support
software were virologically superior to those based on treatment history alone
\cite{haupts2003}.

Harrigan et al. characterised the determinants of emergent resistance in 1,191
antiretroviral-naive adults initiating therapy in British Columbia, finding high
baseline viral load and imperfect adherence to be the principal predictors
\cite{harrigan2005} — a reminder that resistance is partly a consequence of the
regimen chosen and the adherence it permits, which is the forward-looking
dependency our single-decision formulation cannot represent (Section 5.2). The
International Antiviral Society–USA panel's recommendations set out when
resistance testing should inform regimen selection \cite{gunthard2019}, and its
periodically updated mutations figure provides the reference list of
resistance-associated mutations \cite{wensing2019}.

Our work sits alongside rather than within this literature: we take
resistance-adjusted susceptibility as an input and ask what search procedure the
resulting optimisation problem requires. The interpretation algorithms above are
what a deployed system would use to produce that input.

### 2.3 Evolutionary computation on adjacent HIV tasks

Genetic algorithms have also been applied to HIV problems other than therapy
design. Betechuoh et al. used a genetic algorithm to tune multilayer-perceptron
hyperparameters — hidden-node count, learning rate, training cycles and
classification threshold — for predicting HIV status from demographic data,
reporting 84.24% accuracy against 74% for line-search optimisation
\cite{betechuoh2006}. Here the genetic algorithm performs hyperparameter tuning
rather than treatment optimisation, and we note it only to bound the scope of
evolutionary computation in this domain.

### 2.4 How this work has been evaluated

Across this literature, three things are consistently reported: convergence
behaviour, final solution quality under the study's own objective, and
improvement relative to earlier evolutionary variants. Three others are largely
absent: the size of the feasible set being searched — reported, to our knowledge,
only by Neri et al. \cite{neri2007tcbb} — a comparison against exhaustive
enumeration of that set, and the sensitivity of recommendations to the
objective's weights.

We state this as an observation about evaluation practice, not a criticism of the
studies. In the simulation-coupled formulations above it is a defensible
omission: when a single fitness evaluation requires a lengthy agent-based or
cellular-automata simulation, exhaustive enumeration is plainly infeasible and a
baseline nobody could run tells a reader little. **The expensive fitness function
is precisely the condition under which a metaheuristic is warranted, and prior
work operated squarely within it.**

The gap is quantifiable on both axes. A single C-ImmSim evaluation took
approximately 30 minutes \cite{castiglione2007} and a single ODE integration in
Neri et al. approximately 0.2 seconds \cite{neri2007tcbb}; a single evaluation of
our objective takes approximately $1.3 \times 10^{-5}$ seconds. Where Castiglione
et al. required roughly 15,000 CPU-hours on a 128-machine cluster for one
optimisation, our entire 17-patient exhaustive search completes in 8 milliseconds
on one core.

The search spaces differ correspondingly. Neri et al. report approximately
$7.7 \times 10^{318}$ candidate schedules; our feasible set contains 613 regimens
across the whole cohort. Both conclusions are correct for their own formulation,
and the contrast is the point: the case for a metaheuristic is a property of the
problem instance, not of the application domain.

That is what makes the present formulation different, and what makes the baseline
newly informative. Removing the expensive simulation removes the condition that
justified the metaheuristic — and whether the metaheuristic is still earning its
cost becomes an empirical question that had not, to our knowledge, been asked for
this problem. It turns out not to be.

Two further distinctions follow from the same shift. Prior work modelled two drug
classes; the current catalogue contains six, and the choice *between* agents
within a class — with their differing toxicity, resistance and cost profiles — is
the decision a clinician actually faces. And prior work optimised without
clinician interaction; whether such systems should operate autonomously is a
question we take up in Section 6.

Our own experience is the argument for reporting the baseline routinely. Three of
the four failure modes in Section 4 are ones we introduced ourselves, and all
three would have gone undetected without an exact result to check against: each
produced convergence traces and final solutions that looked entirely reasonable.
This is not a hazard peculiar to prior work; it is one we walked into repeatedly
with the baseline available to catch us.

### 2.5 Positioning

Prior evolutionary approaches show that these methods can explore complex HIV
treatment spaces and balance competing objectives. They predominantly address
binary scheduling or structured interruptions, rely on computationally expensive
simulation, and treat drugs as homogeneous rather than modelling agent-specific
effects, toxicities and modern multi-class combinations.

The present work takes the complementary formulation — explicit selection among
differentiated agents under guideline and formulary constraints, with a cheap
objective — and asks what search method that formulation actually requires. The
answer bears directly on the sequencing formulation prior work approached from
the scheduling side, and which we argue in Section 5.2 is where evolutionary
search for this problem properly belongs.
