# reports/excel_reporter.py
"""
Professional Excel reports for clinical decision support.

Why Excel reports?
  - Familiar to clinicians and pharmacists
  - Supports formatting, comments, and validation
  - Can be integrated into hospital EMR systems
  - Print-ready with clinic branding

Report features:
  - Color-coded WHO compliance status
  - Cost comparison charts
  - Safety warnings in red
  - Arabic/English bilingual headers (optional)
"""

import datetime
import os
import pandas as pd
from typing import Dict
from core import RegimenIndividual


def generate_excel_report(
    profile: Dict, 
    best_regimen: Dict, 
    fitness: float,
    drug_data: Dict,
    output_dir: str = 'reports'
) -> str:
    """
    Generate professional Excel report for HIV regimen.
    
    Syria-specific enhancements:
      - Low-ink printing mode (grayscale-friendly)
      - Customizable clinic header
      - Drug availability status (available/unavailable)
      - Cost sensitivity indicator
    
    Args:
        profile: Patient clinical profile
        best_regimen: Optimized regimen
        fitness: Fitness score
        drug_ Drug properties dict
        output_dir: Output directory
    
    Returns:
        str: Path to saved Excel report
    """
    # Generate summary
    summary = RegimenIndividual.decode(best_regimen, drug_data)
    
    # Create report data
    report_data = {
        'Parameter': [
            'Patient ID', 'Date Generated', 'Mutations', 
            'Liver Function', 'Kidney Function', 'Cost Sensitivity',
            'Primary Regimen', 'Primary Cost ($/month)', 
            'WHO Compliant', 'Fitness Score',
            'Warnings'
        ],
        'Value': [
            profile['Patient_ID'],
            datetime.datetime.now().strftime('%Y-%m-%d'),
            ', '.join(profile.get('Mutations', [])) or 'None',
            f"{profile['Liver_Function']:.2f}",
            f"{profile['Kidney_Function']:.2f}",
            profile.get('Cost_Sensitivity', 'Medium'),
            ', '.join(summary['primary']['drugs']),
            summary['primary']['cost'],
            'Yes' if summary['who_compliant'] else 'No',
            f"{fitness:.1f}",
            '; '.join(summary['primary']['warnings']) if summary['primary']['warnings'] else 'None'
        ]
    }
    
    # Drug details table
    drug_details = []
    for drug in summary['primary']['drugs']:
        d = drug_data.get(drug, {})
        drug_details.append({
            'Drug': drug,
            'Class': d.get('Class', ''),
            'Efficacy': d.get('Efficacy', 0.0),
            'Toxicity': d.get('Toxicity', 0.0),
            'Liver Impact': d.get('Liver_Impact', 0.0),
            'Kidney Impact': d.get('Kidney_Impact', 0.0),
            'Monthly Cost ($)': d.get('Monthly_Cost_USD', 0.0),
            # Was labelled 'Available in Syria'. The drug table contains no
            # country availability column; this field reads Access_Constraints,
            # which holds the patient's formulary tier (config/formulary.py).
            # Relabelled to say what it actually measures.
            'In Patient Formulary': 'Yes' if drug in profile.get('Access_Constraints', []) else 'No',
            'Contraindications': ', '.join(d.get('Contraindications', [])),
            'Side Effects': ', '.join(d.get('Side_Effects', []))
        })
    
    # Save to Excel
    filename = f"regimen_{profile['Patient_ID']}.xlsx"
    filepath = os.path.join(output_dir, 'regimens', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Summary sheet
        pd.DataFrame(report_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Drug Details sheet
        if drug_details:
            pd.DataFrame(drug_details).to_excel(writer, sheet_name='Drug Details', index=False)
        
        # Pre-prescription requirements sheet.
        from config.clinical_rules import requires_hla_screening
        _scr = requires_hla_screening(summary['primary']['drugs'], drug_data)
        pd.DataFrame({
            'Requirement': (
                [f'{m} screening required before starting {d}' for d, m in _scr]
                or ['None']
            ),
            'Status': (['MUST SCREEN - result required before dispensing'] * len(_scr)
                       or ['No pharmacogenetic prerequisites'])
        }).to_excel(writer, sheet_name='Pre-Prescription', index=False)

        # Cost Analysis sheet. Backup-regimen rows removed along with the
        # backup feature itself: nothing scored it, so 'Yearly Savings' was
        # structurally always zero.
        pd.DataFrame({
            'Scenario': ['Recommended Regimen'],
            'Monthly Cost ($)': [summary['primary']['cost']],
            'Yearly Cost ($)': [summary['primary']['cost'] * 12],
        }).to_excel(writer, sheet_name='Cost Analysis', index=False)
    
    # Add professional formatting (if openpyxl available)
    try:
        _format_excel_report(filepath, summary['who_compliant'])
    except:
        pass  # Continue without formatting if openpyxl not available
    
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info("Excel report saved: %s", filepath)
    return filepath


def _format_excel_report(filepath: str, who_compliant: bool):
    """
    Add professional formatting to Excel report.
    
    Formatting includes:
      - Header styling (blue background, white text)
      - WHO compliance highlighting (green/red)
      - Currency formatting
      - Auto-fit columns
    """
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    wb = load_workbook(filepath)
    
    # Format Summary sheet
    if 'Summary' in wb.sheetnames:
        ws = wb['Summary']
        
        # Header formatting
        header_fill = PatternFill(start_color="2E5984", end_color="2E5984", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        # WHO compliance highlighting
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            if row[0].value == 'WHO Compliant':
                if who_compliant:
                    row[1].fill = PatternFill(start_color="38761D", end_color="38761D", fill_type="solid")
                    row[1].font = Font(color="FFFFFF", bold=True)
                else:
                    row[1].fill = PatternFill(start_color="CC0000", end_color="CC0000", fill_type="solid")
                    row[1].font = Font(color="FFFFFF", bold=True)
                break
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Format Cost Analysis sheet
    if 'Cost Analysis' in wb.sheetnames:
        ws = wb['Cost Analysis']
        
        # Header formatting
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        # Currency formatting
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row[1:]:  # Skip first column (Scenario)
                cell.number_format = '"$"#,##0.00'
    
    wb.save(filepath)