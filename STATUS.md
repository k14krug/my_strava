# STATUS.md

**Product:** RideWorks. Phase 1 and Phase 2 accepted / complete; Phase 3 not started.

**Current task:** STRAVA-004 — `in_progress`, invoked with `/TASK PR18`; addressing the Owner-approved final Performance-policy and sync-convergence correction.

**Branch / PR:** `task/strava-004-streams` / [PR #18](https://github.com/k14krug/my_strava/pull/18) (draft). Analyst JIT `f9711f4` refreshed from main `2e3ca9b`.

**Authorized behavior:** `virtual-power-evidence-v2` retains file-backed power precedence and admits only validated API stream fallback for Virtual Rides. Sync now automatically rebuilds only when current-policy Performance is pending, and preserves source sync/checkpoint plus prior Performance on rebuild failure. The banner becomes an exception/freshness indicator with Retry Performance update.

**Verification baseline:** prior review correction at `ee84c97` passed 243 full / 57 focused tests and Chromium. Local store: 1,441 Activities / 11 stream observations / 1,022 v1 eligible results; five API-only qualifying power rides and two HR-only. Original Stage A: four exact power/HR overlaps. Original bounded stream GETs: 11. Preserve originals, source evidence and historical v1 rows; independently verify all 1,022 file-backed results plus five API results under v2.

**Next action:** implement and verify v2 eligibility/provenance/freshness, shared post-sync convergence, six-week context, failure/retry/restart/idempotence, and the expected 1,027 eligible / zero pending result. Re-present HARD — Owner; Analyst acceptance remains pending and no Phase 3 work is authorized.
