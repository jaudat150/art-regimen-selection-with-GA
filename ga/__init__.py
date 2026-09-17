"""
Genetic Algorithm implementation for HIV regimen optimization.

Key features:
  - Clinically-aware operators (no unsafe regimens generated)
  - Regimen representation (two NRTIs + one third agent)
  - Progress tracking for clinical audits
  - Robust error handling for edge cases (e.g., no-safe-drugs)

Design philosophy:
  - Operators modify only the third drug (preserves NRTI backbone stability)
  - All operations validated against config/clinical_rules.py
  - Fitness-driven selection (not random)
"""

from .genetic_algorithm import HIVRegimenGA
from .selection import tournament_selection
from .crossover import crossover_regimens
from .mutation import mutate_regimen

__all__ = [
    'HIVRegimenGA',
    'tournament_selection',
    'crossover_regimens',
    'm'
]