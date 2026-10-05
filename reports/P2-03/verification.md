# P2-03 verification — Gate 1 Owner review

**Date:** 2026-10-05.
**Branch / PR:** `task/p2-03-performance-history` / [#15](https://github.com/k14krug/my_strava/pull/15).
**Implementation head:** `fa0d877dc301dd605f612670e6595aafe4e7fc14`; final publication adds documentation/evidence only.
**Controlling correction:** Owner comments on PR #15 and Analyst JIT refreshed from `main` at `3ae14b9`.
**State:** Owner-directed correction implemented and required local verification complete. Stopped at **Gate 1 HARD — Owner**. P2-03 stays `in_progress`; Owner approval and Analyst acceptance are pending.

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
without querying native records. The latest Owner correction presents **one
Performance surface**, with no Current / Trend / History tabs. The default is
**1 year / Rolling 42-day / Trend only**. Four compact cards show Current 42-day
best, Latest eligible ride, Best in last 12 months and Lifetime best, each with
its contributing Activity date/link and evidence age.

Range controls offer **3 mo / 6 mo / 1 yr / 3 yr / All**. View controls offer
**Rolling 42-day / Monthly best / Yearly best**. The dominant rolling step line
is the raw maximum in `(t − 42 days, t]`, tied by earliest Activity then stable
identity. A result expires exactly 42 days after its Activity start; empty
windows remain gaps. It represents demonstrated qualifying evidence rather than
estimated daily performance.

Monthly/yearly views select one strongest eligible raw result per displayed
calendar month/year, using only rides inside the active range and the same
raw-max/earliest-tie rule. Period-best marks sit at their contributing ride dates
with subdued stems from zero; they do not connect successive ride observations.
Empty periods have no mark. Optional ride dots are small and subdued in all
three views and retain inspection/Activity links. The default selected result is
the most recent meaningful best in the active Range/View, including when ride
evidence is enabled. Every eligible result remains accessible in 30-row
supporting evidence pages.

Timed windows and calendar-month range cutoffs end at the page's as-of UTC
instant; month ends clamp to the available calendar day. Unknown-zone Activity
source dates remain labeled and available in period/lifetime evidence, without
inventing membership in absolute clock windows. The full archive has zero such
eligible Activity dates. Known dates are compact browser-local dates with no
GMT suffix. Missing dates are reported rather than assigned invented positions.
Pointer/keyboard inspection retains source date/title/watts, stable Activity
navigation and selected Source/extraction/raw/window provenance. Range/View/
evidence state survives Activity navigation and browser back.

Eligibility & method remains compact and secondary. **Future Performance
candidates** is a collapsed, subordinate product-direction reminder; it labels
possible later durations, athlete context and comparison/signals as candidates,
without controls, calculations, fake data or delivery commitments. Empty/unbuilt
and changed-input states render safely; active navigation remains accurate.
P2-04 comparisons and all other excluded analytical features are not included.

## Automated verification

```bash
.venv/bin/python -m unittest discover -s tests
```

**170 tests passed in 9.234 seconds**: all 142 accepted tests plus 20 P2-03 foundation tests and 8 presentation-window tests.
Existing migration assertions now expect additive schema 4, retaining their
original identity/byte/evidence/rollback checks. Existing navigation checks now
require the real Performance link while continuing to reject fake future pages.
No calculation tests were removed or weakened. Focused verification also passed:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_rideworks_performance*.py'
```

**28 focused tests passed in 2.568 seconds**. Page assertions now require the
three View options, candidates label and removal of obsolete tabs; safe payload,
metadata-only rendering and native calculation checks remain intact.

New synthetic coverage includes selected-input/window/classification context,
Virtual Ride versus outdoor/non-cycling exclusion without stream reads,
CSV-only summary rejection, native classification fallback/ambiguity,
latest non-empty classification identity, multiple eligible versus short competing
Sources, short/no-power reasons, unknown native timezone, deterministic rebuild
and restart, re-extraction/new-source/classification invalidation, fatal failure
retention, corruption detection, missing longitudinal dates, metadata-only reads,
payload escaping, active navigation and safe empty states. Generated TCX and GPX
complete native streams each produce 120 W with the same earliest exact-tie rules.
New presentation tests cover exact 42-day expiry, inclusive arrivals/exclusive
expiry, explicit gaps, valid zero results, raw rather than rounded comparisons,
earliest exact ties, calendar-month/leap-day cutoffs, summary contexts and
evidence age, unknown-zone preservation, empty histories and an independent
direct scan at every change time. Independent native segmentation is compared
with the accepted direct-window oracle on
zero, missing, gap, duplicate/backward and tie cases. Existing P1 calculation tests
retain complete-window, zero/missing/timing/tie/half-up regression coverage.

## Disposable full-history acceptance

The disposable local-only copy, `local_data/p2-03-review`, was made from the accepted
`local_data/p2-02-review` directory before schema migration/rebuild. The accepted
store, original export and original input files were not changed. Both stores,
all personal originals and screenshots remain ignored and local. The copy was
reused for this presentation correction; full rebuild and independent acceptance
were rerun, without reimporting or modifying the accepted P2-02 store.

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
All 1,022 eligible results have supported longitudinal dates and remain
inspectable through All-range ride evidence and supporting history pages.
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
This full independent check was repeated on the final Owner correction.
The persisted calculation and eligibility results are unchanged.

An additional direct scan independently checks the presentation winner at every
ride entry/expiry and at as-of time: **2,019 checkpoints passed**, covering
**208 rolling winner changes**. All four summary contexts agree with independent
raw-value selection. This check does not use the production heap/window selection
as its oracle; the synthetic tests also exercise exact expiry, zero and gaps.

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

- one Performance surface, no obsolete tabs, 1-year / Rolling 42-day / Trend-only defaults;
- all four summary contexts and freshness;
- all **15 Range/View combinations**;
- dominant rolling line and optional **1,022** All-range ride dots;
- monthly/yearly winners independently checked against raw-result maxima at every range;
- monthly/yearly Activity navigation, keyboard inspection and preserved state on back;
- supporting rides enabled in every view without replacing its primary bests;
- all **1,022** results traversed through bounded supporting evidence pages;
- first/middle/last pointer inspection, Home/End/arrow-key inspection;
- pointer click and Enter to the contributing Activity, browser back;
- source title/date/watt readouts, selected provenance and method explanation;
- collapsed future candidates explicitly labeled as unimplemented direction;
- native local dates and full-history period winners in **America/Los_Angeles** and **Asia/Tokyo**;
- every view at **1448×1086**, **1024×900** and **390×844**, without horizontal overflow;
- chart height remains at least 300 px and payload contains no native streams.

The independent browser oracle groups displayed calendar periods with Intl date
parts, sorts eligible raw results by watts/date/identity and compares the complete
set of rendered period winners. Synthetic browser cases in both timezones add
month/year-boundary shifts, leap-day evidence, raw values with equal displayed
watts, earliest exact ties, a valid zero period best, unknown-zone source calendar
dates, future-result exclusion, partial ranges and empty ranges. Empty ranges
have no invented Activity link or fabricated zero result. Synthetic data is
injected only into an isolated verification page, never persisted.

Desktop/phone Rolling screenshots and desktop Monthly/Yearly screenshots were
visually inspected for hierarchy, compact cards and coherent controls, primary
marks versus ride dots, readable chart/readout and RideWorks shell continuity.
Owner visual/usability approval remains pending; local verification does not
assert Owner acceptance.

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
- `output/playwright/p2-03-monthly-desktop.png`
- `output/playwright/p2-03-yearly-desktop.png`

No personal title, Activity ID, Source ID, private input path, native record stream,
coordinate or screenshot is committed/published in the verification artifacts.
`acceptance.json` retains aggregate rebuild/independent/HTTP/Chromium results only.

Under JIT §20, stop at **Gate 1 HARD — Owner** for review of whether the single
Performance surface is useful, Range/View/evidence controls are intuitive, the
three views and summaries make the data practical, and the page meets the visual
quality bar. After explicit
Owner approval, record it and stop at Gate 2 HARD — Analyst for evidence,
calculation/persistence and UI acceptance. **P2-04 has not begun.**
