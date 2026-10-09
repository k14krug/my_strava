# STATUS.md

**Product:** RideWorks.

**Completed:** Phase 1; Phase 2 historical/performance; STRAVA-004; Phase 3 dashboard; **P4-01 Training-State Model Evaluation (research/design)**.

**Phase 4:** Active — Owner approved and Analyst accepted **DESIGN-003**, P4-01 complete. [PR #23](https://github.com/k14krug/rideworks/pull/23), Analyst review `5475713826`.

**Accepted training-state direction:** Show separate 7-/42-day observed kJ and FTP-relative stress with **calculated recorded interval**, **corrected estimated FIT interval**, **partial >=600 s observed segments**, and **unavailable** evidence classes; surface missing contributors and time. For 1 Hz FIT streams only, each internal gap may be **at most 15 seconds** with **total missing <=1%**, and only when valid timing/source/timer eligibility holds. Preserve observed-only API load; no API gap imputation. Verified timer stops/restarts exclude pause time and reset NP. Full-session labels require session-boundary and calculation verification. Dated FTP/no pre-2019 backfill, original source data, outdoor-power exclusion and Performance-v2 remain unchanged.

**Research record:** 131 FIT of 281 interrupted contributor streams screen as potential interval estimates (two additional API cases excluded); one FIT candidate has corroborating boundary/timer metadata, **zero newly verified corrected whole-session calculations**. 311 local Python tests and 52 Node assertions reported passing, with independent calculation/report checks and preservation of 20 production tables/1,422 originals. Private original streams were not re-executed by the Analyst.

**Current task:** No active implementation task. **P4-02 is pending**, with later Owner-confirmed [training-state design direction](docs/design/P4-02-training-state-direction.md): prioritize consistency over fine precision; use qualified measured-power stress with the approved dated FTP history; explore practical HRSS-style outdoor fallback and an interactive 42-/7-day Fitness/Fatigue/Form chart. Owner now approves Elevate-style numerical zero contributions for rare unscored rides (while preserving unavailable evidence), prior-day Form, 42-/7-day model, zero seed, and no v1 projections/zones. Working approximate HR: rest 58 bpm, max 158 bpm; HRSS algorithm and historical HR assumptions remain open. A separately authored JIT and explicit authorization are needed before Dex starts. P4-01 research acceptance is not completion of Phase 4 or production approval.

**Phase 5/6:** Not started. Do not begin automatically.
