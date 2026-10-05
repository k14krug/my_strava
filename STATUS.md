# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete. **Phase 2:** in progress; P2-01/P2-02 accepted and merged.

**Current task:** P2-03 — in_progress.

**Implementation state:** awaiting_owner_review — Gate 1 HARD — Owner. Implementation and required local verification complete.

**Branch / PR:** `task/p2-03-performance-history` / [#15](https://github.com/k14krug/my_strava/pull/15) (draft).

**Implementation head:** `6a8d41277be839a6b316a8066940d36a857ea4e8`; final publication is documentation/evidence only.

**Implemented:** schema 4 durable performance statuses/results, `rebuild-performance`, `virtual-native-power-v1` classification/source selection, unchanged `best-average-power-v1`; stale-input suppression and atomic failure-safe rebuild. Real Performance navigation/page displays all dated eligible points with pointer/keyboard inspection, Activity links, local dates and inspectable provenance. Outdoor/non-virtual power and summary substitutes excluded; no P2-04 work.

**Verification:** 162 tests passed. Disposable full history: 1,434 evaluated, 1,264 Virtual Ride candidates, 1,022 eligible FIT results; 198 short / 39 incomplete timing / 5 incomplete power; 146 outdoor and 24 non-cycling excluded. Every eligible result independently verified exactly. Representative retains 3,621 records / 120 W best-20 / 118 W FIT average. Rebuild idempotence, Store and HTTP process restart, SQLite integrity/foreign keys, accepted Activities/rich/thin regressions and Chromium checks passed. No Virtual/native classification conflicts or missing result dates. Date span 2018-05-13–2026-09-29; desktop/phone no overflow; local dates verified in Los Angeles and Tokyo.

**Evidence:** `reports/P2-03/verification.md`, `reports/P2-03/acceptance.json`. Inputs/stores/private screenshots remain local and ignored.

**Owner review:** **http://127.0.0.1:8768/performance**, disposable `local_data/p2-03-review`, 1,022 points. Startup: `.venv/bin/python -m rideworks --data-dir local_data/p2-03-review serve --port 8768`. Rebuild if needed: `.venv/bin/python -m rideworks --data-dir local_data/p2-03-review rebuild-performance`. Screenshots: `output/playwright/p2-03-performance-desktop.png` and `output/playwright/p2-03-performance-phone.png`.

**Blockers:** Owner visual/usability approval pending; no implementation/verification blocker.

**Next action:** Ken reviews the Performance history and cohort explanation and records approval or bounded corrections. After explicit Owner approval, record it and stop at Gate 2 HARD — Analyst. Do not begin P2-04 automatically.
