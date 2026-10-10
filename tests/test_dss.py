import math
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dss.model import Alternative, Criterion, DecisionSupportModel
from dss.authority import prepare_authorities


def monthly_rows():
    rows = []
    for code, totals in [('E09000001', (120, 120)), ('E09000002', (12, 60)), ('E09000003', (60, 36))]:
        for year, total in zip([2024, 2025], totals):
            for month in range(1, 13):
                rows.append(dict(authority_code=code, authority_name=code, year=year,
                    month_number=month, collisions=10, casualties=100, fatalities=0,
                    ksi_adjusted=total / 12, adjustment_missing=0))
    return rows


class ModelTests(unittest.TestCase):
    def test_known_scores_and_contributions(self):
        model = DecisionSupportModel([Criterion('burden', 3), Criterion('cost', 1, False)])
        result = model.recommend([Alternative('A', {'burden': 10, 'cost': 5}),
                                  Alternative('B', {'burden': 0, 'cost': 0})])
        self.assertEqual(result.ranking, [('A', .75), ('B', .25)])
        self.assertEqual(sum(result.contributions['A'].values()), .75)

    def test_weight_change_reverses_recommendation(self):
        alternatives = [Alternative('A', {'x': 10, 'y': 0}), Alternative('B', {'x': 0, 'y': 10})]
        self.assertEqual(DecisionSupportModel([Criterion('x', 3), Criterion('y', 1)]).recommend(alternatives).chosen, 'A')
        self.assertEqual(DecisionSupportModel([Criterion('x', 1), Criterion('y', 3)]).recommend(alternatives).chosen, 'B')

    def test_constant_and_singleton_do_not_imply_priority(self):
        for direction in [True, False]:
            model = DecisionSupportModel([Criterion('x', 1, direction)])
            result = model.recommend([Alternative('A', {'x': 5}), Alternative('B', {'x': 5})])
            self.assertEqual(result.chosen, 'CHUA_QUYET')
            self.assertTrue(all(score == 0 for _, score in result.ranking))
            self.assertEqual(model.recommend([Alternative('A', {'x': 5})]).chosen, 'CHUA_QUYET')

    def test_ties_threshold_and_no_rounding_before_order(self):
        model = DecisionSupportModel([Criterion('x', 1), Criterion('y', 1)], .6)
        result = model.recommend([Alternative('B', {'x': 0, 'y': 1}), Alternative('A', {'x': 1, 'y': 0})])
        self.assertEqual(result.tied, ('A', 'B'))
        self.assertEqual(result.chosen, 'CHUA_QUYET')
        result = DecisionSupportModel([Criterion('x', 1)]).recommend([
            Alternative('A', {'x': .999999}), Alternative('B', {'x': 1}), Alternative('C', {'x': 0})])
        self.assertEqual(result.chosen, 'B')

    def test_validation_and_missing_active_criteria(self):
        for weights in [[], [Criterion('x', 0)], [Criterion('x', -1)], [Criterion('x', math.nan)],
                        [Criterion('x', 1), Criterion('x', 1)]]:
            with self.assertRaises(ValueError):
                DecisionSupportModel(weights)
        for threshold in [-1, 2, math.inf]:
            with self.assertRaises(ValueError):
                DecisionSupportModel([Criterion('x', 1)], threshold)
        model = DecisionSupportModel([Criterion('x', 1), Criterion('ignored', 0)])
        result = model.recommend([Alternative('A', {'x': 1}), Alternative('B', {'x': math.nan})])
        self.assertEqual(result.excluded, ('B',))


class AuthorityInputTests(unittest.TestCase):
    def test_duplicate_period_and_zero_casualties_are_excluded(self):
        rows = monthly_rows()
        rows.append(dict(rows[0]))
        for row in rows:
            if row['authority_code'] == 'E09000002':
                row['casualties'] = 0
        alternatives, _, excluded = prepare_authorities(rows, [2024, 2025])
        self.assertEqual(len(alternatives), 1)
        self.assertEqual(len(excluded), 2)

    def test_top_n_includes_all_tied_authorities(self):
        from frontend.dss_panel import ranking_table
        alternatives = [Alternative('A', {'x': 1, 'y': 0}),
                        Alternative('B', {'x': 0, 'y': 1}), Alternative('C', {'x': 0, 'y': 0})]
        result = DecisionSupportModel([Criterion('x', 1), Criterion('y', 1)]).recommend(alternatives)
        details = {a.name: {'authority_code': a.name} for a in alternatives}
        table = ranking_table(result, details, 1, 0)
        self.assertEqual(table['rank'].tolist(), [1, 1, 3])
        self.assertEqual(table.recommended.tolist(), [True, True, False])

    def test_exact_annual_measures(self):
        alternatives, details, excluded = prepare_authorities(monthly_rows(), [2024, 2025])
        self.assertEqual(len(alternatives), 3)
        self.assertFalse(excluded)
        self.assertEqual(details['E09000002']['mean_ksi'], 36)
        self.assertEqual(details['E09000002']['ksi_change_pct'], 400)
        self.assertEqual(details['E09000002']['ksi_share_pct'], 3)

    def test_missing_year_or_adjustment_is_excluded(self):
        rows = monthly_rows()
        rows.pop(0)
        rows[24]['adjustment_missing'] = 1
        alternatives, _, excluded = prepare_authorities(rows, [2024, 2025])
        self.assertEqual(len(alternatives), 1)
        self.assertEqual(len(excluded), 2)

    def test_zero_baseline_and_single_year(self):
        rows = monthly_rows()
        for row in rows:
            if row['authority_code'] == 'E09000001' and row['year'] == 2024:
                row['ksi_adjusted'] = 0
        self.assertEqual(len(prepare_authorities(rows, [2024, 2025])[2]), 1)
        _, details, excluded = prepare_authorities(rows, [2025])
        self.assertFalse(excluded)
        self.assertTrue(all(d['ksi_change_pct'] == 0 for d in details.values()))


if __name__ == '__main__':
    unittest.main()
