# P2-03 verification — Gate 1 Owner review

**Date:** 2026-10-04.
**Branch / PR:** `task/p2-03-performance-history` / [#15](https://github.com/k14krug/my_strava/pull/15).
**Implementation head:** `6a8d41277be839a6b316a8066940d36a857ea4e8`; final publication adds documentation/evidence only.
**State:** implementation and required local verification complete. Stopped at **Gate 1 HARD — Owner**. P2-03 stays `in_progress`; Owner approval and Analyst acceptance are pending.

## Behavior and analytical context

`rideworks/performance.py` evaluates current Activity metadata under policy
`virtual-native-power-v1`, then uses the accepted production
`best-average-power-v1` calculation for each candidate native extraction.
The calculation's mathematics are unchanged; its error wording now identifies
native rather than FIT-only extraction. FIT, TCX and GPX can participate.

Classification uses the latest non-empty Strava activity-type observation and
retains its Source identity. With no applicable Strava type, unambiguous native
virtual-session evidence can qualify. Native virtual/outdoor ambiguity excludes
rather than guessing. Outdoor Ride and other non-virtual Activities are excluded
before native stream loading. Virtual Ride native power is accepted for this
purpose, without asserting measured provenance. Summary watts never substitute.

Each candidate is evaluated independently. Exactly one eligible native Source
supports an Activity result. Multiple eligible Sources exclude it; an ineligible
competitor does not invalidate an otherwise unambiguous eligible Source.
Naive native timestamps remain explicitly unsupported. Invalid timestamps,
invalid power, missing extractions or inconsistent native counts are fatal
invariant failures rather than ordinary ineligibility.

Schema **4** adds one specific `performance_history` table keyed by Activity,
duration and policy, with method, selected Source/extraction foreign keys,
input signature, calculation timestamp and compact result/status JSON.
The JSON retains classification identities, per-candidate reasons, raw/display
watts and the complete best-window record/time context. No native stream is copied.
The duration key does not restrict the representation to a fixed duration list.

Rebuild holds one consistent write snapshot and replaces the complete history
atomically. Fatal failures leave previously committed history intact.
Re-extraction cascades away the affected eligible result; current metadata/input
signature checks hide changed classifications, dates or competing extractions.
Rebuild timestamp changes on rerun, while signatures, statuses, selected inputs,
window context and raw/display results remain identical. No background rebuild,
generic dependency framework or universal source ranking is introduced.

The `/performance` read boundary loads persisted results and current metadata,
without querying native records. All dated current eligible results appear
chronologically as individual observed points on a clearly labeled zero-based
watt axis. There is no smoothing or fabricated daily series. Pointer and keyboard
inspection show date, preferred source title, whole watts and an Activity link;
selected Source/extraction/raw/window provenance is inspectable. Known dates are
browser-local; unknown-zone dates retain their supplied calendar day and label.
Unsupported Activity dates are reported and not assigned invented positions.
Activities and Performance have accurate active navigation. Empty/unbuilt and
changed-input states render safely. P2-04 comparisons are not included.

## Automated verification

```bash
.venv/bin/python -m unittest discover -s tests
```

**162 tests passed in 7.307 seconds**: all 142 accepted tests plus 20 P2-03 tests.
Existing migration assertions now expect additive schema 4, retaining their
original identity/byte/evidence/rollback checks. Existing navigation checks now
require the real Performance link while continuing to reject fake future pages.
No calculation tests were removed or weakened.

New synthetic coverage includes selected-input/window/classification context,
Virtual Ride versus outdoor/non-cycling exclusion without stream reads,
CSV-only summary rejection, native classification fallback/ambiguity,
latest non-empty classification identity, multiple eligible versus short competing
Sources, short/no-power reasons, unknown native timezone, deterministic rebuild
and restart, re-extraction/new-source/classification invalidation, fatal failure
retention, corruption detection, missing longitudinal dates, metadata-only reads,
payload escaping, active navigation and safe empty states. Generated TCX and GPX
complete native streams each produce 120 W with the same earliest exact-tie rules.
Independent segmentation is compared with the accepted direct-window oracle on
zero, missing, gap, duplicate/backward and tie cases. Existing P1 calculation tests
retain complete-window, zero/missing/timing/tie/half-up regression coverage.

## Disposable full-history acceptance

A new local-only copy, `local_data/p2-03-review`, was made from the accepted
`local_data/p2-02-review` directory before schema migration/rebuild. The accepted
store, original export and original input files were not changed. Both stores,
all personal originals and screenshots remain ignored and local.

Production rebuild command:

```bash
.venv/bin/python -m rideworks --data-dir local_data/p2-03-review rebuild-performance
```

| Population / status | Count |
|---|---:|
| Evaluated Activities | 1,434 |
| Virtual Ride candidates | 1,264 |
| Eligible trusted results | 1,022 |
| Activity shorter than required | 198 |
| No complete timestamp-contiguous window | 39 |
| No complete power window | 5 |
| Outdoor Ride excluded | 146 |
| Other non-virtual Activity excluded | 24 |

Status/reason counts total **1,434**. The three Virtual Ride ineligible categories
total 242; these ordinary short/incomplete-window cases are covered by the JIT.
No ambiguity or new evidence category appeared. All 146 outdoor Rides and all
24 non-cycling Activities contribute **zero trusted results**. No unresolved
Virtual Ride/native classification disagreement was found.

Every eligible result uses one identified native FIT file Source/current
extraction; eligible format counts are **FIT: 1,022**. TCX/GPX eligibility is
verified with synthetic complete native streams; this archive contains no
qualifying Virtual Ride XML result. No CSV/session/lap summary supplied a result.
All 1,022 eligible results have supported longitudinal dates and are plotted.
Date span: **2018-05-13 through 2026-09-29**. Raw average range:
**61.75083333333333–218.39666666666668 W**. These are observed calculated results,
not claims of measured provenance or estimates for unobserved days.

The Phase 1 representative remains eligible at **120 W**, using its same
**3,621 native records** and accepted best-window semantics. Its rich review
still shows **118 W** FIT average and **120 W** RideWorks best-20.

## Independent analytical verification and rerun

```bash
.venv/bin/python tools/verify_rideworks_performance.py \
  --data-dir '<local-review-store>' --representative '<representative.fit.gz>'
```

The verifier never calls production best-20 or production cohort classification
as its oracle. It independently reads the native records, segments complete
power/absolute one-second runs, enumerates every 1,200-record window with prefix
sums, and uses Decimal half-up rounding. This O(n) implementation differs from
the production rolling sum and was cross-checked against the accepted direct
O(n × 1,200) window verifier on generated cases.

**All 1,434 Activities accounted for; all 1,022 eligible results agree exactly**
on raw/display average, start/end record and timestamp context, sample/window
counts and earliest exact ties. Classification identities and selected
Source/extraction identities agree. Outdoor and non-cycling eligible counts are
zero; CSV/summary substitution is absent. SQLite integrity is `ok`; foreign-key
check is empty.

The verifier rebuilds again and compares every status/result/input signature,
then closes/reopens the Store and compares every persisted result and UI point.
**Idempotent rebuild and restart passed**. Only execution timestamps change.
The final strengthened input-signature version was rebuilt and this full
independent check repeated successfully.

## HTTP and actual browser verification

```bash
.venv/bin/python tools/verify_rideworks_performance_http.py \
  --data-dir '<local-review-store>' --representative '<representative.fit.gz>'
.venv/bin/python tools/verify_rideworks_performance_ui.py \
  --data-dir '<local-review-store>' --port 8768 --session rideworks-p2-03
```

HTTP acceptance starts/stops dedicated verification processes on port 8769.
The accepted full-history Activities search/type/date/sort/pagination, title
provenance and real FIT/TCX/GPX/CSV-only routes passed in two successive processes.
Two further Performance processes each returned exactly the **1,022** persisted
current points. Performance restart equality and absence of native streams,
private runtime paths and coordinates passed. Each process's ownership of the
verification port was checked; no existing review server was mistaken for it.

Managed Chromium was opened through the Playwright skill wrapper, with the cached
CLI used for subsequent commands. Actual browser acceptance passed on final code:
Activities/Performance navigation, all 1,022 payload and SVG points, first/middle/last
pointer inspection, Home/End/arrow-key inspection, pointer click and Enter to the
contributing Activity, browser back, source title/date/watt readouts, selected
provenance and the eligibility explanation. Separate contexts verified native
local date formatting in **America/Los_Angeles** and **Asia/Tokyo**. No horizontal
overflow at **1448×1086** or **390×844**; all points remain available at both widths.
Performance payload contains results/metadata only, with no raw native streams.
Desktop and phone screenshots were visually inspected for chart scale, density,
readable readout/navigation and continuity with the accepted RideWorks shell.

## Owner review handoff

The dedicated full-history review server is running at
**http://127.0.0.1:8768/performance**, backed by `local_data/p2-03-review`.
Expect **1,022 eligible results**. Exact startup command from the repository root:

```bash
.venv/bin/python -m rideworks --data-dir local_data/p2-03-review serve --port 8768
```

The rebuild command above is available if the review copy needs recalculation.
Other older port-8765/8766 instances use separate stores.

Local-only screenshots:

- `output/playwright/p2-03-performance-desktop.png`
- `output/playwright/p2-03-performance-phone.png`

No personal title, Activity ID, Source ID, private input path, native record stream,
coordinate or screenshot is committed/published in the verification artifacts.
`acceptance.json` retains aggregate rebuild/independent/HTTP/Chromium results only.

Under JIT §20, stop at **Gate 1 HARD — Owner** for review of whether the history
is useful/understandable and the cohort explanation is clear. After explicit
Owner approval, record it and stop at Gate 2 HARD — Analyst for evidence,
calculation/persistence and UI acceptance. **P2-04 has not begun.**
