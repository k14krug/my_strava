# STATUS.md

**Product:** RideWorks. Phases 1–3 and STRAVA-004 accepted. Phase 4 research active; Phase 5/6 not started.

**Current task:** P4-01 — Training-state model evaluation and athlete-state inventory. TASKS `in_progress`; STATUS `ready_for_review` at **HARD — Owner** (JIT §§12/14). Owner model/recording-policy choice and subsequent Analyst acceptance outstanding.

**Branch / PR:** `task/p4-01-training-state` / [draft PR #23](https://github.com/k14krug/rideworks/pull/23). Invocation `/TASK P4-01`; JIT's missing declaration uses `/TASK only` fallback. Refreshed main `91842f7`, JIT `645cb48`, Phase 4 contract `a74c97c` integrated.

**Revised research:** Validated the committed 66-entry FTP CSV under Owner-approved effective dates. FTP covers 878/1,028 eligible power rides: 597 complete envelopes plus 281 interrupted recordings with usable segments. All observed work: 1,028 contributions. Exact full-timer stress: 24; one-second summary sensitivity: 75. These are different calculation scopes, not interchangeable full-session TSS.

**Recommendation:** Separate 7-/42-day observed work and partial recorded segment stress (candidate minimum 600 s), with provenance and coverage. Latest 42 days: 31/38 contributors, 11,075.38 kJ observed, 1,428.54 segment points; six outdoor and one ineligible virtual ride omitted. No complete CTL/ATL/TSB or physiological readiness claim.

**Verification:** 303 full / 18 focused tests; independent SQL/integer-window/Decimal checks of 878 dated contributions, 2,718 segment metrics and 70,908 rolling comparisons. All 20 production tables unchanged; 1,422 originals verified; integrity/FKs pass. See `reports/P4-01/verification.md` and `acceptance.json`. Initial retained-evidence census preserved separately.

**Next action:** Owner reviews revised DESIGN-003 and chooses dual partial-segment/work, work-only or strict full-timer stress, including recording/missingness policy. Analyst review and a separately authored P4-02 JIT follow that choice. Stop here: no production changes, P4-02 implementation, merge or task acceptance.
