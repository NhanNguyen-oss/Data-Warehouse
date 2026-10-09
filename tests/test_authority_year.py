import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "etl"))

import authority_year as ay  # noqa: E402

VALID = {"2023": {"E09000017", "E08000019", "E06000063"}, "2024": {"E09000017", "E08000019", "E06000063"}}
CODE_MAP = ay.CodeMap([
    ay.CodeRule("stats19", "EHEATHROW", "E09000017", 2021, 2025, ""),
    ay.CodeRule("stats19", "E08000039", "E08000019", 2025, 2025, ""),
])


def collision(code, year="2023", severity="3", adjusted="0", casualties="1", road_class="3"):
    return {
        "collision_year": year, "local_authority_highway": code, "collision_severity": severity,
        "collision_adjusted_severity_serious": adjusted, "collision_injury_based": "1",
        "number_of_casualties": casualties, "first_road_class": road_class,
    }


def aadf(point, year, code, flow="1000", length="2", road_type="Major", method="Counted"):
    return {
        "count_point_id": point, "year": year, "local_authority_code": code, "local_authority_name": code,
        "all_motor_vehicles": flow, "link_length_km": length, "road_type": road_type, "estimation_method": method,
    }


class CodeMapTest(unittest.TestCase):
    def test_rule_respects_year_window(self):
        self.assertEqual(CODE_MAP.apply("stats19", "E08000039", "2025"), "E08000019")
        self.assertEqual(CODE_MAP.apply("stats19", "E08000039", "2024"), "E08000039")
        self.assertEqual(CODE_MAP.apply("aadf", "EHEATHROW", "2023"), "EHEATHROW")

    def test_committed_map_loads(self):
        rules = ay.CodeMap.load().rules
        self.assertTrue(any(rule.from_code == "EHEATHROW" for rule in rules))


class CollisionAggregateTest(unittest.TestCase):
    def test_remap_unmatched_and_measures(self):
        audit = ay.Audit()
        rows = [
            collision("EHEATHROW", severity="1", casualties="2"),
            collision("E09000017", severity="2", adjusted="1"),
            collision("E09000017", severity="3", adjusted="0.25", road_class="6"),
            collision("E99999999"),
            collision("E09000017", year="2019"),
        ]
        totals, in_scope = ay.aggregate_collisions(rows, {"2023"}, CODE_MAP, VALID, audit)
        self.assertEqual(in_scope, 4)
        bucket = totals[("E09000017", "2023")]
        self.assertEqual(bucket["collisions"], 3)
        self.assertEqual(bucket["fatal_collisions"], 1)
        self.assertEqual(bucket["casualties"], 4)
        self.assertEqual(bucket["major_road_collisions"], 2)
        self.assertAlmostEqual(bucket["adjusted_serious"], 1.25)
        self.assertEqual(totals[(ay.UNMATCHED, "2023")]["collisions"], 1)
        self.assertEqual(audit.remaps[("stats19", "2023", "EHEATHROW", "E09000017", "authority_code_map")], 1)


class AadfAggregateTest(unittest.TestCase):
    def test_stale_code_uses_later_code_of_same_point(self):
        audit = ay.Audit()
        rows = [
            aadf("1", "2023", "E10000006"),
            aadf("1", "2024", "E06000063"),
            aadf("2", "2023", "E10000006"),
            aadf("3", "2023", "E06000063", flow="500", length="", road_type="Minor", method="Estimated"),
        ]
        totals, _, in_scope = ay.aggregate_aadf(rows, {"2023"}, VALID, audit)
        self.assertEqual(in_scope, 3)
        bucket = totals[("E06000063", "2023")]
        self.assertEqual(bucket["aadf_count_points"], 2)
        self.assertEqual(bucket["aadf_major_points"], 1)
        self.assertEqual(bucket["aadf_major_vehicle_km"], 1000 * 2 * 365)
        self.assertEqual(totals[(ay.UNMATCHED, "2023")]["aadf_count_points"], 1)
        self.assertEqual(audit.remaps[("aadf", "2023", "E10000006", "E06000063", "count_point_later_code")], 1)

    def test_leap_year_days(self):
        self.assertEqual(ay.days_in_year("2024"), 366)
        self.assertEqual(ay.days_in_year("2025"), 365)


class CombineTest(unittest.TestCase):
    def test_one_row_per_key_and_no_fan_out(self):
        collisions = {("E09000017", "2023"): Counter(collisions=10, fatal_collisions=1, serious_collisions=2,
                                                     adjusted_serious=2.5, major_road_collisions=4)}
        flows = {("E09000017", "2023"): Counter(aadf_count_points=3, aadf_counted_points=1, aadf_flow_sum=3000,
                                                aadf_major_vehicle_km=2e8)}
        la = {("E09000017", "2023"): {"la_network_km": 100.0, "la_vehicle_km": 1e9},
              ("E08000019", "2023"): {"la_network_km": 50.0, "la_vehicle_km": 5e8}}
        output = ay.combine(collisions, flows, la, {"E09000017": "Hillingdon"})
        self.assertEqual(len(output), 2)
        row = next(r for r in output if r["authority_code"] == "E09000017")
        self.assertEqual(row["collisions"], 10)
        self.assertEqual(row["aadf_count_points"], 3)
        self.assertEqual(row["adjusted_ksi_collisions"], 3.5)
        self.assertEqual(row["aadf_estimated_share_pct"], 66.67)
        self.assertEqual(row["aadf_mean_all_motor_vehicles"], 1000.0)
        self.assertEqual(row["candidate_collisions_per_100m_vkm"], 1.0)
        self.assertEqual(row["candidate_major_collisions_per_100m_major_vkm"], 2.0)
        empty = next(r for r in output if r["authority_code"] == "E08000019")
        self.assertEqual(empty["collisions"], 0)
        self.assertIsNone(empty["severe_collision_share_pct"])
        self.assertIsNone(empty["candidate_major_collisions_per_100m_major_vkm"])
        checks = ay.reconcile(output, 10, 3, 2, ["2023"])
        self.assertEqual(checks["duplicate_keys"], 0)
        self.assertEqual(checks["collisions_output"], 10)
        self.assertEqual(checks["authority_years_missing_collisions"], [("E08000019", "2023")])


if __name__ == "__main__":
    unittest.main()
