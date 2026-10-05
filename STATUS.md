# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete. **Phase 2:** in progress; P2-01/P2-02 accepted and merged.

**Current task:** P2-03 — in_progress.

**Implementation state:** awaiting_owner_review — single-surface Range/View correction complete under JIT at `3ae14b9`; stopped again at Gate 1 HARD — Owner.

**Branch / PR:** `task/p2-03-performance-history` / [#15](https://github.com/k14krug/my_strava/pull/15) (draft).

**Implementation head:** `fa0d877dc301dd605f612670e6595aafe4e7fc14`; final publication adds status/evidence only.

**Implemented:** one Performance surface with five Ranges, Rolling 42-day / Monthly best / Yearly best Views, optional subdued ride dots in every view, four summaries with freshness and complete paged evidence. Default: one year + Rolling 42-day + Trend only. Future Performance candidates is collapsed and clearly unimplemented. Schema 4 / `best-average-power-v1` / `virtual-native-power-v1` remain unchanged; outdoor/non-virtual and summary substitutes remain excluded. No P2-04 work.

**Verification:** 28 focused / 170 full tests passed. Full-history independent check: 1,434 evaluated / 1,264 Virtual candidates / 1,022 eligible FIT results; 198 short / 39 incomplete timing / 5 incomplete power; 146 outdoor and 24 non-cycling excluded. All eligible results agree exactly; rolling winners at 2,019 checkpoints and all four summaries agree. Idempotent rebuild, Store/HTTP restart, SQLite integrity/foreign keys and accepted Activities/rich/thin regressions passed. Chromium verified all 15 Range/View combinations, independent monthly/yearly winners, synthetic calendar/raw/tie/zero/empty/partial-range cases, all 1,022 ride results, pointer/keyboard/Activity/back, Los Angeles/Tokyo dates and desktop/tablet/phone without overflow.

**Evidence:** `reports/P2-03/verification.md`, `reports/P2-03/acceptance.json`. Inputs/stores/private screenshots remain local and ignored.

**Owner review:** **http://127.0.0.1:8768/performance**, disposable `local_data/p2-03-review`. Startup: `.venv/bin/python -m rideworks --data-dir local_data/p2-03-review serve --port 8768`. Rebuild if needed: `.venv/bin/python -m rideworks --data-dir local_data/p2-03-review rebuild-performance`. Screenshots: `output/playwright/p2-03-performance-desktop.png`, `p2-03-performance-phone.png`, `p2-03-monthly-desktop.png`, `p2-03-yearly-desktop.png` in that same directory.

**Blockers:** Owner visual/usability approval pending; no implementation/verification blocker.

**Next action:** Ken reviews usefulness of the single Performance surface, Range/View/evidence controls, three analytical views, summaries, information hierarchy and visual quality. After explicit Owner approval, record it and stop at Gate 2 HARD — Analyst. Do not begin P2-04 automatically.
