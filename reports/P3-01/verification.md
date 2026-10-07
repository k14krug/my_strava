# P3-01 — Corrected Home dashboard and annual mileage goal

The 2026-10-07 [Owner correction in PR #19](https://github.com/k14krug/my_strava/pull/19#issuecomment-6047219191) is implemented and locally verified. **Re-presented at Gate 1 — HARD — Owner**; P3-01 remains `in_progress` with handoff state `ready_for_review`. The first Home review was not approved. Owner approval and subsequent Analyst acceptance remain outstanding; Phase 4/5/6 work has not begun.

Invocation: `/TASK PR #19`. Clean checkout checked and origin fetched unconditionally; existing task branch pulled with fast-forward only, then updated main merged (the STATUS conflict was resolved to record correction work in progress). Refreshed main `d18ce97`, Analyst JIT revision `dc26463`, Phase 3 contract revision `5340e47`; controlling product requirements and AGENTS.md remain unchanged. The JIT still has no Allowed Invocation declaration, so the `/TASK only` fallback controls this run. No JIT controls were authored or changed by Dex.

Branch: `task/p3-01-dashboard`; prior Owner review `2648db8`; corrected implementation commit `d09b957957511b66ecf1c780352fea3684092bef`. [Aggregate acceptance evidence](acceptance.json) includes all **23** checks in the updated Phase 3 contract §11.

## Owner corrections delivered

1. **This Week Miles** replaces the duplicate top YTD goal card. It shows actual cycling distance from local Monday through today. Annual actual/target/progress and calendar pace appear only in Mileage Progress.
2. Mileage Progress shows target, percentage, **miles remaining** and **Needed average: N.N mi/week**. Needed average is remaining target after today's retained mileage, multiplied by seven and divided by calendar days after today to January 1 next year. This is arithmetic goal progress, not training advice.
3. Eleven completed-week bars retain actual miles. The distinct green outlined current bar shows needed weekly average; the green line uses cumulative actual YTD through each completed Sunday, and through today at its current endpoint. Current bar, line endpoint and displayed needed average agree. Actual current-week distance stays in its top card and diagnostic payload. Goal met gives zero; remaining miles with no time gives Unavailable. Points before the configured goal year are unavailable rather than borrowing a previous-year target.
4. Mileage bars/points use an immediate custom miles-only readout on pointer enter/move or keyboard focus. Leave/blur hides immediately; Escape dismisses. No mileage SVG `<title>` or title attributes remain. Tooltip position is bounded to the viewport; no timer, hover delay or client calculation is introduced.
5. Recent Activities adds **Avg Pwr**, selected from understood file session `avg_power`, then an understood single TCX lap when needed, then current API summary `average_watts`, otherwise Unavailable. Known zero is retained. CSV watts and raw sample averages are excluded; chosen source/context remain in the dashboard payload. Performance-v2 eligibility and best-20 calculation are unchanged.

Home `/`, Activities `/activities`, stable Activity Review URLs, old filtered-root redirects, Settings goal protections/persistence, accepted mileage distance/date semantics and existing sync/freshness behavior remain intact. No schema or new dependency change was needed for this correction.

**Owner review goal remains 2026 / 2,200 mi**, explicitly confirmed by “Keep 2,200 mi.” The complete live goal record, including updated time, was preserved. Temporary 1,234.50 / 5,678.25-mi goals were exercised only in disposable synthetic stores and cleared afterward. No default was seeded.

## Verification

**276 full automated tests and 23 focused dashboard/goal tests passed**. Seven additional meaningful tests cover cumulative required-week history/current-bar semantics, met-goal/year-end/leap/missing states, LA/Tokyo year edges, source-power precedence/currentness/zero/single-vs-multiple TCX laps, corrected annual-panel placement, and independent-oracle rejection of wrong required values/power. The existing actual FIT/API conflict test now covers file summary watts against conflicting API watts and retains the metadata-only read check.

The full suite also preserves prior goal protection, atomic migration/write rollback, export/source/history, Activity Review, Performance-v2, Strava sync/streams, failure/retry and restart coverage. JavaScript syntax and `git diff --check` pass.

Actual Chromium passed:

- fresh synthetic Home and Settings goal set/update/clear, no default, new/enriched sync, exception banner after failure/restart, later unchanged-sync recovery;
- live read-only Home in Los Angeles and Tokyo, annual goal preservation, search/sort/disjoint pagination/back state, recent links/Avg Pwr, Performance references and restart with identical actual/required period data;
- completed/current bar values, required-point values and SVG geometry, with the current bar and line endpoint aligned to the same needed-average value;
- **48 immediate tooltip lifecycle checks per run** (12 bars + 12 required points at two widths), including enter/move/leave/focus/blur in the same JavaScript turn, actual pointer hover/leave on bar and point, real keyboard Tab/Escape, mileage-only content and viewport clipping checks;
- desktop 1,448-pixel and phone 390-pixel layouts with no overflow; live screenshots also inspected visually;
- Settings/OAuth regression: decline/reconnect, clean callback, disabled controls during sync, automatic convergence, near-expiry refresh, restart/idempotent rerun, failure/manual retry/later-sync recovery, disconnect retaining history and source integrity;
- seven established live API Activity Reviews: complete payload/source labels/offsets, charts/keyboard inspection, FIT precedence, local best-20/six-week context and Performance integration, LA/Tokyo, desktop/phone, restart/cache reuse with zero stream requests and no table changes.

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

LA Owner presentation: **2,200-mi target; 69.0% complete; 681.8 mi remaining; 56.1 mi/week needed** over 85 calendar days after today. Actual this week is **26.3 mi**, independent of the needed current chart bar. Linear calendar pace is 169.5 mi behind (280/365 elapsed days). Current 42-day best remains **195 W**; latest eligible is **160 W**, 35 W below its previous-six-week best. These statements are neutral source-based arithmetic, not training prescriptions.

### Originals, migration, sync and restart

The correction does not change schema 7. Verification repeats the disposable schema-6 migration replay: only the new goal table is removed/version reset on a database copy, then the real migration runs. All **19 preexisting table fingerprints** survive. This is replay evidence; the accepted live store was already schema 7 at explicit baseline capture and was never downgraded.

Live verification preserves native/export tables, every prior Activity/API/stream observation, **1,441 v1 rows**, the goal tuple and all **1,422 original/export artifact SHA-256/size checks**. Integrity and foreign-key checks pass. Current Performance has **1,028 eligible / zero pending**; the increase from the first handoff follows the already-present newly synced ride under unchanged v2 policy. Originals were never altered; no tokens were copied into replay stores.

Correction live verification and its rerun are **read-only**, with zero external API calls. Earlier first-presentation evidence retained in `acceptance.json` records one real bounded metadata sync: three unchanged Activities, zero new observations, three cached streams reused, zero stream GETs and automatic current Performance without another action. Fresh synthetic sync now separately verifies new/enriched Home data, failure persistence and recovery on the corrected implementation. No new real sync was needed to verify this presentation-only correction.

## Updated Phase 3 checklist

All **23 implementation/verification checks** in the updated contract §11 pass. Owner/Analyst acceptance remains separate.

| # | Check | Evidence |
|---|---|---|
| 1–3 | Routes, goal edits, no default | live/synthetic Chromium and storage/action tests |
| 4–7 | Cycling and distance source precedence | independent SQL; FIT/API overlap; API-only and CSV-only fixtures |
| 8–10 | Independent mileage and calendar/leap | fifteen periods, both browser zones, controlled edges and unit tests |
| 11 | Goal math including current needed/week | independent Decimal calculation |
| 12 | Required history and current needed bar | twelve cumulative points; SVG values/geometry; actual current week retained |
| 13 | Immediate miles-only tooltip | forty-eight lifecycle checks per run; actual pointer/keyboard at both widths |
| 14 | Recent evidence and Avg Pwr | six independent value/source/context checks; source precedence fixtures |
| 15–17 | Cards/chart/neutral context | Performance page and separate result/event/prior-window scan |
| 18–19 | Sync and Home failure state | prior real sync; fresh synthetic new/enriched/failure/restart/recovery |
| 20–21 | Restart and usable layouts | unchanged goal/period/required values; desktop/phone Chromium |
| 22 | Full regression | 276 full / 23 focused; Settings/OAuth and seven live Activity Reviews |
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

Owner review app restarted with the corrected runtime: [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings goal](http://127.0.0.1:8771/settings#annual-goal). Review the corrected cards, annual progress/needed average, chart semantics/tooltips and recent Avg Pwr on desktop/phone. **Stop at HARD — Owner** under JIT §15. Explicit Owner approval precedes Gate 2 — HARD — Analyst. No Phase 4/5/6 implementation or next task.
