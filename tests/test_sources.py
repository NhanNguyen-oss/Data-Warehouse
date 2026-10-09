import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "etl"))

import sources  # noqa: E402


class CountCsvRowsTest(unittest.TestCase):
    def test_quoted_newlines_count_as_one_record(self):
        text = 'a,b\n1,"line one\nline two"\n2,x\n'
        rows, header = sources.count_csv_rows(io.StringIO(text))
        self.assertEqual(rows, 2)
        self.assertEqual(header, ["a", "b"])

    def test_header_only(self):
        rows, header = sources.count_csv_rows(io.StringIO("a,b\n"))
        self.assertEqual((rows, header), (0, ["a", "b"]))


class DescribeMembersTest(unittest.TestCase):
    def test_zip_members_are_described(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("inner.csv", "x,y,z\n1,2,3\n4,5,6\n")
                archive.writestr("readme.txt", "ignored")
            members = sources.describe_members(path)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]["name"], "inner.csv")
        self.assertEqual(members[0]["rows"], 2)
        self.assertEqual(members[0]["columns"], 3)


class VerifyTest(unittest.TestCase):
    def test_detects_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.csv"
            data.write_text("a\n1\n", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"sources": [
                {"path": "data.csv", "sha256": sources.sha256_of(data)},
                {"path": "missing.csv", "sha256": "0" * 64},
                {"path": "never-downloaded.csv"},
            ]}), encoding="utf-8")
            original_root = sources.ROOT
            sources.ROOT = root
            try:
                self.assertEqual(sources.verify(manifest), ["missing.csv: thiếu trên máy"])
                data.write_text("a\n2\n", encoding="utf-8")
                problems = sources.verify(manifest)
            finally:
                sources.ROOT = original_root
        self.assertEqual(len(problems), 2)
        self.assertIn("data.csv", problems[0])


class RegistryTest(unittest.TestCase):
    def test_ids_are_unique_and_traffic_has_urls(self):
        ids = [source.source_id for source in sources.SOURCES]
        self.assertEqual(len(ids), len(set(ids)))
        for source in sources.SOURCES:
            if source.source_id.startswith("traffic_"):
                self.assertTrue(source.download_url)
                self.assertTrue(source.relative_path.startswith("traffic/"))


if __name__ == "__main__":
    unittest.main()
