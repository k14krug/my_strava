# STATUS.md

**Product:** RideWorks

**P1-01 — Durable single-FIT activity import:** done

**Accepted implementation:** PR #10, implementation head `5c872ea`

**Acceptance:** HARD — Analyst gate passed. The requested FIT activity-envelope correction is clean: import now requires exactly one `file_id` whose type is `activity`, with missing/duplicate regressions proving failure leaves no completed metadata, original, or staging artifact.

**Verification:** 39 tests passed (22 RideWorks + 17 research). Representative local acceptance passed with 3,621 complete power/HR records, 3,620 one-second timestamp deltas, exact original preservation, restart/idempotency, and successful/failed re-extraction behavior.

**Evidence:** `reports/P1-01/verification.md`

**Blockers:** none

**P1-02 — Single-ride analysis core:** pending; JIT not yet authored.

**Next action:** Analyst authors the deliberately narrow P1-02 JIT. Do not begin P1-02 implementation until that JIT is committed and explicitly invoked.
