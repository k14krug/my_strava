# STATUS.md

**Product:** RideWorks. **Phase 1:** accepted / complete. **Phase 2:** in progress.

**Accepted:** P2-01/P2-02/P2-03 done; PR #15 merged as `4f1a58d39177887e965ddd1a74db95c62c17e0b0`.

**Current task:** P2-04 — in_progress.

**Implementation state:** awaiting_owner_review — implementation/verification complete; stopped at Gate 1 HARD — Owner under `docs/tasks/P2-04.md`.

**Branch / PR:** `task/p2-04-recent-context` / [#16](https://github.com/k14krug/my_strava/pull/16) (draft).

**Implementation head:** `8ef30c93ce797f4a0e019c34b6663fb3f00c84be`; final publication adds status/evidence only.

**Implemented:** compact neutral Recent context inside Best 20-minute power, prior Activity/date and View Performance links, secondary method/input/window details. Exact `(t − 42 days, t)`; self/endpoints excluded; raw max then earliest start/Activity ID. Stale/missing/ineligible/unknown-time current and empty prior windows stay unavailable. No new table, archive import/reparse or automatic Performance rebuild; comparison reads current persisted metadata/results. Thin and ordinary current FIT behavior retained; long Unavailable source metrics fit the phone grid.

**Verification:** 185 full / 15 focused tests passed. Copied accepted P2-03 store: 1,434 statuses / 1,022 eligible; 1,012 with prior / 10 without; all independently verified; 412 ineligible remain excluded. Native-read/mutation/import/reparse/rebuild guards pass. Persisted history/originals unchanged; Store/HTTP restart and SQLite checks pass. Accepted Activities/rich/thin regressions and Chromium available/no-prior/outdoor, navigation/back/provenance, Los Angeles/Tokyo dates and desktop/phone no overflow pass. Representative: 120 W current / 195 W prior, 118 W FIT average, 3,621 native records.

**Evidence:** `reports/P2-04/verification.md`, `reports/P2-04/acceptance.json`.

**Owner review:** http://127.0.0.1:8769/. Startup: `.venv/bin/python -m rideworks --data-dir local_data/p2-04-review serve --port 8769`. Private exact routes: `output/playwright/p2-04-review-links.json` (`representative`, `no_prior`, `outdoor`). Screenshots: `output/playwright/p2-04-recent-desktop.png`, `output/playwright/p2-04-recent-phone.png`. Inputs/copy/links/images remain ignored/local.

**Blockers:** Owner usability approval pending; no implementation/verification blocker.

**Next action:** Ken reviews whether Recent context answers the prior-six-week question clearly without cluttering Activity Review. After explicit Owner approval, record it and stop at HARD — Analyst. Do not begin P2-05 automatically.
