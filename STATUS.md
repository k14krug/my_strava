# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete — P1-01/P1-02/P1-03 done.

**Phase 2 — Historical context and performance history:** in progress.

**P2-01 — Historical Strava-export import and enrichment:** done — Analyst accepted PR #13 on 2026-10-04.

**PR #13:** merged to `main` as `57c00ae396bfb1e9c2c4c72ff42c5628afda9940`.

**P2-01 verification:** 123 tests passed; clean seeded full export passed with 1,434 Activities / 1,421 artifacts / 13 CSV-only Activities, zero failures/unresolved associations; restart/idempotent rerun passed; all originals verified; all 18 integer lap timestamps across 17 Sources preserved losslessly and reproduced.

**P2-01 evidence:** `reports/P2-01/verification.md`, `reports/P2-01/acceptance.json`.

**Current task:** P2-02 — in_progress.

**Implementation state:** awaiting_owner_review — Gate 1 HARD — Owner; requested corrections implemented and verified.

**Branch / PR:** `task/p2-02-activities-browser` / [#14](https://github.com/k14krug/my_strava/pull/14) (draft).

**Implementation head:** `a1a42eb767ab7434ef0a9f2890cd912054183441`; final handoff publication is documentation/evidence only.

**Implemented:** dedicated Date column beside Title, with known dates on one line and no timezone suffix; absolute times and From/To use the same browser-local calendar day; unknown-zone dates retain their supplied day. 30-row cycling-first browser; GET title/type/subtype/date/timezone/sort/page state; preferred source titles with provenance; stable rich FIT and thin TCX/GPX/CSV-only/ambiguous-FIT reviews. Metadata browsing does not load native streams or rewrite source evidence.

**Verification:** 142 tests passed. Clean local review store contains all 1,434 Activities / 1,421 file Sources / 13 CSV-only Activities, zero failures/unresolved associations. Full-history HTTP/restart and actual Chromium acceptance passed. 1,410 cycling Activities, 47 cycling / 48 all pages. Representative FIT retains 118 W average / 120 W best-20. Local-day display/filtering verified in Los Angeles, Tokyo and UTC, including UTC-midnight crossing; DST boundary tests pass. No horizontal overflow at desktop/tablet/phone widths.

**Evidence:** `reports/P2-02/verification.md`, `reports/P2-02/acceptance.json`. Private screenshots remain under ignored `output/playwright/p2-02-*.png`.

**Local Owner review:** use the full-history server at **http://127.0.0.1:8766/** (1,410 cycling / 1,434 total). Port 8765 is the separate older one-activity instance and must not be used for this review. Startup from repo root: `.venv/bin/python -m rideworks --data-dir local_data/p2-02-review serve --port 8766`.

**Blockers:** Owner visual/usability approval pending; no implementation/verification blocker.

**Next action:** Ken reviews the corrected full-history browser on port 8766 and records explicit approval or bounded corrections. After Owner approval, record it and stop at Gate 2 HARD — Analyst. Do not begin P2-03.
