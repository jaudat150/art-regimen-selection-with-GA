# reports/__init__.py
"""
Clinical report generators for HIV regimen optimization.

Design principles:
  - Clinician-first language (no technical jargon)
  - Syria-ready formatting (Arabic support, low-ink printing)
  - Actionable recommendations (not just data)
  - Multiple formats for different clinic capabilities
"""

from .excel_reporter import generate_excel_report

__all__ = ['generate_excel_report']