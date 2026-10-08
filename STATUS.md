# STATUS.md

**Product:** RideWorks. Phase 1, Phase 2 and STRAVA-004 accepted / complete. P3-01 awaits Owner review; Phase 4/5/6 not started.

**Current task:** P3-01, `ready_for_review` after `/TASK P3-01` Owner-requested YTD mileage investigation. `TASKS.md` remains `in_progress`. Numeric discrepancy, Owner approval and Analyst acceptance remain outstanding.

**Branch / PR:** `task/p3-01-dashboard` / [draft PR #19](https://github.com/k14krug/my_strava/pull/19). Runtime unchanged at `1cc01b6`; controlling JIT `3820120` / Phase 3 contract `38211d2`.

**Findings:** LA YTD reproduces 1,518.211351955 mi: 120 cycling Activities, 112 distance contributors. All eight unavailable entries are Ride, each GPX+export-backed with an established Strava ID, no explicit GPX distance and no retained API summary. No ignored known-unit distance or association defect found; existing-evidence recovery is zero. File-first adds only 0.12 m versus retained API values. Approximately 112.79 mi remains unallocated against the Owner's approximate Strava reference; the missing eight's mileage is unknown.

**Verification:** Private reconciliation covers all 120 YTD Activities plus one year-boundary exclusion. Independent SQL/Decimal selection agrees with production; 113 original-file hashes/sizes and distance evidence plus original CSV checked; integrity/FKs pass. Fifteen live source/association/goal/sync tables match the snapshot. Zero Strava requests or source/runtime changes. Prior runtime tests: 276 full / 23 focused (not rerun). Aggregate findings: `reports/P3-01/verification.md`; detailed identities/raw evidence remain private/local.

**Running review:** [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings goal](http://127.0.0.1:8771/settings#annual-goal). Owner-confirmed 2026 / 2,200-mi goal unchanged.

**Next action:** **Gate 1 — HARD — Owner:** review findings and decide whether to authorize at most eight bounded summary-window GETs, retaining only the eight established IDs (plus at most one token-refresh POST). No enrichment performed. Exact-ID detail GETs require a narrow endpoint exception; neither path is implemented. Any authorized maintenance must preserve the forward-sync checkpoint and recheck dates/types/mileage. No approval, merge, next task or Phase 4/5/6.
