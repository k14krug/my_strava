# STATUS.md

**Product:** RideWorks. Phase 1 and Phase 2 accepted / complete; Phase 3 not started.

**Current task:** STRAVA-004 — `in_progress`, invoked with `/TASK`; awaiting Owner review at **Gate 1 — HARD — Owner**.

**Branch / PR:** `task/strava-004-streams` / [PR #18](https://github.com/k14krug/my_strava/pull/18) (draft). Implementation head: `584de0a0e0dd3511a30c0097cdd72d14bc7cf29c`.

**Implementation:** Stage A passed: four overlaps, 13,076 exact timestamp pairs per power/HR signal, 100% agreement; independent qualifying best-20 means/windows equal. Cadence comparison unavailable from accepted FIT extraction. Stage B preserves separate API stream evidence and adds normal bounded Sync now enrichment. Seven known API-only rides now have charts: five power+HR, two HR-only. FIT remains authoritative; trusted Performance eligibility unchanged.

**Verification:** 236 full / 50 focused Strava tests passed. Live and synthetic Chromium, P2-05 Settings/OAuth/rebuild regression, migration, restart/idempotence, integrity/FKs passed. Eleven live stream GETs total; rerun zero GETs/new observations. Live rate header values unavailable. All 16 accepted tables and source originals unchanged: 1,441 Activities / 1,022 eligible Performance / 0 pending. [Evidence and reproduction](reports/STRAVA-004/verification.md).

**Review:** Existing app at `http://127.0.0.1:8771/`, running final code. Private `output/playwright/strava-004-review-links.json` contains newest API-only / FIT overlap links supplied directly to Ken. Expand “Strava API stream evidence” for provenance.

**Next action:** Owner reviews whether the API-only graph is useful and honest about source, timing, missing signals, and gaps. The JIT requires stopping here. After explicit Owner approval, Gate 2 is Analyst review; task is not accepted and no next task is authorized.
