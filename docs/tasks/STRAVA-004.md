# STRAVA-004 — Strava activity-stream enrichment and FIT comparison

**Status:** Analyst-authored JIT; implementation not started  
**Follow-up type:** Owner-prioritized post-Phase-2 activity-review improvement  
**Phase 3:** not started  
**Authoritative Strava documentation review:** 2026-10-05

## 1. Purpose

Make newly synchronized Strava API-only rides capable of a useful RideWorks
time-series Activity Review **without pretending an API stream is automatically
equivalent to preserved FIT evidence**.

The task starts with evidence, not UI implementation:

1. fetch current Strava activity streams for the live overlap rides that already
   have both Strava identity and preserved FIT evidence;
2. compare Strava streams against the corresponding RideWorks FIT streams;
3. determine what the API stream actually preserves, transforms, omits or
   downsamples;
4. only if the evidence supports it, persist Strava stream evidence and use it
   for Activity Review charts on post-export API-only rides.

This task does **not** automatically make Strava API power eligible for trusted
Performance history or personal records.

## 2. Why this task exists

P2-05 completed forward Strava metadata synchronization and proved:

- 7 new post-export API-only Activities;
- 4 overlap Activities enriched by established Strava identity;
- no overlap duplicates;
- API-only Activities currently get thin review because no detailed stream
  evidence is retained.

The Owner explicitly wants those new rides to show useful graphs and approved
the evidence-first approach: compare Strava streams with FIT on the overlaps
before deciding how far API streams may be trusted.

Relevant product requirements:

- PR-003 — durable history from the best available sources;
- PR-004 — source evidence and interpretation remain distinct;
- PR-006 — provenance matters;
- ACT-002 / ACT-008 — multiple Sources and later enrichment;
- REV-002 — time-series Activity Review where evidence is available;
- REV-003 — detailed power can support best-effort analysis, subject to evidence;
- REV-010 — source/stream inspectability;
- PERF-004 — evidence quality controls longitudinal eligibility.

## 3. Allowed invocation

`/TASK` or `/AUTOTASK`.

This authorizes STRAVA-004 only.

Phase 3 dashboard implementation must not begin as a side effect of this task.

## 4. Current authoritative Strava stream behavior

Verified from current Strava developer documentation on 2026-10-05.

Official references:

- <https://developers.strava.com/docs/reference/>
- <https://developers.strava.com/docs/authentication/>

### 4.1 Endpoint and scope

The documented activity-stream endpoint is:

```
GET /api/v3/activities/{id}/streams
```

with required:

- `keys`;
- `key_by_type=true`.

It requires `activity:read`, and `activity:read_all` for Only You activities.

RideWorks already holds `activity:read_all`; **do not request a broader scope**
for this task.

### 4.2 Requested streams

For STRAVA-004 request only the signals needed for current/future Activity
Review validation:

- `time`;
- `watts`;
- `heartrate`;
- `cadence`;
- `moving`.

Do not request latitude/longitude, map, segment, route or social data.

A missing optional stream is evidence of unavailability, not an error to repair.

### 4.3 Stream metadata

Current Strava stream objects expose:

- `data`;
- `original_size`;
- `resolution` — `low`, `medium` or `high`;
- `series_type` — `distance` or `time`.

Do not assume that:

- `high` means original device samples;
- `data.length == original_size`;
- samples are exactly one second apart;
- different stream types have identical lengths;
- API watts are measured merely because `device_watts` is true in summary
  metadata;
- API stream timing is interchangeable with FIT record timestamps.

These are findings to establish from the overlap comparison.

## 5. Stage A — live overlap comparison before product use

Use the accepted P2-05 live review store and its existing Strava connection.
Do not create a second independently rotating token state merely for research.

The live P2-05 evidence contains four overlap Activities that were enriched by
established Strava identity. For each overlap that has exactly one supported FIT
analysis Source:

1. identify its current Strava activity identity from stored source evidence;
2. fetch only the five requested stream types;
3. keep the response local/ignored while comparison is running;
4. compare it with the preserved FIT extraction without modifying either source.

If an overlap does not have one supported FIT source, report it and exclude it
from exact FIT comparison rather than substituting XML/summary data.

### 5.1 Comparison evidence

For every comparable overlap report, without publishing private IDs/titles:

- stream types returned/missing;
- `resolution`, `series_type`, `original_size`, returned data length;
- first/last `time` value;
- time monotonicity and duplicate/backward values;
- actual time deltas and gap distribution;
- FIT record count and comparable API sample count;
- timestamp/elapsed-time alignment method;
- matching coverage;
- exact-match counts/rates for watts, HR and cadence at genuinely comparable
  timestamps;
- zero handling;
- missing-value handling;
- first mismatch examples in aggregate/anonymous form, not raw private streams;
- whether API values appear shifted, resampled, interpolated, smoothed,
  downsampled or otherwise transformed.

Do not coerce one source into another merely to improve the match.

### 5.2 Experimental best-20 comparison

For research only, if the Strava `time` + `watts` evidence independently
satisfies the accepted exact 1-second / complete-power window requirements,
calculate the same 1,200-s best-average result from the API stream and compare
its raw/display result and selected elapsed window with the FIT result.

This comparison must use an independent verifier rather than calling the
production FIT analysis as its own oracle.

Even an exact match here does **not** enroll API streams into trusted
Performance history in STRAVA-004.

### 5.3 HARD evidence stop

Stop and report before Activity Review integration if the comparison finds any
material uncertainty that would make a graph misleading, including:

- API `time` cannot be aligned meaningfully to the ride;
- signal arrays cannot be paired with time without invention;
- values differ materially from FIT in a way not explained by explicit sampling;
- Strava returns unexpectedly downsampled/transformed evidence for these rides;
- watts/HR provenance becomes ambiguous;
- the endpoint behaves materially differently from current documentation.

The point of Stage A is to learn what Strava actually returns for this rider,
not to force the planned implementation through.

## 6. Stage B — durable Strava stream evidence

If Stage A supports Activity Review use, add the smallest source-centered
representation needed to retain the fetched stream evidence.

Required provenance includes:

- RideWorks Activity;
- Strava external activity identity;
- retrieval time;
- mapping/version identifier;
- requested/returned stream types;
- each stream's `resolution`, `series_type`, `original_size`;
- exact returned data values in their returned order;
- API-source relationship.

Preserve existing Strava summary observations separately.

Do not label API streams as FIT/native-file records.

Do not overwrite file Sources, file extractions or original artifacts.

Do not store coordinates because they are not requested.

Do not store tokens with stream evidence.

A repeated identical stream fetch must be idempotent. A changed later stream
response should remain distinguishable from the earlier observation if retaining
both stays simple; do not silently rewrite history without provenance.

## 7. Stream enrichment workflow

After Stage A passes, normal **Sync now** should be capable of enriching newly
created post-export API-only cycling Activities with the requested streams
without another rider workflow.

Keep metadata synchronization robust:

- metadata sync success must not be rolled back merely because one activity has
  no optional HR/cadence stream;
- stream fetch failures must be explicit and retryable;
- do not convert a stream-fetch problem into duplicate Activity creation;
- do not fetch streams for years of historical Strava activities;
- do not fetch streams for the entire imported 1,434-Activity archive.

### 7.1 Bounded catch-up

STRAVA-004 may perform one bounded catch-up for the **7 post-export API-only
Activities already created by P2-05**.

That is targeted enrichment of known recent Activities, not historical API
harvesting.

Future Sync now runs should enrich newly observed API-only cycling Activities
and may retry recent post-export API-only Activities that still lack stream
evidence.

Keep requests sequential and continue to obey the accepted P2-05 rate-limit
handling. Do not add concurrency to increase throughput.

## 8. Activity Review behavior

File-backed behavior remains authoritative and unchanged.

### 8.1 File-backed Activity

If a supported FIT source exists:

- keep the existing FIT-backed rich Activity Review;
- do not switch the graph to Strava streams;
- keep current best-20 calculation/source semantics;
- API streams remain additional inspectable evidence only.

### 8.2 API-only Activity with usable streams

Replace the current blanket "Detailed RideWorks review unavailable" behavior
with an evidence-appropriate stream-backed review.

At minimum:

- render the existing RideWorks time-series chart treatment for available
  **power and heart rate**;
- use the returned Strava time points directly; do not invent one-second samples;
- break/represent missing evidence honestly according to actual returned timing;
- label the chart/source as **Strava API stream evidence**;
- expose `resolution`, `series_type`, `original_size` and retrieved-at
  provenance in details;
- retain Strava summary metrics separately from stream evidence;
- do not claim a FIT/native file exists.

Cadence may be retained for later display even if the current chart remains
power + HR.

### 8.3 API-only Activity without usable streams

Keep thin review and say why stream review is unavailable.

Do not substitute summary average watts for a time series.

## 9. Performance boundary

STRAVA-004 is primarily an Activity Review task.

Regardless of Stage A similarity:

- do not automatically add API-only rides to `virtual-native-power-v1`;
- do not change the 1,022 accepted eligible Performance cohort merely because
  Strava streams were fetched;
- do not recast API stream watts as FIT/native evidence;
- do not add API-stream best-20 to lifetime/monthly/yearly/rolling trends;
- do not change prior-six-week trusted context.

Stage A should produce a clear recommendation for a **future** eligibility
decision:

1. API streams appear equivalent enough to investigate trusted analytical use;
2. API streams are suitable for visual review but not trusted Performance;
3. API streams are too transformed/incomplete for either use.

That recommendation is evidence, not an automatic policy change.

## 10. Timing semantics

Strava's `TimeStream.data` is a sequence of seconds; preserve it as returned.

For browser display, an API-only absolute chart timestamp may be derived as:

```
activity start_date + returned time offset
```

only as an explicit presentation mapping from two Strava API observations.

Keep the original start date, time offsets and mapping version inspectable.

Do not rewrite the returned offsets into a fake FIT record stream.

Do not infer missing intermediate seconds.

## 11. API/client behavior

Extend the accepted P2-05 Strava client narrowly.

Requirements:

- fixed HTTPS activity-stream endpoint only;
- existing access-token refresh behavior;
- existing 20-second finite timeout unless evidence shows a stream response
  needs a modestly different documented bound;
- bounded JSON size with a reasoned limit suitable for ride streams;
- redirect rejection;
- rate headers inspected on every response;
- 429/exhaustion stops stream enrichment without busy retry;
- no parallel fan-out;
- response shape and numeric arrays validated before persistence;
- errors never include tokens, raw response bodies, private IDs or coordinates.

Do not introduce a generic HTTP framework.

## 12. Tests

Automated tests use fake API responses only.

Cover at minimum:

### Stream parsing/provenance

- requested key list and `key_by_type=true`;
- missing optional streams;
- high/medium/low metadata retained;
- `series_type` retained;
- `original_size` retained even when it differs from returned length;
- zero watts/HR/cadence remain zero;
- malformed types, NaN/inf, invalid arrays and excessive payload fail clearly;
- identical rerun is idempotent;
- changed stream evidence does not silently overwrite provenance.

### Timing

- 1-second timing;
- non-1-second/downsampled timing;
- pauses/gaps;
- duplicate/backward offsets rejected or handled explicitly according to the
  established stream contract;
- no invented intermediate points.

### Source precedence

- FIT-backed ride remains FIT-rich even with API stream evidence;
- API-only + usable streams becomes stream-backed review;
- API-only + unavailable streams stays thin;
- API summary watts never become a time series;
- no change to trusted Performance eligibility.

### UI

- post-export API-only power/HR chart;
- source label/provenance;
- LA/Tokyo absolute date behavior;
- desktop/phone no overflow;
- restart retains stream-backed review;
- P2-05 Settings/Activities/Performance/reminder regressions remain intact.

## 13. Live verification

Use the accepted P2-05 live review store with its existing authorization for
Stage A. Keep private activity IDs/titles out of published reports.

Before Stage B mutations, create an ignored local baseline/backup of the accepted
database/source state. Do not duplicate or independently use its token file.

Required live evidence:

1. all available overlap FIT/API stream comparisons;
2. explicit stream metadata and alignment findings;
3. experimental best-20 comparison where evidence qualifies;
4. zero archive re-imports;
5. zero full-history API stream crawling;
6. bounded stream calls only for overlap research plus the 7 known post-export
   API-only catch-up after Stage A passes;
7. API-only Activity Review graphs for the recent post-export rides that return
   usable power/HR;
8. FIT-backed overlap reviews unchanged;
9. accepted 1,022 Performance eligibility unchanged;
10. restart/idempotence;
11. SQLite integrity/foreign keys.

## 14. Verification report

Create `reports/STRAVA-004/verification.md`.

Publish only aggregate/anonymized evidence:

- Strava documentation review date;
- endpoint/scope/keys;
- overlap count;
- per-overlap anonymous stream metadata;
- sample-count/timing comparison;
- exact-match/difference statistics;
- best-20 comparison where qualifying;
- conclusion about graph suitability;
- explicit separate conclusion about trusted Performance suitability;
- stream-fetch counts;
- post-export graph counts;
- rate-limit usage;
- test counts;
- restart/idempotence/integrity results.

Never publish tokens, client secret, athlete ID, Strava activity IDs, private
titles, coordinates or raw personal stream arrays.

## 15. Review gates

### Gate A — evidence gate

If Stage A reveals material differences/uncertainty, stop and present the
comparison before implementing graph consumption.

If Stage A clearly supports Activity Review use, continue within STRAVA-004 to
Stage B without inventing trusted Performance eligibility.

### Gate 1 — HARD — Owner

After stream-backed Activity Review is available:

- keep STRAVA-004 `in_progress`;
- provide the existing RideWorks review URL;
- point the Owner to at least the newest API-only ride and one FIT-backed
  overlap;
- show source/provenance details;
- stop for Owner review of whether the API-only graph is useful and honest.

### Gate 2 — HARD — Analyst

After explicit Owner approval:

- verify Stage A evidence and its conclusion;
- verify no trusted Performance policy changed;
- verify source precedence/provenance/timing;
- verify bounded API access and no historical stream harvest;
- verify tests/restart/idempotence/integrity;
- accept or return actionable corrections.

Do not begin Phase 3 automatically after STRAVA-004.

## 16. Explicit non-goals

STRAVA-004 does not implement:

- historical bulk stream harvesting;
- automatic trusted Performance eligibility for API streams;
- new power-duration policies;
- TSS/CTL/ATL/TSB;
- FTP history;
- outdoor estimated-power reconstruction;
- maps/routes/coordinates;
- segments/laps/zones;
- workout intent/outcome;
- dashboard/goal/planning features;
- webhooks/background synchronization;
- multi-athlete support.

## 17. Stop-and-report conditions

Stop and report if:

- current Strava stream behavior materially differs from §4;
- the four overlaps do not provide enough FIT-backed comparison evidence;
- API streams show material unexplained transformation;
- stream timing cannot support an honest chart without interpolation/invention;
- live stream access unexpectedly needs broader OAuth scope;
- the task would require historical API stream crawling;
- implementation would change trusted Performance eligibility;
- stream enrichment would require a generalized source-reconciliation redesign;
- Phase 3/dashboard work begins to enter scope.

## 18. Handoff

At Owner Gate provide:

- branch / PR / head;
- focused/full test counts;
- Stage A comparison summary;
- graph-suitability conclusion;
- trusted-Performance conclusion;
- number of recent API-only Activities stream-enriched;
- number with usable power/HR graphs;
- bounded live API request count;
- review URL;
- verification report path;
- explicit statement that trusted Performance eligibility is unchanged and
  Phase 3 has not begun.
