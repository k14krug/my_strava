# STATUS.md

**Product:** RideWorks.

**Phase 1:** accepted / complete.

**Phase 2 — Historical context and performance history:** accepted / complete.

**P2-01 through P2-05:** done.

**P2-05 / PR #17:** Owner and Analyst accepted; merged to `main` as `e78c8a6c2de4f4e21aaa2937ae33d1e011901947`.

**Final Phase 2 live evidence:** 1,441 Activities / 1,417 cycling after forward Strava sync; 7 post-export API-only Activities surfaced in correct chronology; 4 overlap rides enriched without duplication; restart reruns created no duplicate Activities/observations; explicit Performance rebuild evaluated 1,441 Activities, retained 1,022 eligible results and cleared 11 pending to zero. 219 full / 33 focused tests and Chromium acceptance passed.

**Current task boundary:** STRAVA-004 — Strava activity-stream enrichment and FIT comparison.

**JIT:** `docs/tasks/STRAVA-004.md` authored from current Strava stream/authentication documentation.

**Purpose:** compare Strava time/watts/HR/cadence/moving streams against preserved FIT evidence on the four overlap rides, then use bounded recent stream enrichment for API-only Activity Review graphs only if that evidence supports it.

**Trusted Performance boundary:** unchanged. STRAVA-004 must not add API streams to `virtual-native-power-v1` or alter the accepted 1,022-result cohort.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Phase 3:** not started.

**Next action:** invoke STRAVA-004 when ready. Stage A compares live Strava streams with FIT before product use; material mismatch stops the task before graph integration.
