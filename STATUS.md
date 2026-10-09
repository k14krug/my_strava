# STATUS.md

**Product:** RideWorks.

**Completed:** Phase 1; Phase 2 historical/performance; STRAVA-004; Phase 3 dashboard.

**Roadmap:** Phase 4 Training State → Phase 5 workout intent/outcome and initial planning → Phase 6 adaptive planning. Phase 5/6 not started.

**Current task:** P4-01 — Training-state model evaluation / athlete-state inventory; **in_progress**, continuing existing draft [PR #23](https://github.com/k14krug/rideworks/pull/23), branch `task/p4-01-training-state`.

**JIT:** `docs/tasks/P4-01.md` §§14–15. **Allowed Invocation: `/TASK only`**; no `/AUTOTASK` or automatic cross-gate continuation. Acceptance: `docs/PHASE_4_ACCEPTANCE.md`.

**Retained research:** 66 Owner-approved date-effective historical Strava FTP entries are publicly committed in PR #23 (`data/athlete/strava_ftp_history.csv`); earliest is 2019-07-18, no earlier backfill. New FTP intersects 878/1,028 Performance-v2 eligible power rides; 281 have interrupted recordings recoverable as observed segments. Prior P4-01 strict/full-timer evidence and 303 passing tests are research, not production acceptance.

**New Owner direction — 2026-10-09:** Run a **bounded Sauce for Strava comparison** before choosing a final workload/stress model. Use Sauce open source at `4b6d4f42bf` as an engineering reference; compare active-time/gap-corrected estimates with RideWorks observed-only 600-second segments and strict full-timer stress. Inject reproducible dropout into suitable complete-reference rides, assess numerical error and coverage, then compare real interrupted rides where truth is unknown. Original sources, trusted streams, outdoor power exclusion and Performance-v2 remain unchanged. Document imputation and gaps explicitly, not as measured watts. JIT §15 and latest PR #23 comments control the experiment.

**Next action:** Dex continues `/TASK P4-01`, runs local/disposable comparisons, updates DESIGN-003 and verification/tests in PR #23, then stops at **HARD — Owner** with evidence and model/recording-rule alternatives. **No Owner model acceptance, Analyst acceptance, P4-02, production FTP persistence, schema/UI change, or Phase 5/6 work yet.**
