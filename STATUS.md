# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete.

**Phase 2 — Historical context and performance history:** in progress.

**P2-01 — Historical Strava-export import and enrichment:** done.

**P2-02 — Scalable Activities browser:** done.

**P2-03 — Trusted 20-minute Performance history:** done — Owner and Analyst accepted PR #15 on 2026-10-05.

**PR #15:** merged to `main` as `4f1a58d39177887e965ddd1a74db95c62c17e0b0`.

**P2-03 verification:** 170 full / 28 focused tests passed. Full-history accounting: 1,434 Activities / 1,264 Virtual Ride candidates / 1,022 eligible trusted best-20 results; all eligible results independently verified exactly. Outdoor/non-cycling power excluded; rebuild/restart/idempotence and Chromium acceptance passed. Final Performance UI uses one Range/View surface with Rolling 42-day / Monthly best / Yearly best and Owner-approved line-chart presentation.

**P2-03 evidence:** `reports/P2-03/verification.md`, `reports/P2-03/acceptance.json`.

**Current task:** P2-04 — pending implementation.

**P2-04 JIT:** authored — `docs/tasks/P2-04.md`.

**P2-04 purpose:** add neutral prior-six-week context to eligible Activity Review: current trusted best-20 versus the highest eligible raw best-20 in the exact prior `(t - 42 days, t)` interval, excluding the current Activity.

**Data rule:** P2-04 consumes the accepted persisted RideWorks/P2-03 history. It must not reopen/re-import the historical Strava archive, rebuild the durable source store, or automatically rebuild Performance merely to render Activity Review.

**Review gates:** implementation stops first at HARD — Owner for Activity Review usability, then at HARD — Analyst for final interval/eligibility/data-access acceptance.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Blockers:** none.

**Next action:** Ken may invoke `/TASK` or `/AUTOTASK` for P2-04. Do not begin P2-05 automatically.
