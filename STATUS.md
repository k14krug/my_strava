# STATUS.md

**Product:** RideWorks

**Phase 1 — Useful single-ride review:** accepted / complete

**P1-01:** done — accepted on PR #10

**P1-02:** done — accepted on PR #11

**P1-03:** done — accepted at Gate 2 on PR #12

**Phase 2 — Historical context and performance history:** planned; implementation not started

**Phase 2 acceptance:** authored — `docs/PHASE_2_ACCEPTANCE.md`

**P2-01 — Historical Strava-export import and enrichment:** pending

**P2-01 JIT:** authored — `docs/tasks/P2-01.md`

**Allowed invocation:** `/TASK` or `/AUTOTASK`

**Phase 2 settled decisions:** import all 1,434 known activities; preserve real source titles with provenance; scale the Activities browser with pagination/search/filter/sort; trusted best-20 history initially uses eligible Virtual Ride native source power under `best-average-power-v1`; outdoor power is excluded from that trusted trend as suspect; recent context is current best-20 versus prior 42-day best; manual pairwise ride comparison is not required; finish Phase 2 with normal forward-looking Strava synchronization for new activities.

**P2-01 representative enrichment proof:** seed the accepted Phase 1 representative FIT, then bulk-import the export and prove the same RideWorks Activity is enriched with Strava-export evidence rather than duplicated.

**Blockers:** none.

**Next action:** Ken may invoke `/TASK` or `/AUTOTASK` for P2-01. Do not begin P2-02 automatically after P2-01 implementation/review, and do not begin Phase 3 automatically.
