from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from fit_fixture import make_fit
from rideworks import Store
from rideworks.analysis import AnalysisError, BEST_20_METHOD, analyze_activity, best_20_minute_power
from rideworks.fit import decode_fit
from tools.verify_rideworks_analysis import independent_best_20

BASE = datetime(2020, 1, 1, tzinfo=timezone.utc)
CONTEXT = dict(activity_id='activity', source_id='source', extraction_id='extraction')


def records_for(powers, offsets=None):
    if offsets is None:
        offsets = range(len(powers))
    return [dict(record_index=i, source_order=i + 100,
                 timestamp=None if offset is None else (BASE + timedelta(seconds=offset)).isoformat(),
                 power=power, heart_rate=100)
            for i, (power, offset) in enumerate(zip(powers, offsets))]


class Best20Tests(unittest.TestCase):
    def calculate(self, records):
        return best_20_minute_power(records, **CONTEXT)

    def test_exactly_1200_samples_need_no_endpoint_sample(self):
        result = self.calculate(records_for([180] * 1200))
        self.assertEqual(result['status'], 'available')
        self.assertTrue(result['eligible'])
        self.assertEqual(result['sample_count'], 1200)
        self.assertEqual(result['duration_seconds'], 1200)
        self.assertEqual(result['eligible_window_count'], 1)
        self.assertEqual(result['start_record_index'], 0)
        self.assertEqual(result['end_exclusive_record_index'], 1200)
        self.assertEqual(result['start_timestamp'], BASE.isoformat())
        self.assertEqual(result['end_exclusive_timestamp'], (BASE + timedelta(seconds=1200)).isoformat())
        self.assertEqual(result['average_watts'], 180)
        self.assertEqual(result['rounded_watts'], 180)
        self.assertEqual(result['method'], BEST_20_METHOD)
        self.assertEqual(result['origin'], 'calculated')
        for key, value in CONTEXT.items():
            self.assertEqual(result[key], value)

    def test_1199_samples_and_empty_input_are_unavailable(self):
        for count in (0, 1199):
            result = self.calculate(records_for([180] * count))
            self.assertEqual(result['status'], 'unavailable')
            self.assertFalse(result['eligible'])
            self.assertEqual(result['reason'], 'activity_shorter_than_required')
            self.assertIsNone(result['average_watts'])
            self.assertIsNone(result['rounded_watts'])
            self.assertIsNone(result['start_record_index'])

    def test_sliding_windows_include_final_candidate(self):
        result = self.calculate(records_for([0] + [200] * 1200))
        self.assertEqual(result['start_record_index'], 1)
        self.assertEqual(result['end_exclusive_record_index'], 1201)
        self.assertEqual(result['average_watts'], 200)
        self.assertEqual(result['eligible_window_count'], 2)

    def test_final_large_sample_is_averaged_in_complete_window(self):
        result = self.calculate(records_for([100] * 1199 + [1000]))
        self.assertEqual(result['average_watts'], 100.75)
        self.assertEqual(result['rounded_watts'], 101)

    def test_zero_watts_are_included_and_all_zero_is_available(self):
        result = self.calculate(records_for([0] + [100] * 1199))
        self.assertAlmostEqual(result['average_watts'], 119900 / 1200)
        zeros = self.calculate(records_for([0] * 1200))
        self.assertEqual(zeros['status'], 'available')
        self.assertEqual(zeros['average_watts'], 0)
        self.assertEqual(zeros['rounded_watts'], 0)

    def test_missing_power_invalidates_only_windows_containing_it(self):
        result = self.calculate(records_for([None] + [100] * 1200))
        self.assertEqual(result['start_record_index'], 1)
        self.assertEqual(result['average_watts'], 100)
        self.assertEqual(result['eligible_window_count'], 1)

    def test_no_complete_power_window_returns_explicit_unavailable(self):
        powers = [100] * 1200
        powers[600] = None
        result = self.calculate(records_for(powers))
        self.assertEqual(result['reason'], 'no_complete_power_window')
        self.assertEqual(result['status'], 'unavailable')
        self.assertIsNone(result['average_watts'])

    def test_eligible_block_elsewhere_survives_missing_power(self):
        result = self.calculate(records_for([100] * 1200 + [None] + [200] * 1200))
        self.assertEqual(result['start_record_index'], 1201)
        self.assertEqual(result['average_watts'], 200)
        self.assertEqual(result['eligible_window_count'], 2)

    def test_gap_duplicate_backward_and_missing_time_invalidate_spanning_window(self):
        cases = dict(gap=[0] + list(range(2, 1201)),
                     duplicate=[0] + list(range(1199)),
                     backward=[2] + list(range(1199)),
                     missing=[None] + list(range(1199)))
        for name, offsets in cases.items():
            with self.subTest(name=name):
                result = self.calculate(records_for([100] * 1200, offsets))
                self.assertEqual(result['reason'], 'no_complete_timestamp_contiguous_window')
                self.assertEqual(result['status'], 'unavailable')
                self.assertEqual(result['eligible_window_count'], 0)

    def test_gap_duplicate_backward_and_missing_time_before_window_do_not_disqualify_it(self):
        cases = dict(gap=[0] + list(range(2, 1202)),
                     duplicate=[0] + list(range(1200)),
                     backward=[2] + list(range(1200)),
                     missing=[None] + list(range(1200)))
        for name, offsets in cases.items():
            with self.subTest(name=name):
                result = self.calculate(records_for([100] * 1201, offsets))
                self.assertEqual(result['start_record_index'], 1)
                self.assertEqual(result['average_watts'], 100)
                self.assertEqual(result['eligible_window_count'], 1)

    def test_missing_heart_rate_does_not_invalidate_power_window(self):
        records = records_for([100] * 1200)
        for record in records:
            record['heart_rate'] = None
        self.assertEqual(self.calculate(records)['status'], 'available')
        self.assertTrue(all(r['heart_rate'] is None for r in records))

    def test_equal_unrounded_means_select_earliest_record_order(self):
        result = self.calculate(records_for([100] * 1202))
        self.assertEqual(result['start_record_index'], 0)
        self.assertEqual(result['eligible_window_count'], 3)

    def test_better_unrounded_mean_wins_even_when_rounded_watts_tie(self):
        result = self.calculate(records_for([100] * 1200 + [101]))
        self.assertEqual(result['start_record_index'], 1)
        self.assertAlmostEqual(result['average_watts'], 120001 / 1200)
        self.assertEqual(result['rounded_watts'], 100)

    def test_rounding_below_at_and_above_half_watt(self):
        for final, expected in ((699, 100), (700, 101), (701, 101)):
            with self.subTest(final=final):
                result = self.calculate(records_for([100] * 1199 + [final]))
                self.assertEqual(result['rounded_watts'], expected)
                self.assertAlmostEqual(result['average_watts'], (119900 + final) / 1200)

    def test_unexpected_power_fails_without_silent_repair(self):
        for invalid in (-1, float('nan')):
            records = records_for([100] * 1200)
            records[600]['power'] = invalid
            with self.assertRaisesRegex(AnalysisError, 'Unexpected power'):
                self.calculate(records)
            self.assertIs(records[600]['power'], invalid)


class AnalysisBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / 'synthetic.fit'
        self.input.write_bytes((Path(__file__).parent / 'fixtures' / 'single_activity.fit').read_bytes())
        self.store = Store(self.root / 'data')
        self.addCleanup(self.store.close)
        self.imported = self.store.import_fit(self.input)

    def test_source_summary_native_evidence_and_identity_remain_distinct(self):
        evidence = self.store.get_source(self.imported['source_id'])
        before = deepcopy(evidence)
        analysis = analyze_activity(self.store, self.imported['activity_id'])
        self.assertEqual(analysis['source_summary']['values'], evidence['summary'])
        self.assertEqual(analysis['source_summary']['source_id'], self.imported['source_id'])
        self.assertEqual(analysis['source_summary']['extraction_id'], self.imported['extraction_id'])
        self.assertEqual(analysis['source_summary']['evidence_kind'], 'FIT session source summary')
        self.assertEqual(analysis['source_summary']['values']['total_elapsed_time'], 2.0)
        self.assertEqual(analysis['source_summary']['values']['total_timer_time'], 1.0)
        self.assertIsNone(analysis['source_summary']['values']['avg_power'])
        self.assertEqual(analysis['native_records'], evidence['records'])
        self.assertEqual([r['power'] for r in analysis['native_records']], [0, None, 180])
        self.assertEqual([r['heart_rate'] for r in analysis['native_records']], [100, None, 110])
        self.assertEqual(analysis['availability'], evidence['availability'])
        self.assertEqual(analysis['extraction']['extraction_id'], self.imported['extraction_id'])
        self.assertEqual(analysis['best_20_minute_power']['status'], 'unavailable')
        self.assertEqual(self.store.get_source(self.imported['source_id']), before)

    def test_analysis_needs_no_external_or_preserved_artifact_reparse(self):
        self.input.unlink()
        with patch('rideworks.store.decode_fit', side_effect=AssertionError('analysis must use stored evidence')):
            result = analyze_activity(self.store, self.imported['activity_id'])
        self.assertEqual(len(result['native_records']), 3)

    def test_missing_non_fit_or_missing_extraction_fails_clearly(self):
        snapshot = self.store.get_activity(self.imported['activity_id'])
        for variant in ('no_source', 'non_fit', 'no_extraction'):
            with self.subTest(variant=variant):
                candidate = deepcopy(snapshot)
                if variant == 'no_source':
                    candidate['sources'] = []
                elif variant == 'non_fit':
                    candidate['sources'][0]['source']['kind'] = 'other'
                else:
                    candidate['sources'][0]['extraction'] = None
                boundary = Mock(spec=Store)
                boundary.get_activity.return_value = candidate
                with self.assertRaisesRegex(AnalysisError, 'no usable current'):
                    analyze_activity(boundary, self.imported['activity_id'])

    def test_multiple_fit_sources_require_selection_decision(self):
        snapshot = self.store.get_activity(self.imported['activity_id'])
        second = deepcopy(snapshot['sources'][0])
        second['source']['source_id'] = 'other-source'
        snapshot['sources'].append(second)
        boundary = Mock(spec=Store)
        boundary.get_activity.return_value = snapshot
        with self.assertRaisesRegex(AnalysisError, 'Multiple candidate FIT Sources'):
            analyze_activity(boundary, self.imported['activity_id'])

    def test_reextraction_recalculates_from_new_current_evidence(self):
        synthetic = self.root / 'complete.fit'
        synthetic.write_bytes(make_fit(powers=[100] * 1200, heart_rates=[110] * 1200,
                                      timestamps=range(1100000000, 1100001200)))
        imported = self.store.import_fit(synthetic)
        first = analyze_activity(self.store, imported['activity_id'])
        self.assertEqual(first['best_20_minute_power']['average_watts'], 100)
        parsed = decode_fit(synthetic, 'plain')
        # Simulate a replacement extraction with revised decoded evidence, so
        # merely changing the reported UUID while returning a cached mean fails.
        revised = replace(parsed, records=[replace(r, power=200) for r in parsed.records])
        with patch('rideworks.store.decode_fit', return_value=revised):
            rebuilt = self.store.reextract(imported['source_id'])
        second = analyze_activity(self.store, imported['activity_id'])
        self.assertNotEqual(first['extraction']['extraction_id'], second['extraction']['extraction_id'])
        self.assertEqual(second['extraction']['extraction_id'], rebuilt['extraction_id'])
        self.assertEqual(second['best_20_minute_power']['extraction_id'], rebuilt['extraction_id'])
        self.assertEqual(second['best_20_minute_power']['average_watts'], 200)
        self.assertEqual(first['best_20_minute_power']['average_watts'], 100)
        self.assertIsNone(second['source_summary']['values']['avg_power'])

    def test_cli_output_is_compact(self):
        output = subprocess.check_output(
            [sys.executable, '-m', 'rideworks', '--data-dir', str(self.store.data_dir),
             'analyze', self.imported['activity_id']], text=True)
        result = json.loads(output)
        self.assertNotIn('native_records', result)
        self.assertEqual(result['native_record_count'], 3)
        self.assertEqual(result['best_20_minute_power']['status'], 'unavailable')
        self.assertNotIn('position_lat', output)
        self.assertNotIn(str(self.root), output)


class IndependentVerificationTests(unittest.TestCase):
    def test_direct_sum_and_rounding_do_not_call_production_helper(self):
        with patch('rideworks.analysis.best_20_minute_power', side_effect=AssertionError('oracle must be independent')):
            result = independent_best_20(records_for([100] * 1199 + [1000]))
        self.assertEqual(result['average_watts'], 100.75)
        self.assertEqual(result['rounded_watts'], 101)
        self.assertEqual(result['start_record_index'], 0)

    def test_independent_tie_and_half_up_rounding(self):
        result = independent_best_20(records_for([100] * 1199 + [700, 100]))
        self.assertEqual(result['average_watts'], 100.5)
        self.assertEqual(result['rounded_watts'], 101)
        self.assertEqual(result['start_record_index'], 0)
        self.assertEqual(result['eligible_window_count'], 2)

    def test_independent_missing_power_and_timing_defects(self):
        for records in (records_for([None] + [100] * 1200),
                        records_for([100] * 1201, [0] + list(range(2, 1202)))):
            result = independent_best_20(records)
            self.assertEqual(result['start_record_index'], 1)
            self.assertEqual(result['average_watts'], 100)
            self.assertEqual(result['eligible_window_count'], 1)

    def test_independent_no_window_and_zero_window_are_distinct(self):
        self.assertIsNone(independent_best_20(records_for([100] * 1199)))
        self.assertIsNone(independent_best_20(records_for([None] * 1200)))
        result = independent_best_20(records_for([0] * 1200))
        self.assertEqual(result['average_watts'], 0)
        self.assertEqual(result['rounded_watts'], 0)


if __name__ == '__main__':
    unittest.main()
