import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import inspect_activity_samples as tool


GPX = b'''<?xml version="1.0"?><gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:g="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" creator="Garmin"><trk><trkseg>
<trkpt lat="1" lon="2"><time>2020-01-01T00:00:00Z</time><ele>10</ele><extensions><g:TrackPointExtension><g:hr>100</g:hr><g:cad>80</g:cad><g:atemp>20</g:atemp><g:power>150</g:power></g:TrackPointExtension></extensions></trkpt>
<trkpt lat="1" lon="2"><time>2020-01-01T00:00:01Z</time><ele>11</ele></trkpt>
</trkseg></trk></gpx>'''
TCX = b'''          <?xml version="1.0"?><TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" xmlns:ae="http://www.garmin.com/xmlschemas/ActivityExtension/v2"><Activities><Activity Sport="Biking"><Lap><TotalTimeSeconds>35</TotalTimeSeconds><DistanceMeters>500</DistanceMeters><AverageHeartRateBpm><Value>120</Value></AverageHeartRateBpm><Extensions><ae:LX><ae:AvgWatts>150</ae:AvgWatts></ae:LX></Extensions><Track>
<Trackpoint><Time>2020-01-01T00:00:00Z</Time><Position><LatitudeDegrees>1</LatitudeDegrees><LongitudeDegrees>2</LongitudeDegrees></Position><HeartRateBpm><Value>120</Value></HeartRateBpm><Extensions><ae:TPX><ae:Watts>145</ae:Watts></ae:TPX></Extensions></Trackpoint>
<Trackpoint><Time>2020-01-01T00:00:01Z</Time><Position><LatitudeDegrees>1</LatitudeDegrees><LongitudeDegrees>2</LongitudeDegrees></Position><HeartRateBpm><Value>121</Value></HeartRateBpm><Extensions><ae:TPX><ae:Watts>155</ae:Watts></ae:TPX></Extensions></Trackpoint>
</Track></Lap></Activity></Activities></TrainingCenterDatabase>'''


class SampleInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private-export-name"
        (self.root / "activities").mkdir(parents=True)
        (self.root / "activities" / "1.gpx").write_bytes(GPX)
        (self.root / "activities" / "2.tcx.gz").write_bytes(gzip.compress(TCX, mtime=0))
        (self.root / "activities.csv").write_text(
            "Activity ID,Activity Date,Activity Type,Filename,Elapsed Time,Distance,Distance,Average Watts,Activity Name,Activity Description\n"
            "1,Jan 1 2020,Ride,activities/1.gpx,35,0.5,500,150,Secret Route,Private words\n"
            "2,Jan 1 2020,Ride,activities/2.tcx.gz,35,0.5,500,150,Other Secret,More private words\n"
            "3,Jan 2 2020,Walk,,20,0.1,100,,No File Secret,Hidden details\n",
            encoding="utf-8")
        self.inventory = Path(self.temp.name) / "inventory.json"
        self.inventory.write_text(json.dumps({"candidate_files": [
            {"activity_id": "1", "file": "activities/1.gpx", "format": ".gpx", "reasons": ["test"]},
            {"activity_id": "2", "file": "activities/2.tcx.gz", "format": ".tcx.gz", "reasons": ["test"]},
        ]}), encoding="utf-8")

    def test_xml_gzip_extensions_comparison_and_privacy(self):
        report = tool.inspect_export(self.root, self.inventory)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["resolved_candidate_count"], 2)
        by_id = {item["activity_id"]: item for item in report["candidate_samples"]}
        gpx = by_id["1"]["source_evidence"]
        tcx = by_id["2"]["source_evidence"]
        self.assertEqual(gpx["signals"]["power"]["points_with_value"], 1)
        self.assertEqual(gpx["signals"]["heart_rate"]["points_with_value"], 1)
        self.assertEqual(gpx["signals"]["gps"]["points_with_value"], 2)
        self.assertEqual(gpx["signals"]["temperature"]["points_with_value"], 1)
        self.assertTrue(any("TrackPointExtension" in tag for tag in gpx["extension_tag_names"]))
        self.assertEqual(tcx["leading_xml_whitespace_bytes_removed"], 10)
        self.assertEqual(tcx["summary"]["elapsed_seconds"]["value"], 35)
        self.assertEqual(tcx["summary"]["distance_m"]["value"], 500)
        self.assertEqual(tcx["record_power_count"], 2)
        self.assertEqual(tcx["summary_power_field_count"], 1)
        self.assertEqual(by_id["2"]["csv_source_comparison"]["distance_m"]["status"],
                         "both_present_apparently_consistent")
        self.assertEqual(by_id["2"]["power_evidence"]["provenance_classification"], "unknown")
        self.assertEqual(report["no_file_row_count"], 1)
        self.assertEqual(report["no_file_rows"][0]["activity_id"], "3")
        output = json.dumps(report)
        for private in ("Secret Route", "Private words", "Other Secret", "No File Secret",
                        "private-export-name", self.temp.name):
            self.assertNotIn(private, output)

    def test_resolution_error_is_explicit(self):
        data = json.loads(self.inventory.read_text())
        data["candidate_files"][0]["file"] = "activities/999.gpx"
        self.inventory.write_text(json.dumps(data))
        report = tool.inspect_export(self.root, self.inventory)
        self.assertEqual(report["status"], "resolution_failed")
        self.assertEqual(report["resolution_errors"][0]["activity_id"], "1")

    def test_timing_summary(self):
        times = [tool.parse_time(value) for value in (
            "2020-01-01T00:00:00Z", "2020-01-01T00:00:01Z",
            "2020-01-01T00:00:01Z", "2020-01-01T00:01:00Z")]
        summary = tool.timing_summary(times, 4)
        self.assertEqual(summary["duplicate_timestamps"], 1)
        self.assertEqual(summary["positive_delta_seconds"]["median"], 30)
        self.assertEqual(summary["large_gap_count"], 0)
        many = [tool.parse_time(f"2020-01-01T00:00:{second:02d}Z") for second in (0, 1, 2, 3)]
        many.append(tool.parse_time("2020-01-01T00:01:00Z"))
        self.assertEqual(tool.timing_summary(many, 5)["large_gap_count"], 1)

    def test_fit_summarizer_keeps_fields_without_serial_values(self):
        def field(name, value, number=1, dev=False):
            return SimpleNamespace(name=name, name_or_num=name, value=value, def_num=number,
                                   units=None, field_def=SimpleNamespace(is_dev=dev))
        frames = [
            SimpleNamespace(frame_type="definition"),
            SimpleNamespace(frame_type="data", name="device_info",
                            fields=[field("serial_number", 123456789), field("manufacturer", "Garmin")]),
            SimpleNamespace(frame_type="data", name="record",
                            fields=[field("timestamp", tool.parse_time("2020-01-01T00:00:00Z")),
                                    field("power", 200), field("custom", 1, 10, True)]),
            SimpleNamespace(frame_type="data", name="session",
                            fields=[field("avg_power", 190), field("total_elapsed_time", 1)]),
        ]
        report = tool.fit_message_summary(frames)
        self.assertEqual(report["definition_frame_count"], 1)
        self.assertEqual(report["record_power_count"], 1)
        self.assertEqual(report["summary_power_field_count"], 1)
        self.assertTrue(any(item["developer_field"] for item in report["message_fields"]["record"]))
        self.assertNotIn("123456789", json.dumps(report))

    def test_deterministic_files(self):
        output = Path(self.temp.name) / "results"
        self.assertEqual(tool.main([str(self.root), str(self.inventory), "--output-dir", str(output)]), 0)
        first = [(output / name).read_bytes() for name in ("sample_inspection.json", "sample_inspection.md")]
        self.assertEqual(tool.main([str(self.root), str(self.inventory), "--output-dir", str(output)]), 0)
        second = [(output / name).read_bytes() for name in ("sample_inspection.json", "sample_inspection.md")]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
