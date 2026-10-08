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


**Owner correction — 2026-10-07:** PR #19 remains at HARD — Owner. Remove duplicate YTD goal top card and replace it with This Week Miles. Keep annual goal information only under Mileage Progress; add miles remaining + needed average mi/week. Weekly chart: completed bars = actual, current bar = needed weekly average going forward, overlay historical/current needed-mi/week line. Replace delayed native SVG hover with immediate miles-only tooltip. Add Avg Pwr to Recent Activities using file summary first, then current API summary fallback. Re-present HARD — Owner after correction.


**Owner correction — current-week bar (2026-10-07):** Latest Owner decision supersedes the prior mixed-bar rule. All mileage bars represent actual cycling miles. Historical bars are completed-week actuals; the current bar is actual Monday-through-today mileage and must match This Week Miles. The green line alone represents needed average miles/week going forward. Re-present HARD — Owner after this minor correction.


**Owner correction — Targeted historical summary enrichment (2026-10-08):** The eight unresolved 2026 YTD distance omissions are all outdoor Ride Activities with GPX + export evidence and established Strava IDs, but no retained known-unit distance/API summary. Owner authorized at most eight direct Strava `GET /activities/{id}` summary requests using existing `activity:read_all`, sequentially and through the existing summary allowlist. No historical list crawl, stream requests, fuzzy matching, CSV-unit guessing or GPX-derived distance. After enrichment, independently reconcile YTD mileage against the Owner-reported ~1,631 mi; explain any residual before Owner approval. Verify normal future Sync now already supplies API distance/duration fallback for newly synchronized GPX rides.
