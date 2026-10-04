#!/usr/bin/env python3
"""Disposable P1-01 acceptance; stdout contains only compact derived facts.

Requires the RideWorks package installed in the active Python environment.
Never mutates the supplied original or retains raw streams in its output.
"""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from rideworks import Store


def verify(input_path, work_dir=None):
    original_bytes = input_path.read_bytes()
    with tempfile.TemporaryDirectory(prefix='rideworks-acceptance-', dir=work_dir) as temporary:
        root = Path(temporary)
        disposable = root / 'input' / input_path.name
        disposable.parent.mkdir()
        shutil.copyfile(input_path, disposable)
        data_dir = root / 'data'

        def cli(command, argument):
            output = subprocess.check_output(
                [sys.executable, '-m', 'rideworks', '--data-dir', str(data_dir), command, str(argument)],
                cwd=root, text=True,
            )
            return json.loads(output)

        imported = cli('import-fit', disposable)
        assert imported['status'] == 'imported'
        with Store(data_dir) as store:
            evidence = store.get_source(imported['source_id'])
            for table in ('activities', 'sources', 'sessions'):
                assert store.connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 1
            source, extraction, summary = (evidence[k] for k in ('source', 'extraction', 'summary'))
            stored_bytes = (data_dir / source['stored_path']).read_bytes()
            assert stored_bytes == original_bytes
            assert source['sha256'] == hashlib.sha256(original_bytes).hexdigest()
            assert source['byte_size'] == len(original_bytes)
            assert source['packaging'] == 'gzip' and source['content_format'] == 'FIT'
            assert extraction['parser_name'] == 'fitdecode' and extraction['parser_version'] == '0.11.0'
            assert extraction['mapping_version'] == 'fit-v2'
            assert extraction['artifact_sha256'] == source['sha256']
            records = evidence['records']
            assert len(records) == 3621
            assert [r['record_index'] for r in records] == list(range(3621))
            assert all(records[i]['source_order'] < records[i + 1]['source_order'] for i in range(3620))
            assert all(r['timestamp'] is not None for r in records)
            stamps = [datetime.fromisoformat(r['timestamp']) for r in records]
            deltas = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])]
            assert len(deltas) == 3620 and set(deltas) == {1.0}
            for signal in ('power', 'heart_rate'):
                assert evidence['availability'][signal]['present'] == 3621
                assert evidence['availability'][signal]['missing'] == 0
                assert evidence['availability'][signal]['origin'] == 'unknown'
            assert summary['total_elapsed_time'] == 3620.0
            assert summary['total_timer_time'] == 3621.0
            expected = dict(sport='cycling', sub_sport='virtual_activity', total_distance=21575.35,
                            total_ascent=256, avg_power=118, max_power=136, avg_heart_rate=111,
                            max_heart_rate=124, avg_cadence=77)
            for key, value in expected.items():
                assert summary[key] == value, key
            assert summary['start_time'] is not None and summary['timestamp'] is not None
            assert len(evidence['laps']) == 2 and len(evidence['events']) == 2
        repeated = cli('import-fit', disposable)
        assert repeated['status'] == 'already_imported'
        for key in ('activity_id', 'source_id', 'extraction_id'):
            assert imported[key] == repeated[key]
        inspected = cli('inspect', imported['activity_id'])
        assert 'records' not in inspected['sources'][0]
        assert 'position_lat' not in json.dumps(inspected) and 'position_long' not in json.dumps(inspected)
        with Store(data_dir) as store:
            assert store.get_activity(imported['activity_id'])['sources'][0] == evidence
        disposable.unlink()  # only our copy; Ken's artifact is untouched
        rebuilt = cli('reextract', imported['source_id'])
        assert rebuilt['activity_id'] == imported['activity_id']
        assert rebuilt['source_id'] == imported['source_id']
        assert rebuilt['extraction_id'] != imported['extraction_id']
        with Store(data_dir) as store:
            before = store.get_source(imported['source_id'])
            # Compare all normalized values apart from extraction identity.
            for section in ('summary', 'records', 'laps', 'events'):
                rows_before = evidence[section] if isinstance(evidence[section], list) else [evidence[section]]
                rows_after = before[section] if isinstance(before[section], list) else [before[section]]
                without_id = lambda rows: [{k: v for k, v in r.items() if k != 'extraction_id'} for r in rows]
                assert without_id(rows_before) == without_id(rows_after)
            store.connection.execute("""CREATE TRIGGER acceptance_failure BEFORE INSERT ON records
                BEGIN SELECT RAISE(ABORT, 'deliberately induced verification failure'); END""")
            try:
                store.reextract(imported['source_id'])
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError('Induced failure did not occur')
            assert store.get_source(imported['source_id']) == before
            store.connection.execute('DROP TRIGGER acceptance_failure')
        with Store(data_dir) as reopened:
            assert reopened.get_source(imported['source_id']) == before
        assert input_path.read_bytes() == original_bytes
        return dict(
            result='passed', artifact_sha256=source['sha256'], artifact_byte_size=source['byte_size'],
            session_count=1, record_count=3621, power_present=3621, heart_rate_present=3621,
            positive_timestamp_deltas=3620, unique_delta_seconds=[1], duplicate_timestamps=0,
            backward_timestamps=0, missing_timestamps=0, lap_count=2, event_count=2,
            elapsed_seconds=summary['total_elapsed_time'], timer_seconds=summary['total_timer_time'],
            exact_original_preserved=True, repeat_import_same_identity=True,
            process_restart_retrieval=True, reextract_without_external_input=True,
            reextract_changes_revision=True, failed_reextract_preserves_previous=True,
            compact_inspect_no_streams=True, supplied_original_unchanged=True,
            parser_version=extraction['parser_version'], mapping_version=extraction['mapping_version'],
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--work-dir', type=Path, help='Existing parent for a disposable acceptance directory')
    args = parser.parse_args()
    print(json.dumps(verify(args.input.resolve(), args.work_dir), indent=2))


if __name__ == '__main__':
    main()
