# P1-02 verification

**Product:** RideWorks

**Date:** 2026-10-02

**Branch:** `task/p1-02-single-ride-analysis`

**Implementation commit:** `6851477`

**PR:** [#11](https://github.com/k14krug/my_strava/pull/11)

**Base:** refreshed `main` at `67c27ab`, including accepted P1-01 and the Analyst-authored P1-02 brief.

**State:** implementation and verification complete; awaiting HARD — Analyst review.

## Analysis boundary and semantics

`rideworks.analysis.analyze_activity(store, activity_id)` consumes P1-01's
consistent `get_activity` snapshot. It returns Activity/Source/extraction
metadata, source-attributed FIT session summary, unchanged native records,
availability, and a separate calculated best-20 result. It uses no SQL, FIT
reparsing, research-report JSON, Strava access, source ranking or result cache.
The optional `analyze` CLI exposes a compact version without native records.

Method **`best-average-power-v1`** uses exactly 1,200 consecutive source records,
complete power and exact one-second timestamp deltas. Its half-open interval is
`[t, t + 1200 seconds)`; 1,200 samples suffice without an extra endpoint sample.
Zero contributes to the mean; missing power never becomes an eligible zero.
Timing defects invalidate windows spanning them, leaving complete windows
elsewhere eligible. Equal unrounded means select the earliest record order.

Production uses a rolling integer sum and counts of missing power/bad adjacent
timestamp deltas. It compares unrounded sums and rounds the selected mean to
nearest whole watt, halves upward, using exact integer arithmetic. The original
records remain unchanged. Unexpected power values fail for investigation.
No eligible window returns explicit unavailable status, a reason and null
selected-window/power values. Multi-source choice fails clearly.

Each call calculates from the current extraction and reports its identity.
Re-extraction requires no cache invalidation mechanism or analytical schema.
The accepted importer, extraction mapping (`fit-v1`) and storage schema are
unchanged. No P1-03 UI or later-phase calculation has been implemented.

## Environment and automated verification

The task reused the isolated installed RideWorks environment at
`/tmp/rideworks-p1-01-venv`: Python 3.10.12, fitdecode 0.11.0 and SQLite 3.37.2.
New analysis/verification code uses only the standard library and the accepted
RideWorks read boundary. No dependencies or infrastructure were added.

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/rideworks-p1-01-venv/bin/python -m unittest discover -s tests -v
```

**64 tests passed:** 25 P1-02 tests, 22 P1-01 tests and 17 research tests.

Synthetic coverage includes:

- source attribution, unchanged source summary, distinct elapsed/timer values,
  null summaries, native order/timestamps/power/HR, legitimate zero and missing
  values, availability and current Source/extraction identity;
- exactly 1,200 samples, insufficient 1,199 samples, final sliding candidates,
  zero-inclusive means and all-zero available results;
- missing power invalidating only affected windows, complete windows elsewhere,
  gaps, duplicates, backward and missing timestamps, and defects immediately
  before a complete window;
- earliest unrounded ties, better unrounded means despite equal rounded watts,
  and below/at/above half-watt rounding;
- explicit unavailable states, unexpected values, no external reparse,
  missing/unusable Source/extraction, ambiguous multiple FIT Sources and compact CLI;
- recalculation against revised current evidence after re-extraction, beyond
  merely reporting a changed UUID;
- independently expressed direct sums, tie/rounding, missingness/timing and
  zero/unavailable distinction, including a check that the verifier never calls
  the production best-window helper.

All synthetic FIT inputs use the existing privacy-safe fixture or its stdlib
builder and temporary directories. No personal test fixture was introduced.

## Independent representative acceptance

Exact command:

```bash
/tmp/rideworks-p1-01-venv/bin/python tools/verify_rideworks_analysis.py --input local_data/p1-01-input/21538875902.fit.gz --work-dir /tmp
```

The utility imports its own disposable copy through P1-01, obtains the RideWorks
Activity ID, reads current normalized evidence, and removes only the disposable
input before analysis. It never modifies the supplied representative artifact.
It checks API and separate-process CLI output and cleans its disposable store.

The independent calculation enumerates each start position, checks timestamps
against the first timestamp plus offsets `0..1199`, directly sums all 1,200
samples, compares Decimal means and rounds with `ROUND_HALF_UP`. It does not
call the production rolling/best-window helper or share its timing/rounding
helpers. It retrieves input records independently through `Store.get_source`.

**Result: passed.** No best-20 target was taken from Strava or previous research.

| Evidence/result | Production | Independent / verification |
| --- | --- | --- |
| FIT Sources / current sessions | 1 / 1 | Single-source boundary confirmed |
| Native records | 3,621 | Unchanged from stored extraction |
| Power / HR present | 3,621 / 3,621 | Missing counts 0 / 0 |
| Positive timestamp deltas | 3,620 | Every delta exactly 1 second |
| Missing / duplicate / backward timestamps | 0 / 0 / 0 | Matches P1-01 acceptance |
| Eligible candidate windows | 2,422 | 2,422 |
| Selected start record index | 204 | 204 |
| End-exclusive record index | 1,404 | 1,404 |
| Window offsets from first record | `[204 s, 1404 s)` | Exact match |
| Window duration / sample count | 1,200 s / 1,200 | Exact match |
| Unrounded average watts | 120.11916666666667 W | 120.11916666666667 W |
| Rounded whole watts | 120 W | 120 W |
| Unrounded difference | 0.0 W | Meets <= 0.01 W tolerance |
| FIT source session average power | 118 W | Remains separate and unchanged |
| FIT elapsed / timer duration | 3,620 s / 3,621 s | Remain distinct |

Application-generated identities for this disposable run (not external ride IDs):

- Activity: `370b8ebb-0b54-4cba-90b9-6e882ead9bed`
- Source: `b2f5ee57-5892-40fd-b607-3153aae88f8e`
- Extraction consumed: `cfb77aa2-ce1c-4b21-88d3-53df72294df9`

The result includes those identities, method/version, calculated origin, duration,
sample count, start/end indices and timestamps, raw/rounded watts and eligibility.
IDs change between disposable runs; the calculated value and selected indices
are reproducible from the same extraction evidence.

Additional acceptance checks passed:

- all required available FIT summary fields remain source evidence; average
  power is not overwritten by the best-20 derivation;
- API native records/availability are identical to the P1-01 read snapshot;
  no resampling, interpolation, smoothing, deduplication or manufactured samples;
- compact CLI matches the API's compact view without raw streams, coordinates
  or absolute input/runtime paths;
- source evidence is unchanged after analysis;
- after P1-01 re-extraction, a fresh analysis reports the new current extraction
  ID and recalculates the same best-20 result;
- the supplied original is unchanged and only disposable data were removed.

## Handoff and privacy

Material changes are one analysis module, the small CLI command, synthetic tests,
a separate acceptance/verifier utility, usage documentation and lifecycle state.
There is no new persistence schema, cache, general metrics framework, source
ranking, UI, historical state, bulk import or legacy runtime change.

No personal FIT, export archive, database, raw stream, coordinates, secret or
private absolute source path is committed. The report contains compact derived
facts and permitted local relative input tokens only.

P1-02 remains `in_progress` with implementation `ready_for_review`. Analyst
acceptance of the analysis boundary, semantics and independent verification is
outstanding. P1-03 has not begun.
