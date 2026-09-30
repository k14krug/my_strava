import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import census_activity_coverage as tool

GPX = b'''<?xml version="1.0"?><gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:t="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" creator="Garmin"><trk><trkseg>
<trkpt lat="1" lon="2"><time>2020-01-01T00:00:00Z</time><ele>10</ele><extensions><t:TrackPointExtension><t:hr>100</t:hr><t:cad>80</t:cad></t:TrackPointExtension></extensions></trkpt>
<trkpt lat="1" lon="2"><time>2020-01-01T00:00:01Z</time><ele>11</ele><extensions><t:TrackPointExtension><t:hr>101</t:hr></t:TrackPointExtension></extensions></trkpt>
</trkseg></trk></gpx>'''
TCX = b'''<?xml version="1.0"?><TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" xmlns:a="http://www.garmin.com/xmlschemas/ActivityExtension/v2"><Activities><Activity Sport="Biking"><Lap><Extensions><a:LX><a:AvgWatts>200</a:AvgWatts></a:LX></Extensions><Track><Trackpoint><Time>2021-01-01T00:00:00Z</Time><Extensions><a:TPX><a:Watts>210</a:Watts></a:TPX></Extensions></Trackpoint></Track></Lap></Activity></Activities></TrainingCenterDatabase>'''


class CensusTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "private-export-name"
        (self.root / "activities").mkdir(parents=True)
        (self.root / "activities" / "1.gpx").write_bytes(GPX)
        (self.root / "activities" / "2.tcx.gz").write_bytes(gzip.compress(TCX, mtime=0))
        (self.root / "activities" / "4.gpx").write_text("<gpx><broken>", encoding="utf-8")
        (self.root / "activities.csv").write_text(
            "Activity ID,Activity Date,Activity Type,Filename,Average Watts,Activity Name,Activity Description\n"
            "1,Jan 1 2020,Ride,activities/1.gpx,150,Secret Route,Private words\n"
            "2,Jan 1 2021,Virtual Ride,activities/2.tcx.gz,200,Other Secret,More private words\n"
            "3,Jan 2 2021,Walk,,,No File Secret,Hidden details\n"
            "4,Jan 3 2021,Ride,activities/4.gpx,,Corrupt Secret,Hidden data\n"
            "5,Jan 4 2021,Ride,activities/5.gpx,,Missing Secret,Hidden data\n", encoding="utf-8")
        self.output = Path(temp.name) / "results"

    def report(self):
        return tool.census(self.root)

    def test_population_format_year_and_failure_reconciliation(self):
        report = self.report()
        pop = report["totals"]["population"]
        self.assertEqual((pop["csv_rows"], pop["source_file_backed_rows"], pop["no_file_rows"]), (5, 4, 1))
        self.assertEqual((pop["attempted_source_files"], pop["parsed_source_files"], pop["failed_source_files"]), (4, 2, 2))
        self.assertEqual(report["by_year"]["2020"]["format_counts"], {".gpx": 1})
        self.assertEqual(report["by_year"]["2021"]["csv_rows"], 4)
        self.assertEqual(report["by_activity_type"]["Ride"]["csv_rows"], 3)
        self.assertIn({"year": "2021", "activity_type": "Virtual Ride", "format": ".tcx.gz", "csv_rows": 1}, report["by_year_type_format"])
        self.assertEqual(report["structure"]["GPX"]["denominator_parsed_files"], 1)
        self.assertEqual(report["structure"]["TCX"]["denominator_parsed_files"], 1)
        self.assertEqual(report["diagnostics"]["category_counts"], {"xml_parse_failure": 1, "missing_or_unsafe_file": 1})

    def test_signals_cycling_power_and_extensions(self):
        report = self.report()
        self.assertEqual(report["totals"]["source_signal_coverage"]["gps"]["files"], 1)
        self.assertEqual(report["totals"]["source_signal_coverage"]["power"]["files"], 1)
        ride = report["cycling_cohorts"]["Ride"]
        self.assertEqual(ride["combinations"]["position_altitude_heart_rate_without_source_record_power"], 1)
        self.assertEqual(ride["combinations"]["cadence_without_source_record_power"], 1)
        self.assertEqual(ride["combinations"]["csv_power_without_source_record_power"], 1)
        virtual = report["cycling_cohorts"]["Virtual Ride"]
        self.assertEqual(virtual["combinations"]["source_record_power"], 1)
        self.assertEqual(report["totals"]["source_summary_power_files"], 1)
        self.assertEqual(sum(report["totals"]["power_matrix_all_rows"].values()), 5)
        self.assertTrue(any("TrackPointExtension" in key for key in report["structure"]["GPX"]["extension_tags_by_file"]))
        self.assertTrue(any("TPX" in key for key in report["structure"]["TCX"]["extension_tags_by_file"]))

    def test_gpx_nonpoint_summary_power_without_record_power(self):
        path = self.root / "activities" / "6.gpx"
        path.write_bytes(b'<gpx><extensions><avgPower>125</avgPower><maxPower>200</maxPower></extensions><trk><trkseg><trkpt lat="1" lon="2"><time>2021-01-01T00:00:00Z</time></trkpt></trkseg></trk></gpx>')
        self.assertEqual(tool.gpx_summary_power_tag_count(path), 2)
        self.assertEqual(tool.gpx_summary_power_tag_count(self.root / "activities" / "1.gpx"), 0)
        row = {"id": "6", "reference": "activities/6.gpx", "format": ".gpx", "status": "pending"}
        tool.inspect_one(self.root, row)
        self.assertEqual(row["status"], "parsed")
        self.assertFalse(row["record_power"])
        self.assertTrue(row["summary_power"])

    def test_timing_aggregation_and_fit_structure_file_prevalence(self):
        rows = [
            {"status": "parsed", "format": ".fit", "structure": {"fit_messages": ["record", "session", "field_description"],
             "fit_record_fields": ["power"], "fit_developer_fields": ["foo"], "fit_device_clue": True}},
            {"status": "parsed", "format": ".fit.gz", "structure": {"fit_messages": ["record", "field_description"],
             "fit_record_fields": ["power"], "fit_developer_fields": ["foo"], "fit_device_clue": False}},
        ]
        fit = tool.structure_counts(rows)["FIT"]
        self.assertEqual(fit["messages_by_file"]["record"], 2)
        self.assertEqual(fit["developer_fields_by_file"]["foo"], 2)
        report = self.report()
        self.assertEqual(report["totals"]["timing"]["denominator_parsed_files"], 2)
        self.assertEqual(report["totals"]["timing"]["files_with_points"], 2)
        self.assertEqual(report["totals"]["timing"]["files_with_large_gaps"], 0)
        synthetic = {"status": "parsed", "reference": "activities/1.fit", "format": ".fit", "signals": {name: False for name in tool.SOURCE_SIGNALS},
                     "signal_points": {name: 0 for name in tool.SOURCE_SIGNALS}, "point_count": 4,
                     "record_power": False, "summary_power": False, "csv_power": False,
                     "timing": {"missing_or_invalid_timestamps": 1, "duplicate_timestamps": 1,
                                "backward_or_incompatible_timestamps": 1, "large_gap_count": 1,
                                "positive_delta_seconds": {"common": 1.0, "median": 2.0}}}
        timing = tool.tally([synthetic])["timing"]
        self.assertEqual(timing["files_with_missing_or_invalid_timestamps"], 1)
        self.assertEqual(timing["files_with_duplicate_timestamps"], 1)
        self.assertEqual(timing["files_with_backward_or_incompatible_timestamps"], 1)
        self.assertEqual(timing["files_with_large_gaps"], 1)

    def test_population_change_stops_before_parse(self):
        baseline = Path(self.output.parent) / "inventory.json"
        baseline.write_text(json.dumps({"csv": {"row_count": 6}, "associations": {
            "exact_matched_activity_file_rows": 4, "rows_without_reference": 2}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs from STRAVA-001"):
            tool.census(self.root, baseline)

    def test_output_deterministic_and_private(self):
        args = [str(self.root), "--inventory", "", "--output-dir", str(self.output)]
        self.assertEqual(tool.main(args), 0)
        first = [(self.output / name).read_bytes() for name in ("coverage_census.json", "coverage_census.md")]
        self.assertEqual(tool.main(args), 0)
        second = [(self.output / name).read_bytes() for name in ("coverage_census.json", "coverage_census.md")]
        self.assertEqual(first, second)
        combined = b"".join(first)
        for private in (b"Secret", b"Private words", b"Hidden", b"private-export-name", str(self.root).encode(), b"lat=", b"lon="):
            self.assertNotIn(private, combined)


if __name__ == "__main__":
    unittest.main()
