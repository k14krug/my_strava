# P2-01 verification — accepted

**State:** accepted / complete.
**Date:** 2026-10-04.
**Branch / PR:** `task/p2-01-historical-import` / [#13](https://github.com/k14krug/my_strava/pull/13).
**Implementation head:** `c131092`; the final publication commit updates documentation/evidence only.
**Controlling JIT:** `docs/tasks/P2-01.md`, including Analyst-authored §16A from `main` at `4bf8f6e`.
**Task lifecycle:** P2-01 accepted by the Analyst and merged to `main` as `57c00ae396bfb1e9c2c4c72ff42c5628afda9940`. P2-02 implementation has not begun.

## Result

The original ZIP imports through one production command into a clean disposable
store seeded with the accepted Phase 1 representative FIT. Final population is
**1,434 Activities**, **1,421 file Sources**, **1,434 CSV row Sources**, **13 CSV-only
Activities**, and **one exact CSV snapshot**. There are **zero failures and zero
unresolved associations**. The representative is enriched on the same Activity,
with real source title evidence available; its title text is not published.

Every preserved original was compared against the received ZIP member bytes and
independently checked for SHA-256/byte size. Restart/reimport preserved the full
source-aware history and every Activity/Source/current-extraction identity,
including row locations and retained integer lap evidence. No duplicate evidence
was created. `acceptance.json` is the exact aggregate verifier output.

## Material implementation

- `rideworks/strava_export.py`: direct ZIP/extracted-root workflow; structural
  preflight and safe member access; allowlisted positional CSV extraction;
  independent row/file failures; compact counts/categories without private text.
- `rideworks/store.py`: shared exact CSV snapshots, attributable row Sources and
  immutable native artifacts, conservative external-ID/exact-artifact association,
  additive migrations, history reads and lossless FIT lap evidence.
- `rideworks/fit.py`: the shared production FIT path, `fit-v2`; strict timing
  outside the authorized `lap.timestamp` exception; conflict checking restricted
  to understood extraction fields.
- `rideworks/xml_activity.py`: bounded standard-library TCX/GPX parsing; native
  timing/order/missingness, explicit segment context and TCX lap summaries.
- `rideworks/__main__.py` / `rideworks/README.md`: one documented bulk command and
  source/migration/format/failure semantics.
- `tests/test_rideworks.py`, `tests/test_rideworks_export.py`,
  `tests/fit_fixture.py`: privacy-safe generated fixtures and regression tests.
- `tools/verify_rideworks_export.py`: seeded production CLI acceptance,
  independent artifact/raw-lap oracles, process restart and idempotent rerun.
  `tools/verify_rideworks_import.py` expects the current versioned FIT mapping.

No frontend redesign, source-ranking system, new historical analysis, Strava API
sync, background/concurrent importer infrastructure, ORM or runtime dependency
was added.

## Lossless FIT timing decision

The prior stop was resolved by the [Analyst comment on PR #13](https://github.com/k14krug/my_strava/pull/13)
and JIT §16A. Integer `lap.timestamp` values are retained **exactly**, associated
with their Source/extraction/lap source order and `timestamp` field in the small
`fit_lap_timestamps` table. Their status is
`present_uninterpreted_non_absolute`; the absolute lap timestamp remains null.
They are not labeled UTC, device-relative or any other timebase. No neighboring
records, start/session timing, elapsed/timer duration or CSV metadata supplies a
replacement value. Aware lap timestamps retain accepted UTC normalization.

Full-export prevalence is **18 such fields across 17 FIT Sources**, rather than
an extrapolation from the seven files diagnosed in the earlier interrupted
prefix. Independent strict fitdecode frame reading verified every integer and
source order against the original. Explicit re-extraction of all 17 affected
Sources reproduced records, laps, events and raw integer/status evidence exactly
apart from the intentionally new extraction revision. These checks ran **after**
restart/rerun identity stability was established.

Record/session/event/lap-start timing remains strict. No different FIT
message/field needed a non-absolute timing exception. `best-average-power-v1`
continues to consume absolute native record timing only.

Schema 3 adds this FIT-specific table with a foreign key to the corresponding
lap. New FIT extraction is `fit-v2`; existing `fit-v1` extraction is not silently
rewritten during migration. Tests demonstrate schema-1 and schema-2 migration
preserving identities/artifacts/typed evidence and failed migration rolling back
DDL/version changes. Failed re-extraction also retains the previous integer lap
evidence and extraction.

Two straightforward parsing defects discovered during verification were fixed
within the authorized format envelope: duplicate unused enhanced speed fields
no longer reject unrelated typed FIT evidence, and Python 3.10 now parses XML
centiseconds exactly. Conflicts in extracted FIT fields still reject mapping.
XML fractional seconds with 1–6 decimal places preserve the exact instant;
unsupported finer precision is explicitly rejected, avoiding silent truncation
on other Python versions. No timestamps were repaired or resampled.

## Verification and versions

```bash
.venv/bin/python -m unittest discover -s tests
```

**123 tests passed:** all 94 prior tests plus 29 P2-01 export/migration/timing tests.
The suite ran with the loopback socket access required by the existing HTTP
server tests. No test was weakened or removed.

Tests cover migration and rollback; actual title/type/date/provenance; exact
shared snapshots; idempotency/changed evidence; seed enrichment and conflicting
association; CSV-only unavailable records; FIT/TCX/GPX/gzip; native missing,
zero, duplicate/backward/gap and fractional timing; source-summary/stream
separation; individual malformed files and rollback; archive/path/symlink safety;
lossless zero/nonzero lap integers; unchanged strict timing for other fields;
re-extraction; unused-versus-extracted field conflicts; and unchanged native
best-20 behavior. Fixtures are generated synthetic data with no personal samples.

**Runtime:** Python 3.10.12; SQLite 3.37.2; `fitdecode==0.11.0` / `fit-v2`;
stdlib ElementTree (Python runtime version) / `xml-activity-v1`;
CSV mapping `strava-export-v1`; schema 3. The final precision guard also passed
all 123 tests and a separate production parse of all **157 real XML artifacts**;
the known export contains no unsupported finer precision.

XML field mapping was checked against
[Garmin TCX v2](https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd),
[ActivityExtension v2](https://www8.garmin.com/xmlschemas/ActivityExtensionv2.xsd)
and [TrackPointExtension v1](https://www8.garmin.com/xmlschemas/TrackPointExtensionv1.xsd).
Unknown/private extensions remain recoverable in exact originals.

The real Phase 1 import/re-extraction and independent best-20 verifiers also
passed using the final FIT code. They retain **3,621 native records**, **118 W FIT
session average**, and independently verified **120 W displayed best-20**, with
zero difference between production and independent unrounded calculations.

## Exact local command shapes

Private paths are redacted. Every full acceptance attempt used newly created
disposable state; successful evidence below comes from the corrected clean run.
No accepted working store was replaced or used as the acceptance scratch store.

```bash
.venv/bin/python tools/verify_rideworks_export.py \
  --export '<local-export.zip>' --work-dir '<local-work-directory>'
```

The verifier invokes the product CLI, then repeats the bulk command in a new
process:

```bash
.venv/bin/python -m rideworks --data-dir '<disposable-data-dir>' import-fit '<disposable-seed.fit.gz>'
.venv/bin/python -m rideworks --data-dir '<disposable-data-dir>' import-strava-export '<local-export.zip>'
```

Additional Phase 1 regression commands (the older helpers need an absolute
work-directory argument because they change the child process working directory):

```bash
.venv/bin/python tools/verify_rideworks_import.py \
  --input '<representative-fit.gz>' --work-dir '<absolute-local-work-directory>'
.venv/bin/python tools/verify_rideworks_analysis.py \
  --input '<representative-fit.gz>' --work-dir '<absolute-local-work-directory>'
```

## Complete import / restarted rerun

| Check | First import | Restarted rerun |
| --- | ---: | ---: |
| CSV rows seen | 1,434 | 1,434 |
| Activities created | 1,433 | 0 |
| Existing Activities reused | 1 | 1,434 |
| Existing Activities enriched | 1 | 0 |
| CSV Sources created | 1,434 | 0 |
| CSV Sources reused | 0 | 1,434 |
| CSV-only Activities | 13 | 13 |
| Referenced artifacts attempted | 1,421 | 1,421 |
| Artifacts imported | 1,420 | 0 |
| Artifacts reused | 1 | 1,421 |
| Failures / unresolved associations | 0 / 0 | 0 / 0 |
| Elapsed seconds | 616.55 | 2.72 |

The one initially reused Activity/artifact is the Phase 1 seed. Its Activity ID,
FIT Source/extraction, typed summary and native evidence remain unchanged after
bulk enrichment and restarted rerun. A separate attributable CSV row Source
supplies the actual source title. Final Activity count is **1,434, not 1,435**.

Actual content/packaging counts matched the known export in both passes:

| Content / received packaging | Count |
| --- | ---: |
| FIT.GZ | 1,264 |
| GPX (plain) | 29 |
| GPX.GZ | 76 |
| TCX.GZ | 52 |

Preflight also matched the known type population: 1,264 Virtual Ride, 146 Ride,
22 Run, one Walk and one Rowing. File-source native power exists in **1,309**
Sources, matching the research coverage count; field presence is not labeled
measured or treated as a trusted-trend eligibility decision.

Additional passed checks:

- all **1,421** received artifacts equal their preserved bytes and stored hashes/sizes;
- the exact CSV is preserved once and row Sources trace to its data-row positions;
- all 13 CSV-only Activities have unavailable native evidence and no fake file Source;
- FIT, TCX, GPX and CSV-only examples are inspectable through production Store;
- SQLite integrity and foreign-key checks pass;
- restart preserves the entire source-aware history read result;
- rerun preserves Activities, file/CSV Sources, current extractions, snapshots,
  row locations and retained integer lap rows exactly;
- source summaries, CSV metadata and native records remain separate;
- integer lap independent-decode and re-extraction checks pass.

The successful verifier removed its disposable store on completion. Previous
interrupted scratch state, if present, remains local and ignored. Original source
files/ZIP were never modified in place.

## Privacy / scope / handoff

`acceptance.json` and this report contain aggregate/structural evidence only.
No raw ZIP/CSV, source FIT/TCX/GPX, native streams, personal database, coordinates,
private source titles/descriptions, absolute personal paths, credentials or
screenshots are included. JIT controls and acceptance criteria are unchanged.
The earlier `stop-evidence.json` is retained as historical structural evidence;
its seven-file diagnosis is superseded for prevalence by the full-run result.

## Analyst acceptance

On **2026-10-04**, the Analyst reviewed PR #13 at head
`64b4247a5545574feb9f24c50a90840d329ad4e7` against the updated P2-01 JIT and
Phase 2 historical-import contract and **accepted P2-01**.

The review confirmed the complete 1,434/1,421/13 population, exact-original
preservation, representative enrichment without duplication, restart/idempotent
rerun, source/evidence separation, schema migration safety, the authorized
lossless FIT lap-timestamp handling, unchanged Phase 1 best-20 behavior, privacy
boundary, and absence of P2-02/P2-03/API-sync scope creep.

The durable Analyst decision is recorded on PR #13. PR #13 was then merged to
`main` as `57c00ae396bfb1e9c2c4c72ff42c5628afda9940`.

P2-02 implementation did not begin as part of this acceptance.
