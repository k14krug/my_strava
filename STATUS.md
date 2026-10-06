# STATUS.md

**Product:** RideWorks.

**Phase 1:** accepted / complete.

**Phase 2 — Historical context and performance history:** accepted / complete.

**STRAVA-004 — Strava activity-stream enrichment and FIT comparison:** accepted / complete.

**PR #18:** Owner and Analyst accepted; merged to `main` as `e7920493dfadbb5f15b0352315cce433f7991ecd`.

**Current Performance policy:** `virtual-power-evidence-v2` / `best-average-power-v1` / 1,200 s.

**Final live result:** 1,441 Activities / 11 retained stream observations / **1,027 eligible Performance / 0 pending**. All 1,022 prior file-backed eligible results reproduce unchanged; 5 validated API-only Virtual Rides are eligible; 2 HR-only outdoor rides are current/ineligible. FIT/API overlaps remain single file-backed points.

**Sync behavior:** normal Sync now performs bounded metadata + stream enrichment and automatically converges Performance only when current-policy history is pending/stale. Successful sync leaves Performance current. The app-wide Performance banner is reserved for unresolved update/failure and offers retry.

**Verification:** 253 full / 57 focused Strava / 38 focused Performance tests, independent file/API result verification, six-week contributor verification, Chromium desktop/phone + LA/Tokyo, failure/retry, restart/idempotence, SQLite integrity/FKs all passed. Initial stream access remained bounded at 11 GETs; the final correction made zero new stream GETs.

**Evidence:** `reports/STRAVA-004/verification.md`, `reports/STRAVA-004/acceptance.json`.

**Phase 3:** not started.

**Current implementation task:** none.

**Next action:** await Owner direction before authoring or starting the next implementation task.
