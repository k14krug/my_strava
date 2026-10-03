#!/usr/bin/env python3
"""Disposable P1-02 acceptance with an independent direct-window calculation.

Requires RideWorks installed in the active environment. Normal output contains
compact facts/results, never raw streams, coordinates or private input paths.
"""

import argparse
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from rideworks import Store
from rideworks.analysis import analyze_activity, compact_analysis


def independent_best_20(records):
    """Enumerate and directly sum each 1,200-sample window; no rolling helper.

    Timestamp checks use each candidate's start plus the sample offset. Decimal
    means and ROUND_HALF_UP independently express the JIT's rounding rule.
    """
    timestamps = [None if r['timestamp'] is None else datetime.fromisoformat(r['timestamp'])
                  for r in records]
    best, best_mean = None, None
    eligible_count = 0
    for start in range(len(records) - 1200 + 1):
        candidate = records[start:start + 1200]
        first = timestamps[start]
        if first is None:
            continue
        if not all(timestamps[start + offset] == first + timedelta(seconds=offset)
                   for offset in range(1200)):
            continue
        if any(r['power'] is None for r in candidate):
            continue
        mean = Decimal(sum(r['power'] for r in candidate)) / Decimal(1200)
        eligible_count += 1
        if best_mean is None or mean > best_mean:
            best_mean = mean
            best = dict(start_record_index=candidate[0]['record_index'],
                        end_exclusive_record_index=candidate[-1]['record_index'] + 1,
                        start_timestamp=candidate[0]['timestamp'],
                        end_exclusive_timestamp=(first + timedelta(seconds=1200)).isoformat(),
                        sample_count=1200, average_watts=float(mean),
                        rounded_watts=int(mean.quantize(Decimal('1'), rounding=ROUND_HALF_UP)))
    if best is not None:
        best['eligible_window_count'] = eligible_count
    return best


def verify(input_path, work_dir=None):
    received = input_path.read_bytes()
    with tempfile.TemporaryDirectory(prefix='rideworks-analysis-', dir=work_dir) as temporary:
        root = Path(temporary)
        supplied = root / input_path.name
        shutil.copyfile(input_path, supplied)
        data_dir = root / 'data'
        with Store(data_dir) as store:
            imported = store.import_fit(supplied)
            snapshot = store.get_activity(imported['activity_id'])
            assert len(snapshot['sources']) == 1
            evidence = snapshot['sources'][0]
            assert evidence['source']['kind'] == 'file_fit'
            assert evidence['source']['content_format'] == 'FIT'
            records = evidence['records']
            assert len(records) == 3621
            assert all(r['timestamp'] is not None for r in records)
            timestamps = [datetime.fromisoformat(r['timestamp']) for r in records]
            deltas = [(b - a).total_seconds() for a, b in zip(timestamps, timestamps[1:])]
            assert len(deltas) == 3620 and set(deltas) == {1.0}
            assert all(r['power'] is not None for r in records)
            assert all(r['heart_rate'] is not None for r in records)
            for signal in ('power', 'heart_rate'):
                assert evidence['availability'][signal]['present'] == 3621
                assert evidence['availability'][signal]['missing'] == 0
            summary = evidence['summary']
            fields = ('start_time', 'timestamp', 'sport', 'sub_sport', 'total_elapsed_time',
                      'total_timer_time', 'total_distance', 'total_ascent', 'avg_power',
                      'max_power', 'avg_heart_rate', 'max_heart_rate', 'avg_cadence')
            assert all(summary[field] is not None for field in fields)
            assert summary['total_elapsed_time'] == 3620
            assert summary['total_timer_time'] == 3621
            supplied.unlink()  # only a disposable copy, never Ken's original
            analysis = analyze_activity(store, imported['activity_id'])
            assert analysis['source_summary']['values'] == summary
            assert analysis['native_records'] == records
            assert analysis['availability'] == evidence['availability']
            independent = independent_best_20(store.get_source(imported['source_id'])['records'])
            best = analysis['best_20_minute_power']
            assert best['status'] == 'available' and best['eligible']
            assert best['origin'] == 'calculated'
            assert best['method'] == 'best-average-power-v1'
            assert best['duration_seconds'] == 1200 and best['sample_count'] == 1200
            assert best['activity_id'] == imported['activity_id']
            assert best['source_id'] == imported['source_id']
            assert best['extraction_id'] == imported['extraction_id']
            assert independent is not None
            difference = abs(best['average_watts'] - independent['average_watts'])
            assert difference <= 0.01
            for key in ('rounded_watts', 'start_record_index', 'end_exclusive_record_index',
                        'start_timestamp', 'end_exclusive_timestamp', 'eligible_window_count'):
                assert best[key] == independent[key], key
            # The ordinary CLI exposes the same current analysis, without streams.
            cli_output = subprocess.check_output(
                [sys.executable, '-m', 'rideworks', '--data-dir', str(data_dir),
                 'analyze', imported['activity_id']], cwd=root, text=True)
            assert json.loads(cli_output) == compact_analysis(analysis)
            assert 'native_records' not in json.loads(cli_output)
            assert 'position_lat' not in cli_output and 'position_long' not in cli_output
            assert str(root) not in cli_output
            assert store.get_source(imported['source_id']) == evidence
            rebuilt = store.reextract(imported['source_id'])
            current = analyze_activity(store, imported['activity_id'])
            assert current['extraction']['extraction_id'] == rebuilt['extraction_id']
            assert current['best_20_minute_power']['extraction_id'] == rebuilt['extraction_id']
            assert rebuilt['extraction_id'] != imported['extraction_id']
            assert current['best_20_minute_power']['average_watts'] == best['average_watts']
            assert current['source_summary']['values']['avg_power'] == summary['avg_power']
        assert input_path.read_bytes() == received
        return dict(
            result='passed', activity_id=imported['activity_id'], source_id=imported['source_id'],
            extraction_id=imported['extraction_id'], source_count=1, record_count=3621,
            power_present=3621, heart_rate_present=3621, positive_timestamp_deltas=3620,
            unique_delta_seconds=[1], missing_timestamps=0, duplicate_timestamps=0,
            backward_timestamps=0, best_20=best, independent_best_20=independent,
            unrounded_difference_watts=difference, source_session_average_power=summary['avg_power'],
            source_summary_unchanged=True, native_records_unchanged=True,
            no_resampling_interpolation_smoothing=True, analysis_without_external_input=True,
            analysis_reports_new_extraction_after_reextract=True, compact_cli_no_streams=True,
            supplied_original_unchanged=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--work-dir', type=Path, help='Existing parent of a disposable acceptance directory')
    args = parser.parse_args()
    print(json.dumps(verify(args.input.resolve(), args.work_dir), indent=2))


if __name__ == '__main__':
    main()
