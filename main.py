"""
HIV Regimen Optimizer — Main Execution Script

Clinical-grade system for optimizing HIV treatment regimens based on WHO 2024 guidelines, drug resistance profiles, and patient-specific factors.

Features:
  - WHO 2024 guideline compliance
  - Resistance-aware regimen design
  - Cost/toxicity/adherence multi-objective optimization
  - Excel-based data (clinician-friendly)
  - Text/Excel reports for clinics without printers

Usage:
  python main.py                    # Optimize all patients
  python main.py --patient ID      # Optimize specific patient
  python main.py --setup           # Create Excel templates

"""

import os
import sys
import argparse
import time
import traceback
import logging
from datetime import datetime

# Local modules
from utils import setup_environment, create_drugs_template, create_patients_template
from reports import generate_excel_report
from data import load_drug_data, load_patient_profiles
from core import RegimenIndividual
from ga import HIVRegimenGA
from config.constants import POPULATION_SIZE, GENERATIONS, SEED
from visualization import GAVisualizer, DrugRegimenVisualizer

_logger = logging.getLogger(__name__)

# Default logging configuration (may be adjusted after CLI parse)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def print_banner():
    """Log professional banner with system info (no emojis)."""
    _logger.info("%s", "=" * 60)
    _logger.info("HIV REGIMEN OPTIMIZER")
    _logger.info("WHO-Guideline Compliant | Syria-Ready | Excel-Based")
    _logger.info("%s", "=" * 60)
    _logger.info("Started: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    _logger.info("Python: %s | PID: %s", sys.version.split()[0], os.getpid())
    _logger.info("%s", "=" * 60)


def setup_mode():
    """Create empty Excel templates for new users."""
    _logger.info("Setting up clinical templates...")
    create_drugs_template('data/drugs.xlsx')
    create_patients_template('data/patients.xlsx')
    _logger.info("Setup complete")
    sys.exit(0)


def validate_data_files():
    """Validate required data files exist and are valid."""
    from utils import validate_excel_file
    
    # Check data directory
    if not os.path.exists('data'):
        _logger.error("Error: 'data' directory not found. Run: python main.py --setup")
        sys.exit(1)
    
    # Validate drugs.xlsx
    if not validate_excel_file('data/drugs.xlsx', ['Drugs', 'Resistance']):
        sys.exit(1)
    
    # Validate patients.xlsx
    if not validate_excel_file('data/patients.xlsx'):
        sys.exit(1)


def optimize_patient(profile: dict, drug_data: dict, output_dir: str, pop_size: int = POPULATION_SIZE, generations: int = GENERATIONS, seed: int = SEED) -> bool:
    """Optimize regimen for a single patient."""
    try:
        _logger.info("Optimizing patient: %s", profile.get('Patient_ID', 'unknown'))

        # Clinical summary (use safe defaults)
        mutations = ', '.join(profile.get('Mutations', []) or []) or 'None'
        liver = profile.get('Liver_Function', 1.0)
        kidney = profile.get('Kidney_Function', 1.0)
        _logger.info("Mutations: %s | Liver/Kidney: %.2f/%.2f | Cost Sensitivity: %s",
                     mutations, liver, kidney, profile.get('Cost_Sensitivity', 'Medium'))

        # Run GA
        start_time = time.time()
        ga = HIVRegimenGA(profile=profile, drug_data=drug_data, pop_size=pop_size, generations=generations, seed=seed)
        best_regimen, fitness = ga.run()
        if '--visualize' in sys.argv:  # Optional flag
            from visualization import GAVisualizer, DrugRegimenVisualizer
            
            ga_viz = GAVisualizer(output_dir=os.path.join(output_dir, 'viz'))
            drug_viz = DrugRegimenVisualizer(output_dir=os.path.join(output_dir, 'viz'))
            
            # GA convergence plot
            ga_viz.plot_convergence(ga, profile['Patient_ID'])
            
            # Store for aggregate plots later
            if not hasattr(optimize_patient, 'all_results'):
                optimize_patient.all_results = []
            optimize_patient.all_results.append({
                'regimen': best_regimen,
                'fitness': fitness,
                'patient_id': profile['Patient_ID']
            })
        elapsed = time.time() - start_time
        
        # Generate reports
        _logger.info("Generating reports (time: %.1fs)", elapsed)
        excel_report = generate_excel_report(profile, best_regimen, fitness, drug_data, output_dir)
        
        # Print summary
        _logger.info("Clinical summary:")
        summary = RegimenIndividual.decode(best_regimen, drug_data)
        
        _logger.info("Primary: %s", ', '.join(summary['primary']['drugs']))
        _logger.info("Primary cost: $%s/month", summary['primary']['cost'])
        _logger.info("WHO compliant: %s", 'Yes' if summary['who_compliant'] else 'No')
        _logger.info("Fitness: %.1f", fitness)

        if summary['primary']['warnings']:
            _logger.info("Warnings: %s", '; '.join(summary['primary']['warnings']))
        
        return True
        
    except KeyboardInterrupt:
        _logger.info("Optimization interrupted by user for %s", profile.get('Patient_ID', 'unknown'))
        return False
    except Exception as e:
        _logger.exception("Optimization failed for %s: %s", profile.get('Patient_ID', 'unknown'), e)
        if '--debug' in sys.argv:
            traceback.print_exc()
        return False


def main():
    # === 1. Parse command-line arguments ===
    parser = argparse.ArgumentParser(description='HIV Regimen Optimizer')
    parser.add_argument('--setup', action='store_true', help='Create Excel templates')
    parser.add_argument('--patient', type=str, help='Optimize specific patient ID')
    parser.add_argument('--debug', action='store_true', help='Show detailed error traces')
    parser.add_argument('--verbose', action='store_true', help='Show detailed CLI output')
    parser.add_argument('--visualize', action='store_true', help='Generate visualization plots')

    args = parser.parse_args()

    # Adjust logging based on CLI flags
    root = logging.getLogger()
    # Default: minimal summary (quiet). Use --verbose for detailed INFO output.
    if args.verbose:
        root.setLevel(logging.INFO)
    else:
        root.setLevel(logging.WARNING)


    # === 2. Setup mode ===
    if args.setup:
        setup_mode()
    
    # === 3. Print banner and setup environment ===
    print_banner()
    output_dir = setup_environment()
    
    # === 4. Validate and load data ===
    _logger.info("Loading clinical data...")
    validate_data_files()
    
    try:
        drug_data = load_drug_data()
        patients = load_patient_profiles()
        _logger.info("Loaded %d drugs and %d patients", len(drug_data), len(patients))
    except Exception as e:
        _logger.error("FATAL: Failed to load data — %s", e)
        _logger.error("Please check your Excel files in the 'data/' directory.")
        sys.exit(1)
    
    # === 5. Filter patients if --patient specified ===
    if args.patient:
        patients = [p for p in patients if p['Patient_ID'] == args.patient]
        if not patients:
            _logger.error("Patient '%s' not found in data/patients.xlsx", args.patient)
            sys.exit(1)
    
    # === 6. Optimize for each patient ===
    _logger.info("%s", "=" * 60)
    _logger.info("OPTIMIZING %d PATIENT(S)", len(patients))
    _logger.info("%s", "=" * 60)
    
    start_total = time.time()
    success_count = 0
    
    for i, profile in enumerate(patients, 1):
        _logger.info("[%d/%d] Processing patient %s", i, len(patients), profile.get('Patient_ID', 'unknown'))
        if optimize_patient(profile, drug_data, output_dir):
            success_count += 1
    
    # === 7. Final report ===
    elapsed_total = time.time() - start_total
    _logger.info("%s", "=" * 60)
    _logger.info("OPTIMIZATION COMPLETE")
    _logger.info("%s", "=" * 60)
    if not args.verbose:
        # Minimal summary by default (no emojis)
        print(f"Patients processed: {success_count}/{len(patients)}")
        print(f"Total time: {elapsed_total:.1f} seconds")
        print(f"Reports saved in: {os.path.abspath(output_dir)}")
    else:
        _logger.info("Patients processed: %d/%d", success_count, len(patients))
        _logger.info("Total time: %.1f seconds", elapsed_total)
        _logger.info("Reports saved in: %s", os.path.abspath(output_dir))
        _logger.info("Next steps:")
        _logger.info("  Review Excel reports in 'reports/regimens/'")
        _logger.info("  Edit data/patients.xlsx to add new cases")
        _logger.info("%s", "=" * 60)
    # === Aggregate visualizations (after all patients processed) ===
    if '--visualize' in sys.argv and hasattr(optimize_patient, 'all_results'):
        from visualization import DrugRegimenVisualizer
        
        results = optimize_patient.all_results
        drug_viz = DrugRegimenVisualizer(output_dir=os.path.join(output_dir, 'viz'))
        
        regimens = [r['regimen'] for r in results]
        fitnesses = [r['fitness'] for r in results]
        patient_ids = [r['patient_id'] for r in results]
        
        drug_viz.plot_drug_frequency(regimens, drug_data, patient_ids)
        # plot_class_balance and plot_cost_efficacy_scatter removed from the
        # default run. The class-distribution pie is tautological -- every
        # regimen is two NRTIs plus one third agent by construction, so NRTI is
        # always exactly 66.7% -- and the cost/efficacy scatter collapses
        # duplicate optima into overlapping points. Both remain available in
        # visualization/ if wanted explicitly.
        
        _logger.info("✓ Visualizations saved to: %s", os.path.join(output_dir, 'viz'))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Process interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logging.error("UNEXPECTED ERROR: %s", e)
        if '--debug' in sys.argv:
            traceback.print_exc()
        logging.error("Tip: Run with --debug for detailed error information")
        sys.exit(1)