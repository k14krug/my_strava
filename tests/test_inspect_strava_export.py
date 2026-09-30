import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import inspect_strava_export as tool


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private-export-name"
        (self.root / "activities").mkdir(parents=True)

    def make_csv(self, lines):
        (self.root / "activities.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def make_file(self, name, size):
        path = self.root / "activities" / name
        path.write_bytes(b"x" * size)

    def test_schema_matching_anomalies_and_coverage(self):
        self.make_csv([
            "Activity ID,Activity Date,Sport Type,Filename,Trainer,Average Power,Custom Column",
            "101,Jan 2 2020,Ride,activities/101.fit.gz,0,150,private free text",
            "102,Feb 3 2021,VirtualRide,activities/102.tcx,1,,other free text",
            "103,Mar 4 2022,Ride,activities/103.gpx,,100,",
            "104,Apr 5 2022,Ride,activities/404.fit,,,",
            "105,May 6 2022,Ride,activities/101.fit.gz,,,",
            "106,Jun 7 2022,Ride,,,,",
            "101,Jul 8 2022,Ride,activities/CASE.fit,,,",
        ])
        self.make_file("101.fit.gz", 100)
        self.make_file("102.tcx", 2500)
        self.make_file("103.gpx", 4000)
        self.make_file("case.fit", 0)
        self.make_file("999.fit", 700)
        report = tool.inventory(self.root)
        self.assertEqual(report["csv"]["row_count"], 7)
        self.assertEqual(report["csv"]["columns"][-1], "Custom Column")
        self.assertEqual(report["csv"]["column_nonempty_counts"]["Custom Column"], 2)
        self.assertIn("distance", report["csv"]["expected_fields_absent"])
        self.assertEqual(report["csv"]["earliest_date"], "2020-01-02")
        self.assertEqual(report["csv"]["counts_by_year"]["2022"], 5)
        self.assertEqual(report["associations"]["references_existing_exactly"], 4)
        self.assertEqual(report["associations"]["references_missing_exactly"], 2)
        self.assertEqual(report["associations"]["rows_without_reference"], 1)
        self.assertEqual(report["anomalies"]["counts"]["row_without_file_reference"], 1)
        self.assertEqual(report["associations"]["unreferenced_activity_file_count"], 2)
        self.assertEqual(report["associations"]["duplicate_reference_count"], 1)
        self.assertEqual(report["associations"]["duplicate_activity_id_count"], 1)
        self.assertEqual(report["anomalies"]["counts"]["case_mismatch"], 1)
        self.assertEqual(report["file_format_coverage"]["by_year"]["2020"][".fit.gz"], 1)
        self.assertEqual(report["file_sizes"]["zero_byte_count"], 1)
        self.assertTrue(any("earliest dated activity" in candidate["reasons"]
                            for candidate in report["candidate_files"]))
        self.assertTrue(any("unreferenced activity file" in candidate["reasons"]
                            for candidate in report["candidate_files"]))
        self.assertFalse(any("proxy (Activity Type:" in reason
                             for candidate in report["candidate_files"]
                             for reason in candidate["reasons"]))
        output = json.dumps(report, sort_keys=True)
        self.assertNotIn("private-export-name", output)
        self.assertNotIn("private free text", output)
        self.assertNotIn(self.temp.name, output)
        self.assertEqual(output, json.dumps(tool.inventory(self.root), sort_keys=True))

    def test_duplicate_headers_and_route_gpx_exclusion(self):
        self.make_csv([
            "Activity ID,Activity Date,Filename,Distance,Distance,Average Watts",
            "1,2020-01-01,activities/1.fit,,12,150",
        ])
        self.make_file("1.fit", 10)
        (self.root / "routes").mkdir()
        (self.root / "routes" / "1.gpx").write_bytes(b"route")
        report = tool.inventory(self.root)
        self.assertEqual(report["csv"]["columns"].count("Distance"), 2)
        distance = [item for item in report["csv"]["column_details"] if item["name"] == "Distance"]
        self.assertEqual([item["nonempty_count"] for item in distance], [0, 1])
        self.assertEqual(report["structure"]["activity_formats"][".fit"]["count"], 1)
        self.assertEqual(report["associations"]["unreferenced_activity_file_count"], 0)
        self.assertEqual(report["csv"]["recognized_fields"]["power"], ["Average Watts"])

    def test_cycling_modality_candidates_use_activity_type_without_trainer(self):
        self.make_csv([
            "Activity ID,Activity Date,Activity Type,Filename",
            "1,2020-01-01,Ride,activities/1.fit",
            "2,2020-01-02,Virtual Ride,activities/2.fit",
        ])
        self.make_file("1.fit", 2000)
        self.make_file("2.fit", 2000)
        report = tool.inventory(self.root)
        self.assertEqual(report["csv"]["recognized_fields"]["trainer"], [])
        by_id = {candidate["activity_id"]: candidate["reasons"]
                 for candidate in report["candidate_files"]}
        self.assertIn("outdoor-ride proxy (Activity Type: Ride)", by_id["1"])
        self.assertIn("virtual/indoor proxy (Activity Type: Virtual Ride)", by_id["2"])

    def test_compound_extension_and_size_definition(self):
        self.assertEqual(tool.extension("example.FIT.GZ"), ".fit.gz")
        self.assertEqual(tool.size_statistics([0, 100, 2000, 3000, 4000])["p90_bytes"], 4000)
        self.assertEqual(tool.size_statistics([0, 100, 2000, 3000])["median_bytes"], 1050)

    def test_rejects_missing_csv_and_unrecognizable_schema(self):
        with self.assertRaisesRegex(ValueError, "activities.csv"):
            tool.inventory(self.root)
        self.make_csv(["Other,Columns", "abc,def"])
        with self.assertRaisesRegex(ValueError, "no recognizable"):
            tool.inventory(self.root)

    def test_report_writes_outside_source_and_is_byte_stable(self):
        self.make_csv(["Activity ID,Activity Date,Filename", "1,2020-01-01,activities/1.fit"])
        self.make_file("1.fit", 10)
        output = Path(self.temp.name) / "results"
        self.assertEqual(tool.main([str(self.root), "--output-dir", str(output)]), 0)
        first = [(output / filename).read_bytes() for filename in ("inventory.json", "inventory.md")]
        self.assertEqual(tool.main([str(self.root), "--output-dir", str(output)]), 0)
        second = [(output / filename).read_bytes() for filename in ("inventory.json", "inventory.md")]
        self.assertEqual(first, second)
        self.assertNotIn(str(self.root).encode(), first[0])


if __name__ == "__main__":
    unittest.main()
