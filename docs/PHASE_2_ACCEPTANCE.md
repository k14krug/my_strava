# RideWorks Phase 2 Acceptance — Historical Context and Performance History

**Status:** accepted / complete  
**Controlling source:** `docs/PRODUCT_REQUIREMENTS.md`  
**Supporting decisions:** `docs/design/DESIGN-001.md`, `docs/design/DESIGN-002.md`  
**Precondition:** Phase 1 accepted / complete

## 1. Phase goal

Phase 2 must stop treating one ride as an isolated event.

The rider should be able to bring the existing Strava-export history into RideWorks, browse that history practically, see a trustworthy 20-minute-power history from an explicitly conservative evidence cohort, and understand a current eligible result against recent prior performance.

Phase 2 is not a general training-state phase. It does not need to decide whether performance changes are good/bad, calculate fatigue/fitness, reconstruct outdoor power, or compare arbitrary pairs of rides.

## 2. Product decisions settled for Phase 2

The following are explicit Owner decisions for this phase.

1. Import the complete known activity population, not cycling only.
2. Preserve non-cycling activities as durable history even though RideWorks remains cycling-focused.
3. Historical best-20 calculations initially use only eligible native source-power evidence; CSV/summary watts are not substitutes for missing streams.
4. Outdoor power numbers are considered untrusted/suspect for Phase 2 performance-history purposes and must not enter the trusted best-20 trend.
5. Eligible Virtual Ride native source-power streams form the initial trusted best-20 cohort when they satisfy the accepted complete-window semantics.
6. The first recent-performance baseline is the **prior six-week best**.
7. Manual pairwise ride-to-ride comparison is not a required Phase 2 capability.
8. The historical import should be one practical bulk workflow and must be idempotent.
9. New activities after the historical export baseline should be able to enter/enrich RideWorks through a normal forward-looking Strava synchronization path in Phase 2.
10. The Activities browser must scale beyond a one-ride list; Strava's paginated/searchable/filterable history is a useful interaction reference, not a specification of exact columns or features.

## 3. Historical export population

The known Strava export research established:

- **1,434** activity rows in `activities.csv`;
- **1,421** rows with exact referenced activity files;
- **13** CSV-only activity rows;
- file-backed population:
  - 1,264 FIT.GZ;
  - 105 GPX/GPX.GZ;
  - 52 TCX.GZ;
- activity-type population:
  - 1,264 Virtual Ride;
  - 146 Ride;
  - 22 Run;
  - 1 Walk;
  - 1 Rowing;
- history spanning 2010 through 2026.

These counts are acceptance evidence for the researched export, not universal importer assumptions.

The raw personal export remains local-only and must not be committed.

## 4. P2 historical-import contract

### 4.1 User workflow

There must be one documented bulk-import workflow against the Strava export, preferably accepting the export ZIP directly when practical.

An extracted export root may also be supported if that keeps implementation materially simpler, but the rider must not manually import 1,421 activity files one at a time.

### 4.2 Relevant source preservation

The importer must preserve useful source evidence without copying irrelevant Strava-account export content into RideWorks merely because it is present in the ZIP.

For the activity-history slice, preserve at minimum:

- the `activities.csv` evidence needed to reproduce imported Strava-export observations and associations;
- each referenced FIT/TCX/GPX activity artifact unchanged;
- artifact identity/integrity metadata;
- source format/packaging metadata needed for later reparsing;
- the Strava activity ID and other imported metadata as source evidence, not Activity identity.

Preserving the entire outer ZIP container is not required if all required activity evidence is preserved exactly and the import remains reproducible/inspectable.

### 4.3 Activity/source association

A Strava CSV row and the file it explicitly references are established source relationships and may enrich the same RideWorks Activity.

The import must use application-owned Activity identity.

For the Phase 1 representative ride, importing the historical export must enrich the already-known Activity rather than create a second activity when exact artifact/source evidence establishes the relationship.

For new export rows, one Strava activity row normally creates one Activity unless evidence establishes that an existing RideWorks Activity represents that event.

Ambiguous associations must remain unresolved rather than forced.

### 4.4 CSV-only activities

The 13 known rows without file references remain legitimate Activities with Strava-export source evidence.

Do not manufacture detailed streams or mark signals as observed absent merely because the source artifact is unavailable.

### 4.5 Actual activity titles

Preserve the actual source activity title/name when the Strava export supplies it.

Title is separate from type/subtype.

A source title may become the preferred display title for the Activity while retaining provenance and without destroying a prior derived fallback.

### 4.6 Format support

Production historical import must handle the formats actually present in the known export:

- FIT/FIT.GZ;
- TCX/TCX.GZ;
- GPX/GPX.GZ;
- CSV-only row evidence.

Import does not require every format to expose the same fields.

Typed source evidence should be extracted only where semantics are understood. Missing or unavailable fields remain explicit.

### 4.7 Idempotency and failure behavior

Re-importing the same export must not create duplicate Activities or duplicate equivalent Sources.

A failure in one activity/file must be reportable without silently discarding successfully imported independent activities.

No failed source should appear as a completed successful import.

The final import report must make counts and failures inspectable.

## 5. Scalable Activities browser

Once historical import exists, the current one-ride Activities page is insufficient.

The Activities experience must support a history on the order of the known 1,434 activities without rendering one unbounded list.

Minimum behavior:

- newest-first default;
- bounded pagination;
- search by activity title/name;
- filter by activity type/subtype;
- practical date/year or date-range filtering;
- useful sorting including date and at least selected ride-summary fields that are genuinely available;
- opening an Activity Review from the result row/card;
- source title shown when available;
- derived fallback visibly identified when a source title is unavailable;
- missing summary evidence shown honestly.

Exact page size, columns, filter-control layout, and responsive behavior are implementation/UI details rather than contract decisions.

Do not recreate Strava's private/deleted/social/tag-management controls unless RideWorks has an actual use for them.

## 6. Trusted Phase 2 best-20 history

### 6.1 Eligibility purpose

Phase 2 needs a **trusted performance-history cohort**, not every numeric power value available in every source.

Eligibility is analysis-specific. It is not a universal claim that one source type is always superior.

### 6.2 Initial trusted cohort

For Phase 2, a best-20 result may enter the trusted historical trend only when:

1. the activity is a cycling Virtual Ride under the available source/export classification;
2. a native source power stream is present;
3. the stream contains a complete eligible 20-minute window under the accepted `best-average-power-v1` semantics;
4. the result is calculated from that native source stream, not from CSV average watts, source summary average watts, weighted power, or another summary substitute.

The result must not be labeled `measured` merely because power exists. The eligibility decision is narrower: Virtual Ride native power is accepted for this Phase 2 historical comparison purpose.

### 6.3 Outdoor exclusion

Outdoor/`Ride` power is excluded from the trusted Phase 2 best-20 trend, even when a source point-power stream exists.

Reason: the Owner considers historical outdoor power numbers suspect, and prior archive research established that field/stream presence does not prove measured provenance.

Outdoor source power remains preserved evidence and may remain visible where useful with provenance. It must not silently contribute to the trusted Phase 2 performance trend.

Outdoor estimated-power reconstruction remains a separate later design/implementation problem.

### 6.4 Calculation semantics

Reuse the accepted P1-02 `best-average-power-v1` complete-window semantics:

- 1,200 consecutive source records;
- timestamps `t` through `t+1199`;
- half-open interval `[t, t+1200)`;
- every adjacent timestamp delta exactly one second;
- all 1,200 power values non-null;
- legitimate zero watts count;
- missing values invalidate the candidate window;
- no resampling, interpolation, smoothing, gap repair, or deduplication;
- evaluate every eligible window;
- highest raw average wins;
- ties choose the earliest window;
- retain unrounded result and context;
- display nearest whole watt using the accepted .5-up policy.

Activities that do not satisfy these narrow rules are ineligible for this Phase 2 trend rather than being repaired.

### 6.5 Durable longitudinal result

Because best-20 history is repeatedly consumed longitudinally, Phase 2 should retain a durable/versioned analytical result or an equivalently reproducible persisted history keyed to:

- Activity;
- source/extraction evidence;
- method/version;
- raw average;
- display value;
- start/end context;
- eligibility/status.

A later re-extraction or method change must be able to invalidate/recalculate affected results without rewriting source evidence.

## 7. Performance-history experience

Phase 2 must add a real rider-facing Performance/history view for the trusted 20-minute results.

Minimum behavior:

- chronological 20-minute-power history;
- all eligible historical points available, not only a recent sample;
- date and activity identity/title available for a point;
- clicking/opening a point can navigate to the contributing Activity Review;
- ineligible/missing activities are not plotted as fabricated zeroes;
- the view states or makes inspectable the eligibility policy;
- no outdoor estimated/suspect watts are silently mixed into the trusted line.

The exact chart library, zoom controls, aggregation controls, and additional durations are not fixed by this contract.

## 8. Prior-six-week comparison

For an eligible activity with a current best-20 result:

- define the comparison window as the **42 days immediately preceding the current activity start**, excluding the current activity;
- consider only eligible trusted Phase 2 best-20 results under the same method/eligibility policy;
- select the highest raw best-20 result in that prior window;
- if tied, deterministic selection is required but the exact tie presentation need not imply significance;
- if no eligible prior result exists, show the baseline as unavailable rather than fabricating one.

The Activity Review should show enough context to answer:

> How does this ride's best 20-minute power compare with my best eligible result in the previous six weeks?

Presentation should be neutral:

- show current and prior values;
- a watt difference may be shown;
- do not automatically label higher as good or lower as bad;
- do not use green/red semantics without an interpretation that actually supports them.

Manual selection of another ride for side-by-side comparison is not required.

## 9. Multiple-source enrichment proof

Phase 2 must prove ACT-002/ACT-008 in real data.

At minimum:

- the Phase 1 representative FIT-backed Activity is enriched with its Strava-export metadata/title rather than duplicated;
- source evidence remains separately attributable;
- Strava-export values do not overwrite FIT source summaries merely because they look equivalent;
- the UI can use the preferred source title while provenance remains inspectable.

## 10. Forward-looking Strava synchronization

Phase 2 must finish with a normal incremental path for activities created after the historical export baseline.

Product requirements:

- synchronization is forward-looking/incremental, not a mechanism for bulk-harvesting years of historical API data;
- the first useful workflow may be user-invoked rather than continuously polling;
- new Strava activities can create or enrich RideWorks Activities;
- known Strava external identity is retained as source identity, not RideWorks Activity identity;
- synchronization must conservatively associate with an already-imported local/FIT Activity when strong evidence establishes the relationship;
- actual Strava title/type/useful metadata should enrich the Activity with provenance;
- useful API-derived evidence may be retained;
- authentication/secrets remain local and out of Git;
- rate limits, scopes, token behavior, API terms, and any webhook obligations must be re-verified from current authoritative Strava documentation in the P2-05 JIT before implementation.

Phase 2 does not require background cloud hosting or a generalized sync service.

## 11. Explicit Phase 2 non-goals

Phase 2 does not require:

- manual pairwise ride comparison;
- outdoor estimated-power reconstruction;
- treating outdoor power as trusted performance evidence;
- normalized/weighted power as a RideWorks-calculated metric;
- FTP history;
- arbitrary-duration power curves beyond the already accepted best-20 slice;
- training load, fatigue, recovery, fitness, or training-state scores;
- workout-intent/outcome analysis;
- goals/dashboard implementation;
- planning/next-workout behavior;
- automatic local file watching;
- Strava social features;
- bulk historical Strava API harvesting;
- user accounts/cloud deployment;
- mobile/native application work;
- generalized multi-athlete architecture.

## 12. Phase 2 acceptance contract

Phase 2 is accepted only when all of the following are true.

### Historical history

1. The known 1,434-row export can be imported through one documented bulk workflow.
2. All 1,434 CSV rows are accounted for in the import result.
3. All 1,421 referenced source artifacts are attempted and successful known artifacts are preserved unchanged.
4. The 13 CSV-only rows are represented as Activities with honest evidence availability.
5. FIT/TCX/GPX evidence remains attributable to its source.
6. Strava-export row evidence remains attributable to the Strava export source.
7. Actual source activity titles are preserved with provenance.
8. Re-running the same import is idempotent.
9. The already-imported Phase 1 representative ride is enriched rather than duplicated.
10. Import failures, if any, are explicit and do not silently invalidate unrelated successful imports.

### Activities browser

11. The Activities browser remains practical with the full imported history.
12. Results are paginated/bounded rather than one unbounded list.
13. Title search works.
14. Activity type/subtype filtering works.
15. Practical date filtering works.
16. Useful sorting works.
17. A listed activity opens its stable Activity Review route.

### Performance history

18. Trusted best-20 history uses the Phase 2 Virtual Ride/native-source eligibility rule.
19. Outdoor Ride power is excluded from the trusted trend.
20. CSV/source-summary watts are not substituted for a missing native stream.
21. Best-20 calculations preserve the accepted `best-average-power-v1` semantics.
22. Ineligible rides remain visibly ineligible/unavailable rather than being repaired or plotted as zero.
23. The rider can view chronological trusted 20-minute-power history.
24. A plotted result can be traced/opened to its contributing Activity.
25. Material result provenance/method is inspectable/reproducible.

### Historical context in Activity Review

26. An eligible Activity Review can show current best-20 against the prior 42-day best.
27. The current activity is excluded from its own baseline.
28. No-baseline cases display unavailable.
29. Presentation is neutral and does not equate a higher/lower number with good/bad by default.

### Incremental new activity path

30. A documented normal Strava synchronization workflow can fetch new/post-baseline activity metadata under current API rules.
31. Sync is incremental/forward-looking rather than historical bulk harvesting.
32. Sync can create a new Activity or conservatively enrich an existing one without silent duplication.
33. Strava title/type/useful metadata retain Strava provenance.
34. Credentials/tokens are not committed.
35. Current authoritative Strava authentication/rate-limit/terms behavior is verified during implementation.

### Product acceptance

36. Owner confirms that the full-history Activities browser is practical for normal use.
37. Owner confirms that the 20-minute history and prior-six-week context answer the Phase 2 question: **"How does this compare with my past performance?"**
38. Analyst accepts the evidence-quality/eligibility behavior and final Phase 2 verification.
39. Phase 3 does not begin automatically.

## 13. Planned Phase 2 task sequence

### P2-01 — Historical Strava-export import and enrichment

**Outcome:** all known historical activities enter RideWorks durably from one bulk workflow; real Strava titles/metadata and referenced FIT/TCX/GPX evidence coexist; the Phase 1 representative Activity is enriched rather than duplicated.

Primary requirements: PR-003 through PR-009, PR-012, ACT-001 through ACT-008, DATA-001 through DATA-006.

### P2-02 — Scalable Activities browser

**Outcome:** the full imported history is practically searchable/filterable/sortable/paginated and opens stable Activity Review routes.

Primary requirements: PR-002, PR-013, REV-001, REV-010, Phase 2 product acceptance.

### P2-03 — Trusted 20-minute performance history

**Outcome:** RideWorks derives and presents a chronological trusted best-20 history from eligible Virtual Ride native source power, explicitly excluding outdoor/suspect power from the trend.

Primary requirements: REV-003, REV-004, PERF-001 through PERF-004, DATA-003, DATA-004.

### P2-04 — Six-week historical context in Activity Review

**Outcome:** an eligible ride shows its best-20 against the prior 42-day eligible best using neutral, explainable presentation and links into the Performance history.

Primary requirements: REV-004, REV-009, REV-010, PERF-002, PERF-004.

### P2-05 — Incremental Strava synchronization

**Outcome:** after the historical export baseline, a normal forward-looking sync can create/enrich new activities with useful Strava metadata without bulk historical API harvesting or silent duplication.

Primary requirements: PR-003, PR-006, ACT-002, ACT-003, ACT-008, DATA-002, Phase 2 incremental-sync outcome.

## 14. Task-control intent

Detailed JIT briefs are authored one task at a time.

The Phase 2 task sequence does not itself authorize implementation.

P2-01 through P2-05 are accepted and complete. Phase 2 was accepted on 2026-10-05 with PR #17 merged as `e78c8a6c2de4f4e21aaa2937ae33d1e011901947`. Phase 3 implementation does not begin automatically.

Each task will state:

- Allowed Invocation;
- review gates;
- exact local-data procedure;
- verification requirements;
- stop-and-report conditions.

Phase 2 must not begin Phase 3 automatically after final acceptance.
