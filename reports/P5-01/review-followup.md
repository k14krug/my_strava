# P5-01 — Completed ride, next ride and Plan v2 correction

**JIT §10 corrections implemented for HARD — Analyst Gate 1 review.**
Existing [draft PR #26](https://github.com/k14krug/rideworks/pull/26) remains
unaccepted; Owner Gate 2 and merge remain pending. This report supersedes the
initial [v1 verification](verification.md) wherever next-ride selection, visual
layout or weekly frequency policy differs.

## Actual Owner case: before and after

The verifier uses a disposable copy of the **updated, already-synced local history**,
including the October 10 Recovery activity. No new API request or import was run
by this correction. The accepted primary source store stays untouched.

| Case | Previous implementation | Corrected behavior |
| --- | --- | --- |
| Recovery already recorded today | Primary Next Ride was an optional Easy spin today | Home, Plan and current Activity Review agree on **tomorrow Race**; today's Recovery is separate completed context |
| Two synced no-ride dates after the known VO2 session | An uncertain older race could suppress today's opportunity | Before today's ride, **today Race** is a conditional quality option; old race uncertainty remains one visible exception |
| Prior race confirmed, before today's ride | Rigid two-in-seven veto selected Z2 | **Race remains an available quality option**, explicitly labeled the third hard date in seven after two supported recovery dates |
| Heavy legs with today's Recovery already logged | Feedback affected today's secondary spin | The **next prospective ride** becomes Recovery; quality is postponed |
| Historic Activity Review | Workout context and Plan link only | **Current next ride** uses the live plan, with no claim it was the recommendation immediately after that historical ride |

The known last hard session is the independently identified October 7 VO2 workout.
October 8/9 are no-record dates covered by the successful sync: **assumed rest for
planning**, never invented activities. October 10's approximately 40-minute,
94-W recovery is actual evidence. The corrected plan displays nine calendar dates
including completed today, with upcoming hard recommendations at offsets **1, 4,
8**. All future dates remain conditional.

The before-ride challenge filters today's completed activity out of the same real
history in memory and explicitly assumes current sync. It is a counterfactual
planning check, not a claim that RideWorks captured a recommendation before the
actual ride. The prior planner is loaded from commit `9ac386d` for the behavioral
comparison. Private details and old/new state remain ignored; the public
[aggregate](review-followup.json) contains no ride names, identities or streams.

## Frequency and classification

`rolling-advisor-v2` treats two hard sessions in seven dates as a **preference**.
The immediate next quality opportunity can exceed it after two supported recovery
dates, current sync, no conflicting unclassified recovery effort and no heavy-leg
report. A third-in-seven recommendation explicitly names the exception. Existing actual
excess is not escalated to a fourth hard recommendation. The
remaining projected rotation favors two in seven, so three-hard weeks are not the
new default. Missing today is not assumed rest; a completed but unclassified
current-day ride cannot establish recovery for this exception.

An uncertain race **before** the latest known hard session remains relevant to the
weekly count and receives a quick confirmation control. It does not invent a new
recovery timer or erase independently supported later recovery dates. Uncertain
training **after** the last known hard session still makes current-day quality
provisional/easier. This is an explicit source-aware distinction, not an inferred
medical readiness score.

`observed-stimulus-v2` evaluates already-retained, uniquely current ride metadata.
Explicit `workout_type=11` can establish **source-reported Race**, separately from
rider-confirmed or power-inferred stimulus. Strava's current documentation exposes
this field; its official v3 enumeration identifies 11 as ride race.
[Current reference](https://developers.strava.com/docs/reference/#api-models-SummaryActivity),
[official v3 enumeration](https://strava.github.io/api/v3/activities/).
A title alone does not fill absent metadata. The actual October 4 source has no
retained race subtype and remains uncertain until confirmed. **Confirm this was a
race** is directly available in the context area; its action immediately reloads
the shared planner. Original observations and accepted power trust rules stay intact.

## Visual implementation

The [Analyst HTML reference](../../docs/mockups/plan-rotation-v2.html) was opened
in local Chromium through a loopback static server, and compared with actual
1440px desktop and 320/390px phone screenshots. Plan v2 retains RideWorks colors
and navigation, with:

- Separate completed-today and next-ride headline cards; before riding, today's
  recommendation leads instead.
- Three prominent hard milestones linked to the corresponding chronological
  hard cards, with dates taken directly from the shared planner.
- A compact, complete rotation: emphasized hard cards and grouped low-intensity
  rows, each retaining its individual date, category, duration and approximate watts.
- One **Why this plan?** context area for frequency, sync, recovery and leg feedback.
  No generic provisional sentence repeated in each daily row. Exact method and
  source details remain below the rotation in disclosure sections.
- A prominent Activity Review next-ride panel before the chart, with the same
  live calculation and explicit historical-review label. Pre-ride intent stays
  distinct from the current recommendation.

Private actual screenshots remain ignored locally. The following **source-neutral
synthetic captures** show the production UI for durable visual review; they are
labeled illustrations and contain no personal activity records:

[Desktop completed-today view](plan-v2-synthetic-desktop.png),
[mobile full rotation](plan-v2-synthetic-mobile.png),
[before-ride third-in-seven example](plan-v2-synthetic-before.png).

## Verification and preservation

Exact counts and results: [follow-up checks](review-followup-checks.json).

- **412 full Python tests**, including **29 focused planning tests**, pass.
  New regressions cover revisit after a new sync, shared Home/Plan/Review next date,
  actual hard/easy completion, before-ride eligibility, uncertain/confirmed race,
  third-in-seven exception, supported versus unclassified recovery, heavy legs,
  stale sync, midnight/timezones, explicit metadata and intent preservation.
- **144 actual-case Chromium assertions** pass, including exact three-page
  date/type/target/reason agreement; completed-today separation; three milestone
  dates matching all chronological hard cards; compact low-day grouping; quick
  race confirmation/reset; heavy feedback/reset; historical-review labeling;
  keyboard form and milestone navigation; desktop/320/390px overflow; existing
  Activities, Performance, Training State and Settings; deterministic reload.
- **12 additional before-ride browser assertions** and **5 stale-sync assertions**
  pass on synthetic previews. They exercise today's quality option, Home/Plan
  agreement, explicit intent, conditional third-in-seven explanation, and one
  stale warning without calling unsynced prior dates rest.
- The same-clock full Training State and Performance outputs match the baseline
  exactly. **20 source tables and 1,422 original artifacts** are independently
  preserved. Replaceable stress/classification caches are allowed to populate;
  model formulas, power/HR eligibility and original measurements are unchanged.
  SQLite integrity is `ok`, with zero foreign-key violations.
- Approved FTP copies and the exact Elevate benchmark retain their hashes. Full
  existing sync tests pass; no change to Strava access, OAuth, normalization or
  synchronization strategy. No credentials, activity streams, private screenshots
  or databases are committed.

The actual-case verifier compares source tables/originals against a fresh copy of
the Owner's updated source history, rather than against the older pre-sync store.
This preserves the legitimately new activity without misreporting it as a planner
mutation. Browser test corrections and feedback are applied only to the disposable
copy and cleared before the final handoff.

## Reproduce

Create isolated copies of the already-synced accepted store, preserving originals
and copying SQLite consistently. Keep the primary store unchanged. Then:

```sh
.venv/bin/python -m unittest discover -s tests -q
git show 9ac386d:rideworks/planning.py > local_data/p5-01-v2/prior-planning.py
.venv/bin/python tools/verify_planning_v2.py \
  --data-dir local_data/p5-01-v2/store \
  --baseline-dir local_data/p5-01-v2/baseline \
  --prior-planner local_data/p5-01-v2/prior-planning.py \
  --as-of 2026-10-11T00:10:00+00:00 \
  --private-output local_data/p5-01-v2/behavior-private.json \
  --aggregate-output reports/P5-01/review-followup.json
.venv/bin/python -m rideworks --data-dir local_data/p5-01-v2/store serve --port 8775
"$HOME/.codex/skills/playwright/scripts/playwright_cli.sh" -s=p501v2 open http://127.0.0.1:8775/plan
npx --yes --package @playwright/cli playwright-cli -s=p501v2 run-code \
  "$(cat tools/verify_planning_v2_browser.js)"
```

The actual-case browser verifier expects the October 10 post-sync case and clean
test feedback. Synthetic-only before-ride/visual fixtures require a **new empty**
data directory; they deliberately refuse an existing database:

```sh
.venv/bin/python tools/preview_planning_v2.py \
  --data-dir local_data/p5-01-v2/synthetic-store
.venv/bin/python tools/preview_planning_v2.py \
  --data-dir local_data/p5-01-v2/synthetic-before-store --before-ride
.venv/bin/python -m rideworks --data-dir local_data/p5-01-v2/synthetic-before-store serve --port 8777
"$HOME/.codex/skills/playwright/scripts/playwright_cli.sh" -s=p501before open http://127.0.0.1:8777/plan
npx --yes --package @playwright/cli playwright-cli -s=p501before run-code \
  "$(cat tools/verify_planning_v2_preview_browser.js)"
```

Synthetic previews use the current local day. For the stale-only check, move **the
synthetic checkpoint only** back two dates, reload, and assert `fresh=false`, an
Easy primary suggestion, one context status warning, zero repeated daily warnings,
and no assumed-rest claim for the uncovered prior date. Private screenshot capture
paths and detailed evidence remain in ignored local data/browser output.

## Return gate

Review is needed for the implemented JIT §10 behavior, the explicit soft-guideline
exception, evidence-qualified race correction and actual/synthetic visual results.
**Stop at HARD — Analyst Gate 1.** Owner Gate 2 is still pending; no Phase 5
acceptance, merge or Phase 6 work has been inferred.
