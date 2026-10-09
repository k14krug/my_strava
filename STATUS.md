# STATUS.md

**Product:** RideWorks.

**Completed:** Phase 1; Phase 2 historical/performance; STRAVA-004; Phase 3 dashboard.

**Current task:** P4-01 — **ready_for_review at HARD — Analyst**; TASKS remains `in_progress`. Branch `task/p4-01-training-state`, [draft PR #23](https://github.com/k14krug/rideworks/pull/23). Main `20cfbb6`, JIT §16 `36c72d0`, contract §8.2 `67ad8ca` integrated; `/TASK only`.

**Owner design approved:** Separate 7-/42-day observed work/stress with calculated, estimated, partial and unavailable classes; FIT-only gaps ≤15 s and ≤1% total missing; API observed-only; validated timer split/reset outranks heuristics. DESIGN-003 now records these choices. Verified screen: **131 FIT + 2 API = prior 133**, with API correction excluded. Recent 42 days: 23 complete envelopes, 2 FIT estimate screens, 6 partial contributors, 7 omitted rides. Missing time/unknown boundaries remain explicit.

**Reporting correction:** One eligible interrupted FIT has corroborating boundary/timer metadata, contrary to the earlier zero claim. No corrected whole-session calculation was verified. The audit does not promote it to a whole-session label.

**Verification:** 311 full tests / 26 research tests, 52 Node assertions; published comparison checks and full preservation rerun. All 20 production tables / 1,422 originals unchanged. [Current verification](reports/P4-01/verification.md). Historical experiment outputs and FTP CSV unchanged; no production behavior or Performance-v2 changes.

**Next action:** Analyst reviews the reconciled design, FIT-only count, pause/fallback precedence and boundary-count correction for P4-01 acceptance. Owner choice is resolved; task acceptance is not. No merge, P4-02, production import, Phase 5/6 or automatic next task.
