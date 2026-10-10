# STATUS.md

**Product:** RideWorks.
**Current task:** P4-02 — Longitudinal Training State and Fitness Trend.
**State:** ready_for_review after the revised same-source HR summary correction and behavioral validation. HARD — Analyst Gate 1 remains uncleared.
**Branch:** `task/p4-02-training-state`; [draft PR #24](https://github.com/k14krug/rideworks/pull/24).
**Authority:** Latest explicit `/TASK P4-02`; revised Analyst JIT and design direction at `010eff5`. Invocation remains `/TASK only`; Owner Gate 2 follows Analyst authorization.
**Delivered:** Existing Training State, hover/selection and FTP update implementation retained. Versioned independent same-source HR summary fallback now works with defective streams; source/mean/duration, rejected coverage and unverified completeness/pause semantics remain inspectable. Power rules, source originals and approved FTP remain unchanged; no partial HR default.
**Verification:** 348 full / 32 focused Python tests; 286 general + 76 private representative browser assertions. Five distinct high/ordinary/low and recent outdoor cases checked across 42/90 days. Independent 3,053 daily-model / 1,022 observed-power / 874 HR-formula checks; all 20 existing tables / 1,422 originals preserved. Home/Performance checked at identical clocks; Activities unchanged.
**Findings:** 1,102/1,418 cycling rides scored; 316 unavailable. Outdoor improves 7/148 to 10/148, recent 42 days 3/6 to 6/6, 90 days 7/11 to 10/11. Fifty scores change via eligible summaries (23 newly scored; 27 replace partial power); every power candidate stays identical. Required private regression now contributes independent summary HRSS with expected daily/next-day model response. Historical outdoor gaps remain.
**Privacy/reference:** Approved original Elevate CSV unchanged and integrity-verified; 14 projections excluded. Vendor results/settings never production inputs; approved dated FTP authoritative. Private Activity cases, before/after details and screenshots stay local-only.
**Review app:** `http://127.0.0.1:8772/training-state` on the verified private copy; existing production store/server retained.
**Evidence:** [HR summary correction and behavioral validation](reports/P4-02/hr-summary-verification.md); earlier reports remain historical evidence.
**Next action:** Await HARD — Analyst Gate 1 source/code/data/browser review. No acceptance, merge, Owner Gate 2 or later phase.
