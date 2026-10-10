# STATUS.md

**Product:** RideWorks.
**Current task:** P4-02 — Longitudinal Training State and Fitness Trend.
**State:** ready_for_review — diagnostic complete at **HARD — Analyst** after Owner Gate 2 was not accepted. Prior HR Gate 1 release does not clear this new blocker.
**Branch:** `task/p4-02-training-state`; [draft PR #24](https://github.com/k14krug/rideworks/pull/24).
**Authority:** Latest `/TASK P4-02`; refreshed Analyst JIT §12/design at `2942449`. Invocation remains `/TASK only`; diagnosis and correction plan precede material implementation.
**Delivered:** Read-only power-source diagnostic and synthetic tests. Existing Training State, independent HR summary correction, hover and FTP implementation retained unchanged. Private diagnosis covers nine Activities, independently selected interval/threshold workouts, ordinary/low comparisons and the outdoor HR regression.
**Findings:** Mandatory workout passes Performance best-20; its retained power is partial and current precedence selects HR. Decoupling best-20 alone cannot fix that case. Separately, 117 best-20-ineligible FIT rides have stress candidates: 53 calculated, 19 corrected estimates, 45 partials. Proposed bounded stress evaluator and separate partial-power precedence/evidence decision await Analyst review.
**Verification:** 353 full / five focused diagnostic Python tests; 218 Chromium assertions in 3-/12-month views; 141 independent power-interval checks; repeated diagnosis identical. Prior HR behavior rerun unchanged. All 20 original tables / 1,422 artifacts preserved; all-table digest includes unchanged derived cache. Production code, Performance-v2, approved FTP and exact Elevate reference unchanged; 14 projections excluded.
**Review app:** `http://127.0.0.1:8772/training-state` on the existing verified private copy. Accepted production store/server retained.
**Evidence:** [Source-neutral diagnosis and correction plan](reports/P4-02/interval-power-diagnosis.md); [safe aggregates](reports/P4-02/interval-power-diagnosis.json). Exact per-source/ride diagnosis, surrounding-day responses, reference curves and screenshots remain local-only under `local_data/p4-02-interval-diagnosis/` and `output/playwright/`.
**Next action:** Analyst reviews the diagnosis and explicitly authorizes/revises the bounded correction plan and disposition of partial power versus HR summaries. No material source-policy change before authorization. Re-verify authorized changes at Gate 1, then repeat Owner Gate 2. No merge, task/Phase 4 acceptance or later task.
