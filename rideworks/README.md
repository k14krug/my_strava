# RideWorks

P1-01 uses Python 3.10+, standard-library SQLite, and `fitdecode==0.11.0`.
It runs independently of the retired Strava application and its dependencies.
From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m rideworks import-fit /path/to/activity.fit.gz
.venv/bin/python -m rideworks inspect <activity-id>
.venv/bin/python -m rideworks reextract <source-id>
```

The installed `rideworks` command provides the same interface. Place the optional
`--data-dir /path/to/private-data` before the subcommand. Directory precedence is
explicit argument, `RIDEWORKS_DATA_DIR`, then `~/.rideworks`. Relative explicit
paths resolve at invocation; the default is independent of the working directory.
Originals and the SQLite database are private runtime data; keep them out of Git.

A successful import returns independently generated Activity and Source UUIDs
and the current extraction UUID. Reimporting identical received bytes verifies
the established original and returns those same identities. Different bytes,
including different gzip packaging, create a separate Activity in this phase.
Filename suffixes do not establish packaging or FIT validity. Original basenames
are retained for inspection; external paths are not persisted.

`Store(data_dir)` is a context manager. `import_fit(path)` and
`reextract(source_id)` return identity/status dictionaries. `get_activity(id)`
returns `activity` metadata and a `sources` list; `get_source(id)` returns one
Source snapshot containing `source`, `extraction`, `summary`, `records`, `laps`,
`events`, and `availability`. These methods use a consistent database read
transaction. `inspect(id)` omits records and detailed lap/event rows.

The physical tables have typed columns, with each normalized row linked to its
extraction and thus to its Source. Activity contains identity and creation time
only. Multiple Sources can reference an Activity; association/reconciliation
of different artifacts is deferred. Source owns one current extraction. A
successful re-extraction replaces that extraction transactionally and changes
its UUID, allowing later calculations to detect stale inputs. Old extraction
snapshots are not retained in P1-01.

Records preserve `record_index` (zero-based record ordinal) and `source_order`
(zero-based decoder frame ordinal, including headers and definitions). Retrieve
in record order, retaining duplicates, backward times, gaps and nulls. Timestamps
are ISO 8601 UTC strings; missing timestamps are null. Device-relative timestamps
are rejected instead of guessed into calendar time. Source summary units are
seconds, metres, watts, bpm and rpm as specified by `SUMMARY_UNITS`.
Elapsed and timer time remain separate. The decoder's default processor supplies
UTC date-time decoding and FIT source units; the presentation-unit processor is
not used. See the upstream [processor source](https://github.com/polyvertex/fitdecode/blob/master/fitdecode/processors.py).

Power/HR availability includes total, present and missing counts, with statuses
`present`, `present_with_missing` or `observed_absent`. Origin is independently
`unknown`; field presence does not prove measurement. Other record signals are
not extracted, and remain recoverable from the original. No application analysis
metrics are calculated here.

Import copies received bytes to managed staging, hashes and parses that copy,
and places exact bytes under `originals/<sha256>.fit[.gz]` using exclusive file
creation. Files and directory entries are synchronized before the database
transaction commits. Mutations serialize with a SQLite write transaction.
Failed imports roll back all metadata and safely remove newly created
unreferenced originals. A crash may leave an unreferenced original/staging file;
an identical original is reused only after integrity verification. Established
originals are never silently overwritten or repaired. Re-extraction verifies
stored integrity before decoding and leaves the prior current extraction intact
on decoder or database failure.

Only one FIT file with one activity session and exactly one `file_id` whose type
is `activity` is supported. Missing/duplicate `file_id` messages, chained FIT
files, multiple sessions, non-activity file types, malformed gzip/FIT, and invalid
CRCs fail clearly. Exact originals enable later extraction of fields omitted here.

Verification:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/verify_rideworks_import.py --input "$P1_01_INPUT" --work-dir /tmp
```

Set `P1_01_INPUT` to the local-only representative `21538875902.fit.gz`. The
acceptance utility uses and removes a disposable copy and disposable store,
runs CLI commands from a different working directory, and emits only compact
facts. It never modifies the supplied file. Run with assertions enabled.

P1-02 adds on-demand activity analysis:

```bash
.venv/bin/python -m rideworks analyze <activity-id>
.venv/bin/python tools/verify_rideworks_analysis.py --input "$P1_01_INPUT" --work-dir /tmp
```

`rideworks.analysis.analyze_activity(store, activity_id)` consumes the P1-01
read boundary and returns `activity`, `source`, `extraction`, `source_summary`,
`native_records`, `availability`, and `best_20_minute_power`. The summary's
`values` remain source-supplied FIT session evidence; the best-20 result is
explicitly `calculated` and identifies its Activity, Source and extraction.
The native record dictionaries, including order, timestamps, zero and null
values, pass through unchanged. The normal `analyze` CLI omits those records.

Method `best-average-power-v1` evaluates exactly 1,200 consecutive records with
complete power and exact one-second timestamp deltas. Each candidate represents
`[start, start + 1200 seconds)` and requires no additional endpoint sample.
Zero watts contribute to the mean. Missing power and timing defects disqualify
only the windows containing/spanning them. Equal unrounded means select the
earliest source-record window. The result includes unrounded watts, nearest
whole watts with .5 upward rounding, selected indices/times and eligibility.
No eligible window returns `unavailable` with a reason and null result values.
Unexpected power values fail clearly for investigation rather than being repaired.

There is no result cache or analytical database schema. Each call reads the
current extraction and recalculates. Multiple candidate FIT Sources fail with
an explicit selection-decision error; no source-ranking policy is introduced.
`tools/verify_rideworks_analysis.py` independently enumerates complete windows,
directly sums their samples, and applies Decimal half-up rounding. It compares
its result against the application, checks source/native evidence unchanged,
and verifies analysis after re-extraction using a disposable store/input copy.
Run verification with assertions enabled.

## Local browser review (P1-03)

Import once, then start the server with that same private data directory:

```bash
.venv/bin/python -m rideworks --data-dir local_data/p1-03-review import-fit local_data/p1-01-input/21538875902.fit.gz
.venv/bin/python -m rideworks --data-dir local_data/p1-03-review serve --port 8765
```

Open the printed URL, normally `http://127.0.0.1:8765/`, and select a ride in
Activities. The stable review URL is `/activities/<activity-id>`. Stop with
Ctrl+C and run the same server command to reopen the activity without importing
again. Use `serve --port 8767` to choose a different local port. The server binds
only to `127.0.0.1`; it has no account, upload or remote-hosting workflow.

The browser application uses Python's standard-library HTTP server, server-rendered
HTML and packaged local CSS/JavaScript/SVG. No retired application imports,
new runtime dependencies, frontend build step, CDN or external runtime requests
are required. `Store.list_activities()` lists activities with exactly one current
FIT Source/session; it does not choose among ambiguous Sources.

Normal review uses miles, feet, W, bpm and rpm; original source SI values remain
unchanged. Dates use the browser's local timezone with a visible offset (labeled
source UTC fallback without JavaScript). FIT elapsed and timer durations are
distinct. The best-20 panel consumes the accepted `analyze_activity` result and
labels it RideWorks-calculated, separately from FIT session summaries.

The chart receives native record indices, UTC timestamps, power and HR unchanged
in native order. Elapsed time is a display transformation relative to the source
session start (first available native timestamp if start is absent). Zero remains
a sample; missing values/timestamps break paths, as do forward gaps greater than
one second and backward jumps. Records without timestamps remain inspectable
with arrow keys rather than being assigned invented times. Pointer inspection
chooses the nearest timestamped native sample, with the first native record
winning an equal-distance tie. Focus the chart and use arrow keys, Home or End
to inspect every record, including duplicate timestamps. Each signal has its
own labeled axis. No resampling, smoothing or analytical recalculation occurs
in the browser.

Source and calculation details expose identities, artifact integrity, versions,
availability and unknown sensor origins without private paths or coordinates.
The local SVG mark follows the verified compact brand board; Owner approval of
the applied identity and screen is required before Phase 1 acceptance. See
`reports/P1-03/verification.md` for the review procedure and evidence.

## Optional repository .env startup configuration

From the repository root, optionally copy the safe `.env.example` to `.env` and
edit its local values. `.env` remains Git-ignored; do not commit its contents.
The CLI finds this file next to the checkout's `pyproject.toml`, independently
of the launch directory. Installed wheels without a checkout do not look for
`.env`; exported environment variables and CLI flags still work.

| Setting | Precedence / default | Meaning |
| --- | --- | --- |
| Data directory | `--data-dir` > exported `RIDEWORKS_DATA_DIR` > repository `.env` > `~/.rideworks` | Applies to all CLI commands. Original/source data stays private. |
| Server port | `serve --port` > exported `FLASK_RUN_PORT` > repository `.env` > `8765` | Decimal integer 1–65535; always binds to `127.0.0.1`. |
| Request diagnostics | exported `FLASK_DEBUG` > repository `.env` > off | Accepts 0/1, false/true, no/yes or off/on, case-insensitively. |

`FLASK_DEBUG` retains the familiar variable name but enables only server-console
GET status and response timing. Errors report the exception class without private
paths, query strings, credentials or tracebacks in the browser. There is **no
Flask debugger or automatic reloader**; restart the server to pick up Python
changes. No Flask dependency was introduced.

Only these three keys are read. Exported variables are not overwritten and the
process environment is not mutated. The small file reader accepts `KEY=value`,
optional `export `, single/double quotes, blank lines and `#` comments. Quote
values with spaces or literal `#`. There is no shell execution, interpolation,
variable expansion or multiline syntax. Unrelated legacy settings are ignored.
The last file assignment wins. Selected invalid port/debug values fail before
the server binds; higher-priority CLI/exported values bypass overridden file
values. An empty data directory is rejected rather than treated as the checkout.
Relative data-directory paths retain the existing resolution at invocation.

The explicit review command above remains deterministic even if `.env` selects
another data directory or port. With the example values, this shorthand also works:

```bash
.venv/bin/python -m rideworks serve
```

## Current activity titles and future source-title finding

Phase 1 has no actual source activity-name field. Both Activities and review
therefore show an explicitly **Derived title**: type label plus the FIT source
start date in UTC, using fixed English month names (for example
`Virtual Ride — Sep 29, 2026`). This does not depend on today's date, browser
locale/timezone or import time. Missing date remains `date unavailable`; no
calendar value is manufactured. Cycling type and Virtual Activity subtype stay
separate. Title origin/basis are inspectable in Source details.

The Owner correction records a future durable-history requirement: preserve and
prefer an actual source activity title when available, with provenance (for
example Strava export/API `Activity Name`), while retaining type/subtype separately.
This task adds no source-title persistence/reconciliation, API/export enrichment
or naming policy beyond the explicitly derived FIT-only fallback.
