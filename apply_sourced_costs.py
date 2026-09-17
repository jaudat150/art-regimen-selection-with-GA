"""
Rewrite drugs.xlsx monthly costs from the sourced table in config/drug_costs.py.

Writes data/drugs_sourced.xlsx and a provenance CSV for the paper appendix.
Usage:  python apply_sourced_costs.py
"""
import pandas as pd
from config.drug_costs import monthly_cost, provenance_table, unsourced_drugs

sheets = pd.read_excel('data/drugs.xlsx', sheet_name=None)
df = sheets['Drugs']
old = df['Monthly_Cost_USD'].copy()
df['Monthly_Cost_USD'] = [monthly_cost(d) if monthly_cost(d) is not None else c
                          for d, c in zip(df['Drug'], df['Monthly_Cost_USD'])]
with pd.ExcelWriter('data/drugs_sourced.xlsx', engine='openpyxl') as w:
    for name, sheet in sheets.items():
        sheet.to_excel(w, sheet_name=name, index=False)

pd.DataFrame(provenance_table(),
             columns=['Drug', 'USD_per_person_year', 'USD_per_month',
                      'Source', 'Note']
             ).to_csv('paper/tables/table1b_cost_provenance.csv', index=False)

print(f"{'Drug':<12}{'old $/mo':>10}{'new $/mo':>10}{'change':>10}")
for d, o, n in zip(df['Drug'], old, df['Monthly_Cost_USD']):
    if abs(o - n) > 1e-9:
        print(f'{d:<12}{o:>10.2f}{n:>10.2f}{n/o:>9.2f}x')
print()
print('TLD (TDF+3TC+DTG) per person-year:',
      round(sum(monthly_cost(d) for d in ('TDF', '3TC', 'DTG')) * 12, 2))
print('Estimates (no published LMIC price):', ', '.join(unsourced_drugs()))
print('\nWritten: data/drugs_sourced.xlsx, paper/tables/table1b_cost_provenance.csv')
