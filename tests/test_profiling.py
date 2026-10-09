import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "etl"))

import profiling  # noqa: E402

COLLISION_BASE = {
    "collision_index": "", "collision_year": "2024", "date": "01/02/2024", "time": "08:15",
    "collision_severity": "3", "collision_injury_based": "1", "longitude": "-0.1", "latitude": "51.5",
    "local_authority_highway": "E09000001", "local_authority_highway_current": "E09000001",
    "first_road_class": "3", "junction_control": "-1",
}


def collision(**overrides):
    row = dict(COLLISION_BASE)
    row.update(overrides)
    return row


AADF_BASE = {
    "count_point_id": "1", "year": "2024", "region_name": "London", "local_authority_code": "E09000001",
    "road_category": "PA", "road_type": "Major", "link_length_km": "1.5",
    "estimation_method": "Counted", "estimation_method_detailed": "Manual count",
    "pedal_cycles": "5", "two_wheeled_motor_vehicles": "1", "cars_and_taxis": "10", "buses_and_coaches": "2",
    "LGVs": "3", "HGVs_2_rigid_axle": "1", "HGVs_3_rigid_axle": "0", "HGVs_4_or_more_rigid_axle": "0",
    "HGVs_3_or_4_articulated_axle": "0", "HGVs_5_articulated_axle": "0", "HGVs_6_articulated_axle": "1",
    "all_HGVs": "2", "all_motor_vehicles": "18",
}


def aadf(**overrides):
    row = dict(AADF_BASE)
    row.update(overrides)
    return row


class CollisionProfileTest(unittest.TestCase):
    def test_keys_severity_and_sentinels(self):
        rows = [
            collision(collision_index="A", collision_severity="1"),
            collision(collision_index="A"),
            collision(collision_index="B", collision_year="2025", date="31/12/2024"),
            collision(collision_index="C", collision_year="2019"),
            collision(collision_index="D", local_authority_highway="E06000001",
                      local_authority_highway_current="E06000002", longitude="", latitude=""),
        ]
        result = profiling.profile_collisions(rows, {"2024", "2025"})
        self.assertEqual(result["rows_total"], 5)
        self.assertEqual(result["rows_in_scope"], 4)
        self.assertEqual(result["key"]["duplicates"], 1)
        self.assertEqual(result["date_year_differs_from_collision_year"], 1)
        self.assertEqual(result["severity_by_year"]["2024"], {"fatal": 1, "slight": 2})
        self.assertEqual(result["severe_share_by_year_pct"]["2024"], 33.33)
        self.assertEqual(result["sentinel_empty_or_minus1"]["junction_control"]["count"], 4)
        self.assertEqual(result["coordinates"]["missing"], 1)
        self.assertEqual(result["highway_authority"]["rows_where_highway_differs_from_current"], 1)
        self.assertEqual(result["london"]["collisions_total"], 3)
        self.assertEqual(result["_codes_at_event"]["2024"], ["E06000001", "E09000001"])


class AadfProfileTest(unittest.TestCase):
    def test_key_estimation_link_and_sums(self):
        rows = [
            aadf(),
            aadf(),
            aadf(count_point_id="2", road_type="Minor", link_length_km="", estimation_method="Estimated",
                 all_motor_vehicles="19", local_authority_code="E06000001", region_name="North East"),
            aadf(count_point_id="3", year="2010"),
        ]
        result = profiling.profile_aadf(rows, {"2024"})
        self.assertEqual(result["key"]["duplicates"], 1)
        self.assertEqual(result["rows_in_scope"], 3)
        self.assertEqual(result["estimated_share_pct"], 33.33)
        self.assertEqual(result["link_length_missing_or_nonpositive"]["by_year_and_road_type"]["2024"]["Minor"]["pct"], 100.0)
        self.assertEqual(result["measures"]["rows_where_parts_do_not_sum_to_all_motor_vehicles"], 1)
        self.assertEqual(result["measures"]["all_motor_vehicles_minus_parts"], {"1": 1})
        self.assertEqual(result["measures"]["rows_where_hgv_parts_do_not_sum_to_all_HGVs"], 0)
        self.assertEqual(result["london"]["rows_total"], 2)
        self.assertEqual(result["london"]["rows_where_E09_and_region_name_disagree"], 0)


class CrossSourceTest(unittest.TestCase):
    def test_reports_code_differences_per_year(self):
        collision_profile = {"_codes_current": {"2024": ["E09000001", "E08000039"]},
                             "_codes_at_event": {"2024": ["E09000001", "EHEATHROW"]}}
        aadf_profile = {"_codes": {"2024": ["E09000001", "E08000019"]}, "_points": ["1", "2"]}
        la_profile = {"_codes": {"2024": ["E09000001", "E08000019"]}}
        points = {"_ids": ["1"]}
        result = profiling.cross_source(collision_profile, aadf_profile, points, la_profile)
        current = result["authority_codes_by_year"]["2024"]
        self.assertEqual(current["stats19_not_in_aadf"], ["E08000039"])
        self.assertEqual(current["aadf_not_in_stats19"], ["E08000019"])
        self.assertEqual(current["london"]["matched_all_three"], 1)
        self.assertEqual(result["authority_codes_by_year_at_event"]["2024"]["stats19_not_in_aadf"], ["EHEATHROW"])
        self.assertEqual(result["aadf_points_missing_from_count_points"], 1)


class HelpersTest(unittest.TestCase):
    def test_pct_zero_denominator_is_none(self):
        self.assertIsNone(profiling.pct(1, 0))

    def test_private_keys_are_stripped(self):
        self.assertEqual(profiling.strip_private({"a": 1, "_b": 2, "c": {"_d": 3, "e": 4}}), {"a": 1, "c": {"e": 4}})


if __name__ == "__main__":
    unittest.main()
