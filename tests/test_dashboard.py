"""Configuration and dashboard behavior without a live PostgreSQL dependency."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "frontend"))
import warehouse
import psycopg
import streamlit as st
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "src" / "frontend" / "app.py"


class ConfigurationTests(unittest.TestCase):
    def test_container_settings_preserve_special_password_characters(self):
        from psycopg.conninfo import conninfo_to_dict
        with patch.dict(os.environ, {"PGHOST": "db", "PGPASSWORD": "p@ss=word'", "PGDATABASE": "road_safety_dw"}, clear=True):
            settings = conninfo_to_dict(warehouse.database_url())
        self.assertEqual(settings["host"], "db")
        self.assertEqual(settings["password"], "p@ss=word'")

    def test_environment_overrides_file(self):
        with patch.dict(os.environ, {"DW_DATABASE_URL": "postgresql://environment/db"}):
            self.assertEqual(warehouse.database_url(Path("missing.env")), "postgresql://environment/db")

    def test_quoted_url_and_equals_in_password(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / ".env"
            path.write_text('# comment\nDW_DATABASE_URL="postgresql://u:p=a@localhost/db"\n', encoding="utf-8-sig")
            self.assertEqual(warehouse.database_url(path), "postgresql://u:p=a@localhost/db")

    def test_missing_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(warehouse.DatabaseConfigurationError):
                warehouse.database_url(Path("missing.env"))


class DashboardTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()

    def test_database_failure_has_no_demo_or_secret(self):
        with patch.object(warehouse, "load_monthly_facts", side_effect=psycopg.OperationalError("secret-password")):
            app = AppTest.from_file(str(APP)).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.error), 1)
        self.assertNotIn("secret-password", app.error[0].value)
        self.assertEqual(len(app.metric), 0)

    def test_filters_recompute_metrics_and_empty_selection(self):
        rows = [dict(year=year, month_number=1, authority_code="E09000017",
                     authority_name="Hillingdon", collisions=count, casualties=count+2,
                     fatalities=1, ksi_adjusted=3.5, adjustment_missing=0)
                for year, count in [(2024, 10), (2025, 20)]]
        with patch.object(warehouse, "load_monthly_facts", return_value=rows):
            app = AppTest.from_file(str(APP)).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.metric[0].value, "30")
            app.multiselect[0].set_value([2025]).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.metric[0].value, "20")
            app.multiselect[1].set_value([]).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.metric), 0)
            self.assertEqual(len(app.info), 1)

    def test_incomplete_adjustments_not_presented_as_total(self):
        rows = [dict(year=2025, month_number=1, authority_code="E09000017",
                     authority_name="Hillingdon", collisions=1, casualties=2,
                     fatalities=0, ksi_adjusted=0., adjustment_missing=2)]
        with patch.object(warehouse, "load_monthly_facts", return_value=rows):
            app = AppTest.from_file(str(APP)).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[3].value, "Incomplete")

    def test_dss_weights_and_threshold_change_recommendations(self):
        from test_dss import monthly_rows
        with patch.object(warehouse, 'load_monthly_facts', return_value=monthly_rows()):
            app = AppTest.from_file(str(APP)).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.dataframe[1].value.iloc[0].authority_code, 'E09000001')
            next(s for s in app.slider if s.key == 'dss_threshold').set_value(.95)
            app.run()
            self.assertFalse(app.exception)
            self.assertFalse(app.dataframe[1].value.recommended.any())
            next(s for s in app.slider if s.key == 'dss_threshold').set_value(0.)
            for key, value in [('mean_ksi', 0), ('ksi_share_pct', 0), ('ksi_change_pct', 100)]:
                next(s for s in app.slider if s.key == 'dss_weight_' + key + '_multi').set_value(value)
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.dataframe[1].value.iloc[0].authority_code, 'E09000002')
            next(s for s in app.slider if s.key == 'dss_weight_ksi_change_pct_multi').set_value(0)
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any('above zero' in w.value for w in app.warning))

    def test_dss_single_year_disables_trend(self):
        from test_dss import monthly_rows
        with patch.object(warehouse, 'load_monthly_facts', return_value=monthly_rows()):
            app = AppTest.from_file(str(APP)).run()
            app.multiselect[0].set_value([2025]).run()
            self.assertFalse(app.exception)
            slider = next(s for s in app.slider if s.key == 'dss_weight_ksi_change_pct_single')
            self.assertTrue(slider.disabled)
            self.assertEqual(slider.value, 0)


if __name__ == "__main__":
    unittest.main()
