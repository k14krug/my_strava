# P3-01 — Home dashboard and annual cycling mileage goal

Implementation and required local verification are complete. **Stopped at Gate 1 — HARD — Owner** under `docs/tasks/P3-01.md §15`; P3-01 remains `in_progress`, handoff state `ready_for_review`. Owner approval and subsequent Analyst acceptance remain outstanding. Phase 4/5/6 work has not begun.

Invocation: `/TASK P3-01`. The Analyst JIT has no Allowed Invocation declaration, so AGENTS.md's `/TASK only` fallback controls this run. Controlling sources: `docs/tasks/P3-01.md`, `docs/PHASE_3_ACCEPTANCE.md`, `docs/PRODUCT_REQUIREMENTS.md`; accepted STRAVA-004 Performance-v2 behavior is retained.

Base main: `b56ff3baa065f71b8426c40a189b4f8ee3f98ae8`. Implementation commit: `d975a70b92a2d6272011f697785d77755fad415b`. Branch: `task/p3-01-dashboard`; [draft PR #19](https://github.com/k14krug/my_strava/pull/19).

## Delivered behavior

Home is `/`; the existing Activities browser is `/activities`, with stable `/activities/<id>` reviews. Brand/navigation, filter forms, pagination and internal links use the new routes. Old root filter bookmarks redirect with their query preserved. Home uses bounded `home_tz` while Activities/Settings use `tz`: this keeps legacy root `tz` bookmarks working and establishes the actual browser timezone before dashboard aggregation.

Home shows YTD goal progress, last-seven-day comparison, current 42-day best, latest eligible best-20, six recent cycling Activities, twelve Monday–Sunday mileage buckets, a genuine rolling 42-day Performance snapshot with gaps, and neutral reproducible context. Mileage is recomputed from accepted `history.presentation` summaries; raw samples are not read for mileage. Understood file distance wins, current API distance supplies the fallback, unspecified CSV units remain unavailable, and known zero is valid. Outdoor distance contributes independently of Performance power eligibility.

Schema 7 adds only year, rider-entered target miles and UTC updated time. Settings uses existing POST/nonce/origin protections; strict positive finite input is bounded at 100,000 mi. Goals persist across restart, can be changed/cleared, and remain separate by year. No default target or generic goal engine is introduced.

**Owner review goal: 2026 / 2,200 mi.** The accepted store already contained this target at explicit verification baseline capture. The Owner subsequently confirmed “Keep 2,200 mi.” Live verification preserved its complete record, including updated time. Set/update/clear exercises used disposable synthetic stores with documented temporary targets 1,234.50 and 5,678.25 mi; both were cleared afterward.

## Verification results

- **269 full automated tests passed** (`unittest discover -s tests`); **16 focused dashboard/goal tests passed**. Coverage includes calendar/year/DST/leap boundaries, missing/zero evidence, actual FIT/API overlap, strict goal validation and action protections, restart, schema-6 atomic migration failure/recovery, incomplete preceding migration, and goal-write rollback.
- Actual Chromium passed live Home/Settings/Activities/Performance checks in Los Angeles and Tokyo, desktop and 390-pixel phone layouts, search/sort/disjoint pagination/back state, recent links, card references, goal persistence and restart. A read-only live rerun passed with zero external API calls.
- Disposable synthetic Chromium passed new/enriched sync, explicit set/update/clear/no-default states, file/API conflict, excluded CSV-only distance and Run, failure banner persistence on Home after restart, and later unchanged-sync recovery. Prior Performance rows and committed sync/source evidence survived injected rebuild failure.
- Existing Settings/OAuth Chromium regression passed decline/reconnect, clean callback URL, configured/connected states, disabled controls during sync, automatic convergence, near-expiry token refresh, restart/idempotent rerun, failure/manual retry/later-sync recovery, disconnect retaining history, local dates and desktop/phone controls. The verifier now waits for the final browser-timezone Settings navigation before interacting.
- All **seven live API Activity Reviews** passed complete payload, source/provenance, charts, keyboard inspection, local best-20 and six-week context, FIT precedence, Performance-page integration, Los Angeles/Tokyo, phone/desktop and restart/cache checks. Restart required zero stream requests, reused seven caches, changed no persisted tables and retained **1,027 eligible / zero pending** Performance results.
- `git diff --check` passed. No policy/method, dependency/framework, authentication, background sync, CI or JIT changes were made.

### Independent aggregate checks

`tools/verify_rideworks_dashboard.py` scans durable file sessions, single-lap TCX summaries, current API summaries, CSV date/classification evidence and cached Performance-v2 result rows directly. It does not call production `history.presentation` as its oracle. Decimal sums independently reproduce each of **15 periods** (YTD, last seven, prior seven and twelve weekly buckets), contribution counts/miles and goal math to within 0.000000001. Presentation rounding is not used as the oracle.

Browser-captured dashboard payloads pass in both timezones. Six additional controlled checks use each zone at UTC year-edge instants and a leap-year instant. Absolute dates convert to the browser zone; supported unknown-timezone source dates keep their supplied calendar date. Missing dates and future evidence are counted/excluded.

| Live browser result | Los Angeles | Tokyo |
|---|---:|---:|
| YTD miles | 1,504.764009435 | 1,509.865286726 |
| YTD file contributors | 104 | 105 |
| YTD file miles | 1,415.637321791 | 1,420.738599081 |
| YTD API contributors | 7 | 7 |
| YTD API miles | 89.126687644 | 89.126687644 |
| YTD supported cycling dates | 119 | 120 |
| YTD distance unavailable | 8 | 8 |
| Cycling date unavailable | 0 | 0 |
| Last seven miles | 74.049923447 | 74.049923447 |
| Previous seven miles | 101.354645122 | 101.354645122 |

The YTD difference follows browser-local year membership; it is not an alternative distance calculation. The verification instants also fall on different current local dates (October 7 / October 8). Across the accepted history there are 1,417 cycling Activities (1,269 Virtual Ride / 148 Ride), 24 excluded noncycling Activities and 101 supported cycling source dates with unknown timezone. Three live file/API distance alternatives disagree; the accepted file-first boundary remains deterministic.

For the Owner's Los Angeles review: 2,200-mi target, **68.4% complete**, **695.2 mi remaining**, **182.9 mi behind linear calendar pace** (280/365 local days); last seven is **27.3 mi less** than the preceding seven. Current 42-day best is **195 W**; latest eligible is **120 W**, **75 W below** its accepted previous-six-week best. These are neutral arithmetic statements, not training prescriptions.

Current/latest references and every rolling arrival/expiry/reference event reproduce from accepted cached-v2 results by a separate scan: **252 current live event times**, plus 260/206 event times in the controlled year/leap cases. Best-20 calculation and eligibility policy are unchanged.

### Migration, originals and sync

The live store had already reached schema 7 before the explicit verification snapshot. Accordingly, migration evidence is a **disposable schema-6 replay**, not a claim that an original live schema-6 baseline was captured. Verification backed up the accepted database, removed only the new goal table and reset schema version on the disposable copy, then ran the real additive migration. All **19 preexisting table fingerprints** survived unchanged. The original accepted store was never downgraded.

The live checks retained all prior Activity/API/stream observations, native/export tables, **1,441 historical v1 rows**, and verified SHA-256/size for **1,422 retained original/export artifacts**. Integrity and foreign-key checks passed. No credentials were copied to the migration replay. Raw archives, databases, tokens, private titles/IDs, raw streams and private screenshots remain local-only.

One real bounded Settings **Sync now** requested one metadata page, observed three unchanged Activities, added zero Activities/observations, reused three stream caches, made **zero stream GETs**, and retained current Performance (1,027 eligible / zero pending). Home reflected the retained successful-sync state on reload without a second action. Observed rate headers were application limit 200/2,000 with usage 1/1 and read limit 100/1,000 with usage 1/1; these are observations, not policy assumptions. The later read-only verification rerun made zero external API calls. Synthetic fake-HTTP sync separately demonstrates actual new/enriched Home data and failure/retry convergence.

## Phase 3 contract checklist

All 21 implementation/verification checks in `docs/PHASE_3_ACCEPTANCE.md §11` have passing evidence; this does not substitute for Owner/Analyst acceptance.

| # | Check | Evidence |
|---|---|---|
| 1 | Home and Activities routes | live/synthetic browser; route unit test |
| 2 | Set/change/clear goal | disposable Settings browser; storage/action tests |
| 3 | No invented default | fresh store; unset/historical-year tests |
| 4 | Virtual and outdoor contribute | independent live classification scan; controlled fixture |
| 5 | File wins on overlap | controlled actual FIT/API overlap; live conflicts |
| 6 | API-only distance | seven live YTD contributors; synthetic API-only rides |
| 7 | CSV units not guessed | explicit CSV-only fixture and unit test |
| 8 | Independent YTD/last7/prior7 | direct SQL/Decimal oracle, fifteen periods |
| 9 | LA/Tokyo boundaries | both browser contexts; six controlled year/leap checks |
| 10 | Leap-year pace | 366-day unit test |
| 11 | Independent goal math | live Owner target and Decimal arithmetic |
| 12 | Recent links/evidence | matches Activities in both browser zones |
| 13 | Power cards | Performance page and independent result references |
| 14 | Compact power visualization | independent rolling event/reference scan |
| 15 | Deterministic insights | pace and accepted prior-six-week reproduction |
| 16 | Normal sync refreshes Home | real unchanged sync; synthetic new/enriched sync |
| 17 | Failure visible on Home | injected failure, restart and later-sync recovery |
| 18 | Restart preserves goal/dashboard | live exact goal tuple and periods; synthetic restart |
| 19 | Desktop/phone | real Chromium Home, Settings and Activity Review |
| 20 | Full regression | 269 full / 16 focused; Settings and seven live reviews |
| 21 | Deferred scope absent | diff inspection; no-deferred-metrics unit test |

## Reproduction

The commands below show the commands used with private inputs replaced by placeholders. Choose fresh ignored disposable stores/baseline directories for each UI run; open Chromium sessions first with the installed Playwright CLI. The live Home verifier performs a real bounded metadata sync unless `--skip-sync` is supplied. It preserves existing goal records; a store with no goal uses clearly temporary review targets and clears them. The independent standalone verifier and read-only rerun make no external API calls.

```sh
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m unittest discover -s tests -p test_rideworks_dashboard.py
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --synthetic-dir '<fresh-disposable-store>' --session rideworks-p3-01 --output '<aggregate-output>'
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --data-dir '<accepted-store>' --baseline '<fresh-baseline>' --session rideworks-p3-01 --output '<aggregate-output>'
.venv/bin/python tools/verify_rideworks_dashboard_ui.py --data-dir '<accepted-store>' --baseline '<fresh-rerun-baseline>' --session rideworks-p3-01 --skip-sync --output '<aggregate-output>'
.venv/bin/python tools/verify_rideworks_dashboard.py --data-dir '<accepted-store>' --tz America/Los_Angeles
.venv/bin/python tools/verify_rideworks_dashboard.py --data-dir '<accepted-store>' --tz Asia/Tokyo --as-of 2026-01-01T00:30:00+00:00
.venv/bin/python tools/verify_rideworks_strava_stream_ui.py --data-dir '<accepted-store>' --links '<local-review-links>' --session rideworks-p3-01 --live
.venv/bin/python tools/verify_rideworks_strava_settings_ui.py --synthetic-dir '<fresh-settings-disposable-store>' --session rideworks-p3-settings
.venv/bin/python -m rideworks --data-dir '<accepted-store>' serve --port 8771
```

Aggregate evidence is in [acceptance.json](acceptance.json). Committed screenshots contain generated synthetic Activities and a temporary synthetic target only: [desktop](home-desktop-synthetic.png), [phone](home-phone-synthetic.png). Live desktop/phone screenshots remain private and are available locally to the Owner.

## Owner handoff

Running review URLs: [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings goal](http://127.0.0.1:8771/settings#annual-goal). The browser supplies timezone automatically. Owner goal remains 2,200 mi.

Review the usefulness and prominence of mileage progress, neutral pace wording, recent rides and 20-minute context, and desktop/phone usability. No FTP, Fitness Score, Training Load, Next Workout, adaptive plan, arbitrary-duration power curve or AI Insights was implemented. Stop at **HARD — Owner**; after explicit Owner approval, Gate 2 requires Analyst acceptance. Do not begin Phase 4.
