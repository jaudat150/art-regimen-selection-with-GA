"""
Selection strategies for genetic algorithm.

Why tournament selection?
  - More robust than roulette wheel in small populations
  - Less sensitive to fitness scaling issues
  - Clinically intuitive: "best of 3 candidates" mimics expert panel review

Parameters:
  - tournament_size: 3 (optimal for population size 60)
"""

import random
import copy
from typing import List


def tournament_selection(population: List[dict], fitnesses: List[float], tournament_size: int = 3) -> dict:
    """
    Select an individual using tournament selection.
    
    Algorithm:
      1. Randomly sample k individuals (k = tournament_size)
      2. Return the one with highest fitness
    
    Args:
        population: List of regimen individuals
        fitnesses: Corresponding fitness scores
        tournament_size: Number of candidates to sample
    
    Returns:
        Selected individual (dict)
    """
    # Ensure we don't sample more than population size
    k = min(tournament_size, len(population))
    
    # Randomly select candidates
    candidates = random.sample(range(len(population)), k)

    # Select winner (highest fitness)
    winner_idx = max(candidates, key=lambda i: fitnesses[i])

    # Return a deep copy to avoid accidental in-place mutation
    return copy.deepcopy(population[winner_idx])