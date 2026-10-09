# STATUS.md

**Product:** RideWorks.

**Completed:** Phase 1; Phase 2 historical/performance; STRAVA-004; Phase 3 dashboard.

**Roadmap:** Phase 4 Training State → Phase 5 workout intent/outcome and initial planning → Phase 6 adaptive planning. Phase 5/6 not started.

**Current task:** P4-01 — Training-state model evaluation / athlete-state inventory; **in_progress**, continuing existing draft [PR #23](https://github.com/k14krug/rideworks/pull/23), branch `task/p4-01-training-state`.

**JIT:** `docs/tasks/P4-01.md` §§14–15. **Allowed Invocation: `/TASK only`**; no `/AUTOTASK` or automatic cross-gate continuation. Acceptance: `docs/PHASE_4_ACCEPTANCE.md`.

**Retained research:** 66 Owner-approved date-effective historical Strava FTP entries are publicly committed in PR #23 (`data/athlete/strava_ftp_history.csv`); earliest is 2019-07-18, no earlier backfill. New FTP intersects 878/1,028 Performance-v2 eligible power rides; 281 have interrupted recordings recoverable as observed segments. Prior P4-01 strict/full-timer evidence and 303 passing tests are research, not production acceptance.

**New Owner direction — 2026-10-09:** Run a **bounded Sauce for Strava comparison** before choosing a final workload/stress model. Use Sauce open source at `4b6d4f42bf` as an engineering reference; compare active-time/gap-corrected estimates with RideWorks observed-only 600-second segments and strict full-timer stress. Inject reproducible dropout into suitable complete-reference rides, assess numerical error and coverage, then compare real interrupted rides where truth is unknown. Original sources, trusted streams, outdoor power exclusion and Performance-v2 remain unchanged. Document imputation and gaps explicitly, not as measured watts. JIT §15 and latest PR #23 comments control the experiment.

**Owner-approved P4-01 design — 2026-10-09:** Owner approved separate 7-/42-day observed work and stress with calculated, corrected-estimate, partial segment and unavailable evidence categories; **FIT-only** interior gaps <=15 s each and <=1% of the recorded span; observed-only API load eligible without API gap reconstruction; explicit FIT timer stop/restart boundaries split calculations and reset NP. This supersedes the draft 5-second recommendation. No automatic full-session claims, no missing-to-zero and no policy change to outdoor power/Performance-v2. See controlling JIT §16 and Phase 4 acceptance §8.2.

**Next action:** Dex continues existing draft PR #23 with `/TASK P4-01`: revise DESIGN-003 and verification to match the selected model, validate/report FIT-only 15-second eligible count, confirm pause/fallback rules and rerun checks. Stop at **HARD — Analyst** for acceptance. P4-01 remains in progress; **no merge, P4-02 production work, Phase 5/6, or other automatic next task**.
