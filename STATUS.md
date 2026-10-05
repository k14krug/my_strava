# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete. **Phase 2:** in progress; P2-01/P2-02 accepted and merged.

**Current task:** P2-03 — in_progress.

**Implementation state:** awaiting_owner_review — Owner-directed correction complete under JIT at `98828a8`; stopped at Gate 1 HARD — Owner.

**Branch / PR:** `task/p2-03-performance-history` / [#15](https://github.com/k14krug/my_strava/pull/15) (draft).

**Implementation head:** `64d33bc691c1e9e8fc5745ebb2ff36d2f876db4f`; final publication adds status/evidence only.

**Implemented:** Current / Trend / History, Trend defaulting to one year with rolling 42-day demonstrated-best line, optional subdued ride dots, five ranges, four compact summaries with freshness, annual peaks and complete paged ride evidence. Calculation/persistence remains schema 4 / `best-average-power-v1` / `virtual-native-power-v1`; excluded outdoor/non-virtual power and summary substitutes remain excluded. No P2-04 work.

**Verification:** 170 tests passed. Full-history independent check: 1,434 evaluated / 1,264 Virtual candidates / 1,022 eligible FIT results; 198 short / 39 incomplete timing / 5 incomplete power; 146 outdoor and 24 non-cycling excluded. All eligible results agree exactly; rolling winners at all 2,019 entry/expiry checkpoints and all four summaries agree. Idempotent rebuild, Store/HTTP restart, SQLite integrity/foreign keys and accepted Activities/rich/thin regressions passed. Chromium verified all modes/ranges, annual peaks, all 1,022 ride results, pointer/keyboard/Activity/back flows, Los Angeles/Tokyo dates and desktop/tablet/phone without overflow. Zero classification conflicts or missing/unknown eligible Activity dates.

**Evidence:** `reports/P2-03/verification.md`, `reports/P2-03/acceptance.json`. Inputs/stores/private screenshots remain local and ignored.

**Owner review:** **http://127.0.0.1:8768/performance**, disposable `local_data/p2-03-review`. Startup: `.venv/bin/python -m rideworks --data-dir local_data/p2-03-review serve --port 8768`. Rebuild if needed: `.venv/bin/python -m rideworks --data-dir local_data/p2-03-review rebuild-performance`. Screenshots: `output/playwright/p2-03-performance-desktop.png`, `p2-03-performance-phone.png`, `p2-03-current-desktop.png`, `p2-03-history-desktop.png` in that same directory.

**Blockers:** Owner visual/usability approval pending; no implementation/verification blocker.

**Next action:** Ken reviews usefulness of the modes, trend readability, summaries/controls, information hierarchy, attractiveness and continuity with accepted RideWorks screens. After explicit Owner approval, record it and stop at Gate 2 HARD — Analyst. Do not begin P2-04 automatically.
