# STATUS.md

**Product:** RideWorks.

**Phase 1:** accepted / complete.

**Phase 2 — Historical context and performance history:** accepted / complete.

**STRAVA-004 — Strava activity-stream enrichment and FIT comparison:** accepted / complete.

**Current Performance policy:** `virtual-power-evidence-v2` / `best-average-power-v1` / 1,200 s.

**Phase 3 — Useful dashboard:** active implementation boundary.

**Acceptance contract:** `docs/PHASE_3_ACCEPTANCE.md`.

**Current task:** P3-01 — Useful dashboard and annual mileage goal.

**JIT:** `docs/tasks/P3-01.md`.

**Owner decisions:** Virtual Ride and outdoor Ride mileage both count toward the annual cycling mileage goal. Dashboard mileage uses the accepted purpose-specific distance evidence order: understood file-backed distance first, then current Strava API summary distance; unspecified CSV units are never guessed. Annual mileage is the first narrow goal; no generic goal engine.

**Planned Phase 3 subset:** Home dashboard at `/`, Activities at `/activities`, annual mileage goal setting, YTD goal/pace, last-7-day mileage, recent cycling Activities, current 42-day best/latest eligible 20-minute result, compact mileage/Performance views and deterministic explainable insights.

**Deferred:** Current FTP history, Fitness Score/Trend, Training Load, Next Workout/Plan, training-state recommendations, adaptive planning, full arbitrary-duration power curve, AI surfaces.

**Current implementation task:** P3-01 is ready for invocation.

**Allowed invocation:** `/TASK P3-01` or `/AUTOTASK P3-01`.

**Phase 4:** not started.
