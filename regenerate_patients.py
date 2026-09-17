"""
Rebuild the synthetic cohort with sourced formulary tiers.

Replaces the ad-hoc 3-4 drug Access_Constraints lists with the WHO-grounded
tiers in config/formulary.py. Clinical fields (mutations, CD4, viral load,
comorbidities) are carried over unchanged -- only the access model changes.

Usage:  python regenerate_patients.py [--seed 9] [--out data/AllPatients_v2.xlsx]
"""
import argparse, random
import pandas as pd
from config.formulary import FORMULARY_TIERS, TIER_DISTRIBUTION, get_formulary


def assign_tiers(n, seed):
    """Deterministic tier assignment matching TIER_DISTRIBUTION as closely as n allows."""
    rng = random.Random(seed)
    names = list(TIER_DISTRIBUTION)
    counts = {t: int(round(TIER_DISTRIBUTION[t] * n)) for t in names}
    while sum(counts.values()) < n:
        counts[names[0]] += 1
    while sum(counts.values()) > n:
        counts[max(counts, key=counts.get)] -= 1
    tiers = [t for t, c in counts.items() for _ in range(c)]
    rng.shuffle(tiers)
    return tiers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='data/AllPatients.xlsx')
    ap.add_argument('--out', default='data/AllPatients_v2.xlsx')
    ap.add_argument('--seed', type=int, default=9)
    args = ap.parse_args()

    df = pd.read_excel(args.src)
    tiers = assign_tiers(len(df), args.seed)

    df['Formulary_Tier'] = tiers
    df['Access_Constraints'] = [', '.join(get_formulary(t)) for t in tiers]

    df.to_excel(args.out, index=False)

    print(f"Wrote {args.out}  ({len(df)} patients)")
    print()
    for t in FORMULARY_TIERS:
        n = tiers.count(t)
        print(f"  {t:<18}{n:>3} patients   {len(get_formulary(t)):>3} drugs available")


if __name__ == '__main__':
    main()
