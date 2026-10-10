"""Command-line DSS using the same warehouse query and model as Streamlit."""
import argparse
from math import isclose
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from frontend.warehouse import DatabaseConfigurationError, load_monthly_facts
from dss.authority import DEFAULT_WEIGHTS, LABELS, prepare_authorities
from dss.model import Criterion, DecisionSupportModel


def main(argv=None):
    parser = argparse.ArgumentParser(description='Rank London authorities for road safety investigation.')
    parser.add_argument('--years', type=int, nargs='+', choices=range(2021, 2026), default=list(range(2021, 2026)))
    parser.add_argument('--weights', type=float, nargs=3, metavar=('BURDEN', 'CHANGE', 'SHARE'))
    parser.add_argument('--threshold', type=float, default=0.)
    parser.add_argument('--top', type=int, default=5)
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error('--top must be positive')
    weights = dict(zip(LABELS, args.weights)) if args.weights is not None else dict(DEFAULT_WEIGHTS)
    if len(set(args.years)) < 2:
        if args.weights and weights['ksi_change_pct'] != 0:
            parser.error('Trend weight must be zero for a single selected year')
        weights['ksi_change_pct'] = 0
    try:
        model = DecisionSupportModel([Criterion(k, v) for k, v in weights.items()], args.threshold)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        rows = load_monthly_facts()
    except (DatabaseConfigurationError, psycopg.Error):
        print('Cannot query PostgreSQL. Check DW_DATABASE_URL and the loaded dw schema.')
        return 1
    alternatives, details, excluded = prepare_authorities(rows, args.years)
    print('Selected years:', ', '.join(map(str, sorted(set(args.years)))))
    print('Eligible authorities:', len(alternatives), '| Excluded:', len(excluded))
    for item in excluded:
        print(item['authority_code'] + ': ' + item['reason'])
    if len(alternatives) < 2:
        print('At least two eligible authorities are needed for comparative recommendations.')
        return 0
    result = model.recommend(alternatives)
    print(result.reason)
    cutoff = result.ranking[min(args.top, len(result.ranking)) - 1][1]
    for code, score in result.ranking:
        if score < cutoff and not isclose(score, cutoff, abs_tol=1e-12):
            continue
        selected = score >= args.threshold and score > 1e-12
        parts = ', '.join(f'{LABELS[k]}={v:.4f}' for k, v in result.contributions[code].items())
        print(f"{code} | {details[code]['authority_name']} | {score:.4f} | "
              f"{'recommend' if selected else 'below threshold'} | {parts}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
