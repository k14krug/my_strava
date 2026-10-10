# P5-01 — Rolling Training Advisor verification

Implemented on `task/p5-01-rolling-advisor` for **HARD — Analyst Gate 1** review in
[draft PR #26](https://github.com/k14krug/rideworks/pull/26); not accepted or merged.
The controlling [JIT](../../docs/tasks/P5-01.md) permits `/AUTOTASK` and requires
Analyst review followed by Owner review on the running app. Phase 6 remains idle.

## Delivered behavior

- Home's Next Recommended Ride sits beside Recent Activities. Plan uses the same
  calculation, current rider-local day, actual history and optional leg feedback.
- Plan begins today and ends at hard recommendation #3, filling every date.
  Hard work already recorded today is actual context, not recommendation #1.
- Recovery follows hard dates: +1 at ~90–100 W; +2 after Race/Threshold at
  ~105–120 W, after VO2 at ~100–110 W. No automatic third recovery date.
  Hard recommendations respect a maximum of two hard dates per rolling seven,
  including known actual hard dates. Unexpected actual excess remains history.
- Race follows structured quality; structured follows Race. Threshold initially
  supports the FTP goal; recent threshold suggests VO2 as the next structured
  type. This is an initial heuristic, without interval progression or Zwift files.
- Heavy legs make today Recovery. Future normal legs/recovery remain explicit
  assumptions; future recommendations never update actual training or stress.
- Successful sync supports **past** assumed-rest inference only before its local
  date. Today stays unfinished. Stale sync, uncertain recent classification or
  unlocatable recent dates makes today's suggestion provisional/easier; future
  quality remains conditional on review/sync confirming the available history.
- Separate classification corrections, optional date-scoped feedback and explicit
  pre-ride date-level intent are retained in schema 9. The fourth planning table
  is a replaceable classification cache. No source, FTP or analytical policy edits.
- Activity Review shows actual classification and evidence. No confirmed pre-ride
  intent means **No recorded intent**. A retained same-local-date confirmation can
  support category alignment/difference; neither interval completion nor a unique
  match among multiple same-day rides is asserted. No retrospective suggestions.

## Classification choices and limits for Analyst review

`observed-stimulus-v1` is an engineering heuristic using the accepted trusted
Virtual Ride power source and approved date-effective FTP. It does not use selected
stress as an intensity oracle. Consecutive observed bins alone count; gaps,
nulls and duplicates break bouts. Verified timer pauses are excluded.

- At least six observed 20–90 s bouts at ≥110% of dated FTP suggest VO2.
- At least 480 consecutive observed seconds at ≥90% suggest threshold stimulus.
- Low-intensity inference requires ≥600 s recording span, ≥80% observed span
  coverage, mean ≤70% FTP and fewer than 5% of observations ≥90% FTP. Current
  approximate mean-power ranges distinguish Recovery/Easy/Z2. These are recording
  descriptions, not independently verified full-session physiological purposes.
- Race titles supply an inspectable hint only. A race-like title with hard power
  becomes **Hard (type uncertain)**; title without qualifying hard evidence remains
  **Uncertain**. A rider correction can establish the known type separately.
- Outdoor power remains excluded by accepted trust policy. Unsupported/ambiguous
  power and HR-only evidence remain uncertain for planning classification.

Future hard spacing assumes available classifications are confirmed; if the rider
corrects an ambiguous race, its actual date resets recovery and the rotation.
Unknown race/structured subtype is not silently called a confirmed race. Sparse
recording can hide effort; this feature needs those explicit uncertainty/correction
paths. The screens are not a new readiness or medical model.

## Date-pattern verification

Offsets below are anonymous scenario dates, with today = 0. Every intervening
recommendation is displayed. None recommends Rest/No ride.

| Initial history / state | Upcoming hard offsets | Behavior |
| --- | --- | --- |
| No recent hard, current sync | 0, 3, 7 | Threshold → Race → VO2; eight displayed dates |
| Race yesterday | 2, 6, 9 | Recovery today; Easy +1; structured first |
| VO2 yesterday | 2, 6, 9 | Recovery today; lower-power Easy +1; Race first |
| Race completed today | 3, 7, 10 | Today actual; three future hard dates; eleven dates |
| Easy completed today | 1, 4, 8 | Additional Easy today; future quality starts tomorrow |
| Heavy legs today | 1, 4, 8 | Recovery today; future hard conditional on normal legs |

Focused tests also challenge skipped suggested hard dates, extra actual races,
more than two actual hard dates in seven, mid-recovery starting dates, source
uncertainty, fresh/stale checkpoint boundaries, local midnight/year boundaries,
multiple timezones, correction/reset, intent before/after actual start,
noncycling exclusion, deterministic reload/restart and atomic migration failure.
Existing schema-upgrade expectations now end at schema 9; downgrade simulations
remove the new planning tables before reproducing historical upgrade boundaries.
Existing analytical assertions are retained.

## Private representative evidence

[Safe aggregate verification](behavior.json) comes from a disposable copy of the
accepted store. Detailed selected identities, titles and source references remain
under ignored local data; screenshots remain under ignored browser output.
Representative sources were selected by independent labels/Owner-known workout
context, not by sorting RideWorks stress.

- The known short-interval VO2 session is inferred as VO2 from **31 observed short
  bouts**, with a longest threshold-band run of 30 s. The result is supported by
  actual intervals rather than its modest mean HR or selected stress.
- The selected race-labeled sample has insufficient power-pattern evidence to
  establish a race. It remains uncertain. A **simulated manual correction in the
  disposable verification copy** exercises actual-race rotation, +1 recovery,
  +2 lower intensity and structured next. The correction is removed afterward;
  Dex has not claimed the rider confirmed that source classification.
- The independently labeled Z2 source is inferred as Z2 endurance. The chosen
  easy/recovery-labeled sample lacks qualifying trusted source evidence and remains
  uncertain; a title is not promoted to a completed easy ride.
- At the frozen private as-of, stale sync produces provisional Easy today and
  hard recommendations at offsets 1, 4, 8, with nine daily recommendations.
  This is available-history projection, conditional on sync/classification review.
  An extra skipped date changes the horizon without a fictitious completed hard
  day. An extra simulated actual race produces Recovery and eleven projected dates.

Training State and Performance are identical at the same clock before/after
planning operations. **All 21 preexisting tables are unchanged**, including the
existing stress cache. Independent artifact verification preserves **1,422
originals** and 20 non-cache source tables; SQLite integrity is `ok` and foreign-key
violations zero. Both approved FTP copies and the exact Elevate benchmark retain
their hashes. No API request, source import, raw-data commit or benchmark fitting.

## Browser and test evidence

The full Python suite and browser result are recorded with counts in
[checks.json](checks.json). Chromium checks cover Home/Plan recommendation type,
duration/power/reason parity; actual browser timezone selection; exact horizon;
heavy-feedback update/reset; explicit intent and no retrospective assignment;
Activity Review correction/reset and subsequent rotation; existing Activities,
Performance, Training State and Settings routes; keyboard form order; desktop and
320/390 px layouts with no horizontal overflow. Private screenshots were inspected.
The browser test operates only on the disposable copy and its simulated planning
records are cleared for the final review view.

## Reproduce

Use a disposable copy of the accepted private store and retain the baseline
unchanged. No private activity fixture needs to be added to Git.

```sh
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python tools/verify_planning.py \
  --data-dir local_data/p5-01/store \
  --baseline-dir local_data/p4-02-baseline/store \
  --as-of 2026-10-10T23:00:00+00:00 \
  --private-output local_data/p5-01/behavior-private.json \
  --aggregate-output reports/P5-01/behavior.json
.venv/bin/python -m rideworks --data-dir local_data/p5-01/store serve --port 8773
"$HOME/.codex/skills/playwright/scripts/playwright_cli.sh" -s=p501 open http://127.0.0.1:8773/plan
npx --yes --package @playwright/cli playwright-cli -s=p501 run-code \
  "$(cat tools/verify_planning_browser.js)"
```

The browser verifier assumes the representative store's latest known hard source
is the independently verified VO2 case, and begins without simulated feedback or
intent. It deliberately records a current-date intent and temporarily changes a
classification to exercise the flow. Clear those **planning-only test records**
in the disposable copy afterward. The Python verifier begins without simulated
intent/feedback and reports both private details and a distinct safe aggregate.
Never run a verification correction against the primary history store.

## Gate handoff

**Analyst Gate 1:** review classifier screens and empirical limitations,
conditional rotation/freshness/recovery semantics, event-based horizon, persistence
and intent honesty, browser evidence and preservation. PR stays draft.
**Owner Gate 2:** after Gate 1 release, demonstrate running Home, Plan and Activity
Review and obtain the Owner's usefulness/visual decision. No merge, task acceptance
or Phase 6 implementation has been inferred.
