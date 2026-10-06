# STATUS.md

**Product:** RideWorks. Phase 1 and Phase 2 accepted / complete; Phase 3 not started.

**Current task:** STRAVA-004 — `in_progress`, invoked with `/TASK PR18`. State: `ready_for_review` at **Gate 2 — HARD — Analyst** after explicit Owner approval.

**Branch / PR:** `task/strava-004-streams` / [PR #18](https://github.com/k14krug/my_strava/pull/18) (draft). Analyst JIT `f9711f4` refreshed from main `2e3ca9b`; runtime implementation `cce020b`.

**Implemented:** `virtual-power-evidence-v2` preserves file-backed power precedence and admits strict current API stream fallback for Virtual Rides. Shared web/CLI sync automatically rebuilds only when pending; failure preserves synchronized evidence/checkpoint and prior Performance, with an exception banner and Retry Performance update. Eligible API reviews include normal six-week context and inspectable source provenance.

**Verified:** 253 full / 57 focused Strava / 38 focused Performance tests passed; live/synthetic Chromium, failure/retry/restart/idempotence passed. All 1,022 file-backed results unchanged and independently recomputed; five API results and six-week contributors independently verified. **1,027 eligible / zero pending**, two HR-only outdoor rides current/ineligible; no overlap duplicates. 1,441 Activities / 11 stream observations; historical v1 rows, originals and native/export evidence retained. Correction: three bounded metadata GETs, zero new stream GETs. Real Settings Sync now shows Performance is current without a banner. Evidence: `reports/STRAVA-004/verification.md` and `acceptance.json`.

**Next action:** Analyst reviews PR #18 against the final STRAVA-004 JIT and verification evidence, then accepts or returns actionable feedback. Keep STRAVA-004 `in_progress`; do not begin another task or Phase 3.
