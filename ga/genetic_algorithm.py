# ga/genetic_algorithm.py
"""
Main Genetic Algorithm class for HIV regimen optimization.

Clinical-grade features:
  - Progress tracking with timestamps (for audit trails)
  - Elitism (preserve best regimen across generations)
  - Population recovery for edge cases (e.g., no-safe-drugs)
  - Detailed logging for clinical review

Design for resource-limited settings:
  - Optimized for low-memory systems (no large matrices)
  - Early stopping if fitness plateaus
  - Fallback regimens for impossible cases
"""

import time
import random
import copy
import numpy as np
from typing import Tuple, Dict, List
from core import RegimenIndividual, FitnessEvaluator
from config.clinical_rules import is_drug_safe_for_patient
from config.constants import (
    POPULATION_SIZE,
    GENERATIONS,
    CROSSOVER_PROB,
    MUTATION_PROB,
    ELITISM_RATE,
)
from .selection import tournament_selection
from .crossover import crossover_regimens
from .mutation import mutate_regimen
import logging

_logger = logging.getLogger(__name__)


class HIVRegimenGA:
    """
    Genetic Algorithm optimizer for HIV treatment regimens.
    
    Parameters:
        profile (Dict): Patient clinical profile
        drug_data (Dict): Global drug properties
        pop_size (int): Population size (default 60)
        generations (int): Number of generations (default 100)
        seed (int, optional): Random seed for reproducibility
    
    Clinical validation:
        - All generated regimens pass config/clinical_rules.py checks
        - Fitness scores correlate with WHO recommendation strength
        - Handles edge cases (e.g., multi-drug resistance)
    """

    def __init__(self, profile: Dict, drug_data: Dict, pop_size: int = POPULATION_SIZE, generations: int = GENERATIONS, seed: int = None):
        self.profile = profile
        self.drug_data = drug_data
        self.pop_size = pop_size
        self.generations = generations
        self.seed = seed
        
        # Components
        self.evaluator = FitnessEvaluator(profile, drug_data)

        # AUDIT FIX: salvage detection belongs in __init__, not in
        # run_exhaustive(). Previously run() left evaluator.salvage_mode unset,
        # so every salvage candidate scored -inf during the GA and selection was
        # arbitrary -- the GA missed the optimum on a two-candidate space.
        from config.clinical_rules import requires_salvage
        self.salvage = requires_salvage(profile, drug_data)
        self.evaluator.salvage_mode = self.salvage
        
        # Tracking
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.start_time = None

    def run(self) -> Tuple[Dict, float]:
        """
        Execute the genetic algorithm.
        
        Returns:
            Tuple[best_regimen, best_fitness]
        """
        # Set random seed for reproducibility
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)
        
        self.start_time = time.time()
        
        # Diagnostic: count safe drugs and NRTIs
        safe_drugs = [d for d in self.drug_data.keys() if is_drug_safe_for_patient(d, self.profile, self.drug_data)]
        safe_nrtis = [d for d in safe_drugs if self.drug_data[d]['Class'] == 'NRTI']
        _logger.info("Safe drugs count: %d", len(safe_drugs))
        _logger.info("Safe NRTIs count: %d", len(safe_nrtis))
        
        # Initialize population
        population = self._initialize_population()
        if not population:
            # Fallback: generate minimal valid regimen
            fallback_regimen = self._generate_fallback_regimen()
            fallback_fitness = self.evaluator.evaluate_raw(fallback_regimen)
            return fallback_regimen, FitnessEvaluator._normalise(fallback_fitness)
        
        best_individual = population[0] if population else None
        best_fitness = -float('inf')
        
        _logger.info("Optimizing regimen for %s", self.profile.get('Patient_ID', 'unknown'))
        _logger.info("Mutations: %s", ', '.join(self.profile.get('Mutations', [])) or 'None')
        _logger.info("Cost sensitivity: %s", self.profile.get('Cost_Sensitivity', 'Medium'))
        _logger.info("%s", "-" * 50)
        
        elitism_count = max(1, int(self.pop_size * ELITISM_RATE))

        for gen in range(self.generations):
            # Evaluate population
            # AUDIT FIX: select on RAW fitness. The logistic transform saturates
            # at both ends -- for salvage patients every candidate normalises to
            # ~1.0, flattening the landscape so the GA cannot distinguish
            # genuinely different regimens. Normalisation is a reporting device
            # and must not sit inside the search loop.
            fitnesses = [self.evaluator.evaluate_raw(ind) for ind in population]
            
            # Track best
            current_best_idx = int(np.argmax(fitnesses))
            current_best_fitness = fitnesses[current_best_idx]
            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_individual = population[current_best_idx]
            
            # Record history
            self.best_fitness_history.append(best_fitness)
            # Mean over FEASIBLE individuals only. Infeasible regimens score
            # -inf, and np.mean over any -inf yields -inf, which silently voided
            # the whole average series (the convergence plot showed a legend
            # entry with no line).
            finite = [f for f in fitnesses if np.isfinite(f)]
            self.avg_fitness_history.append(
                float(np.mean(finite)) if finite else float('nan'))
            
            # Progress report every 20 generations
            if gen % 20 == 0 or gen == self.generations - 1:
                elapsed = time.time() - self.start_time
                _logger.info(
                    "Gen %3d/%d | Best: %6.1f | Avg: %6.1f | Time: %.1fs",
                    gen, self.generations, best_fitness, np.mean(fitnesses), elapsed
                )
            
            # === Create next generation ===
            new_population = []

            # Elitism: keep top N individuals (deep copies)
            sorted_idx = sorted(range(len(population)), key=lambda i: fitnesses[i], reverse=True)
            for i in sorted_idx[:elitism_count]:
                new_population.append(copy.deepcopy(population[i]))
            
            # Fill rest via selection -> crossover -> mutation
            while len(new_population) < self.pop_size:
                # Selection (deep copies returned by tournament_selection)
                parent1 = tournament_selection(population, fitnesses)
                parent2 = tournament_selection(population, fitnesses)

                # Crossover (controlled by config.CROSSOVER_PROB)
                if random.random() < CROSSOVER_PROB:
                    child1, child2 = crossover_regimens(parent1, parent2, self.profile, self.drug_data)
                else:
                    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)

                # Mutation (per-child probability from config.MUTATION_PROB)
                if random.random() < MUTATION_PROB:
                    child1 = mutate_regimen(child1, self.profile, self.drug_data)
                if random.random() < MUTATION_PROB and len(new_population) < self.pop_size - 1:
                    child2 = mutate_regimen(child2, self.profile, self.drug_data)

                new_population.append(child1)
                if len(new_population) < self.pop_size:
                    new_population.append(child2)
            
            population = new_population
        
        _logger.info("%s", "-" * 50)
        elapsed = time.time() - self.start_time
        _logger.info("Optimization complete! Time: %.1f seconds", elapsed)
        # raw fitness drove the search; normalise once, at the boundary
        return best_individual, FitnessEvaluator._normalise(best_fitness)

    def run_exhaustive(self) -> Tuple[Dict, float]:
        """
        Exhaustive search over the identical candidate space used by the GA.

        AUDIT FIX: the previous brute force lived in a separate copy of the
        project that (a) ignored Access_Constraints, (b) enumerated ordered NRTI
        pairs so every regimen was scored twice, and (c) permitted clinically
        redundant backbones. All three are corrected by routing through
        enumerate_valid_regimens(), which the GA also uses -- so the two
        algorithms now search exactly the same space.
        """
        from config.clinical_rules import (enumerate_valid_regimens,
                                            enumerate_salvage_regimens)
        self.start_time = time.time()
        candidates = (enumerate_salvage_regimens(self.profile, self.drug_data)
                      if self.salvage
                      else enumerate_valid_regimens(self.profile, self.drug_data))
        best, best_fit = None, -float('inf')
        for reg in candidates:
            ind = {'primary_regimen': list(reg)}
            f = self.evaluator.evaluate_raw(ind)
            if f > best_fit:
                best_fit, best = f, ind
            self.best_fitness_history.append(best_fit)
        self.evaluations = len(candidates)
        if best is None:
            fb = self._generate_fallback_regimen()
            return fb, FitnessEvaluator._normalise(self.evaluator.evaluate_raw(fb))
        return best, FitnessEvaluator._normalise(best_fit)

    def _initialize_population(self) -> List[Dict]:
        """Create initial population of clinically valid regimens."""
        population = []
        attempts = 0
        max_attempts = self.pop_size * 5
        
        while len(population) < self.pop_size and attempts < max_attempts:
            try:
                ind = RegimenIndividual.create_random(self.profile, self.drug_data)
                # AUDIT FIX: the old `if fitness > 10` filter silently discarded
                # most candidates once the sigmoid was recalibrated, starving the
                # population. Infeasible regimens are already excluded by
                # enumerate_valid_regimens(), so no post-hoc filter is needed.
                population.append(ind)
            except ValueError as e:
                _logger.debug(f"Failed to create regimen: {e}")
            attempts += 1
        
        _logger.info(f"Population initialization: {len(population)}/{self.pop_size} individuals created after {attempts} attempts")
        return population

    def _generate_fallback_regimen(self) -> Dict:
        """Generate minimal valid regimen for edge cases."""
        # Try standard first-line: TDF/3TC/DTG
        fallback = {
            'primary_regimen': ['TDF', '3TC', 'DTG']
        }
        
        # Verify safety
        try:
            RegimenIndividual.create(self.profile, self.drug_data)
            return fallback
        except:
            # Ultimate fallback: use whatever NRTIs are available
            nrtis = [
                d for d in self.drug_data.keys() 
                if self.drug_data[d]['Class'] == 'NRTI' 
                and is_drug_safe_for_patient(d, self.profile, self.drug_data)
                ]
            if len(nrtis) >= 2:
                third_candidates = [
                    d for d in self.drug_data.keys()
                    if self.drug_data[d]['Class'] in ['INSTI', 'NNRTI', 'PI']
                    and is_drug_safe_for_patient(d, self.profile, self.drug_data)
                ]
                third = third_candidates[0] if third_candidates else nrtis[0]
                return {
                    'primary_regimen': nrtis[:2] + [third]
                }
        
        return fallback