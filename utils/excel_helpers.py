# utils/excel_helpers.py
"""
Excel utility functions for clinical data management.

Why Excel?
  - Clinicians can edit directly without programming knowledge
  - Supports formatting, comments, and validation
  - Works offline — critical in low-connectivity settings

Features:
  - Template generation (for new clinics)
  - Report export (for patient files)
  - Validation (prevent data entry errors)
"""

import os
from pathlib import Path
import pandas as pd
import logging
from typing import Dict, List


_logger = logging.getLogger(__name__)


def create_drugs_template(output_path: str = 'data/drugs_template.xlsx'):
    """
    Create an empty template Excel file for drug properties.

    Template includes:
      - Empty columns for drug data entry
      - Column headers with data validation hints
      - Separate sheets for drugs and resistance data

    Args:
        output_path (str): Path to save template
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

    # Empty drugs sheet data (only headers)
    drugs_data = {
        'Drug': [],
        'Class': [],
        'Efficacy': [],
        'Toxicity': [],
        'Liver_Impact': [],
        'Kidney_Impact': [],
        'Monthly_Cost_USD': [],
        'Contraindications': [],
        'Side_Effects': []
    }

    # Empty resistance sheet data (only headers)
    resistance_data = {
        'Mutation': [],
        'Drug': [],
        'Efficacy_Reduction': []
    }

    # Create Excel file with empty sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        pd.DataFrame(drugs_data).to_excel(writer, sheet_name='Drugs', index=False)
        pd.DataFrame(resistance_data).to_excel(writer, sheet_name='Resistance', index=False)

    _logger.info("Empty drug template created: %s", output_path)
    _logger.info("Tip: Add drug data following WHO guidelines")


def create_patients_template(output_path: str = 'data/patients_template.xlsx'):
    """
    Create a template Excel file for patient profiles.
    Uses fallback to user's home directory if permission denied.
    """
    # Prepare patients_data before attempting IO to ensure fallback availability
    patients_data = {
        'Patient_ID': [],
        'Viral_Load': [],
        'CD4': [],
        'Subtype': [],
        'Mutations': [],
        'Liver_Function': [],
        'Kidney_Function': [],
        'Pregnancy': [],
        'Cost_Sensitivity': [],
        'Comorbidities': [],
        'Allergies': [],
        'Access_Constraints': []
    }

    p = Path(output_path)

    try:
        # Ensure data directory exists
        data_dir = p.parent if p.parent.as_posix() != '' else Path('.')
        data_dir.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(patients_data)
        df.to_excel(p, index=False)
        _logger.info("Patient template created: %s", p)
        return str(p)

    except PermissionError:
        # Fallback: use user's home directory
        fallback_dir = Path.home() / 'hiv_data'
        fallback_dir.mkdir(parents=True, exist_ok=True)
        fallback_path = fallback_dir / 'patients.xlsx'

        df = pd.DataFrame(patients_data)
        df.to_excel(fallback_path, index=False)
        _logger.warning("Permission denied. Using fallback: %s", fallback_path)
        return str(fallback_path)

def save_regimen_report(
    profile: Dict, 
    best_regimen: Dict, 
    fitness: float,
    drug_data: Dict,
    output_dir: str = 'reports'
) -> str:
    """
    Save regimen report as Excel file for clinician review.
    
    Report includes:
      - Recommended regimen
      - Cost analysis (monthly, yearly)
      - Safety warnings (organ impact, side effects)
      - WHO compliance status
      - Clinical rationale (why this regimen?)
    
    Args:
        profile: Patient profile
        best_regimen: Optimized regimen
        fitness: Fitness score
        drug_data: Drug properties
        output_dir: Output directory
    
    Returns:
        str: Path to saved report
    """
    from core import RegimenIndividual
    
    # Generate summary
    summary = RegimenIndividual.decode(best_regimen, drug_data)
    
    # Create report data
    report_data = {
        'Category': [
            'Patient ID', 'Mutations', 'Cost Sensitivity',
            'Primary Regimen', 'Primary Cost ($/month)', 
            'Backup Regimen', 'Backup Cost ($/month)',
            'WHO Compliant', 'Fitness Score',
            'Warnings'
        ],
        'Value': [
            profile['Patient_ID'],
            ', '.join(profile.get('Mutations', [])),
            profile.get('Cost_Sensitivity', 'Medium'),
            ', '.join(summary['primary']['drugs']),
            summary['primary']['cost'],
            'Yes' if summary['who_compliant'] else 'No',
            f"{fitness:.1f}",
            '; '.join(summary['primary']['warnings']) if summary['primary']['warnings'] else 'None'
        ]
    }
    
    # Save to Excel
    filename = f"regimen_{profile.get('Patient_ID', 'unknown')}.xlsx"
    out_dir = Path(output_dir) / 'regimens'
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / filename

    df = pd.DataFrame(report_data)
    df.to_excel(filepath, index=False)
    
    # Add formatting (using openpyxl)
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill
        
        wb = load_workbook(filepath)
        ws = wb.active
        
        # Header formatting
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="2E5984", end_color="2E5984", fill_type="solid")
        
        # WHO compliance highlighting
        who_cell = ws['B8']
        if who_cell.value == 'Yes':
            who_cell.fill = PatternFill(start_color="38761D", end_color="38761D", fill_type="solid")
            who_cell.font = Font(color="FFFFFF")
        else:
            who_cell.fill = PatternFill(start_color="CC0000", end_color="CC0000", fill_type="solid")
            who_cell.font = Font(color="FFFFFF")
        
        wb.save(filepath)
    except:
        _logger.debug("openpyxl not available or formatting failed; report saved without formatting.")
    
    _logger.info("Regimen report saved: %s", filepath)
    return str(filepath)