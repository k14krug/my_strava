# P2-01 verification — mandatory timing stop

**State:** implementation foundation committed; blocked for Analyst review.
**Date:** 2026-10-04.
**Branch / PR:** `task/p2-01-historical-import` / [#13](https://github.com/k14krug/my_strava/pull/13) (draft).
**Implementation head:** `dd05905`; subsequent handoff commits contain documentation/evidence only.
**Base:** refreshed `main` at `0ee9347`; Phase 1 accepted on merged PR #12.

## Required stop / decision

Seven files encountered during the seeded known-export acceptance have an
integer-valued FIT **lap timestamp**. The accepted production `fit-v1` mapper
requires absolute aware UTC timestamps and rejects these files in
`rideworks.fit._timestamp`. Independent strict fitdecode frame decoding succeeds
for all seven, with one session each and all native **record** timestamps
absolute. The research census characterized record/point timing, so its successful
parse/record-timing findings do not establish the production lap-timing handling.

Dex stopped the acceptance run and made no change to the accepted FIT mapper.
No integer timestamp was guessed into UTC, repaired, replaced with missing,
discarded, or promoted into a new timing interpretation.

This invokes `docs/tasks/P2-01.md` §21 ("known files cannot be parsed without
silently normalizing important timing/evidence") and AGENTS.md's unexpected
source-evidence/requirements-control stop. A lossless typed representation might
resolve the condition, but the handling is not being invented during this stop.

**Analyst action required:** specify/authorize how these non-absolute FIT lap
fields must be preserved, including their relationship to the accepted Phase 1
absolute-timing decoding/analysis contract; alternatively give an explicit other
disposition. Revise/clarify the JIT if needed. The source's integer values alone
are not sufficient evidence to assign a UTC instant or a device-relative clock
interpretation. P2-01 stays `in_progress` and the PR stays draft.

## Implemented foundation

- One documented `import-strava-export` command accepts a ZIP or extracted root.
- Exact CSV snapshots are shared by row Sources; exact FIT/TCX/GPX received bytes
  and gzip packaging are preserved with hash/size metadata.
- Actual titles, separate type/date evidence, positional repeated summary
  columns, row provenance, external identity and changed evidence coexist.
- Exact artifact + explicit CSV reference or established Strava ID supports
  enrichment; conflicting identities and unassociated pre-existing Activities
  are reported without fuzzy reconciliation.
- CSV-only Activities have unavailable native records, not fabricated streams.
- Standard-library TCX/GPX parsing retains native order, missingness, zeroes,
  irregular/unknown timing and segment boundaries. TCX lap summaries remain
  separately named source fields; private XML summaries do not become streams.
- Atomic additive schema-1 → schema-2 migration preserves the Phase 1 tables,
  identities, artifacts and extraction evidence; failed DDL rolls back.
- `Store.activity_history()` supplies source-aware metadata for all Activities;
  existing Phase 1 UI and FIT analysis remain bounded and unchanged.
- Synthetic tests and a disposable real-export verifier are included.

Material files: `rideworks/store.py`, `rideworks/strava_export.py`,
`rideworks/xml_activity.py`, `rideworks/__main__.py`, `rideworks/README.md`,
`tests/test_rideworks_export.py`, `tools/verify_rideworks_export.py`.

## Automated verification

```bash
.venv/bin/python -m unittest discover -s tests
```

**113 tests passed:** all 94 previous tests plus 19 synthetic export/migration
tests. The final suite ran with the loopback socket access needed by the accepted
HTTP server tests; an initial sandbox-only run could not bind those sockets.

Coverage includes real schema-1 fixture migration/read/re-extraction/review,
failed migration rollback, exact snapshot preservation, CSV-only missingness,
source title/type/date/provenance, positional duplicates, equivalent/changed
row evidence, exact-FIT enrichment and restart, changed original bytes,
conflicting/ambiguous association, TCX/GPX/gzip/content detection, irregular
native timestamps, summary/stream separation, malformed independent files,
transaction rollback, traversal/symlink/ZIP structure rejection and CLI partial
failure status. Tests contain generated synthetic data only.

`git diff --check` passed before committing implementation. No tests were rerun
for the handoff-only documentation/evidence commit.

**Runtime:** Python 3.10.12; SQLite 3.37.2; `fitdecode==0.11.0` / `fit-v1`;
stdlib ElementTree (Python runtime version) / `xml-activity-v1`;
CSV mapping `strava-export-v1`; schema 2. XML mappings were checked against
[Garmin TCX v2](https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd),
[ActivityExtension v2](https://www8.garmin.com/xmlschemas/ActivityExtensionv2.xsd)
and [TrackPointExtension v1](https://www8.garmin.com/xmlschemas/TrackPointExtensionv1.xsd)
on 2026-10-04. Unknown/private extensions remain in originals.

## Interrupted local-data acceptance

Exact command shape (private arguments redacted):

```bash
.venv/bin/python tools/verify_rideworks_export.py \
  --export '<local-export.zip>' --work-dir '<local-work-directory>'
```

The verifier invokes the production commands in disposable state:

```bash
.venv/bin/python -m rideworks --data-dir '<disposable-data-dir>' import-fit '<disposable-seed.fit.gz>'
.venv/bin/python -m rideworks --data-dir '<disposable-data-dir>' import-strava-export '<local-export.zip>'
```

Preflight confirmed the controlling known population: **1,434 CSV rows, 1,421
referenced artifacts and 13 no-file rows**, with expected activity-type counts.
The run was interrupted on the diagnosed condition; it did not finish a bulk
report or reach the full-population rerun checks. Post-interruption inspection:

| Evidence | Observed |
| --- | ---: |
| Durable Activities | 241 |
| Strava-export row Sources | 241 |
| Completed file Sources | 233 |
| Exact CSV snapshots | 1 |
| Independently diagnosed FIT files without a completed file Source | 7 |
| Additional row interrupted before file completion | 1 |

These are **partial progress counts**, not a final import result or whole-export
failure prevalence. All 233 completed file artifacts pass independent hash/size
checks. The seven rejected files have CSV evidence but no completed false file
Source/extraction. The extra interrupted row was not classified as another
failure. Original export files were not modified. Disposable partial runtime
state remains local and ignored; no accepted working store was replaced.

The real representative's partial enrichment was inspected separately:

- its existing seeded Activity has exactly one FIT Source and one CSV Source;
- a real source title is available (title text deliberately not published);
- the preserved FIT artifact equals the seed bytes;
- the native record count remains **3,621** and FIT average power remains
  **118 W**, separately attributable to the FIT Source.

Full 1,434-Activity acceptance, all 1,421 attempts/final format counts, full
original/source population comparison, all-format local sample inspection and
restart/idempotent rerun remain **pending**. Full runtime was not measured because
the run was stopped. Nothing here declares P2-01 ready for acceptance.

## Compact diagnosis / reproduction

`stop-evidence.json` contains only row indexes, message/field/type/order and
aggregate evidence. CSV data rows **136, 203, 204, 205, 206, 207 and 209** each
contain one non-absolute `lap.timestamp`. All corresponding record timestamps
are absolute and strict CRC/error frame decoding passes. These are diagnosed
rows in the interrupted prefix, not an assertion that later rows are unaffected.

The independent diagnostic used this command shape after identifying the
uncompleted file Sources (private input redacted):

```bash
RIDEWORKS_VERIFY_EXPORT='<local-export.zip>' .venv/bin/python - <<'PY'
import gzip, io, json, os
from datetime import datetime
import fitdecode
from rideworks.strava_export import ExportInput, read_rows
with ExportInput(os.environ['RIDEWORKS_VERIFY_EXPORT']) as export:
    rows = read_rows(export.read(export.csv_member))
    for index in (136, 203, 204, 205, 206, 207, 209):
        row = rows[index - 1]
        payload = export.read(export.validate_reference(row['filename']))
        if payload[:2] == b'\x1f\x8b':
            payload = gzip.decompress(payload)
        fields = []
        with fitdecode.FitReader(io.BytesIO(payload),
                check_crc=fitdecode.CrcCheck.RAISE,
                error_handling=fitdecode.ErrorHandling.RAISE) as reader:
            for order, frame in enumerate(reader):
                if frame.frame_type != fitdecode.FIT_FRAME_DATA:
                    continue
                if frame.name not in ('session', 'record', 'lap', 'event'):
                    continue
                for field in frame.fields:
                    if field.name in ('timestamp', 'start_time') and field.value is not None and not isinstance(field.value, datetime):
                        fields.append(dict(message=frame.name, field=field.name,
                            decoded_type=type(field.value).__name__, source_order=order))
        print(json.dumps(dict(csv_data_row_index=index, non_absolute_fields=fields)))
PY
```

## Privacy / scope / handoff

No export ZIP/CSV, personal original files, raw streams, databases, coordinates,
private source titles/descriptions, absolute personal paths, credentials or
screenshots are staged or committed. The published JSON/Markdown is deliberately
aggregate/structural evidence. JIT controls and acceptance criteria are unchanged.
No P2-02 browser, historical performance analysis, API sync or Phase 3 work was
started. Analyst timing review is the next action; Dex has stopped.
