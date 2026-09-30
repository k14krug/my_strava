# DESIGN-001 — Durable Activity and Provenance Model

**Status:** accepted design decision  
**Scope:** conceptual product/data model; not a database schema or importer specification

## Purpose

Define the durable conceptual model for historical activities, source evidence, provenance, historical rider/equipment state, derived interpretations, and activity identity.

This decision is grounded in the project framework, the outdoor estimated-power design context, and STRAVA-001 through STRAVA-003. It intentionally stops before choosing database tables, storage engines, parser architecture, or importer implementation.

## Evidence that shaped the decision

STRAVA-001 through STRAVA-003 established that this history is heterogeneous: 1,434 Strava CSV rows exist; 1,421 have exact referenced FIT/TCX/GPX files and 13 are CSV-only. Source point power, source summary power, and Strava CSV power metadata overlap without proven semantic or provenance equivalence. Some source and CSV summaries differ. Field presence does not establish measured provenance. Older XML sources contain useful evidence, recording behavior varies, and unavailable source streams on CSV-only activities are unknown rather than proven absent.

The outdoor estimated-power design additionally requires preserving originals, distinguishing estimated from measured power, reproducible derivations, date-aware FTP/weight/bike state, and explicit uncertainty.

## Settled conceptual model

### Activity

An **Activity** is the application's durable identity for an exercise/activity event. It is not defined by Strava, a FIT file, or any single source. Multiple sources may describe or enrich one Activity.

### Source

A **Source** is information received from outside an application derivation: original FIT/TCX/GPX files, Strava bulk-export records, Strava API records, manual facts/corrections, and future source systems.

Original source artifacts are preserved unchanged whenever available. Exact-file identity can identify duplicate artifacts but is not Activity identity.

### Observation

An **Observation** is evidence supplied by or extracted from a Source: streams, source summaries, Strava metadata, extension values, RPE, historical FTP, and similar facts.

Observations retain source provenance. Conflicting observations may coexist. New sources do not silently overwrite earlier evidence. Field presence alone never establishes a stronger epistemic status; for example, a FIT power stream is source-power evidence but is not automatically classified as measured.

### Historical state

**Historical State** is time-aware rider, equipment, and contextual evidence used to interpret activities: FTP, weight, zone definitions, bike identity/configuration, calibration state, and similar facts.

Historical state has provenance. It may be represented as point-in-time observations or as intervals/configurations when evidence supports an interval. Exact validity intervals must not be invented.

Today's state must not silently be applied backward. An analysis resolves the state applicable to an activity and records the resolution method as part of its derivation. Durable equipment identity is separate from changing equipment configuration.

### Derived interpretation

A **Derived Interpretation** is information calculated or concluded by the application from observations and, when needed, historical state.

Material derivations retain enough information to explain and reproduce them: input evidence, historical context, method/version, material assumptions, uncertainty/confidence, and relevant missing inputs.

Derived information never silently becomes original evidence. Important algorithms remain replaceable and recalculable.

## Provenance policy — settled

The provenance policy is a project decision, not an open design question.

1. Preserve original source artifacts unchanged whenever available.
2. Keep information attributable to the source that supplied it.
3. Keep source-supplied and application-derived information distinct.
4. Do not silently equate measured, supplied/known, calculated, estimated, inferred, and unknown status.
5. Field presence alone does not establish measurement provenance.
6. Preserve competing/overlapping source values rather than silently replacing them.
7. Material derivations identify inputs, method/version, and material assumptions sufficiently for explanation and recalculation.
8. Historical rider/equipment state carries provenance and time context.
9. Missing, unknown, observed-absent, and not-applicable are distinct.
10. Derived artifacts remain related to, but distinct from, originals.
11. There is no universal source ranking; each analysis chooses appropriate evidence and should be able to explain the choice.

Storage granularity is deferred. If an entire stream shares one source, a future schema may store provenance once at stream level rather than redundantly per sample. That is an implementation choice, not an unresolved provenance policy.

## Missing and unavailable information

The model distinguishes at least:

- **unknown/unavailable:** the application does not know whether the fact existed or what its value was
- **observed absent:** an applicable inspected source was observed not to contain it
- **not applicable:** the concept genuinely does not apply

A CSV-only activity therefore has unknown/unavailable source-file streams, not proof that those signals were never recorded.

## Subjective information

RPE, fatigue, sleep, soreness, motivation, workout notes, and contextual statements use the same observation/provenance model. They may inform analysis without silently becoming objective measurements.

## Reproducibly derived state

Explicitly supplied historical zones are retained as observations. Zones calculated from FTP and a zone-system definition remain identifiable as derivations from that FTP plus the method/version. The general rule is: preserve observations; keep reproducibly calculated values identifiable as derivations.

## Activity identity and reconciliation

Every Activity has an application-owned durable identity. Strava IDs and other external IDs are associations, not the application's primary identity.

Sources are associated conservatively in this order:

1. **Explicit external identity — automatic.** Matching trustworthy external IDs establish association.
2. **Established source relationship — automatic.** Explicit relationships supplied by a source establish association; the current Strava CSV-to-file references are an example.
3. **Strong multi-factor match — inferred.** Sources lacking explicit identity may use independent evidence such as start time, duration, type, distance, device clues, and stream timing. The inferred basis is retained.
4. **Ambiguous match — unresolved.** Do not silently merge; allow later/manual resolution.
5. **No credible match — new Activity.** Strava identity is not required.

The association basis is retained: explicit external ID, explicit source relationship, inferred multi-factor match, or manual confirmation/correction. Associations are correctable.

Content hashes answer whether the exact same artifact has already been ingested; they do not establish that different artifacts describe the same Activity.

Temporal/spatial overlap alone does not prove identity. Simultaneous device recordings may describe one Activity, while one service may split a session another records as one. Ambiguous overlap should remain unresolved or explicitly related rather than forced into a merge.

## Evidence selection for analysis

The application preserves available evidence rather than maintaining one universal canonical value for every concept.

An analysis chooses the best-supported evidence for its purpose. Low-confidence reconstructed power, for example, might support approximate workload context while being excluded from peak-power records. Source and recalculated summaries may coexist without assumed semantic equivalence.

Selection policy belongs to the analysis and is explainable/versionable when material.

## Representative cases

### Modern Virtual Ride

One Activity may associate Strava CSV and FIT sources. FIT streams/summaries and Strava metadata coexist. Power presence does not automatically assert measured provenance.

### Outdoor Ride with GPS/HR but no source point power

Source GPS/altitude/HR and separate Strava CSV power metadata may coexist. Later reconstructed power is an estimated application derivation with explicit inputs, method/version, assumptions, and uncertainty.

### Older GPX/TCX activity

The same Activity model applies. XML extensions and summaries retain source context; the activity is not a second-class legacy type merely because it is not FIT.

### CSV-only activity

The Activity remains durable history with Strava CSV evidence. Source-file streams are unknown/unavailable rather than zero or proven never recorded.

### Later supplied original file

A later FIT/TCX/GPX that credibly matches an existing CSV-only Activity enriches it rather than creating a duplicate; the association basis is retained.

## Decisions intentionally deferred

DESIGN-001 does not choose the database engine, schema, framework, provenance storage granularity, stream storage representation, parser architecture, matching thresholds/scoring algorithm, provenance UI, FTP/state interpolation algorithm, exact power-source classification rules, estimated-power algorithm, training-state/planning algorithms, or Strava synchronization implementation.

Those choices must respect this conceptual model and should be made only when the corresponding task requires them.

## Requirements for the next design/implementation phase

A future storage/import design must demonstrate that it can:

- create application-owned Activities
- attach multiple Sources to one Activity
- preserve originals and source associations
- retain conflicting observations without destructive overwrite
- represent historical state without applying today's state backward
- keep derivations reproducible and distinct from source evidence
- represent unknown versus observed-absent information
- reconcile sources conservatively and leave ambiguity unresolved
- support manual correction of identity/association decisions
- add later sources to an existing Activity without losing earlier provenance

The future schema is judged against these requirements; it does not redefine them.

## Decision boundary

DESIGN-001 establishes the durable conceptual model and provenance/identity policy.

It does not authorize implementation by itself. The next design task should translate this model into the simplest practical storage and import design for a private single-rider application, using the representative cases above as tests.
