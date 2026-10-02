# P1-01 verification

**Product:** RideWorks
**Date:** 2026-10-02
**Branch:** `task/p1-01-durable-fit-import`
**Base:** refreshed `main` at `5b0659d`
**State:** implementation and local verification complete; awaiting HARD — Analyst review.

## Implementation and environment

The new `rideworks/` package is independent of the retired application. It uses
SQLite tables for Activity, Source, current extraction, typed session summary,
ordered records, laps and events. Originals are preserved by received-byte hash.
The read API returns consistent Source/extraction snapshots. Re-extraction
replaces only normalized evidence, atomically, while retaining Activity/Source
identity. Legacy application files were ignored, not removed or changed.

- Python: 3.10.12 (GCC 11.4.0)
- fitdecode: 0.11.0, strict CRC/error handling
- RideWorks mapping: `fit-v1`
- SQLite: 3.37.2; schema version 1; foreign keys enabled; full synchronous writes
- Runtime isolation: temporary virtual environment containing RideWorks and
  fitdecode, without the retired application dependencies

Ordinary implementation choices relevant to P1-02:

- UUIDs identify Activity, Source and each current extraction independently.
- Each Source has one current extraction, with obsolete snapshots deleted within
  the same replacement transaction. Later derivations can compare extraction UUIDs.
- SQLite typed columns store source evidence, not a generic EAV or canonical
  Activity summary. Multiple Sources can reference one Activity structurally.
- Record ordinal and decoder frame ordinal are separate from UTC timestamp.
- Timestamp strings use ISO 8601 with explicit UTC offset; null remains missing.
- FIT source units are seconds, metres, watts, bpm and rpm. Timer/elapsed duration
  are separate. No moving-time interpretation is introduced.
- FIT source attribution and unknown signal origin are independent of availability.
- `inspect` includes summaries/counts/metadata, excluding raw streams and detailed
  lap/event rows. Other record signals are not extracted, not observed absent.

The release's installed `DefaultDataProcessor` was inspected and its UTC and
source-unit behavior confirmed against the upstream
[processor source](https://github.com/polyvertex/fitdecode/blob/master/fitdecode/processors.py)
on 2026-10-02. The presentation-unit processor is not used. Device-relative
integer timestamps are rejected rather than guessed into calendar time.

## Commands and automated results

Environment setup used an isolated temporary environment:

```bash
python3 -m venv /tmp/rideworks-p1-01-venv
/tmp/rideworks-p1-01-venv/bin/pip install fitdecode==0.11.0
/tmp/rideworks-p1-01-venv/bin/pip install -e .
```

Final automated command:

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/rideworks-p1-01-venv/bin/python -m unittest discover -s tests -v
```

**37 tests passed:** 20 new RideWorks tests and all 17 existing research tests.
New tests exercise the actual fitdecode path using a 200-byte committed,
synthetic FIT fixture and stdlib-generated variations. The fixture contains no
personal/location data. No FIT-writing dependency was introduced.

Coverage includes persistence, new-process inspection, repeat-import identity,
exact-byte preservation of plain/gzip input, filename independence, differing
packaging as distinct artifacts, summary nulls, legitimate zero power, missing
power/HR, availability counts and unknown origin, duplicate/backward/missing
record timestamps, session/lap/event timing and timer trigger, strict invalid
FIT/gzip/CRC failures, multiple/chained session rejection, database rollback,
stored-original integrity errors without repair, successful extraction revision
replacement, decoder/database re-extraction failures, and verified reuse of
unreferenced originals without overwriting conflicting bytes.

## Representative local acceptance

The representative artifact was copied from the existing ignored local export
into `local_data/p1-01-input/21538875902.fit.gz`; no original was modified.
The acceptance command was:

```bash
/tmp/rideworks-p1-01-venv/bin/python tools/verify_rideworks_import.py --input local_data/p1-01-input/21538875902.fit.gz --work-dir /tmp
```

The utility creates a disposable input copy and store. It invokes import,
repeat-import, inspect and re-extraction through separate CLI processes from a
different working directory, and also verifies the callable read boundary.
It deletes only its own disposable input before re-extraction. Temporary data
are cleaned on exit. A database trigger deliberately aborts record persistence
during re-extraction to verify transaction rollback after replacement has begun.

**Result: passed**, matching the controlling research/acceptance expectations.

| Evidence | Result |
| --- | --- |
| Received artifact SHA-256 | `5830f9ee6b4dd61265f1e8487d7ff62d97fbd54695ea347015e72df2ff27acc6` |
| Received/preserved size | 63,440 bytes |
| Activity / FIT Source / supported session | 1 / 1 / 1 |
| Native record count | 3,621 |
| Power / HR present values | 3,621 / 3,621 |
| Power / HR missing values | 0 / 0 |
| Positive timestamp deltas | 3,620; every delta exactly 1 second |
| Duplicate / backward / missing timestamps | 0 / 0 / 0 |
| Laps / timer events | 2 / 2 |
| Source elapsed / timer duration | 3,620 s / 3,621 s |
| Required source summary evidence | All required fields available and persisted |
| Exact preserved bytes and hash/size | Match supplied artifact |
| Repeat import after process restart | Same Activity, Source and extraction UUIDs |
| Reopened read boundary | Same complete evidence |
| Re-extraction without disposable input | Succeeds from managed original only |
| Successful re-extraction | Same Activity/Source; new extraction UUID; same normalized values |
| Induced failed re-extraction | Previous UUID and all evidence remain usable, including after reopening |
| Compact inspect | No raw stream or coordinate fields |
| Supplied original | Unchanged |

No best-20-minute analysis or UI was implemented. This verifies P1-01's evidence
boundary and does not establish final Phase 1 product acceptance.

## Boundaries and review

Unsupported conditions are reported clearly: invalid gzip/FIT/CRC, multiple
sessions, chained FIT files, non-activity file types and unresolved device-relative
timestamps. Different received bytes are not reconciled as the same ride. There
is no bulk import, ORM, migration framework, web framework, generic storage
abstraction, athlete-state policy or application-derived ride metric.

File placement and database commit cannot be one filesystem transaction. Files
and directory entries are synchronized before SQLite commit; completed metadata
are atomic. A crash can leave an unreferenced original/staging file. Import never
overwrites established originals and can reuse an identical unreferenced original
only after hash/size verification. Ordinary database failures clean newly created
unreferenced originals while protecting established references.

Only the synthetic fixture is committed. The representative FIT, source archive,
personal databases, raw records, coordinates, private absolute source paths and
secrets are not included in this change. Analyst acceptance of the representation
and verification evidence remains outstanding. P1-02 has not begun.
