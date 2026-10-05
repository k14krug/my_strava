# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete — P1-01/P1-02/P1-03 done.

**Phase 2 — Historical context and performance history:** in progress.

**P2-01 — Historical Strava-export import and enrichment:** done — Analyst accepted PR #13.

**P2-02 — Scalable Activities browser:** done — Owner and Analyst accepted PR #14 on 2026-10-04.

**PR #14:** merged to `main` as `683c9880bb0b6ed1cd9569a58be61093ec2cce0e`.

**P2-02 verification:** 142 tests passed; full 1,434-Activity browser accepted with 30-row pages, source titles, search/type/date/sort, browser-local Date column/filter semantics, stable rich/thin Activity routes, and full-history restart/Chromium verification.

**P2-02 evidence:** `reports/P2-02/verification.md`, `reports/P2-02/acceptance.json`.

**Current task:** P2-03 — pending implementation.

**P2-03 JIT:** authored — `docs/tasks/P2-03.md`.

**P2-03 purpose:** build durable trusted 20-minute performance history from eligible Virtual Ride native source power using unchanged `best-average-power-v1`; exclude all outdoor Ride power and summary substitutes; add a real Performance page containing every current eligible historical result and links to contributing Activities.

**Key evidence policy:** Virtual Ride native power is eligible for this Phase 2 longitudinal purpose when a complete native 1,200-record one-second window exists. This is not a claim that the stream is measured. Outdoor Ride power remains preserved but is excluded as suspect.

**Review gates:** implementation stops first at HARD — Owner for the new Performance view, then at HARD — Analyst for final evidence/calculation acceptance.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Blockers:** none.

**Next action:** Ken may invoke `/TASK` or `/AUTOTASK` for P2-03. Do not begin P2-04 automatically.
