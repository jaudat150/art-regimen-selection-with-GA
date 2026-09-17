# utils/__init__.py
"""
Utility functions for environment setup and common operations.

Design goals:
  - Zero external dependencies (only Python standard library)
  - Fail-safe operations (graceful degradation in LMICs)
  - Clinician-friendly outputs (Arabic/English support ready)
"""

from .setup import setup_environment, ensure_output_dir
from .excel_helpers import (
    create_drugs_template,
    create_patients_template,
    save_regimen_report
)
from .helpers import (
    format_duration,
    is_interactive_environment,
    validate_excel_file
)

__all__ = [
    # Setup
    'setup_environment',
    'ensure_output_dir',
    
    # Excel helpers
    'create_drugs_template',
    'create_patients_template',
    'save_regimen_report',
    
    # General helpers
    'format_duration',
    'is_interactive_environment',
    'validate_excel_file'
]