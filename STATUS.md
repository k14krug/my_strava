# STATUS.md

## Current state

**Product:** RideWorks

**Repository:** `k14krug/my_strava` remains the RideWorks development repository. It is retained for its project documents, research evidence, reports, mockups, reviews, and useful diagnostics. The retired Strava application code imposes no compatibility or architecture constraints and may be removed during authorized RideWorks work.

**Workflow bootstrap:** done

**STRAVA-001:** done

**STRAVA-002:** done

**STRAVA-003:** done

**DESIGN-001:** done — Durable activity and provenance model

**DESIGN-002:** done — Source-centered storage and import representation

**Product requirements:** approved — `docs/PRODUCT_REQUIREMENTS.md`

**Phase 1 definition:** done — `docs/PHASE_1_ACCEPTANCE.md`

**Independent readiness reviews:** complete — `docs/reviews/2026-10-02-phase-1-readiness-astra.md`, `docs/reviews/2026-10-02-phase-1-readiness-astra-2.md`

**Readiness corrections:** applied — repository-controlled mockups, illustrative-content clarification, retired legacy `.clinerules`, corrected Phase 1 traceability/timing/calculation boundaries, clarified DESIGN-002 Phase 1 boundary, UI-shell omission rule, and explicit zero legacy-code compatibility obligation.

**Approved UI references:** `docs/mockups/activity-review.png`, `docs/mockups/dashboard.png`

**Implementation authorized:** no

**Blockers:** none

## Next action

Author the Analyst JIT for **P1-01 — Durable single-FIT activity import**. It must establish the clean RideWorks application boundary and incorporate the accepted Astra readiness findings: durable original storage, stable private runtime-data location, input packaging, repeat-import/re-extraction and failure behavior, typed extraction and availability/provenance distinctions, native timing, parser/extraction identity, retrieval for P1-02, legacy-code exclusion/removal discretion, verification, and stop conditions.

Do not begin P1-01 implementation until that JIT is committed. Do not start P1-02 or P1-03 automatically.
