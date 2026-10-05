# P2-04 verification — Gate 1 Owner review

**Date:** 2026-10-05.
**Branch / PR:** `task/p2-04-recent-context` / [#16](https://github.com/k14krug/my_strava/pull/16).
**Implementation head:** `cc12f1f9464c9e98d1b05374e881c83337f1aa6b`; final publication adds status/evidence only.
**Controlling JIT:** Analyst-authored `docs/tasks/P2-04.md` on refreshed `main` at `7831e6e`.
**State:** Owner Gate 1 approved; stopped at **Gate 2 HARD — Analyst**. P2-04 remains `in_progress`; final Analyst acceptance is pending. P2-05 has not begun.

## Behavior and evidence basis

`rideworks/recent_context.py` selects from the accepted current persisted P2-03
metadata/result boundary. Current and prior results must be eligible under
`virtual-native-power-v1` / `best-average-power-v1` / 1,200 seconds. Existing
input-signature/extraction invalidation suppresses stale results before selection.
Outdoor/non-virtual/ineligible results and summary watts cannot enter the baseline.

For established absolute Activity start `t`, the exact prior interval is
**`(t − 42 days, t)`**: both endpoints are excluded. An Activity exactly 42 days
old has expired; an Activity at the same start instant is not prior. The current
Activity is explicitly excluded. Highest raw watts win; exact ties choose earliest
Activity start, then stable Activity ID. Displayed rounding does not select winners.
Unknown-zone prior dates cannot establish timed-window membership. Missing/stale
current results require a Performance rebuild; missing/unknown current dates or
empty prior windows show honest unavailable reasons without fallback or zero.

Activity Review shows a distinct **Compared with previous 6 weeks** inset inside
the existing Best 20-minute power panel. This ride / Prior 42-day best use prominent
values, followed by a neutral difference of displayed whole watts, compact prior date/title,
explicit Open prior ride and visible View Performance. Method/input/window
provenance stays collapsed under Comparison details. No-baseline Unavailable uses
the same prominent value treatment, with no invented difference or prior link.

The rider-facing difference subtracts the two displayed whole-watt values,
so 120 W versus 195 W reads 75 W below. Equal displayed values say Same displayed
watts, including differing raw averages that round to the same label. Raw
averages still choose the baseline and remain inspectable in details. No percentage,
good/bad colors or fitness interpretation is introduced. Ordinary current FIT
analysis remains separate; thin reviews keep their existing behavior.

This addresses the Owner usability correction in PR #16 and the Analyst JIT
revisions through `7831e6e`: the previous small Recent context row was visually
buried, and raw-derived differences conflicted with the visible arithmetic.
Only this presentation and its verification changed; interval selection, trusted
eligibility, persisted results and data access remain unchanged.

The Activity route holds one read snapshot across metadata, ordinary current
analysis and comparison. Baseline selection loads no native streams and performs
no import, reparse, rebuild or persisted comparison write. Existing current-ride
native chart/calculation reads remain normal. Performance semantics/schema are
unchanged. A bounded phone fix keeps long Unavailable source-metric labels inside
the existing two-column metric grid; source values are unchanged.

## Automated verification

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m unittest discover -s tests -p 'test_rideworks_recent_context.py'
```

**186 full tests passed in 8.398 seconds**: 170 accepted tests plus 16 P2-04
tests. The focused run passed all **16 tests in 1.208 seconds**. Neutral above,
below and equal labels, consistent subtraction of displayed watts and sub-watt
display boundaries are covered without mutating context. Raw baseline selection
and input provenance remain tested separately.

Coverage includes both open endpoints, an instant inside expiry, same-time/future
exclusion, self exclusion, raw versus rounded ties, earliest-time/identity ties,
valid zero baselines, no older-period fallback, unknown prior/current timezone,
missing current result/date, wrong policy/method/duration, outdoor/non-cycling/
ineligible candidates, pending/stale current/prior input suppression, unchanged
inputs/results, source-title escaping and neutral styling. Real synthetic FIT
stores verify rich values/links/details, no native baseline API access or automatic
rebuild, only current native analysis on rendering, clear no-baseline states,
outdoor ordinary best-20 retained and thin ambiguous review without fake context.
Accepted migration, calculation, source, Activities and Performance tests stay intact.

The displayed-difference correction reran focused/full tests and actual Chromium.
The full-history independent, data-access and HTTP/restart evidence below was
completed on the preceding implementation (`443ab424aba4a468fd0f7cbb6b828174039b57cd`) and is retained: this
correction changes only presentation; the selector, persistence and data access
code are unchanged. No archive import or source recalculation was performed.

## Accepted-store copy and full-history acceptance

`local_data/p2-04-review` was copied from the accepted full-history P2-03
`local_data/p2-03-review` store. Immutable originals were copied, and SQLite's
backup API made the consistent database copy. The accepted source store, export
and original inputs were not changed. The Strava archive was not reopened or
reimported; source artifacts were not reparsed; Performance was not rebuilt.

| Population / outcome | Count |
|---|---:|
| Current persisted Activity statuses | 1,434 |
| Eligible absolute-time Activities evaluated | 1,022 |
| With an eligible prior baseline | 1,012 |
| No qualifying prior baseline | 10 |
| Ineligible current Activities checked | 412 |
| Unknown eligible Activity times | 0 |
| Pending/stale Performance inputs in review copy | 0 |

Available + no-prior totals **1,022**. Ordinary no-baseline cases are expected,
with no material unknown-time/source category. All 412 ineligible Activities
remain unavailable for trusted context. Their accepted P2-03 distribution remains
198 short / 39 incomplete timing / 5 incomplete power, plus 146 outdoor Rides and
24 non-cycling Activities. No current Activity supplies its own baseline.

The representative retains **120 W** native best-20, **118 W** FIT source average
and **3,621** native records. Its correctly selected prior best is **195 W**. The neutral difference is
**75 W below**, subtracting displayed 120 W from 195 W. Raw averages
120.11916666666667 and 194.54333333333332 W remain inspectable in details
and retain their analytical role in selecting the prior result.
These are factual calculated/source values with separate provenance, without
training-state interpretation.

## Independent verifier, data-access guards and restart

```bash
.venv/bin/python tools/verify_rideworks_recent_context.py \
  --data-dir '<accepted-store-copy>' --representative '<representative.fit.gz>'
```

For every eligible Activity, the independent oracle filters all persisted trusted
points into the exact open interval and sorts by raw watts/start/identity. It
never calls the production recent-context selector as its oracle. **All 1,022
current/prior selections agree**, including Activity/Source/extraction identities,
raw/display watts, bounds, self exclusion and all 10 unavailable cases. Every
ineligible Activity is also checked for unavailable context.

During baseline evaluation, a SQLite authorizer denies native records/laps/events
reads and mutations. Guards also reject native Activity/Source APIs, imports,
re-extraction and Performance rebuild calls. The guard passed. Existing native
records are loaded only afterward for the ordinary representative regression.

All persisted Performance rows, including execution timestamps and input context,
remain exactly unchanged. Original artifact sizes/modification times stay intact.
Closing/reopening the Store preserves every comparison without recomputation of
native results or reimport. SQLite integrity is `ok`; foreign-key check is empty.
The verifier emits aggregate JSON and writes ignored private review links locally.

## HTTP and actual Chromium acceptance

```bash
.venv/bin/python tools/verify_rideworks_recent_context_http.py \
  --data-dir '<accepted-store-copy>' --representative '<representative.fit.gz>'
.venv/bin/python tools/verify_rideworks_recent_context_ui.py \
  --port 8769 --session rideworks-p2-04
```

HTTP verification runs dedicated processes on port 8770. Accepted full-history
Activities search/type/date/sort/pagination/title and FIT/TCX/GPX/CSV-only review
regressions pass through restart. Two further processes return identical Recent
context for the representative, clear unavailable/no-prior/outdoor cases, stable
prior/Performance links and no native/runtime/location data in comparison markup.
All persisted Performance rows remain unchanged after startup/rendering/restart.

Managed Chromium verifies real Performance-to-Activity navigation, the clear comparison heading, prominent 120/195 W
values, displayed-derived 75 W below and explicit Open prior ride action, prior Activity and browser back, View Performance and back, closed
secondary provenance, no-baseline Unavailable without a fabricated link, and
ineligible rich review that retains ordinary chart/best-20 while excluding trusted
context. Source title, 118 W average and 3,621 native chart samples remain intact.
Four synthetic cases are additionally rendered by the production comparison
panel in Chromium: exact equal, unequal raw averages with equal displayed
watts, and sub-watt raw gaps crossing display boundaries in both directions.
Current/prior labels and the difference agree; exact raw detail values remain
intact. These synthetic panel checks supplement the real full-store navigation.
Prior dates match native browser-local compact formatting in **Los Angeles** and
**Tokyo**. Desktop **1448×1086** and phone **390×844** have no horizontal overflow,
including the ineligible phone case. Screenshots were visually inspected for
hierarchy, compact neutral values and continuity with accepted Activity Review.

## Owner handoff and privacy

The dedicated P2-04 server is running at **http://127.0.0.1:8769/**.
Exact startup from repository root:

```bash
.venv/bin/python -m rideworks --data-dir local_data/p2-04-review serve --port 8769
```

Exact private review routes are in ignored
`output/playwright/p2-04-review-links.json`: `representative`, `no_prior`, `outdoor`.
They are handed to Ken locally rather than published with personal Activity IDs.
Local screenshots:

- `output/playwright/p2-04-recent-desktop.png`
- `output/playwright/p2-04-recent-phone.png`
- `output/playwright/p2-04-no-prior-phone.png`

Inputs, store copy, native files, private links and screenshots remain local and
ignored. Published evidence contains only aggregate counts/values and reproducible
commands, with no personal title/Activity/Source/extraction ID, original input path,
coordinate or native stream.

Under JIT §20, stop at **Gate 1 HARD — Owner** for whether Compared with previous 6 weeks is immediately noticeable and
answers the previous-six-week question without cluttering Activity Review.
After explicit Owner approval, record it and stop at Gate 2 HARD — Analyst for
interval/trust/data-access/UI acceptance. **P2-05 remains pending.**


## Owner approval and Gate 2 handoff

On **2026-10-05**, the Owner explicitly approved the final P2-04
Activity Review comparison after the prominent six-week context and
displayed-arithmetic corrections.

P2-04 remains `in_progress`. Final acceptance belongs to the Analyst at Gate 2.
P2-05 has not begun.
