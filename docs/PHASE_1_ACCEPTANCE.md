# Phase 1 Acceptance — Useful Single-Ride Review

**Status:** approved planning contract for Phase 1  
**Controlling source:** `docs/PRODUCT_REQUIREMENTS.md`  
**Supporting decisions:** `docs/design/DESIGN-001.md`, `docs/design/DESIGN-002.md`

## 1. Phase goal

Phase 1 must produce the first genuinely useful rider-facing capability:

> Import one real representative ride and review it well enough that the rider can understand how the ride went without opening Strava.

Phase 1 is not complete merely because a file can be parsed or stored.

The phase deliberately proves one narrow end-to-end experience before expanding to historical comparison, dashboard, workout-intent analysis, or planning.

## 2. Requirements covered

Phase 1 directly exercises:

- PR-002 — Product-first implementation
- PR-003 — Durable application-owned history
- PR-004 through PR-010 — evidence/interpretation separation, originals, provenance, historical context boundary, reproducibility, competing evidence, explainability
- PR-012 — visible missing data
- ACT-001, ACT-004 through ACT-007
- REV-001 through REV-004
- REV-009 and REV-010
- DATA-001 through DATA-006 where they are relevant to this slice
- Phase 1 outcomes in `docs/PRODUCT_REQUIREMENTS.md`

It does not need to satisfy Phase 2+ capabilities.

## 3. Representative ride

The primary Phase 1 acceptance activity is the existing Strava-export candidate:

- **Strava activity ID:** `20383280617`
- **Export artifact token:** `activities/21538875902.fit.gz`
- **Date:** 2026-09-29
- **Observed source type:** FIT
- **Observed activity label in export research:** Virtual Ride
- **Observed source evidence:** 3,621 record points with power, heart rate, cadence, position/altitude-related fields, and 1-second median timing; no large gaps were found in STRAVA-002.

This activity is intentionally chosen because it is recent, detailed, long enough for a 20-minute effort calculation, and contains the core signals needed for a useful first review.

The raw source file remains local-only. Dex may require Ken to provide or confirm the local export path during implementation.

### Why only one primary case in Phase 1

Phase 1 is a product slice, not a coverage test.

It does **not** need to prove:

- GPX or TCX import;
- CSV-only activities;
- later source enrichment;
- multiple simultaneous source artifacts;
- missing-power outdoor rides;
- estimated power;
- historical comparison.

Those remain important requirements and are deferred to later phases/tasks rather than being smuggled into the first slice.

A small synthetic fixture may be committed for repeatable automated tests if the JIT explicitly authorizes it and it contains no unnecessary personal/location data.

## 4. Minimum activity-review experience

For the representative activity, the rider must be able to open an activity-review page/view that contains the following.

### 4.1 Activity identity/header

Show enough information to identify the ride:

- activity date/time;
- cycling/activity type available from the imported source;
- durable application-owned Activity identity.

A polished naming system is not required in Phase 1.

### 4.2 Source-backed ride summary

Show the following when the FIT source supplies the relevant summary evidence:

- elapsed duration / timer duration as represented by the source;
- distance;
- total ascent/elevation gain when supplied;
- average power;
- maximum power;
- average heart rate;
- maximum heart rate;
- average cadence.

For Phase 1, these summary values should remain explicitly attributable to the FIT source/session evidence.

Do not create a general canonical-summary policy merely to fill a card.

If a required source summary is unavailable, display it as unavailable rather than silently inventing a substitute.

### 4.3 Native time-series review

Show at minimum:

- power over time;
- heart rate over time.

The chart must preserve native timing relationships. Import or presentation must not silently regularize, smooth, interpolate, or manufacture samples.

Phase 1 does not require cadence, elevation, speed, map, or interval overlays in the chart.

### 4.4 Best 20-minute power

Calculate and display the activity's best 20-minute average power from the source record-power evidence.

For the primary representative ride, STRAVA-002 found approximately 1-second native timing with no large gaps, so Phase 1 does not need to solve the general irregular-sampling/gap-policy problem.

The calculation must:

- use source record power rather than a vendor summary;
- be implemented as an application derivation;
- be independently testable/reproducible;
- retain enough method/version/source context to distinguish it from source-supplied summaries.

General interpolation and gap semantics remain deferred until a case actually requires them.

### 4.5 Inspectability

The normal page should stay reasonably clean, but there must be a practical way to inspect at least:

- preserved source artifact identity/metadata;
- which displayed summary values came from the FIT source;
- that best 20-minute power was application-calculated;
- source stream availability;
- parser/extraction version when material.

This may initially be a simple details section rather than polished provenance UI.

### 4.6 Visual/layout direction

The supplied **Strava Activity screen** mockup is the preferred visual reference for P1-03 and for later growth of the activity-review experience.

Phase 1 should preserve the mockup's overall composition even though several later capabilities are intentionally absent:

- persistent left navigation and application identity;
- strong ride header with date/type/source context;
- a row of prominent ride-metric cards;
- a large central **Ride Power & Heart Rate** chart;
- supporting analysis below the main chart, with best 20-minute power represented in a compact performance panel;
- a right-hand **Ride Summary**-style panel;
- provenance/details kept secondary so the normal review remains clean.

Phase 1 must **not** implement fake placeholders for later mockup features such as AI Insights, Compare to Recent, Next Workout, Zone Breakdown, or Laps/Intervals. Those areas may be absent or the remaining panels may naturally occupy the available space until the underlying capability is implemented.

Exact pixel matching, colors, typography, and spacing are not frozen. The acceptance concern is recognizable structure, hierarchy, density, and visual character.

A materially different generic developer/admin page does not satisfy the intended Phase 1 product direction merely because it contains the required data.

## 5. Narrow Phase 1 presentation policy

Phase 1 deliberately avoids solving global evidence selection.

For the representative FIT activity:

- FIT session/source summaries are the presentation source for the summary fields listed above when present;
- native FIT record power and heart-rate streams drive the Phase 1 charts;
- application-calculated best 20-minute power is shown as a derivation;
- absent values remain unavailable;
- no Strava CSV/API value is silently substituted into the review.

This is a Phase 1 policy for one source-rich activity, not a universal ranking rule.

## 6. Explicit Phase 1 non-goals

Phase 1 does not require:

- dashboard;
- historical 20-minute trend;
- comparison with another ride;
- goals tracking;
- planned-workout representation;
- "harder than intended" interpretation;
- training load, fatigue, recovery, or fitness score;
- normalized-power-style metrics;
- zones;
- interval detection;
- map;
- Strava synchronization;
- Strava API integration;
- bulk historical import;
- GPX/TCX production support;
- outdoor estimated-power reconstruction;
- adaptive planning;
- AI-generated ride interpretation;
- final production architecture for later phases.

These may be reconsidered only if implementation proves one is genuinely necessary to make the Phase 1 acceptance experience work.

## 7. Phase 1 acceptance contract

Phase 1 is accepted only when all of the following are true.

### Data durability and identity

1. Importing the representative FIT creates a durable application-owned Activity identity.
2. The source artifact is preserved unchanged in application-managed durable storage or an explicitly defined equivalent durable location.
3. Artifact integrity can be verified, such as by content hash.
4. The FIT Source remains explicitly associated with the Activity.
5. Typed normalized evidence can be rebuilt from the preserved original without reacquiring the file.
6. Native source timing and gaps are not silently altered during import.

### Review capability

7. The rider can open the imported activity in the application.
8. The activity header identifies the ride sufficiently for Phase 1.
9. The required available summary metrics are visible.
10. Power and heart-rate time-series are reviewable.
11. Best 20-minute power is displayed when the source data permits it.
12. The page is usable without opening Strava to understand the basic ride outcome.

### Evidence and correctness

13. Source-supplied summaries remain distinguishable from application-calculated metrics.
14. The 20-minute result can be reproduced by an independent verification calculation within a documented tolerance.
15. Missing evidence is displayed as unavailable rather than silently fabricated.
16. Relevant source/provenance details can be inspected.
17. Re-import/re-extraction does not silently create a duplicate Activity for the same established source artifact.
18. Automated tests cover meaningful reusable behavior and the representative local-data acceptance procedure is documented and run.

### Product acceptance

19. Ken reviews the Phase 1 activity page using the representative ride and agrees that it is useful enough to answer the narrow question: **"How did this ride go?"**
20. The page recognizably follows the approved Strava Activity screen mockup's overall layout and visual hierarchy, while omitting capabilities not yet implemented.
21. Any required Owner-facing visual/usability changes from that review are completed before Phase 1 is declared accepted.

## 8. Planned Phase 1 task sequence

### P1-01 — Durable single-FIT activity import

**Outcome:** The representative FIT can enter the future application as a durable Activity + Source with preserved original artifact and typed normalized evidence.

Primary requirements: ACT-001, ACT-004, ACT-005, ACT-006, DATA-001, DATA-002, DATA-006.

Expected implementation concerns may include the minimum physical storage/application boundary required by this slice. Choices must remain simple and must not pretend to settle later architecture that Phase 1 does not need.

### P1-02 — Single-ride analysis core

**Outcome:** The imported ride exposes the Phase 1 source-backed summary, native power/HR streams, and a reproducible application-derived best 20-minute power.

Primary requirements: ACT-007, REV-001, REV-002, REV-003, REV-009, DATA-003, DATA-004.

This task must not expand into zones, normalized power, training load, interval detection, or broad power-duration modeling.

### P1-03 — Activity review experience and Phase 1 acceptance

**Outcome:** A rider-facing activity-review page/view combines the trusted Phase 1 evidence and analysis into a useful post-ride experience, with enough inspectability to understand where values came from.

Primary requirements: REV-001 through REV-004 as applicable to one ride, REV-009, REV-010, PR-002, PR-010, Phase 1 product acceptance.

This task includes the Owner visual/usability review boundary. It must stop for that review before Phase 1 is declared accepted.

## 9. Task-control intent

Detailed JIT briefs are still authored one task at a time.

The task list does not itself authorize implementation.

For each task the Analyst will declare:

- `Allowed Invocation`;
- any `SOFT`, `HARD — Analyst`, or `HARD — Owner` gates;
- exact local-data procedure;
- verification and acceptance details.

The likely use of `/AUTOTASK` is for bounded implementation work with clearly preauthorized soft gates. Product, data-policy, or architecture questions that materially exceed this contract remain hard review boundaries.

## 10. What Phase 1 intentionally teaches us

Phase 1 should answer practical questions needed before later phases, including:

- whether the source-centered model is simple enough in real application code;
- what minimum durable stream representation works well for activity review;
- what the activity page actually needs once real source evidence is displayed;
- which calculations deserve persistence versus on-demand calculation;
- which physical implementation choices are worth keeping.

Those lessons may refine later implementation choices, but they must not retroactively weaken the controlling provenance and durability requirements.
