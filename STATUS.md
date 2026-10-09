# STATUS.md

**Product:** RideWorks.

**Phase 1:** accepted / complete.

**Phase 2 — Historical context and performance history:** accepted / complete.

**STRAVA-004 — Strava activity-stream enrichment and FIT comparison:** accepted / complete.

**Phase 3 — Useful dashboard:** accepted / complete.

**Roadmap decision — 2026-10-08:** Training State moves ahead of planning.

- **Phase 4:** Training State — “Where am I now?”
- **Phase 5:** Workout intent/outcome and initial planning — “Did I accomplish today's workout, and what is tomorrow?”
- **Phase 6:** Adaptive planning — “What should change next?”

This supersedes the older Phase 4/5 order.

**Phase 4 acceptance:** `docs/PHASE_4_ACCEPTANCE.md`.

**Current task:** P4-01 — Training-state model evaluation and athlete-state inventory.

**JIT:** `docs/tasks/P4-01.md`.

**Task type:** research/design first. Do not implement a production CTL/ATL/TSB/Fitness/Fatigue model until the candidate models and historical athlete-state evidence are reviewed.

**Key gate:** Historical FTP/weight/zones/HR reference values are date-aware. Today's FTP must not be silently applied backward. Outdoor suspect power and estimated power are excluded from the first power-load baseline. Missing load evidence is not zero.

**Candidate comparison:** classic TSS/CTL/ATL/TSB-style baseline, simpler transparent recent/long workload, HR-derived fallback if reference data supports it, and separate external/context signals. Industry convention is a baseline, not the product decision.

**Current implementation task:** P4-01 ready for invocation.

**Allowed invocation:** `/TASK P4-01` or `/AUTOTASK P4-01`.

**Phase 5/6:** not started.
