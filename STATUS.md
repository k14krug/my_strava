# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete.

**Phase 2 — Historical context and performance history:** in progress.

**P2-01:** done.  
**P2-02:** done.  
**P2-03:** done.  
**P2-04:** done — Owner and Analyst accepted PR #16; merged as `16ef375434700ab7d2b5fb3a5c2cae000e049c12`.

**Current task:** P2-05 — pending implementation.

**P2-05 JIT:** authored — `docs/tasks/P2-05.md`.

**P2-05 purpose:** add a normal user-invoked, forward-looking Strava synchronization path for post-export activity metadata and conservative Activity enrichment/creation, without historical API harvesting.

**Authoritative Strava review:** completed 2026-10-05 against current OAuth, activity-list, rate-limit, webhook, API Agreement and API Policy documentation.

**P2-05 key boundary:** use `activity:read_all` only; user-invoked sync; `GET /athlete/activities`; narrow export-boundary/recent overlap; no API streams/social/segments; no polling/background cloud service; no automatic Performance rebuild; secrets/tokens remain local.

**Known policy tension:** current Strava policy documents seven-day caching/deletion obligations. RideWorks retains the Owner's previously explicit decision to keep useful API-derived evidence in this private durable history while documenting that policy risk and without concealment/evasion.

**Review gates:** Gate 1 HARD — Owner after a real local connect/sync against a disposable accepted-history copy; Gate 2 HARD — Analyst / Phase 2 acceptance after Owner approval.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Blockers:** none.

**Next action:** Ken may invoke `/TASK` or `/AUTOTASK` for P2-05. Do not begin Phase 3 automatically.
