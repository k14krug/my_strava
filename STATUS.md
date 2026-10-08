# STATUS.md

**Product:** RideWorks. Phase 1, Phase 2 and STRAVA-004 accepted / complete. P3-01 awaits Owner review; Phase 4/5/6 not started.

**Current task:** P3-01, `ready_for_review` after `/TASK P3-01` Owner-authorized targeted summary enrichment. `TASKS.md` remains `in_progress`; Owner/Analyst acceptance remains outstanding.

**Branch / PR:** `task/p3-01-dashboard` / [draft PR #19](https://github.com/k14krug/my_strava/pull/19). Runtime `38183e3`; refreshed main `a2faa70`; Analyst JIT `25b7d5e` / Phase 3 contract `8c2c284`.

**Result:** Exactly eight established GPX/export outdoor Rides received allowlisted current API summaries via eight sequential direct-ID GETs and one token-refresh POST. Zero list/stream requests, new Activities or CSV-unit/coordinate-derived values. Added **112.984110296 mi**; LA YTD **1,631.195462250 mi**, 120 contributors / zero distance unavailable. File 104 / 1,415.637321791 mi; API 16 / 215.558140460 mi. All eight selected distances/durations use API summary provenance. Forward-sync checkpoint preserved.

**Residual:** Reference-minus-RideWorks against approximately 1,631 mi is **−0.195462250 mi**, consistent with whole-mile reported precision. The material deficit is explained by the eight omissions; exact current Strava equality remains unverified.

**Verification:** 284 full / 8 focused tests pass, including normal future GPX Sync now fallback without historical requests. Independent SQL/Decimal, offline eight-observation idempotence, 17 unchanged native/export/goal/sync/stream tables, all 1,422 original hashes/sizes and integrity/FKs pass. Fresh live Chromium LA/Tokyo, desktop/phone, chart/tooltip, restart/search/sort/pagination and all eight target Activity Reviews (16 at both widths) pass. Performance converged atomically: 1,028 eligible / zero pending; outdoor eligibility unchanged. Private full reconciliation/target evidence remains local; aggregates in `reports/P3-01/verification.md` / `acceptance.json`.

**Owner goal / review:** 2026 / 2,200-mi goal and updated timestamp unchanged. Home shows 1,631.2 mi, 74.1%, 568.8 mi remaining and 47.4 mi/week needed. Actual current card/bar 26.3 mi. [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings goal](http://127.0.0.1:8771/settings#annual-goal); review server restarted on corrected runtime. Screenshots remain private.

**Next action:** Re-present **Gate 1 — HARD — Owner**: review restored distances/durations, post-enrichment total and the approximate-reference residual limitation. Explicit Owner approval precedes Gate 2 — HARD — Analyst acceptance. No approval, merge, next task or Phase 4/5/6.
