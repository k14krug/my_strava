# DESIGN-002 — Source-Centered Storage and Import Representation

**Status:** accepted design decision  
**Scope:** logical storage/import representation and durability rules; not a physical database schema or importer implementation

## Purpose

Translate DESIGN-001 into the simplest practical durable representation for this private single-rider application.

This decision defines what the application must preserve, what may be normalized, where provenance naturally lives, how native time-series evidence is handled, and how source summaries differ from application-derived analytical metrics. It intentionally stops before selecting SQL tables, stream encodings, parser modules, indexes, caches, or a database engine.

## Requirements used

- `docs/design/DESIGN-001.md`
- STRAVA-001 through STRAVA-003 findings
- Project principles requiring durable source history, explicit provenance, historical athlete/equipment state, reproducible derivations, and visible uncertainty/missingness

## Decision summary

Use a **typed, source-centered durable representation**:

```text
Activity identity
    |
    +-- Sources and immutable original artifacts
    |       |
    |       +-- typed normalized source evidence
    |       +-- native source timing/streams
    |
    +-------------------------+
                              |
Historical state/context      |
(independent, time-aware)     |
              |               |
              +----> versioned derived analysis
```

Activity owns durable identity. Sources own imported evidence. **Historical state is independent and time-aware; it is not owned by the Activity merely because an analysis resolves historical state for that Activity's date.** Derived analysis explicitly consumes source evidence and resolved historical context.

Do not create a universal observation/EAV store merely because DESIGN-001 uses “Observation” as conceptual vocabulary. Do not collapse competing evidence into canonical Activity fields.

## Activity representation

Activity remains deliberately small. It represents the application's durable exercise/event identity and lifecycle, not a container of supposedly authoritative cycling summaries.

Common metrics such as distance, elevation gain, moving time, average heart rate, average power, calories, and similar values must not automatically become provenance-free canonical Activity fields.

When multiple sources or derivations provide competing values, those values coexist and an analysis or presentation policy selects appropriate evidence for its purpose.

## Source representation

Source is first-class and associated with an Activity.

Sources include, as applicable:

- original FIT/TCX/GPX artifacts
- Strava bulk-export records/artifacts
- Strava API evidence
- manual supplied information/corrections
- future source systems

The association retains its basis as established by DESIGN-001: explicit external identity, established source relationship, inferred multi-factor match, or manual confirmation/correction.

Exact artifact hashes support artifact identity/deduplication, not Activity identity.

## Preserve original artifacts and normalized extraction

For file-based imports, preserve both:

1. **the original artifact**, unchanged and durable; and
2. **a normalized typed extraction** of evidence the application understands.

The original artifact is immutable evidence. It allows future reparsing, investigation of fields not initially understood, and correction of importer/parser defects without reacquiring the source.

The normalized extraction is the application's usable representation and is attributable to its Source. It is rebuildable from the preserved artifact.

Parsing/extraction methods are versioned when a change can materially affect extracted meaning or values.

A generic complete parser dump is not required as a permanent intermediate archive when the preserved original artifact already provides recoverability. Cheap opaque source metadata may be retained when useful, but “serialize everything the parser saw forever” is not a design rule.

Compression/container details are source-artifact metadata rather than logical activity semantics. Preserve the artifact as received while identifying its parseable content format.

The same principle extends beyond FIT/TCX/GPX: preserve useful source context for bulk-export and API evidence rather than immediately reducing it to provenance-free Activity values.

## Typed source evidence rather than universal EAV

Use typed representations for evidence whose semantics are understood: source metadata, session/lap summaries, device information, signal streams, and other useful source-specific structures.

A source naturally provides a provenance boundary. A FIT heart-rate stream belonging to FIT Source X already establishes its source provenance; provenance need not be redundantly attached to every sample when it is uniform across the stream.

Source-specific fields that only appear semantically equivalent must not be collapsed merely because names or units look similar. For example, Strava CSV power metadata, FIT session power summaries, FIT record power, and GPX extension power-like summaries remain distinct evidence channels until their semantics justify stronger equivalence.

## Native timing and signal preservation

Import normalizes representation, not evidence.

Preserve source samples and timing substantially as supplied by the source. Import may decode timestamps, units, and source encodings into usable normalized types, but must not silently:

- interpolate missing samples
- regularize samples onto a fixed interval
- smooth signals
- remove meaningful gaps
- manufacture samples to align signals
- discard duplicate timestamps merely to create a cleaner timeline

STRAVA-003 found duplicate timestamps and substantial gaps in otherwise parseable source files. These are recording characteristics and must not be silently repaired during durable import.

Logical signal streams may be heart rate, power, cadence, position, altitude, speed, distance, temperature, and similar signals. This logical separation does not require one physical database structure per signal; physical co-storage is allowed if signal provenance and availability remain clear.

Preserve meaningful source timing structure such as session/lap boundaries, timer/event information, and elapsed/timer distinctions when available.

## Alignment, interpolation, smoothing, and resampling

Alignment and signal transformation are derivations, not import mutations.

When an analysis needs a common timeline, its method must define the relevant choices, such as target interval, interpolation policy, gap limits, smoothing, and signal-specific handling.

There is no universal application rule that all missing samples are interpolated. Appropriate handling depends on the signal and analytical purpose.

Reusable aligned/transformed series may themselves be materialized derived results when useful, but their source streams and transformation method remain identifiable.

## Source summaries and recalculated summaries

Source-supplied summaries are preserved as source evidence.

If the application independently calculates a similar metric from source streams, the result is a derivation. It does not overwrite the source summary.

For example, a FIT session average heart rate and an application-calculated average heart rate may coexist even when they differ. The difference can reveal boundary or calculation semantics and must not be silently resolved during ingestion.

## Derived analytical metrics

Persistence is driven primarily by **semantic identity and longitudinal usefulness**, not merely computational expense.

Three broad categories apply:

1. **Source summaries:** preserve as source evidence.
2. **Analysis metrics:** persist when they form useful durable analytical history or are repeatedly consumed longitudinally; retain method/version and material dependencies.
3. **Presentation-only aggregates:** calculate on demand when cheap, unambiguous, and not part of durable longitudinal analysis.

Examples of analysis metrics may include normalized-power-style metrics, training load, peak-power values/curves, corrected elevation gain, calculated moving time, estimated energy, reconstructed power summaries, and other versioned interpretations.

Derived results are reproducible products, not immutable source evidence. They may have lifecycle states such as current, superseded, or invalidated. The system need not retain every obsolete execution forever, but must retain enough information/history where material analytical changes need explanation or reproduction.

## Evidence selection

Do not maintain a universal canonical-value table initially.

Analysis and presentation layers select evidence explicitly for their purpose. A policy may, for example, choose a suitable source-file distance over Strava metadata and fall back to a derived value, but the alternatives remain preserved.

Material selection policies should be explainable and versionable.

Longitudinal analysis should consume explicit qualifying analytical evidence rather than opportunistically mixing whichever summary field happens to be populated across activities.

## Historical state

Historical rider/equipment/context state remains independent of Activity source evidence and is time-aware, as established in DESIGN-001.

Typed state observations/configurations should make questions such as “what FTP evidence applied around this activity?” straightforward without applying today's values backward.

Explicitly supplied state remains source evidence. State calculated from other evidence is a derivation. Resolution of applicable state for an analysis is part of that analysis's reproducible context.

Exact physical table decomposition remains deferred.

## Derived interpretations and dependencies

Material derivations have durable identity sufficient to identify:

- derivation kind
- method/algorithm and material version
- relevant source evidence inputs
- resolved historical state/context
- material assumptions
- uncertainty/confidence where applicable
- outputs

A later algorithm version may supersede an earlier result without rewriting the underlying source evidence.

Derived artifacts such as an estimated-power FIT remain linked to, but distinct from, original source artifacts.

## Representative-case validation

### Modern Virtual Ride

One Activity can associate Strava CSV evidence and an original FIT artifact. FIT streams/summaries and Strava metadata coexist. Import does not need to declare one universal canonical power value.

### Outdoor Ride with GPS/HR but no source point power

GPS/altitude/HR remain source evidence. Strava CSV power metadata remains a separate evidence channel. A later reconstructed power stream is a versioned application derivation with explicit inputs, assumptions, context, and uncertainty.

### Older GPX/TCX activity

The same Activity/Source model applies. Useful XML extensions remain source-contextual evidence. Lack of FIT does not make the Activity a legacy special case.

### CSV-only activity

The Activity and Strava source evidence exist without a fake empty source-file artifact or fake empty streams. Source-file signals remain unknown/unavailable, not observed zero or proven never recorded.

### Later supplied original file

A later credible FIT/TCX/GPX source can enrich an existing Activity. Earlier Strava evidence remains intact and the association basis is retained.

### Simultaneous device recordings

Multiple source artifacts may belong to one Activity while retaining independent native streams. Import does not have to merge samples onto a common timeline.

## Decisions intentionally deferred

DESIGN-002 does not choose:

- database engine
- SQL/table schema
- exact table decomposition
- stream physical encoding/storage layout
- indexes
- cache/materialization mechanics
- parser/package architecture
- parser libraries
- exact matching thresholds
- exact historical-state resolution/interpolation rules
- exact metric formulas
- provenance UI
- exact derivation dependency storage mechanism
- retention policy for superseded derived results
- Strava synchronization implementation

Those choices must satisfy DESIGN-001 and DESIGN-002 and should be selected only when an implementation slice requires them.

## Requirements for the first implementation slice

The first implementation design must demonstrate the simplest practical path that can:

- create app-owned Activity identities
- represent a Source association with explicit association basis
- preserve original file artifacts unchanged
- extract useful typed source evidence without destructive canonicalization
- preserve native source timing and gaps
- distinguish unavailable signals from observed evidence
- allow later reparsing/re-extraction
- remain structurally capable of associating additional Sources with the same Activity later
- leave room for time-aware historical state and versioned derivations without requiring those entire systems to be implemented at once

For **RideWorks Phase 1**, the real implementation proof is intentionally narrower than the full set of representative cases described above. P1-01 may prove the structure with one source-rich FIT Activity. It does **not** need to demonstrate real multi-source enrichment, CSV-only activities, GPX/TCX production support, or later-file reconciliation.

Those broader cases remain design requirements that the Phase 1 representation must not make impossible. Real multi-source/activity enrichment is a Phase 2 product outcome under the controlling product requirements.

The implementation slice should prove the properties required by its current phase rather than attempting to build the entire RideWorks application model in one task.

## Decision boundary

DESIGN-002 establishes the logical storage/import representation and durability rules.

It does not authorize implementation by itself. The next step is to define a deliberately narrow first implementation slice and its acceptance tests, then author the corresponding JIT before Dex begins work.
