"""Interactive DSS over the same filtered warehouse aggregates as the dashboard."""
from pathlib import Path
import sys
from math import isclose
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dss.authority import DEFAULT_WEIGHTS, LABELS, prepare_authorities
from dss.model import Criterion, DecisionSupportModel


def ranking_table(result, details, top_n, threshold):
    rows = []
    rank, previous = 0, None
    for position, (code, score) in enumerate(result.ranking, 1):
        if previous is None or not isclose(score, previous, abs_tol=1e-12):
            rank = position
        previous = score
        rows.append({**details[code], 'rank': rank, 'score': score,
                     'recommended': rank <= top_n and score >= threshold and score > 1e-12,
                     **{key + '_contribution': result.contributions[code].get(key, 0.)
                        for key in LABELS}})
    return pd.DataFrame(rows)


def render_dss(view, years):
    st.header('Decision support · Authority priorities')
    st.caption('Prioritize authorities for road safety investigation using the selected years and authorities. '
               'These relative scores support comparison; they do not predict intervention benefits.')
    has_trend = len(set(years)) > 1
    defaults = {**DEFAULT_WEIGHTS, 'ksi_change_pct': DEFAULT_WEIGHTS['ksi_change_pct'] if has_trend else 0}
    with st.expander('Criteria and assumptions'):
        st.markdown('''| Criterion | Measure | Exploratory default | Purpose |
| --- | --- | --- | --- |
| Annual adjusted KSI | Adjusted casualty-level KSI / selected years | 50 | Emphasize severe injury burden |
| KSI change (%) | (Last selected year / first selected year − 1) × 100 | 30 | Emphasize worsening outcomes |
| Adjusted KSI share (%) | Adjusted KSI / all casualties × 100 | 20 | Emphasize severity composition |

Higher values receive higher priority. Weights are normalized to sum to 1. Defaults are exploratory,
not calibrated policy weights. Burden and severity share are related; inspect sensitivity to weights.
Min-max normalization uses the eligible authorities currently selected. Constant criteria contribute zero.
Changing the comparison set can change scores. A single authority cannot be comparatively ranked.
Only complete selected calendar years with severity adjustments are eligible. Zero denominators and
undefined percentage changes are excluded and reported. Missing data is never replaced by demo data.
Traffic exposure and population rates are pending warehouse integration. Ties share a rank and may
increase the number of recommendations beyond the requested top N.''')
    if not has_trend:
        st.info('Select at least two years to compare change. Trend weight is zero for a single year.')
    cols = st.columns(3)
    weights = {}
    for col, (key, label) in zip(cols, LABELS.items()):
        weights[key] = col.slider(label + ' weight', 0, 100, defaults[key],
                                  disabled=key == 'ksi_change_pct' and not has_trend,
                                  key='dss_weight_' + key + ('_single' if not has_trend else '_multi'))
    threshold = st.slider('Minimum priority score', 0.0, 1.0, 0.0, 0.05, key='dss_threshold')
    top_n = st.number_input('Authorities to recommend (ties included)', min_value=1, max_value=33,
                            value=5, step=1, key='dss_top_n')
    if not sum(weights.values()):
        st.warning('Set at least one weight above zero.')
        return
    alternatives, details, excluded = prepare_authorities(view.to_dict('records'), years)
    if excluded:
        st.warning(f'{len(excluded)} authorities excluded by data eligibility checks.')
        st.dataframe(pd.DataFrame(excluded), hide_index=True, width="stretch")
    if len(alternatives) < 2:
        st.info('At least two authorities with complete selected years are needed for comparative recommendations.')
        return
    model = DecisionSupportModel([Criterion(key, value) for key, value in weights.items()], threshold)
    result = model.recommend(alternatives)
    current = ranking_table(result, details, top_n, threshold)
    baseline_model = DecisionSupportModel([Criterion(key, value) for key, value in defaults.items()])
    baseline = ranking_table(baseline_model.recommend(alternatives), details, top_n, 0)
    comparison = current.merge(baseline[['authority_code', 'rank', 'score', 'recommended']],
                               on='authority_code', suffixes=('', '_baseline'))
    comparison['rank_gain'] = comparison.rank_baseline - comparison['rank']
    comparison['selected_years'] = ','.join(map(str, sorted(set(years))))
    comparison['threshold'] = threshold
    comparison['top_n'] = top_n
    for key, value in weights.items():
        comparison['weight_' + key] = value / sum(weights.values())
    st.caption('Effective weights: ' + ', '.join(f'{LABELS[k]} {v/sum(weights.values()):.0%}'
                                              for k, v in weights.items()))
    selected = current[current.recommended]
    if selected.empty:
        st.info('No authority meets the threshold with a positive comparative score.')
    else:
        st.success('Recommended for investigation: ' + ', '.join(selected.authority_name))
        leader = current.iloc[0]
        parts = result.contributions[leader.authority_code]
        strongest = max(parts, key=parts.get)
        st.write(f"{leader.authority_name}: score {leader.score:.4f}; largest contribution is "
                 f"{LABELS[strongest]} ({parts[strongest]:.4f} score points). " + result.reason)
    st.subheader('Ranking and criterion contributions')
    st.dataframe(current, hide_index=True, width="stretch")
    st.subheader('What-if comparison with default weights')
    changed = int((comparison['rank'] != comparison.rank_baseline).sum())
    selection_changes = int((comparison.recommended != comparison.recommended_baseline).sum())
    st.write(f'{changed} authorities changed rank; {selection_changes} changed recommendation status. '
             'Baseline uses default weights and a zero threshold on the same eligible authorities.')
    st.dataframe(comparison[['authority_name', 'rank_baseline', 'rank', 'rank_gain',
                             'score_baseline', 'score', 'recommended_baseline', 'recommended']],
                 hide_index=True, width="stretch")
    st.download_button('Download DSS comparison', comparison.to_csv(index=False).encode('utf-8-sig'),
                       'london_dss_comparison.csv', 'text/csv')
