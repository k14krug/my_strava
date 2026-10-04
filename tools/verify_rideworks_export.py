#!/usr/bin/env python3
"""Disposable P2-01 acceptance against the known local export.

Uses product CLI commands, then independent byte/hash comparisons and Store
reads. stdout contains only aggregate evidence; personal titles, paths, raw
streams and stable source IDs are deliberately excluded.
"""
import argparse
from collections import Counter
import hashlib
import gzip
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time

import fitdecode
from rideworks import Store, RideWorksError
from rideworks.strava_export import ExportInput, read_rows

REPRESENTATIVE_FILE = 'activities/21538875902.fit.gz'
EXPECTED_TYPES = {'Virtual Ride': 1264, 'Ride': 146, 'Run': 22, 'Walk': 1, 'Rowing': 1}
EXPECTED_FORMATS = {'FIT.GZ': 1264, 'GPX': 29, 'GPX.GZ': 76, 'TCX.GZ': 52}


def require(condition, label):
    if not condition:
        raise RideWorksError('Acceptance check failed: ' + label)


def verify(export_path, work_dir=None):
    with ExportInput(export_path) as export:
        csv_payload = export.read(export.csv_member)
        rows = read_rows(csv_payload)
        counts = (len(rows), sum(bool(row['filename']) for row in rows), sum(not row['filename'] for row in rows))
        require(counts == (1434,1421,13), f'known population differs: {counts}')
        require(dict(Counter(row['activity_type'] for row in rows)) == EXPECTED_TYPES, 'known type counts differ')
        seed_bytes = export.read(export.validate_reference(REPRESENTATIVE_FILE))
        # All path validation precedes writing disposable acceptance state.
        for row in rows:
            if row['filename']:
                export.validate_reference(row['filename'])
        with tempfile.TemporaryDirectory(prefix='p2-01-acceptance-', dir=work_dir) as temporary:
            root = Path(temporary)
            seed = root/'seed.fit.gz'
            seed.write_bytes(seed_bytes)
            data_dir = root/'data'

            def cli(command, argument):
                run = subprocess.run([sys.executable, '-m', 'rideworks', '--data-dir', str(data_dir), command, str(argument)],
                                     capture_output=True, text=True)
                # Never echo command strings or stderr: they may contain local
                # paths or decoder contents. Bulk reports have fixed categories.
                require(bool(run.stdout), 'CLI produced no JSON result')
                result = json.loads(run.stdout)
                return result, run.returncode

            seeded, code = cli('import-fit', seed)
            require(code == 0 and seeded['status'] == 'imported', 'representative seed import')
            with Store(data_dir) as store:
                seed_evidence = store.get_source(seeded['source_id'])
            started = time.monotonic()
            first, code = cli('import-strava-export', export_path)
            first_seconds = time.monotonic() - started
            require(code == 0 and first['status'] == 'completed', 'known files must import without failures')
            require(first['csv_rows_seen'] == 1434 and first['referenced_artifacts_attempted'] == 1421, 'first import population')
            require(first['activities_created'] == 1433, 'seeded creation count')
            require(first['existing_activities_enriched'] == 1 and first['artifacts_reused'] == 1, 'representative enrichment')
            require(first['format_counts'] == EXPECTED_FORMATS, 'known content/packaging format counts')
            with Store(data_dir) as store:
                history = store.activity_history()
                require(len(history) == 1434, 'final Activity count must be 1434, not 1435')
                require(store.get_source(seeded['source_id']) == seed_evidence, 'seed FIT source/extraction unchanged')
                enriched = store.get_activity(seeded['activity_id'])
                csv_sources = [s for s in enriched['sources'] if s['source']['kind'] == 'strava_export']
                require(len(csv_sources) == 1 and bool(csv_sources[0]['summary']['title']), 'real source title available')
                require(len(enriched['sources']) == 2, 'same Activity has FIT and CSV sources')
                require(store.connection.execute('PRAGMA user_version').fetchone()[0] == 3, 'schema version')
                require(store.connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'SQLite integrity')
                require(not store.connection.execute('PRAGMA foreign_key_check').fetchall(), 'foreign-key integrity')
                require(store.connection.execute('SELECT COUNT(*) FROM export_snapshots').fetchone()[0] == 1, 'single CSV snapshot')
                originals = {row['sha256']: dict(row) for row in store.connection.execute('SELECT * FROM sources')}
                require(len(originals) == 1421, 'file-source count')
                for row in rows:
                    if not row['filename']:
                        continue
                    supplied = export.read(export.validate_reference(row['filename']))
                    digest = hashlib.sha256(supplied).hexdigest()
                    source = originals[digest]
                    preserved = (data_dir/source['stored_path']).read_bytes()
                    require(preserved == supplied, 'all exact originals match received bytes')
                    require(source['byte_size'] == len(supplied), 'all original sizes')
                    require(hashlib.sha256(preserved).hexdigest() == source['sha256'], 'all original hashes')
                snapshot = store.connection.execute('SELECT * FROM export_snapshots').fetchone()
                require((data_dir/snapshot['stored_path']).read_bytes() == csv_payload, 'exact CSV preserved')
                csv_only = [item for item in history if all(s['source']['kind']=='strava_export' for s in item['sources'])]
                require(len(csv_only) == 13, 'CSV-only Activity population')
                require(all(s['availability']['power']['status'] == 'unavailable' for item in csv_only for s in item['sources']),
                        'CSV-only streams unavailable, not observed absent')
                samples = {}
                for item in history:
                    for source in item['sources']:
                        fmt = source['source']['content_format']
                        if fmt in ('FIT','TCX','GPX') and fmt not in samples:
                            detail = store.get_source(source['source']['source_id'])
                            require(detail['extraction']['record_count'] > 0, 'sample native records available')
                            require(len(detail['records']) == detail['extraction']['record_count'], 'sample record counts')
                            require(detail['extraction']['power_origin'] == 'unknown', 'no measured-power claim inferred')
                            samples[fmt] = True
                require(set(samples) == {'FIT','TCX','GPX'}, 'FIT/TCX/GPX readable through Store')
                require(store.get_activity(csv_only[0]['activity']['activity_id'])['sources'][0]['records'] is None,
                        'CSV-only Store read has no native records')
                lap_sources = [r[0] for r in store.connection.execute('''
                    SELECT DISTINCT e.source_id FROM fit_lap_timestamps t
                    JOIN extractions e ON e.extraction_id=t.extraction_id
                ''')]
                lap_field_count = 0
                for source_id in lap_sources:
                    detail = store.get_source(source_id)
                    source = detail['source']
                    artifact = (data_dir/source['stored_path']).read_bytes()
                    decoded = gzip.decompress(artifact) if source['packaging']=='gzip' else artifact
                    # Independent raw-field oracle: do not invoke production
                    # decode_fit/_timestamp as their own preservation check.
                    raw_fields = []
                    with fitdecode.FitReader(io.BytesIO(decoded), check_crc=fitdecode.CrcCheck.RAISE,
                            error_handling=fitdecode.ErrorHandling.RAISE) as reader:
                        for order, frame in enumerate(reader):
                            if frame.frame_type != fitdecode.FIT_FRAME_DATA or frame.name != 'lap':
                                continue
                            for field in frame.fields:
                                if field.name == 'timestamp' and type(field.value) is int:
                                    raw_fields.append(dict(source_order=order, field_name='timestamp',
                                        raw_integer=field.value, status='present_uninterpreted_non_absolute'))
                    actual = [{k:v for k,v in field.items() if k != 'extraction_id'}
                              for field in detail['fit_lap_timestamps']]
                    require(actual == raw_fields, 'lap integers equal independent original-field decode')
                    laps = {lap['source_order']:lap for lap in detail['laps']}
                    require(all(laps[field['source_order']]['timestamp'] is None for field in actual),
                            'uninterpreted lap absolute timestamp unavailable')
                    require(detail['extraction']['mapping_version']=='fit-v2', 'versioned lap mapping')
                    lap_field_count += len(actual)
                before_ids = {table: [tuple(r) for r in store.connection.execute(f'SELECT * FROM {table} ORDER BY 1')]
                              for table in ('activities','sources','extractions','strava_export_sources','export_snapshots','export_row_locations','fit_lap_timestamps')}
                native_power_sources = sum(s['native_power_stream_exists'] for item in history for s in item['sources'])
            started = time.monotonic()
            second, code = cli('import-strava-export', export_path)
            second_seconds = time.monotonic() - started
            require(code == 0 and second['status']=='completed', 'rerun success after process restart')
            require(second['activities_created'] == second['csv_sources_created'] == second['artifacts_imported'] == 0,
                    'rerun creates no Activities/Sources/artifacts')
            require(second['artifacts_reused'] == 1421 and second['csv_sources_reused'] == 1434, 'all evidence reused')
            with Store(data_dir) as restarted:
                require(restarted.activity_history() == history, 'history survives process restart/rerun unchanged')
                after_ids = {table: [tuple(r) for r in restarted.connection.execute(f'SELECT * FROM {table} ORDER BY 1')]
                             for table in before_ids}
                require(after_ids == before_ids, 'all identities/extraction revisions/snapshot rows remain stable')
                # Re-extract only after proving restart/rerun identity stability;
                # a new extraction revision is intentional, not a rerun mutation.
                for source_id in lap_sources:
                    before = restarted.get_source(source_id)
                    restarted.reextract(source_id)
                    after = restarted.get_source(source_id)
                    require(after['source'] == before['source'], 're-extraction keeps source identity')
                    for section in ('records','laps','events','fit_lap_timestamps'):
                        without_id = lambda rows: [{k:v for k,v in row.items() if k!='extraction_id'} for row in rows]
                        require(without_id(before[section]) == without_id(after[section]),
                                're-extraction preserves native and uninterpreted lap evidence')
            return dict(result='passed', schema_version=3, first_import=first, restarted_rerun=second,
                        final_activity_count=1434, file_source_count=1421, csv_source_count=1434,
                        csv_only_activity_count=13, csv_snapshot_count=1, all_originals_exact_and_verified=True,
                        representative_activity_id_preserved=True, representative_fit_evidence_unchanged=True,
                        representative_source_title_available=True, process_restart_history_unchanged=True,
                        all_identities_stable_on_rerun=True, sampled_store_read_formats=['FIT','TCX','GPX','CSV-only'],
                        uninterpreted_lap_timestamp_source_count=len(lap_sources),
                        uninterpreted_lap_timestamp_field_count=lap_field_count,
                        lap_integer_independent_decode_verified=True,
                        lap_integer_reextraction_verified=True,
                        native_power_source_count=native_power_sources,
                        first_import_elapsed_seconds=round(first_seconds,2), rerun_elapsed_seconds=round(second_seconds,2),
                        python_version=sys.version.split()[0], sqlite_version=sqlite3.sqlite_version)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', required=True, type=Path)
    parser.add_argument('--work-dir', type=Path, help='Parent directory for disposable acceptance state')
    args = parser.parse_args()
    try:
        result = verify(args.export.resolve(), args.work_dir)
    except RideWorksError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
