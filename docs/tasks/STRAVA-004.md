# STRAVA-004 — Strava activity-stream enrichment and FIT comparison

**Status:** accepted / complete  
**Follow-up type:** Owner-prioritized post-Phase-2 activity-review improvement  
**Phase 3:** not started  
**Authoritative Strava documentation review:** 2026-10-05  
**Acceptance:** Owner and Analyst accepted PR #18; merged to `main` as `e7920493dfadbb5f15b0352315cce433f7991ecd` on 2026-10-06.

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

Stage A has now established exact FIT/API agreement on the four overlap rides.
By explicit Owner decision on 2026-10-06, STRAVA-004 also updates the versioned
Performance eligibility policy so that **validated Strava API power-stream
evidence may contribute to Performance when no file-backed power evidence is
available**. This is a controlled policy revision, not a claim that all API
streams are inherently equivalent to FIT.

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

The original JIT treated exact overlap agreement as research only. After the
observed exact match and Owner review, that conservative boundary is superseded
by §9: only API observations matching the validated evidence shape may become
Performance-eligible under the new versioned policy.

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
with an evidence-appropriate stream-backed review that follows the **same overall
Activity Review hierarchy as a normal supported FIT ride** wherever Strava
evidence genuinely supports the section. The Owner should not see a chart
floating above raw provenance while the normal summary/review structure is
missing.

Required rider-facing structure:

1. **summary metric cards** above the chart;
2. the existing **Ride power & heart rate** chart;
3. an activity-local **Best 20-minute power** panel when the API watts/time
   stream qualifies under the accepted complete-window semantics;
4. the normal right-side **Ride summary** panel;
5. provenance/details below/secondary.

#### Summary metric cards

Use current Strava API **summary evidence**, not inferred stream statistics, for
the normal four cards:

- Elapsed duration;
- Distance;
- Average power;
- Average heart rate.

Missing values show Unavailable. The section must be labeled/inspectable as
Strava API summary evidence and must not imply that summary averages were
calculated from the retained API stream.

#### Ride summary

Provide the normal Ride summary treatment from current Strava API summary
evidence, using available fields such as:

- elapsed duration;
- moving duration;
- distance;
- total elevation gain;
- average / maximum power;
- average / maximum heart rate;
- average cadence;
- kilojoules where supplied and useful.

Do not manufacture FIT-only fields such as timer duration when Strava does not
supply an equivalent. Missing fields remain Unavailable or may be omitted when
that is clearer. Label the panel **Strava API summary evidence**.

#### Chart

- render the existing RideWorks time-series chart treatment for available
  **power and heart rate**;
- use the returned Strava time points directly; do not invent one-second samples;
- break/represent missing evidence honestly according to actual returned timing;
- label the chart/source as **Strava API stream evidence**;
- expose `resolution`, `series_type`, `original_size` and retrieved-at
  provenance in details;
- do not claim a FIT/native file exists.

Cadence may be retained for later display even if the current chart remains
power + HR.

#### Activity-local Best 20-minute power

For an API-only Activity with `time` + `watts`, RideWorks may calculate and
show a **ride-local review result** using the accepted
`best-average-power-v1` complete-window semantics:

- exactly 1,200 samples;
- exactly one-second consecutive returned time offsets;
- complete power values;
- zero watts count;
- gaps, duplicate/backward offsets or missing power invalidate affected windows;
- no interpolation, resampling, smoothing or repair;
- maximum raw average wins; exact tie chooses earliest window;
- rider-facing whole watts use the accepted half-up display rule.

This result is calculated from **Strava API stream evidence**, not native FIT
evidence. The panel must say so prominently enough that the provenance is not
ambiguous.

The API-stream ride-local calculation is also the candidate calculation used by
the Performance policy in §9. It remains source-attributable as Strava API
stream evidence and must never be relabeled as native FIT evidence.

If the Activity satisfies §9's API eligibility requirements, the same
best-average result may be persisted into Performance history under
`virtual-power-evidence-v2` and participate normally in rolling/monthly/yearly/
lifetime Performance and the prior-six-week comparison.

If the Activity does not satisfy §9, the ride-local panel may still show the
result only when its own complete-window requirements are met, but it must state
that it is excluded from Performance history and give the eligibility reason.

Where no qualifying API watts/time window exists, show **Unavailable** with an
honest reason such as no watts stream, activity too short, incomplete power, or
no complete one-second window.

The calculation details should expose returned-offset window bounds, raw
average, sample count, eligible-window count and the API-stream source/method
without pretending to have native FIT record indices/timestamps.

The four exact FIT/API overlap comparisons are the evidence basis for the
narrow API eligibility path in §9. Performance provenance remains explicit so a
future policy can be recalculated without confusing API streams with file
evidence.

### 8.3 API-only Activity without usable streams

Keep thin review and say why stream review is unavailable.

Do not substitute summary average watts for a time series.

## 9. Performance eligibility policy v2

The original accepted policy `virtual-native-power-v1` was intentionally
file/native-only. STRAVA-004 evidence showed that, for all four comparable
overlap rides, current Strava power and heart-rate streams matched preserved FIT
samples exactly at the same absolute timestamps, including zeros and the shared
gap, and produced identical qualifying best-20 results/windows.

By explicit Owner decision, replace that policy for current Performance with:

```
virtual-power-evidence-v2
```

The method remains `best-average-power-v1` / 1,200 seconds.

This is an **eligibility policy**, not an assertion that every source is equally
authoritative or that every Strava stream is measured power.

### 9.1 Classification boundary

Only Activities classified as **Virtual Ride** are candidates.

Outdoor Ride power remains excluded under the existing evidence-quality
decision. STRAVA-004 does not change outdoor estimated/measured-power policy.

### 9.2 Evidence precedence

Evaluate evidence in this order:

1. **File-backed power evidence controls when present.**
   - Preserve the accepted native-file evaluation semantics.
   - If exactly one supported file-backed power candidate is eligible, use it.
   - If file-backed power exists but is ineligible because its own timing/power
     evidence does not produce an eligible result, do **not** use the API stream
     to bypass that failure.
   - Existing multiple-native-source ambiguity remains an ineligible condition.
2. **Strava API stream fallback is allowed only when there is no file-backed
   power evidence for the Activity.**

Therefore the four FIT/API overlaps remain file-backed Performance results; API
streams are corroborating evidence on those Activities, not duplicate points.

### 9.3 API-stream eligibility requirements

An API-only Virtual Ride may contribute to Performance only when all of the
following are true:

- there is exactly one **current** Strava stream observation associated with the
  current Strava summary observation;
- the current Strava summary says `device_watts=true`; false or missing does
  not establish eligible device power;
- both `time` and `watts` streams are present;
- both streams report `resolution=high`;
- for both streams, `original_size == returned_length`;
- the returned `time` and `watts` arrays have the same length;
- time offsets are finite non-negative integer seconds, strictly increasing;
- watts values are finite non-negative numeric values or explicit missing
  values as supported by the retained stream contract;
- the accepted complete-window calculation finds at least one window of exactly
  1,200 returned samples with consecutive one-second offsets and complete power;
- zero watts count;
- gaps, missing power, duplicate/backward timing and non-one-second edges
  invalidate affected windows;
- no interpolation, resampling, smoothing or repair occurs.

The best result uses the same raw-max / earliest-exact-tie /
whole-watt-half-up rules as the file-backed method.

A `high` label alone is not sufficient; the returned arrays/timing must pass
the checks above. Conversely, do not manufacture extra requirements not backed
by the validated overlap evidence.

### 9.4 API ineligibility reasons

Persist explicit reasons such as:

- `api_power_stream_unavailable`;
- `api_device_watts_not_confirmed`;
- `api_stream_not_high_resolution`;
- `api_stream_not_full_length`;
- `api_stream_length_mismatch`;
- `api_stream_invalid_timing`;
- `activity_shorter_than_required`;
- `no_complete_timestamp_contiguous_window`;
- `no_complete_power_window`.

The two current HR-only rides are expected to remain legitimately ineligible and
must **not** keep any warning/banner active once Performance is current.

### 9.5 Durable provenance

A persisted API-stream Performance result must remain distinguishable from a
file-backed result.

Do not fake an extraction ID or insert Strava stream rows into native
`records`.

The existing `performance_history.source_id` / `extraction_id` fields may
remain null for an API-stream result if that is the smallest safe schema choice.
The result JSON and Performance input signature must explicitly retain at least:

- evidence kind = Strava API stream;
- stream Source ID;
- related current Strava summary Source ID;
- stream observation digest/mapping version;
- `device_watts` source value;
- method/policy/duration;
- returned-offset window bounds;
- raw average / rounded watts;
- eligible-window count.

File-backed results retain their current source/extraction provenance.

### 9.6 Performance input signature and policy migration

Performance freshness must include the evidence actually used by v2.

For API-stream candidates, changes to the current stream observation, related
current summary observation, classification, `device_watts`, or relevant
mapping/content digest must make the stored result stale/pending.

Changing `POLICY` from v1 to v2 must itself make the old v1 history non-current
until a v2 rebuild succeeds. Old v1 rows may remain as historical/reproducible
evidence; they must not be selected by the current Performance page.

A v2 rebuild must independently verify that all **1,022 existing file-backed
eligible results reproduce unchanged** and add only API-stream results that pass
§9.3. On the current live review store, the expected evidence-derived outcome is
**1,027 eligible = 1,022 file-backed + 5 API-stream**, with the two HR-only
post-export Activities remaining ineligible.

### 9.7 Six-week comparison and rider-facing wording

Once an API-stream Activity is eligible under v2, it participates normally in
the exact accepted prior window `(t - 42 days, t)`, including the
**Compared with previous 6 weeks** Activity Review panel.

Current and prior results may come from different eligible evidence kinds.
Winner/tie semantics remain raw best watts, then earliest Activity start, then
stable Activity ID.

The panel/provenance must make the current result's evidence kind inspectable
without cluttering the main comparison.

Avoid presenting **Trusted Performance** as an absolute rider-facing quality
label. Prefer **Performance**, **Performance history**, or
**Performance-eligible evidence**. The versioned policy and evidence provenance
carry the actual trust/eligibility semantics.

### 9.8 Sync converges Performance automatically

Revise the earlier explicit-rebuild workflow.

After a successful **Sync now** has completed metadata and bounded stream
enrichment:

1. inspect current Performance freshness under the current policy;
2. if `pending == 0`, skip the rebuild;
3. if any result is missing/stale/pending — including because the policy version
   changed — run the same atomic `rebuild_performance(store)` used by the
   maintenance CLI;
4. report the Performance update as part of the sync outcome.

This must be shared behavior for the in-app Sync now path and the secondary CLI
sync path; do not maintain two synchronization/rebuild policies.

A successful ordinary sync should therefore leave Performance current without a
second rider action.

The rebuild remains atomic. If it fails:

- keep successfully synchronized source/stream evidence and the sync checkpoint;
- preserve the previously committed Performance rows;
- do not claim Performance is current;
- show an actionable **Performance update incomplete** state and retain a manual
  **Retry Performance update** / rebuild action;
- a later sync must retry while pending remains even if no additional Strava
  evidence changed.

Do not roll back valid synchronized source evidence merely because derived
Performance recalculation failed.

### 9.9 Banner semantics

The app-wide Performance banner is now an **exception/freshness indicator**, not
a routine second step after Sync now.

Normal successful sync + rebuild => no banner.

Show the banner only while current-policy Performance has unresolved
missing/stale/pending results, for example after:

- a rebuild failure/interruption;
- a policy-version change before the next successful convergence;
- relevant evidence changed outside the normal successful sync path.

Suggested rider-facing wording:

> **Performance update incomplete** — RideWorks has new or changed evidence that
> is not yet reflected in Performance. Retry Performance update.

Legitimately ineligible Activities (for example the two HR-only rides) do not
keep the banner active once they have current v2 ineligible result rows.

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
- file-backed Performance precedence is retained;
- qualifying API-only Virtual Ride stream evidence may enter v2 Performance;
- ineligible API evidence retains an explicit reason.

### UI

- API-only summary metric cards use Strava summary evidence and match the normal RideWorks hierarchy;
- API-only Ride summary panel uses available Strava summary fields without FIT-only invention;
- post-export API-only power/HR chart;
- qualifying API-only watts/time stream shows activity-local best-20 with exact accepted complete-window semantics;
- API-only local best-20 is labeled Strava API stream evidence;
- qualifying API-only v2 result shows Compared with previous 6 weeks using the exact accepted prior-window semantics;
- HR-only / no-watts stream shows Best 20-minute power as Unavailable rather than using summary watts and persists a current ineligible Performance result;
- all 1,022 existing file-backed eligible results reproduce unchanged under v2;
- current live cohort becomes 1,027 eligible: 1,022 file-backed + 5 API-stream;
- FIT/API overlap rides remain file-backed Performance results, never duplicate API points;
- API stream with device_watts false/missing, non-high/full-length evidence, malformed timing or incomplete window remains ineligible;
- Performance provenance distinguishes file vs Strava API stream;
- user-facing pages avoid using Trusted Performance as an absolute quality label;
- source label/provenance;
- LA/Tokyo absolute date behavior;
- desktop/phone no overflow;
- restart retains stream-backed review;
- Sync now automatically rebuilds when Performance is pending under v2 and reports Performance updated;
- idempotent sync with pending=0 skips rebuild;
- policy migration v1→v2 triggers rebuild even when Strava returns no new Activities/streams;
- rebuild failure preserves synchronized evidence/checkpoint and prior committed Performance, leaves pending state, shows Performance update incomplete, and a later sync retries;
- HR-only current ineligible results do not keep the banner visible;
- successful sync/rebuild clears the banner without a second Owner action;
- manual rebuild/retry remains available only as recovery;
- P2-05 Settings/Activities/Performance regressions remain intact.

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
9. v2 rebuild independently proves all 1,022 accepted file-backed eligible results unchanged;
10. exactly the five qualifying API-only rides join Performance, for 1,027 eligible total on the current store;
11. the two HR-only rides have current explicit ineligible results and do not create a banner;
12. at least one qualifying API-only ride shows the normal Compared with previous 6 weeks panel;
13. run Sync now after the v2 policy change and prove it automatically converges Performance without a separate rebuild click;
14. rerun Sync now with no changes and prove it skips unnecessary rebuild/network stream fetches;
15. restart/idempotence;
16. SQLite integrity/foreign keys.

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
- show the API-only ride with normal summary cards, chart, Performance-eligible best-20, Ride summary and Compared with previous 6 weeks;
- show Settings after Sync now with Performance already current and no routine rebuild banner;
- demonstrate an exception/banner path synthetically or locally without corrupting the live store;
- stop for Owner review of whether Activity Review and Sync now now behave as one coherent workflow.

### Gate 2 — HARD — Analyst

After explicit Owner approval:

- verify Stage A evidence and its conclusion;
- verify `virtual-power-evidence-v2` exactly implements the Owner-approved eligibility/preference rules;
- independently verify 1,022 file-backed results unchanged and the five live API-only results eligible, with two HR-only results explicitly ineligible;
- verify API/FIT overlap precedence and no duplicate Performance points;
- verify automatic post-sync Performance convergence and exception-only banner semantics;
- verify source precedence/provenance/timing;
- verify bounded API access and no historical stream harvest;
- verify tests/restart/idempotence/integrity;
- accept or return actionable corrections.

Do not begin Phase 3 automatically after STRAVA-004.

## 16. Explicit non-goals

STRAVA-004 does not implement:

- historical bulk stream harvesting;
- broader/unvalidated API-stream eligibility beyond the exact v2 rules in §9;
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
- implementation would broaden API Performance eligibility beyond §9 without another Owner decision;
- stream enrichment would require a generalized source-reconciliation redesign;
- Phase 3/dashboard work begins to enter scope.

## 18. Handoff

At Owner Gate provide:

- branch / PR / head;
- focused/full test counts;
- Stage A comparison summary;
- graph-suitability conclusion;
- Performance-v2 eligibility conclusion and exact policy identifier;
- number of recent API-only Activities stream-enriched;
- number with usable power/HR graphs;
- number of API-only Activities eligible/ineligible for Performance and reasons;
- independent proof all 1,022 file-backed results are unchanged;
- final eligible cohort count (expected 1,027 on current live evidence);
- proof qualifying API ride receives prior-six-week context;
- proof Sync now automatically converges Performance and leaves no routine banner;
- bounded live API request count;
- review URL;
- verification report path;
- explicit statement that trusted Performance eligibility is unchanged and
  Phase 3 has not begun.
