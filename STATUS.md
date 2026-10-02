# STATUS.md

**Product:** RideWorks

**P1-01 — Durable single-FIT activity import:** done

**Accepted implementation:** PR #10, implementation head `5c872ea`

**P1-01 verification:** 39 tests passed (22 RideWorks + 17 research). Representative local acceptance passed with 3,621 complete power/HR records, 3,620 one-second timestamp deltas, exact original preservation, restart/idempotency, and successful/failed re-extraction behavior.

**P1-02 — Single-ride analysis core:** pending

**P1-02 JIT:** authored — `docs/tasks/P1-02.md`

**Allowed invocation:** `/TASK or /AUTOTASK`

**P1-02 scope:** expose the accepted FIT source summary/native power-HR evidence and calculate one transparent application derivation: best 20-minute average power using complete 1,200-sample one-second windows. No UI, zones, normalized power, training load, interval detection, broad power curves, or analysis-persistence framework.

**Implementation decision:** calculate best-20 on demand from the current P1-01 extraction and return explicit Source/extraction/method context; do not add durable analytical-result persistence in this slice.

**Blockers:** none

**Next action:** Ken may invoke `/TASK` or `/AUTOTASK` for P1-02. Do not begin P1-03 automatically.
