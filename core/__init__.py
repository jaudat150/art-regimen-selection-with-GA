"""
Core clinical logic: regimen representation and fitness evaluation.

This module is:
  - Algorithm-agnostic (works with GA or any manual design)
  - Clinically validated (every function has medical rationale)
  - Production-ready (handles edge cases like no-safe-drugs)
"""

from .individual import RegimenIndividual
from .fitness_evaluator import FitnessEvaluator

__all__ = ['RegimenIndividual', 'FitnessEvaluator']