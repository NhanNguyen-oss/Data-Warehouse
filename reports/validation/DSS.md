# London road safety DSS validation

Verified 2026-10-10 (Asia/Bangkok) against the loaded PostgreSQL warehouse.

The DSS consumes the dashboard's read-only monthly warehouse query. Collision and
casualty facts are aggregated independently; KSI is measured at casualty level.
No raw CSV or demo observations are used as DSS input.

## Criteria and methodology

| Criterion | Definition | Exploratory default weight |
| --- | --- | ---: |
| Annual adjusted KSI | Sum of adjusted KSI / number of selected years | 50% |
| KSI change | (Last selected year's KSI / first selected year's KSI - 1) × 100% | 30% |
| Adjusted KSI share | Sum of adjusted KSI / sum of casualties × 100% | 20% |

Adjusted KSI = fatalities + adjusted serious casualties. All criteria prioritize
higher values. Default weights emphasize injury burden, followed by deterioration
and severity composition; they are exploratory assumptions, not calibrated policy.
Burden favors larger authorities; burden and severity share are related. Percentage
change can be volatile with small initial KSI. First/last-year KSI and casualty
denominators are included in the ranking for inspection. This model prioritizes
investigation, without estimating the effect of spending or interventions.

Weights must be finite, nonnegative, and not all zero; they are normalized to sum
to one. Criteria are min-max normalized over the selected eligible authorities.
Constant criteria contribute zero. Missing/nonfinite active inputs are excluded
by the model. The authority preparation step conservatively requires complete
selected calendar years and severity adjustments for all criteria, even if a
weight is zero, so what-if scenarios use the same eligible comparison set.
Zero casualty denominators or zero initial KSI with positive final KSI are
excluded with reasons. Both endpoint KSI values zero give zero change. A single
year disables the trend criterion. Nonconsecutive selections use the first and
last selected years and are not annualized growth rates.

Ranks are computed before display rounding. Ties share a rank and are included
at the top-N boundary. A score must be positive and meet the user's threshold
to qualify; constant criteria and a single authority do not establish comparative
priority. Scores and thresholds are relative to the comparison set, not risk
probabilities. The default-weight scenario uses a zero threshold on the same
eligible authorities. The comparison CSV includes years, weights, threshold,
top N, raw criteria, weighted contributions, and ranking/status changes.

## Live checks

- Years 2021–2025: 33 eligible authorities; no exclusions.
- Default weights, threshold 0, top 5:

| Authority | Score |
| --- | ---: |
| Westminster | 0.7276 |
| Southwark | 0.5660 |
| City of London | 0.5000 |
| Kensington and Chelsea | 0.4942 |
| Lambeth | 0.4622 |

- Trend-only scenario: City of London ranks first; 32 authorities change rank.
- Live Streamlit AppTest exercised default ranking, changed weights, and the
  single-year view without application errors. Single-year 2025: 33 eligible.
- Unit/UI suite: 35 tests pass, covering analytical scores/contributions, reversed
  priority, invalid weights, missing/nonfinite inputs, constants, singleton,
  ties, thresholds, duplicate/missing months, zero denominators, zero baseline,
  all-zero weights in the UI, and single-year controls.

Reproduce the default DSS from PowerShell:

```powershell
.venv\Scripts\python.exe src/dss/model.py --years 2021 2022 2023 2024 2025 --top 5
.venv\Scripts\python.exe src/dss/model.py --weights 0 100 0 --top 5
.venv\Scripts\python.exe -m unittest discover -s tests
```

Traffic exposure, population rates, and causal impact evaluation remain pending.
This validates the implemented decision rule and its data flow, not stakeholder
acceptance or the effectiveness of any proposed road safety intervention.
