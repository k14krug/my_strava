# STATUS.md

**Product:** RideWorks.

**Completed:** Phase 1; Phase 2 historical/performance; STRAVA-004; Phase 3 dashboard.

**Current task:** P4-01 — Training-state model evaluation; **ready_for_review** at **HARD — Owner**. TASKS remains `in_progress`. Branch `task/p4-01-training-state`, [draft PR #23](https://github.com/k14krug/rideworks/pull/23).

**Controls:** Refreshed main `fb4761d`, JIT `fb5b9dd` §§14–15, Phase 4 contract `f915bc6`; `/TASK only`. Latest Analyst source review and Owner Sauce authorization addressed. No model or task acceptance.

**Research:** Retained the 66-entry Owner-approved dated FTP history and its effective-date rules. Compared exact pinned Sauce functions with strict timer and observed ≥600 s segment stress using 48 references / 1,823 controlled cases, plus all 281 actual interruptions and 23 recent complete envelopes. Short-loss correction substantially reduces omitted contribution; long gaps can fail severely. Revised DESIGN-003 proposes distinct calculated, estimated and partial 7-/42-day work/stress views. A ≤5 s / ≤1% candidate admits 47 interrupted intervals (46 FIT, one API); none establishes a newly qualifying whole-ride estimate. API calibration and pause convention remain explicit limits.

**Verification:** 310 full Python tests (25 research), 52 Node assertions; independent checks of 2,127 cases / 8,508 variants and 816 published distributions. All 20 production tables and 1,422 originals preserved. [Current evidence](reports/P4-01/verification.md). No production behavior, Performance-v2, schema/UI or FTP CSV changes.

**Next action:** Owner chooses evidence categories, gap/missingness threshold, API applicability and pause rules from revised DESIGN-003. Analyst acceptance follows that choice. Stop here: no merge, P4-02, production FTP import, Phase 5/6 or automatic continuation.
