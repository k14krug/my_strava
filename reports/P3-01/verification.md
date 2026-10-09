# P3-01 — Dashboard verification and YTD mileage investigation

## 2026-10-08 Recent Mileage consolidation — HARD — Owner

The [Owner-approved consolidation](https://github.com/k14krug/rideworks/pull/19#issuecomment-6071254155) is implemented at **`6d9160e8510caa5734f776ba785a5f1da64ae35e`**, following current Analyst JIT §8.3 (`473a173`) and Phase 3 contract (`18fb186`) on refreshed main `23ac11d`. Branch `task/p3-01-dashboard`, [PR #19](https://github.com/k14krug/rideworks/pull/19). P3-01 stays `in_progress` / `ready_for_review`; re-presented HARD — Owner, with Owner/Analyst task acceptance outstanding. No Phase 4/5/6 work.

Three top cards now show **Recent Mileage**, **Current 42-day best** and **Latest eligible 20-minute ride**. Recent Mileage contains **This Week** (actual Monday-through-today miles) and **Last 7 Days** (trailing seven-day actuals and neutral prior-seven-day comparison). Desktop values sit side by side with a divider; phone values stack with a horizontal divider. Annual goal information stays in Mileage Progress. No fourth metric or new calculation was added. Distance selection, calendar/goal calculations, chart semantics, Avg Pwr, targeted enrichment and Performance-v2 are unchanged.

**285 full tests / 24 focused dashboard tests pass.** The added regression uses distinct source-backed period values (2 mi this week, 7 mi last seven, 3 mi previous seven) to assert the combined card retains both values, places the neutral 4-mi comparison only under Last 7 Days and contains exactly three top cards.

Fresh live and disposable synthetic Chromium pass LA/Tokyo source/calendar checks, all twelve actual bars/required-line geometry, 48 live / 46 synthetic immediate tooltip lifecycle checks, recent source-power/links, search/sort/pagination and restart. New DOM/geometry checks assert both submetrics are inside Recent Mileage, exactly three summary cards, side-by-side desktop layout and stacked phone layout. Both 1,448-pixel desktop and 390-pixel phone screenshots were refreshed and inspected. Independent SQL/Decimal again reproduces fifteen mileage periods, twelve required points and current Performance references. The exact 2,200-mi goal tuple, all 1,422 artifact hashes and 1,441 v1 rows remain intact; integrity/FKs pass. Live verification makes **zero external API calls**; synthetic sync/failure/recovery uses fake HTTP only. No historical enrichment is repeated.

The enriched LA YTD remains **1,631.195462250 mi** (1,631.2 displayed), 120 contributors / zero distance unavailable; current actual week **26.3 mi**. This card consolidation does not revise the approximate-Strava residual conclusion below. Performance stays 1,028 eligible / zero pending.

Reproduction (private inputs replaced with placeholders; use fresh ignored disposable directories and open the managed Chromium session first):

```sh
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m unittest discover -s tests -p test_rideworks_dashboard.py
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --synthetic-dir '<fresh-disposable-store>' --session rideworks-p3-01 --output '<aggregate-output>'
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --data-dir '<accepted-store>' --baseline '<fresh-baseline>' --session rideworks-p3-01 --skip-sync --output '<aggregate-output>'
.venv/bin/python -m rideworks --data-dir '<accepted-store>' serve --port 8771
```

[Aggregate evidence](acceptance.json), [synthetic desktop](home-desktop-synthetic.png), [synthetic phone](home-phone-synthetic.png). Live screenshots remain private. [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings](http://127.0.0.1:8771/settings#annual-goal). Owner review requested for the consolidated card and desktop/phone readability, per current JIT §15. Explicit Owner approval precedes Analyst acceptance; no next task.

## Prior authorized enrichment evidence

## 2026-10-08 Authorized targeted summary enrichment — HARD — Owner

**Result:** all eight established GPX-backed outdoor Ride Activities now have current, allowlisted Strava API summary distance and elapsed duration. They add **181,830.3 metres = 112.984110296 mi**. LA YTD is **1,631.195462250 mi** (Home **1,631.2 mi**), with **120 contributors / zero distance-unavailable Activities**.

This correction follows the [Owner's explicit authorization](https://github.com/k14krug/my_strava/pull/19#issuecomment-6063242126) and Analyst JIT §8.2. `/TASK P3-01` was used under the JIT's missing-declaration `/TASK only` fallback. Clean branch checked, origin fetched unconditionally and task branch pulled; refreshed main `a2faa70` was merged, bringing in JIT `25b7d5e` and Phase 3 contract `8c2c284`. Only the STATUS merge conflict required resolution. Implementation: **`38183e31792ca1133d50a2f2b1bc8689c5f3414a`**. P3-01 remains `in_progress`; Owner and Analyst acceptance remain outstanding.

### Post-enrichment reconciliation

| LA YTD evidence | Before | After |
|---|---:|---:|
| Supported cycling Activities | 120 | 120 |
| Distance contributors | 112 | 120 |
| Distance unavailable | 8 | **0** |
| File contributors / miles | 104 / 1,415.637321791 | unchanged |
| API contributors / miles | 8 / 102.574030164 | **16 / 215.558140460** |
| Total miles | 1,518.211351955 | **1,631.195462250** |

All eight repaired Activities remain **Ride** (zero Virtual Ride). Each is still associated with its original GPX/export evidence and same RideWorks Activity/Strava identity. Each selected distance and elapsed duration exactly matches its current API summary; both selected-source contexts are **Strava API summary**. No new Activity was created. The private full reconciliation was regenerated for all 120 YTD Activities and the relevant boundary exclusion, retaining per-Activity identity/date/classification, selection and alternatives/provenance. The private target table also records both selected metrics and API evidence. No titles, IDs, original details, source paths or coordinates are published here.

The API summaries now supply absolute start instants where the GPX entries previously relied on supported export dates with unknown timezone. Independent LA calendar membership remains 120 Activities. Understood FIT/TCX distance still takes precedence; the four file/API overlaps and their summed **+0.12 m file-minus-API** difference are unchanged. API distance is used for these GPX rides because the files have no explicit understood session distance; no coordinates or raw samples were used to calculate mileage.

### Residual against the Owner's approximate Strava report

Using **1,631 mi as an approximate reference**, reference minus RideWorks is **−0.195462250 mi**: RideWorks is about 0.2 mi higher. The recomputed total rounds to **1,631 whole miles**, consistent with the Owner's report. The eight omitted Activities explain the material ~113-mile deficit; their API mileage is slightly larger than the gap estimated from a whole-mile reference. The known file-first effect is only **+0.000074565 mi**, leaving an API-comparable reference difference of approximately **−0.195387686 mi**.

There is **no remaining material shortfall against the approximate reference**. The remaining 0.195462250 mi is within its whole-mile rounding resolution. This establishes agreement at the reported precision, **not exact current Strava equality**: an exact Strava total/display rule and complete current Strava-side membership were not independently obtained. Do not promote the approximate reference into an oracle or claim a proved exact zero residual. Owner review remains required.

The stored **2026 / 2,200-mi goal and its updated timestamp are unchanged**. Current LA goal display: **74.1% complete, 568.8 mi remaining, 47.4 mi/week needed**. Current actual week remains **26.3 mi** in card/bar. Calendar-day-dependent seven-day/pace values use October 8 for this run; they need not equal the October 7 prior handoff.

### Bounded operation and implementation

The live run made **eight sequential `GET /activities/{id}` requests** for exactly the privately reconciled IDs, plus **one OAuth refresh POST**. **Zero activity-list, stream, segment, lap or other activity GETs**; no historical crawl, search, fuzzy association or new Activity creation. Existing `activity:read_all`, HTTPS endpoint restriction, 20-second timeout, no credential-forwarding redirects, response-size/JSON checks, rotating-token persistence and stop-on-rate/auth/error behavior were reused. Final read/overall rate usage was **8/100 and 8/200** for the short interval, **8/1,000 and 8/2,000** for the day.

- `ApiClient.activity_summary` adds only the numeric-ID detail endpoint to the GET allowlist, with separate request accounting.
- `repair-strava-summaries --targets <private-manifest>` is an explicit bounded maintenance command, independent of normal Sync now. The manifest maps at most eight established Strava IDs to existing GPX/export Ride Activities and is validated in full before HTTP begins.
- Responses pass through the existing `normalize` summary allowlist. Maps/coordinates, descriptions, social fields, segments, laps and photos from DetailedActivity are discarded; the full response is never persisted or logged.
- The existing observation transaction gains an established-target mode: it rechecks exact association and does not write the forward-sync checkpoint. Each successful response commits independently; later failures stop requests while retaining earlier successes. Missing distance retains the valid filtered observation, then stops explicitly. No value is manufactured.
- Successful source changes made Performance pending; the accepted atomic `converge_performance` path completed. **1,028 eligible / zero pending**; all repaired outdoor rides remain excluded under the unchanged outdoor Performance policy.

Official [Get Activity](https://developers.strava.com/docs/reference/#api-Activities-getActivityById) and [rate-limit documentation](https://developers.strava.com/docs/rate-limits/) were checked 2026-10-08. The new JIT explicitly authorizes the narrow direct-ID exception previously proposed as needing authorization.

### Verification

**284 full regression tests passed; eight focused repair tests passed** (the full suite includes all 23 existing dashboard tests). Focused coverage includes eight sequential requests; source/identity checks before any request; wrong athlete/ID/type/shape rejection; summary allowlisting; file/export preservation; zero-distance support; missing-distance stop; partial HTTP failure retaining earlier summaries; token rotation and exhausted-rate/401 handling; idempotence; unchanged checkpoint; and unchanged outdoor Performance eligibility.

A focused **normal future Sync now** regression imports a generated GPX-backed outdoor ride with an established export ID and no distance/duration. One normal recent list request supplies its API summary; existing association is enriched, both selected values use API provenance, Home adds one mile, and no direct historical or stream request occurs. This repair is not wired into normal sync.

Fresh live checks additionally passed:

- independent SQL/Decimal reproduces every selected target metric, source counts, added mileage and YTD; existing independent dashboard verification reproduces fifteen periods, twelve cumulative required points, goal calculations and Performance references;
- **17 native/export/goal/sync/stream tables** match the pre-enrichment snapshot, including a streaming fingerprint of all native records; all twelve prior API observations/current links remain unchanged and exactly eight new observations/links were added;
- **all 1,422 original/export artifact hashes and sizes**, source allowlist, integrity `ok`, zero FK violations; unchanged Activity count, original goal tuple and forward-sync checkpoint;
- an offline replay of the eight retained normalized API observations into a disposable copy produces **eight unchanged / zero new observations** and preserves the checkpoint. No second live fetch was performed;
- actual Chromium Home in LA/Tokyo, desktop/phone, 48 immediate tooltip lifecycle checks, current bar/card and line/needed agreement, search/sort/disjoint pagination, Performance links, Settings goal preservation and restart with identical dashboard data;
- all eight target Activities checked in the Activities browser and Activity Review at both widths (**16 reviews**): selected distance/duration API provenance, exact API metres/seconds and preserved GPX/export evidence; no overflow;
- the first browser attempt exposed a verifier assumption: the required-line point overlapped the center of the bar group's bounding box. The verifier now hovers the bar's own hit area away from the point. Fresh rerun passed; product chart behavior was not changed.

Fresh live browser verification used `--skip-sync` and made no further external requests. Prior synthetic goal/action/normal-sync/failure-recovery and Settings/OAuth evidence below remains historical; the full automated suite was freshly rerun. Live desktop/phone screenshots remain private and were visually inspected. The earlier 23-check mapping below is historical; updated contract checks 23–25 are supported by this section, with check 24 limited to the Owner's approximate reported precision. Check 26 remains true: Phase 4/5/6 are unimplemented.

### Reproduction and handoff

```sh
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m unittest discover -s tests -p test_rideworks_strava_summary_repair.py
.venv/bin/python -m rideworks --data-dir '<accepted-store>' repair-strava-summaries --targets '<private-eight-ID-manifest>'
.venv/bin/python '<private-post-enrichment-verifier>'
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --data-dir '<accepted-store>' --baseline '<fresh-private-baseline>' --session rideworks-p3-enrichment --skip-sync --output '<private-aggregate-output>'
```

The live repair command above was executed **once** for this authorization; it is not a request to repeat the eight GETs. Exact paths/commands, before/after snapshots, filtered private target results, full reconciliation, offline-idempotence evidence and live screenshots remain ignored/local.

**Re-present Gate 1 — HARD — Owner:** [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings goal](http://127.0.0.1:8771/settings#annual-goal). Review the restored eight distances/durations and **1,631.2-mi** Home total, and the residual limitation against the approximate Strava reference. No approval or PR merge; subsequent Analyst acceptance remains outstanding. No Phase 4/5/6 or next task.


## Prior investigation (before authorized enrichment)

## 2026-10-08 Owner-requested YTD mileage reconciliation — HARD — Owner

**Finding:** the eight distance-unavailable YTD Activities are **8 Ride / 0 Virtual Ride**. Every one is **GPX-file-backed with an associated Strava export row and an established Strava activity ID**. None is CSV-only; none has any retained API summary, superseded API observation, or API stream. Their originals contain no explicit distance field. This is a missing understood-distance-evidence case, not a demonstrated parsing, association, aggregation, or Performance-eligibility defect.

Investigation only, authorized by `/TASK P3-01` and the latest Owner PR comments. Clean task branch refreshed with `git fetch origin --prune` and fast-forward pull; JIT, controlling requirements/Phase 3 contract, recent PR comments and empty review-thread list read. Runtime remains `1cc01b6`; mileage selection, source data and JIT controls were not changed. No Strava API request, token refresh, enrichment, merge, approval or Phase 4/5/6 work occurred. Public documentation was read to assess the proposed request path.

### Activity-level coverage and selected totals

A private SQLite backup of the accepted review store was opened with `mode=ro` and `query_only=ON`. The private reconciliation contains one row per 2026 cycling Activity, plus the relevant year-boundary exclusion, with identity/title/date/type; LA YTD membership; selected metres/miles/source; file/API/export source case; all source identities and association provenance; current and superseded API evidence; CSV distance columns and their unspecified units; file session/lap distance evidence; original-file distance fields; signed file-minus-API delta; and explicit missing-distance reason. A private CSV provides the compact table; JSON and compressed raw-distance evidence preserve the detail. Private titles, IDs, original details and local paths are not included here or on the PR.

Fixed comparison: `2026-10-08T15:00:00+00:00`, `America/Los_Angeles`. The retained store reproduces the Owner's **1,518.2 mi** dashboard value. Mileage uses exact `1609.344` metres/mile and Decimal sums, independently checked against production presentation/aggregation.

| LA YTD selection | Activities | Miles |
|---|---:|---:|
| File distance | 104 | 1,415.637321791 |
| Current API distance | 8 | 102.574030164 |
| Distance unavailable | 8 | Unknown; excluded |
| Total supported cycling dates / contributors | 120 / 112 | **1,518.211351955** |

Classification is **109 Virtual Ride / 11 Ride**. File contributors are 103 Virtual Ride FIT sessions and one Ride TCX single lap; API contributors are six Virtual Ride and two Ride. All eight unavailable entries are Ride. No cycling Activity has an unsupported/missing date; the eight GPX-backed entries use supported export dates with unknown timezone, as the accepted policy requires.

Source associations across the 120: **108 file + export without API**, **4 file + export + API**, **8 API without files/export**. Zero CSV-only or other-source cases. Four file/API overlaps have API-minus-file differences of 0, −0.03, −0.04 and −0.05 metres. All three previously reported conflicts are in this YTD cohort.

### The eight unavailable Activities

The same findings hold for **each of the eight**, individually verified in the private table:

| Question | Result |
|---|---|
| Type | Ride; no Virtual Ride |
| Retained source type | GPX file + associated export row |
| Established Strava ID | Yes, distinct and unambiguously associated |
| Understood file summary distance | Absent |
| Other explicit distance in original GPX | Absent, including extensions |
| Retained current/historical API summary distance | None; no API observation at all |
| Retained API distance stream | None |
| CSV evidence | Both repeated Distance columns retained; units unspecified. Other original distance-related columns were inspected and preserved privately without assigning units. |
| Ignored known-unit distance | None found |
| Current YTD membership / mileage contribution | Included in dated Activity count / no distance contribution |
| Mileage recoverable from existing known-unit evidence | **0 mi evidenced**, not a claim that the ride had zero distance |

Thus recoverable known-unit mileage is zero for the GPX+export category; there are no unavailable CSV-only, API-associated, FIT, TCX or other-source Activities to recover. GPX coordinates could support a newly calculated distance, but that would require a calculation/policy decision, not recovery of an existing distance summary. No GPS distance was calculated and no CSV unit was inferred.

`xml_activity._gpx` intentionally does not manufacture a session distance/duration from points. `history.presentation` then correctly falls through to current API distance, which is absent here. All eight predate the initial recent-sync window; the forward-only `strava_api.sync_window` intentionally never visited them. No hidden API observation was lost through the presentation join, and no conflicting established Strava association was found. No parsing/association fix is proposed on this evidence.

### What explains the reported gap—and what remains unknown

- File-first precedence adds **0.12 m = 0.000074565 mi** compared with retained API values. Substituting the API values would *reduce* RideWorks to **1,518.211277390 mi**. It cannot explain a roughly 113-mile shortfall.
- Distance attributable to the eight unavailable Activities is **unknown**. Existing known-unit evidence measures none of it; their combined actual/Strava mileage must not be reported as zero or inferred from CSV values.
- Taking **1,631 mi only as the Owner's approximate reference**, the present gap is **112.788648045 mi**. After accounting for the known API-minus-file effect, **112.788722610 mi** remains unallocated between the eight missing distances and any other Strava-side membership/current-distance/display differences.
- If `M` is the eventual API mileage of those eight and their current API dates/types preserve YTD membership, unchanged RideWorks policy would yield `1518.211351955 + M` miles. The unexplained remainder against the approximate reference would be `112.788648045 − M`; separating the known file/API effect leaves `112.788722610 − M`.
- The year-boundary Activity responsible for the prior **5.101277291-mi** LA/Tokyo difference is separately documented privately; timezone choice does not establish the missing ~113 miles.

The cause of the eight omissions is established. **The full numerical Strava/RideWorks reconciliation is not established yet.** Retained current API distance covers only 12 YTD Activities (the four overlaps plus eight API-selected entries), not the whole year. Neither an exact current Strava YTD total nor complete current Strava membership is retained. This investigation therefore cannot assert that the eight missing distances exhaust the discrepancy or that Strava's displayed total is an oracle.

### Proposed bounded enrichment; not executed

Under the existing summary-list endpoint restriction, propose **at most eight sequential `GET /athlete/activities` requests**, one bounded date window per missing Activity, with `page=1`, `per_page=100`. Each CSV date has unknown timezone, so use a conservative three-UTC-day window surrounding that supplied date; do not assign that date a guessed offset. Retain only the eight allowlisted exact Strava IDs and discard unrelated returned summaries. Stop for review if a target is absent, the page is full, identity/account/type/date is unexpected, or distance is invalid/missing; do not paginate or widen into a historical crawl. No stream/detail/segment requests. At most **one additional OAuth refresh POST** if needed: maximum **8 activity GETs / 9 HTTP requests**, fewer on an early stop.

This uses the existing `activity:read_all` scope and documented list endpoint/metre-valued distance; existing rate-header checks and stop-on-429/auth/network behavior remain applicable. [Strava activity API reference](https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities), [SummaryActivity distance](https://developers.strava.com/docs/reference/#api-models-SummaryActivity), [rate limits](https://developers.strava.com/docs/rate-limits/), [authentication](https://developers.strava.com/docs/authentication/) checked 2026-10-08.

An exact-ID alternative is **eight `GET /activities/{id}` requests**, supported by Strava with the same scope, but it is **not currently allowed by RideWorks' client endpoint allowlist**, and P2-05 §4.2 restricts detail requests when summary fields suffice. It would need an explicit narrow Analyst-authored exception/implementation brief; the summary-window proposal above stays within that endpoint restriction. [Get Activity documentation](https://developers.strava.com/docs/reference/#api-Activities-getActivityById).

Either implementation would need a separately authorized bounded maintenance operation: validate the connected athlete and fixed IDs; attach observations to the eight existing Activities; preserve file/export provenance; leave the normal sync checkpoint unchanged (the existing `apply_observations` helper also writes that checkpoint and must not be reused naively); perform normal derived-state convergence as required; and rerun this reconciliation. No new mileage selection rule is needed. Expected effect, conditional on valid matching API responses: **8 → 0 unavailable and 112 → 120 contributors**, adding the returned metre distances converted to miles. The numeric increment is unknown until retrieval; exact agreement with ~1,631 is not promised.

### Verification and reproduction

Fresh investigation checks: independent SQL classification/date/distance selection agrees Activity-by-Activity with production; Decimal sums reproduce YTD and four overlap deltas; every relevant original file's hash/size verified; original FIT session distances agree with stored summaries; raw FIT distance fields and XML distance evidence inspected; preserved CSV bytes/hash and all distance-related headers inspected; established IDs checked across export/API associations; all API observations checked independently of current-source joins; integrity check `ok`, zero foreign-key violations. Fifteen live source/association/goal/sync tables still match the pre-investigation snapshot. Existing 276 full / 23 focused test results below belong to the preceding runtime change; they were not rerun for this read-only investigation.

The complete diagnostic script, database snapshot, exact invocation and machine-readable/private human-readable outputs remain local and ignored. Reproduction uses the private script with explicit paths, never the original data as an output:

```sh
.venv/bin/python '<private-reconciliation-script>' \
  --snapshot '<private-read-only-snapshot>' \
  --data-dir '<accepted-store>' \
  --output-dir '<private-output-directory>' \
  --as-of 2026-10-08T15:00:00+00:00
```

**Stop: Gate 1 — HARD — Owner.** Decision needed: authorize the bounded summary enrichment proposal, or request a different evidence source. P3-01 remains `in_progress`; handoff is `ready_for_review` with the numeric discrepancy unresolved. No approval or merge; subsequent Analyst acceptance remains outstanding.


## Prior dashboard implementation verification (2026-10-07)

The following records the preceding runtime change; it is not new test execution or Owner acceptance.

The latest 2026-10-07 [Owner correction in PR #19](https://github.com/k14krug/my_strava/pull/19#issuecomment-6048149785) is implemented and locally verified. **All mileage bars now show actual miles; the green line alone shows needed average/week.** This explicitly supersedes the earlier current-bar needed-pace decision. **Re-presented at Gate 1 — HARD — Owner**; P3-01 remains `in_progress` with handoff state `ready_for_review`. The first Home review was not approved. Owner approval and subsequent Analyst acceptance remain outstanding; Phase 4/5/6 work has not begun.

Invocation: `/TASK PR #19`. Clean checkout checked and origin fetched unconditionally; existing task branch pulled with fast-forward only, then updated main merged (the STATUS conflict was resolved to record correction work in progress). Refreshed main `e490bca`, Analyst JIT revision `3820120`, Phase 3 contract revision `38211d2`; controlling product requirements and AGENTS.md remain unchanged. The JIT still has no Allowed Invocation declaration, so the `/TASK only` fallback controls this run. No JIT controls were authored or changed by Dex.

Branch: `task/p3-01-dashboard`; prior Owner review `8101625`; corrected implementation commit `1cc01b645e745199b12b41bff7064e21540ab62b`. [Aggregate acceptance evidence](acceptance.json) includes all **23** checks in the updated Phase 3 contract §11.

## Owner corrections delivered

1. **This Week Miles** replaces the duplicate top YTD goal card. It shows actual cycling distance from local Monday through today. Annual actual/target/progress and calendar pace appear only in Mileage Progress.
2. Mileage Progress shows target, percentage, **miles remaining** and **Needed average: N.N mi/week**. Needed average is remaining target after today's retained mileage, multiplied by seven and divided by calendar days after today to January 1 next year. This is arithmetic goal progress, not training advice.
3. All twelve bars show actual miles. Eleven completed-week bars retain their actual totals; the blue outlined current bar shows actual Monday-through-today distance and agrees exactly with This Week Miles and the diagnostic payload. The green line alone uses cumulative actual YTD through each completed Sunday, and through today at its current endpoint. Its current endpoint agrees with displayed needed average. Bar tooltips show actuals; line-point tooltips show required weekly values. Needed pace is zero when the goal is met, while bars retain actual mileage; remaining miles with no time gives Unavailable needed pace. Points before the configured goal year are unavailable rather than borrowing a previous-year target.
4. Mileage bars/points use an immediate custom miles-only readout on pointer enter/move or keyboard focus. Leave/blur hides immediately; Escape dismisses. No mileage SVG `<title>` or title attributes remain. Tooltip position is bounded to the viewport; no timer, hover delay or client calculation is introduced.
5. Recent Activities adds **Avg Pwr**, selected from understood file session `avg_power`, then an understood single TCX lap when needed, then current API summary `average_watts`, otherwise Unavailable. Known zero is retained. CSV watts and raw sample averages are excluded; chosen source/context remain in the dashboard payload. Performance-v2 eligibility and best-20 calculation are unchanged.

Home `/`, Activities `/activities`, stable Activity Review URLs, old filtered-root redirects, Settings goal protections/persistence, accepted mileage distance/date semantics and existing sync/freshness behavior remain intact. No schema or new dependency change was needed for this correction.

**Owner review goal remains 2026 / 2,200 mi**, explicitly confirmed by “Keep 2,200 mi.” The complete live goal record, including updated time, was preserved. Temporary 1,234.50 / 5,678.25-mi goals were exercised only in disposable synthetic stores and cleared afterward. No default was seeded.

## Verification

**276 full automated tests and 23 focused dashboard/goal tests passed**. Focused tests cover cumulative required-week history/current-bar semantics, met-goal/year-end/leap/missing states, LA/Tokyo year edges, source-power precedence/currentness/zero/single-vs-multiple TCX laps, corrected annual-panel placement, and independent-oracle rejection of wrong required values/power. The existing actual FIT/API conflict test covers file summary watts against conflicting API watts and retains the metadata-only read check.

The current-bar tests now also reject substituting needed pace for actual mileage, retain actual mileage when a goal is met or unset, and assert all twelve bar kinds are actual. Historical actual bars and required-line calculations are unchanged.

The full suite also preserves prior goal protection, atomic migration/write rollback, export/source/history, Activity Review, Performance-v2, Strava sync/streams, failure/retry and restart coverage. JavaScript syntax and `git diff --check` pass.

Actual Chromium passed:

- fresh synthetic Home and Settings goal set/update/clear, no default, new/enriched sync, exception banner after failure/restart, later unchanged-sync recovery;
- live read-only Home in Los Angeles and Tokyo, annual goal preservation, search/sort/disjoint pagination/back state, recent links/Avg Pwr, Performance references and restart with identical actual/required period data;
- all completed/current bar actual values and SVG geometry, current-bar agreement with This Week Miles, required-line point values/geometry and endpoint agreement with displayed needed average;
- **48 immediate tooltip lifecycle checks per run** (12 bars + 12 required points at two widths), including enter/move/leave/focus/blur in the same JavaScript turn, actual pointer hover/leave on bar and point, real keyboard Tab/Escape, mileage-only content and viewport clipping checks;
- desktop 1,448-pixel and phone 390-pixel layouts with no overflow; live screenshots also inspected visually;
- Prior Settings/OAuth regression on `d09b957` (unchanged by this narrow bar correction): decline/reconnect, clean callback, disabled controls during sync, automatic convergence, near-expiry refresh, restart/idempotent rerun, failure/manual retry/later-sync recovery, disconnect retaining history and source integrity;
- Prior seven established live API Activity Reviews on `d09b957` (unchanged by this narrow bar correction): complete payload/source labels/offsets, charts/keyboard inspection, FIT precedence, local best-20/six-week context and Performance integration, LA/Tokyo, desktop/phone, restart/cache reuse with zero stream requests and no table changes.

### Independent calculation and provenance

`tools/verify_rideworks_dashboard.py` reads durable summaries directly via SQL, independently of production `history.presentation`. Decimal source sums reproduce **15 mileage periods** plus **12 cumulative YTD/required-week points**, current needed average, percentage/remaining/calendar pace and each recent average-power value/source/context to 0.000000001 tolerance. It scans accepted cached-v2 results separately for current/latest/prior-six-week references and **252 rolling Performance event times**. Production functions and displayed rounding are not their own oracle; a test deliberately corrupts required values and power and proves rejection.

Six controlled checks use LA/Tokyo at two UTC year-edge instants and a leap-year instant; unit tests also cover DST, missing/unknown-timezone dates, future evidence, goal met and year-end/no-time cases. Before January 1 of the current goal year there is no required-pace point for that target. Completed actual bars can still show preceding-year mileage; annual YTD excludes it.

| Current live result | Los Angeles | Tokyo |
|---|---:|---:|
| Actual this week | 26.302518293 mi | 44.086783186 mi |
| YTD miles | 1,518.211351955 | 1,523.312629245 |
| YTD file contributors / miles | 104 / 1,415.637321791 | 105 / 1,420.738599081 |
| YTD API contributors / miles | 8 / 102.574030164 | 8 / 102.574030164 |
| YTD supported cycling dates | 120 | 121 |
| YTD distance unavailable | 8 | 8 |
| Cycling date unavailable | 0 | 0 |
| Last seven miles | 87.497265967 | 87.497265967 |
| Previous seven miles | 101.354645122 | 101.354645122 |
| Needed average miles/week | 56.147300427 | 56.390614230 |

Differences follow browser-local day/year membership; source distance is unchanged. The browser instants fall on October 7 in LA and October 8 in Tokyo. The accepted review baseline already included one additional API-backed cycling Activity since the first handoff: 1,442 total Activities, 1,418 cycling (1,270 Virtual / 148 Ride), 24 noncycling and 101 supported cycling source dates with unknown timezone. No live external request or Activity mutation was performed by correction verification.

LA Owner presentation: **2,200-mi target; 69.0% complete; 681.8 mi remaining; 56.1 mi/week needed** over 85 calendar days after today. Actual this week is **26.3 mi** in both card and current blue bar; the green line endpoint independently remains **56.1 mi/week**. Linear calendar pace is 169.5 mi behind (280/365 elapsed days). Current 42-day best remains **195 W**; latest eligible is **160 W**, 35 W below its previous-six-week best. These statements are neutral source-based arithmetic, not training prescriptions.

### Originals, migration, sync and restart

The correction does not change schema 7. Verification repeats the disposable schema-6 migration replay: only the new goal table is removed/version reset on a database copy, then the real migration runs. All **19 preexisting table fingerprints** survive. This is replay evidence; the accepted live store was already schema 7 at explicit baseline capture and was never downgraded.

Live verification preserves native/export tables, every prior Activity/API/stream observation, **1,441 v1 rows**, the goal tuple and all **1,422 original/export artifact SHA-256/size checks**. Integrity and foreign-key checks pass. Current Performance has **1,028 eligible / zero pending**; the increase from the first handoff follows the already-present newly synced ride under unchanged v2 policy. Originals were never altered; no tokens were copied into replay stores.

Latest current-bar live verification is **read-only**, with zero external API calls. The preceding correction and its rerun were also read-only. Earlier first-presentation evidence retained in `acceptance.json` records one real bounded metadata sync: three unchanged Activities, zero new observations, three cached streams reused, zero stream GETs and automatic current Performance without another action. Fresh synthetic sync now separately verifies new/enriched Home data, failure persistence and recovery on the corrected implementation. No new real sync was needed to verify this presentation-only correction.

## Updated Phase 3 checklist

All **23 implementation/verification checks** in the updated contract §11 pass. Owner/Analyst acceptance remains separate.

| # | Check | Evidence |
|---|---|---|
| 1–3 | Routes, goal edits, no default | live/synthetic Chromium and storage/action tests |
| 4–7 | Cycling and distance source precedence | independent SQL; FIT/API overlap; API-only and CSV-only fixtures |
| 8–10 | Independent mileage and calendar/leap | fifteen periods, both browser zones, controlled edges and unit tests |
| 11 | Goal math including current needed/week | independent Decimal calculation |
| 12 | Required line and current actual bar | twelve actual bars and required points; SVG geometry; current bar/card agreement |
| 13 | Immediate miles-only tooltip | forty-eight lifecycle checks per run; correct actual-bar/required-line tooltip values; pointer/keyboard at both widths |
| 14 | Recent evidence and Avg Pwr | six independent value/source/context checks; source precedence fixtures |
| 15–17 | Cards/chart/neutral context | Performance page and separate result/event/prior-window scan |
| 18–19 | Sync and Home failure state | prior real sync; fresh synthetic new/enriched/failure/restart/recovery |
| 20–21 | Restart and usable layouts | unchanged goal/period/required values; desktop/phone Chromium |
| 22 | Full regression | 276 full / 23 focused rerun; preceding Settings/OAuth and seven live Activity Reviews retained |
| 23 | Deferred scope absent | diff inspection and deferred-metric exclusion test |

## Reproduction and review artifacts

Commands used below replace private inputs with placeholders. Each UI run uses a fresh ignored disposable store/baseline. Open the managed Chromium sessions first. Live `--skip-sync` makes no external API calls; omission performs a real bounded Settings sync. Existing live goal records are preserved; synthetic temporary targets are cleared. Run assertions enabled.

```sh
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m unittest discover -s tests -p test_rideworks_dashboard.py
node --check rideworks/static/home.js
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --synthetic-dir '<fresh-disposable-store>' --session rideworks-p3-01 --output '<aggregate-output>'
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --data-dir '<accepted-store>' --baseline '<fresh-baseline>' --session rideworks-p3-01 --skip-sync --output '<aggregate-output>'
.venv/bin/python tools/verify_rideworks_dashboard.py --data-dir '<accepted-store>' --tz America/Los_Angeles
.venv/bin/python tools/verify_rideworks_strava_stream_ui.py --data-dir '<accepted-store>' --links '<local-review-links>' --session rideworks-p3-01 --live
.venv/bin/python tools/verify_rideworks_strava_settings_ui.py --synthetic-dir '<fresh-settings-disposable-store>' --session rideworks-p3-settings
.venv/bin/python -m rideworks --data-dir '<accepted-store>' serve --port 8771
```

[Aggregate evidence](acceptance.json), [synthetic desktop](home-desktop-synthetic.png), [synthetic phone](home-phone-synthetic.png). Committed images contain generated Activities and a temporary synthetic goal; live screenshots stay private. Private titles/IDs/raw streams/credentials/databases/local paths are not published in evidence.

Owner review app restarted with the corrected runtime: [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings goal](http://127.0.0.1:8771/settings#annual-goal). Review actual mileage in all bars (current bar matches This Week Miles), the separate needed-average line and their respective immediate tooltips on desktop/phone. **Stop at HARD — Owner** under JIT §15. Explicit Owner approval precedes Gate 2 — HARD — Analyst. No Phase 4/5/6 implementation or next task.


## Owner approval and Analyst handoff

On **2026-10-08**, the Owner explicitly approved the final P3-01 / Phase 3
dashboard, including the consolidated Recent Mileage card, annual-goal
presentation, reconciled YTD mileage and bounded GPX/Strava summary repair.

P3-01 remains `in_progress` pending HARD — Analyst review.
Phase 4/5/6 remain unstarted.
