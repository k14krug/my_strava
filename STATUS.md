# STATUS.md

**Product:** RideWorks. Phases 1–3 and STRAVA-004 accepted / complete. Phase 4 research active; Phase 5/6 not started.

**Current task:** P4-01 — Training-state model evaluation and athlete-state inventory. TASKS `in_progress`; STATUS `ready_for_review` at **HARD — Owner** (JIT §12). Owner direction and subsequent Analyst acceptance outstanding.

**Branch / PR:** `task/p4-01-training-state`; review PR being opened. Base `84e7048`, Analyst JIT `e04d0ca`. Invocation `/TASK P4-01`; missing Allowed Invocation uses AGENTS.md's `/TASK only` fallback.

**Delivered:** Proposed DESIGN-003, complete retained-evidence census, current primary-source research, reproducible research tools, synthetic model comparison and anonymized actual-period figures. No production changes or Strava calls.

**Findings:** 1,442 Activities / 1,418 cycling; 1,028 eligible power results (1,022 FIT / 6 API), 693 complete recorded envelopes. Only one usable source-session cycling threshold candidate; no longitudinal FTP or cycling HR-reference history. One elapsed/timer discrepancy demonstrates why elapsed duration alone is unsuitable as workload. Recommended separate 7-/42-day recorded-work summaries with coverage; normalized stress conditional on dated FTP and timing policy.

**Verification:** 293 full / 8 focused research tests; independent SQL/Decimal verifies 693 work results, one session-threshold stress result and 23,636 rolling comparisons. All 20 production tables unchanged; 1,422 original hashes/sizes verified; integrity/FKs pass. Evidence: `reports/P4-01/verification.md` and `acceptance.json`.

**Next action:** Owner review of `docs/design/DESIGN-003-training-state-model.md`: choose workload-first or dated FTP collection first, then Analyst review and a separately authored P4-02 JIT. Stop here under P4-01 §12: “Stop for Owner decision.” No P4-02 implementation or task acceptance yet.
