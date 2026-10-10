"""Prepare comparable authority-level DSS inputs from warehouse monthly aggregates."""
from collections import defaultdict
from math import isfinite
from .model import Alternative

DEFAULT_WEIGHTS = {'mean_ksi': 50, 'ksi_change_pct': 30, 'ksi_share_pct': 20}
LABELS = {'mean_ksi': 'Annual adjusted KSI', 'ksi_change_pct': 'KSI change (%)',
          'ksi_share_pct': 'Adjusted KSI share (%)'}

def prepare_authorities(rows, years):
    """Require complete selected calendar years; do not treat missing rows as zero."""
    years = sorted(set(years))
    if not years:
        raise ValueError('Select at least one year.')
    groups = defaultdict(list)
    for row in rows:
        if row['year'] in years:
            groups[row['authority_code']].append(row)
    alternatives, details, excluded = [], {}, []
    for code, records in sorted(groups.items()):
        name = records[0]['authority_name']
        periods = {(r['year'], r['month_number']) for r in records}
        expected = {(year, month) for year in years for month in range(1, 13)}
        reason = None
        if periods != expected or len(records) != len(expected):
            reason = 'Missing or duplicate authority-month groups.'
        elif any(r['adjustment_missing'] or r['ksi_adjusted'] is None for r in records):
            reason = 'Incomplete severity adjustments.'
        elif any(not isfinite(float(r['ksi_adjusted'])) or float(r['ksi_adjusted']) < 0
                 or not isfinite(float(r['casualties'])) or r['casualties'] < 0 for r in records):
            reason = 'Invalid casualty or KSI totals.'
        if reason:
            excluded.append({'authority_code': code, 'authority_name': name, 'reason': reason})
            continue
        annual = {year: sum(float(r['ksi_adjusted']) for r in records if r['year'] == year)
                  for year in years}
        casualties = sum(r['casualties'] for r in records)
        total = sum(annual.values())
        if casualties <= 0:
            reason = 'No casualty denominator.'
        elif len(years) > 1 and annual[years[0]] == 0 and annual[years[-1]] > 0:
            reason = 'Zero baseline KSI; percentage change is undefined.'
        if reason:
            excluded.append({'authority_code': code, 'authority_name': name, 'reason': reason})
            continue
        change = (100 * (annual[years[-1]] / annual[years[0]] - 1)
                  if len(years) > 1 and annual[years[0]] > 0 else 0.)
        scores = {'mean_ksi': total / len(years), 'ksi_change_pct': change,
                  'ksi_share_pct': 100 * total / casualties}
        alternatives.append(Alternative(code, scores))
        details[code] = {'authority_code': code, 'authority_name': name,
                         'casualties': casualties, 'first_year_ksi': annual[years[0]],
                         'last_year_ksi': annual[years[-1]], **scores}
    return alternatives, details, excluded
