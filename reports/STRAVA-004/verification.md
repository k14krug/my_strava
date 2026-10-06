# STRAVA-004 verification

The October 6, 2026 Owner-approved Performance and sync correction is implemented from Analyst JIT `f9711f4`, refreshed from `main` at `2e3ca9b`. Invocation: `/TASK PR18`. Runtime implementation: `cce020be55dfbe2d5162089e49f667980b2ca7a5`. Stopped at **Gate 1 — HARD — Owner**; task remains `in_progress`, ready for review. Phase 3 has not begun.

## Current result

**1,027 eligible / zero pending** under `virtual-power-evidence-v2`: all **1,022 existing file-backed eligible results reproduced unchanged**, plus **five newly eligible API-only Virtual Rides**. The two HR-only API Activities have explicit current ineligible rows (`outdoor_ride_excluded`: both are outdoor Rides) and cause no banner. The four FIT/API overlaps remain one file-backed point each. The current store has 1,441 Activities, 11 stream observations, 1,441 preserved historical v1 rows and 1,441 current v2 rows.

The [latest Owner correction](https://github.com/k14krug/my_strava/pull/18#issuecomment-6020749731) explicitly supersedes the prior prohibition on API Performance eligibility and the separate routine rebuild action. This report describes current v2 behavior; earlier 1,022-only and manual-rebuild evidence is retained as historical evidence in [acceptance.json](acceptance.json). The JIT's older handoff footer saying eligibility is unchanged is superseded by its §9 and the explicit Owner correction; task controls and JIT were not edited by Dex.

Normal web and CLI sync share **metadata → bounded stream enrichment → freshness → rebuild only if pending**. The first unchanged-data live sync automatically migrated v1 to v2. The second unchanged live sync skipped rebuild. A real Chromium **Settings → Sync now** then also skipped rebuild, displayed **Performance is current**, and left no exception banner. Each request reused the three stream candidates in its existing recent window; no new stream requests or observations were needed.

## Policy, provenance and failure handling

Only Virtual Ride classification qualifies. File-backed power takes precedence, including retained file power that fails the accepted native window rules. API evidence cannot rescue an ineligible file-power result. Existing native-source ambiguity rules are unchanged. File averages/lap summaries may establish retained power evidence but never substitute for sample power.

API fallback requires exactly one current summary/stream pair, `device_watts=true`, time and watts present, both high resolution and full length (`original_size == returned_length`), equal lengths, valid strictly increasing nonnegative integer second offsets, and a complete exact-one-second 1,200-sample power window. Retained watts obey the stream contract (nonnegative integers or null). Zero watts count; gaps, missing values, downsampling and invalid timing are not repaired. Method remains `best-average-power-v1`: highest raw mean, earliest exact tie, integer half-up display rounding.

API results leave native Source/extraction columns null and retain explicit stream/summary Source IDs, digest/mapping, device watts, metadata, method/policy/duration, raw/rounded watts, returned-offset bounds and window counts in result JSON. The input signature includes current stream/summary identities, digest/mapping, summary values and classification; changed observations stale v2. No API samples enter native records, and no native extraction identity or native window timestamp is fabricated. Historical v1 rows remain intact; current pages select v2 only.

All five eligible API rides now show normal **Compared with previous 6 weeks** context. Both endpoints of `(Activity start − 42 days, Activity start)` are excluded; the current Activity excludes itself. Highest raw watts win, followed by earliest Activity start and stable Activity ID. Current/prior evidence kinds are inspectable. Performance pages use policy/provenance rather than an absolute “Trusted Performance” quality label.

An atomic rebuild failure preserves committed source/stream evidence, sync checkpoint and prior Performance rows. Pending results show **Performance update incomplete** and **Retry Performance update**. Synthetic Chromium verified failure, failed manual retry, persistent exception after restart, and successful retry on a later unchanged sync. Current but ineligible results do not keep a banner active. No failure was induced in the live history.

## API access and limits

Official Strava sources were checked for the initial stream implementation: [streams reference](https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams), [authentication](https://developers.strava.com/docs/authentication/), [rate limits](https://developers.strava.com/docs/rate-limits/). Existing `activity:read_all` authorization is reused. The endpoint remains `GET /api/v3/activities/{id}/streams` with only `time,watts,heartrate,cadence,moving` and `key_by_type=true`.

Initial access was **four Stage A + seven bounded catch-up = 11 stream GETs**. This correction made **zero new stream GETs** and **three bounded forward/recent metadata GETs** (migration, unchanged rerun, real web sync). All-seven restart reuse made zero requests/new observations. Initial stream responses exposed no rate-header values; that historical absence is not treated as zero usage. Latest observed metadata headers: application limit **200 / 2,000**, usage **1 / 3**; read limit **100 / 1,000**, usage **1 / 3** (15-minute / daily). Earlier two-sync aggregate observed usage was 2 / 2; separate per-call snapshots were not retained then. Sync now returns detached header snapshots. These are observed headers, not a prediction of remaining budget.

Fetches remain sequential, with existing refresh locking/rotation, 20-second timeout, fixed HTTPS endpoints, no redirects, finite 16 MiB stream limit and 2 MiB metadata/token limit. Synthetic exhaustion/429 checks stop without busy retry. No coordinates, maps, segments, zones, historical athlete crawl or background polling are requested. Source commits survive optional stream failures. Reuse now also requires the current related summary Source; changed summaries require a fresh paired stream observation before qualifying under v2.

## Stage A comparison

Every overlap returned all five requested types. For **each type** in each row below, metadata was `resolution=high`, `series_type=distance`, and `original_size=returned_length=sample count`. Returned metadata is evidence, not an assertion of one-second sampling: actual time offsets were checked independently.

| Anonymous overlap | API/FIT samples | Elapsed offset range (s) | API and FIT consecutive deltas | Power zeros | HR zeros |
| --- | ---: | --- | --- | ---: | ---: |
| overlap-1 | 2,836 | 0–2,847 | 2,834 × 1 s; 1 × 13 s | 49 | 45 |
| overlap-2 | 3,135 | 0–3,134 | 3,134 × 1 s | 18 | 165 |
| overlap-3 | 3,484 | 0–3,483 | 3,483 × 1 s | 25 | 0 |
| overlap-4 | 3,621 | 0–3,620 | 3,620 × 1 s | 17 | 0 |

All API summary starts equaled their FIT session starts (difference 0 seconds). Pairing used **API summary `start_date` + returned offset versus original FIT record timestamp**, with no fitted time shift, index-only pairing, interpolation, or normalization. No duplicate/backward offsets or missing FIT timestamps occurred. Power and HR each had zero missing samples, 100% timestamp coverage, 100% exact agreement, and identical zero counts/patterns. No mismatches needed examples; the 13-second gap in overlap-1 exists in both sources.

Across four rides, each signal had **13,076 exact timestamp pairs**, with zero maximum/mean absolute differences. Sample cadence cannot be compared because the accepted FIT extraction retains only summary cadence. Moving values remain API evidence without invented equivalent FIT flags. These overlaps do not establish fidelity across every Activity/signal or prove measured origin.

The independent experiment segments exact one-second runs and enumerates complete 1,200-sample windows using prefix sums. Gaps or missing power split runs. It uses the accepted complete-window semantics and earliest equal maximum, independently of the production best-20 result. These initial experimental outputs were comparison evidence. The current v2 rebuild retains the overlap results as file-backed power, with no duplicate API points.

| Overlap | Best-20 raw mean (W), API = FIT | Rounded W | Elapsed window [start, end) s | Sum W / 1,200 samples | Eligible windows |
| --- | ---: | ---: | --- | ---: | ---: |
| overlap-1 | 93.32166666666667 | 93 | [13, 1,213) | 111,986 | 1,040 |
| overlap-2 | 181.08583333333334 | 181 | [71, 1,271) | 217,303 | 1,936 |
| overlap-3 | 100.155 | 100 | [480, 1,680) | 120,186 | 2,285 |
| overlap-4 | 120.11916666666667 | 120 | [204, 1,404) | 144,143 | 2,422 |

Raw API-minus-FIT mean difference was 0 W for each; absolute window alignment was identical. The initial comparison did not itself authorize analytical eligibility. The later explicit Owner decision authorizes the strict v2 policy above. Full anonymous per-signal statistics and stream metadata remain under `historical_v1_verification` in [acceptance.json](acceptance.json).

## Activity Review and preservation

Schema 6 stream evidence remains distinct from native records and API summary values. Each immutable observation retains allowed arrays/order, metadata, requested keys, retrieval time, mapping, digest and related summary Source. API-only review uses normal four summary cards → chart → best-20/six-week panel, with Ride summary beside it and collapsed provenance below. Cards and Ride summary use current supplied Strava summary fields; no FIT timer duration is invented. The calculated panel remains labeled **RideWorks-calculated from Strava API stream evidence**, with returned offsets and inspectable v2 eligibility.

Charts preserve nulls and zeros, and break at missing samples or gaps longer than one second. Presentation timestamp uses related summary start plus retained offset. Compact browser-local date/time stays on one line and omits the GMT suffix. All seven complete browser payload hashes/counts/offsets and plotted power/HR counts match retained arrays. Five have power+HR; two have HR only, including a sparse 22-sample observation. Supported FIT chart/review/best-20 remains unchanged and authoritative.

Before migration, a fresh ignored schema-6 backup was made without copying authorization tokens. All 1,441 historical v1 rows are byte-for-byte preserved. Native/export evidence table fingerprints and original file sizes/mtimes are unchanged. Migration intentionally changes current derived Performance and the sync checkpoint; the earlier statement that all 16 accepted tables stayed unchanged belongs to the historical pre-v2 verification. Current review/restart/idempotent stream reuse changes no tables. Final real web sync changes only the sync checkpoint and derived Settings display state. No archive reimport, original-file reparse or re-extraction occurred. SQLite integrity/FKs and restart checks passed.

P2-05's accepted local API retention decision remains controlling. Raw responses, arrays, authorization, databases, private IDs/titles/routes and live screenshots remain ignored local artifacts. Committed outputs contain only aggregate or anonymous evidence.

## Verification and reproduction

**253 full tests passed**, plus **57 focused Strava / 38 focused Performance tests**. New v2 tests cover strict API confirmation/resolution/length/timing/window rules, legitimate zero power, file precedence/no rescue, competing current identities, changed streams/summaries, source signatures, policy migration with unchanged metadata, atomic failed convergence, persisted source/checkpoint and retry on unchanged sync. Existing tests cover stream validation/provenance, token refresh, bounded/rate-limited/failed enrichment and native complete-window behavior.

Independent live checks verified all 1,022 native eligible results against both prior v1 calculation/provenance and a separate contiguous-segment/prefix-sum/Decimal oracle. All five API results match the independent returned-offset prefix verifier; all five exact six-week contributors match a separate direct scan. Performance presentation was independently checked at **2,025 event times**, including **208 rolling changes**, four summary cards and exact 42-day expiry. No duplicate overlap points, zero pending, all historical rows retained, originals/evidence unchanged, integrity/FKs and restart all passed.

Actual Chromium passed all seven live reviews, eligible API six-week/provenance, Performance point provenance and rolling/monthly/yearly views, FIT precedence, desktop/phone layouts and Los Angeles/Tokyo dates. Restart/reuse verifies all seven observations with zero stream GETs. Fresh synthetic Settings/OAuth/reconnect/refresh/disconnect, successful automatic convergence, failure/manual retry/restart/later-sync retry, and new-ride zero/null/gap chart checks passed. The final live web check independently confirms Settings outcome persistence and skips unnecessary rebuild.

Executed correction commands (inputs/outputs are ignored local data):

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_rideworks_strava*.py'
.venv/bin/python -m unittest discover -s tests -p 'test_rideworks_*performance*.py'
.venv/bin/python -m unittest discover -s tests
.venv/bin/python tools/verify_rideworks_performance_v2.py --data-dir local_data/p2-05-review --baseline local_data/strava-004-v2-baseline
.venv/bin/python tools/verify_rideworks_strava_stream_ui.py --data-dir local_data/p2-05-review --session rideworks-strava-004 --live
.venv/bin/python tools/verify_rideworks_strava_stream_synthetic.py --synthetic-dir local_data/strava-004-v2-stream-synthetic --session rideworks-strava-004
.venv/bin/python tools/verify_rideworks_strava_settings_ui.py --synthetic-dir local_data/strava-004-v2-settings --session rideworks-p2-05
.venv/bin/python tools/verify_rideworks_performance_v2_web.py --data-dir local_data/p2-05-review --session rideworks-strava-004
```

The migration verifier performs two real bounded metadata syncs and requires a pre-migration v1 review store with the retained 11 observations, plus a fresh ignored baseline path. **Do not rerun it against the now-migrated store**: its initial-state assertions deliberately reject that. The separate web verifier performs one real bounded metadata sync on a current v2 store. Neither requests new streams when the cache remains current. Repeating either live operation still consumes metadata API calls.

Read-only live browser verification requires an open Playwright CLI Chromium session; it makes no external API requests. Synthetic verifiers use fake HTTP and require fresh disposable directory names. To recompute the original Stage A comparison without network access:

```bash
.venv/bin/python tools/compare_rideworks_strava_streams.py --data-dir local_data/p2-05-review --cache-dir local_data/strava-004-stage-a
```

Original one-time Stage A/catch-up commands and exact historical fingerprints remain in the prior report at commit `ee84c97`; those initial-state checks are not appropriate after intentional policy migration. No new export import or source reconstruction is needed for v2.

## Owner handoff

Branch `task/strava-004-streams`; draft [PR #18](https://github.com/k14krug/my_strava/pull/18); runtime head `cce020be55dfbe2d5162089e49f667980b2ca7a5`. Review app: `http://127.0.0.1:8771/`. Private `output/playwright/strava-004-review-links.json` identifies the newest eligible API ride, both HR-only rides and a FIT overlap; targeted links are supplied directly to Ken. Inspect Calculation details, Comparison details, Summary source and Strava API stream evidence for provenance. Settings shows the completed normal sync with Performance already current.

Required Owner review: does the normal API-only Activity Review (summary cards, chart, Performance-eligible best-20, six-week context and Ride summary) together with one-step Sync now form a useful, coherent and honest workflow? **Stopped at Gate 1 — HARD — Owner**, as required by the Analyst-authored JIT §15. Explicit Owner approval precedes Gate 2 — HARD — Analyst. Substantive task acceptance and Phase 3 remain pending; no next task begins automatically.


## Owner approval and Gate 2 handoff

On **2026-10-06**, the Owner explicitly approved the final STRAVA-004
Activity Review and one-step Sync now workflow, including
`virtual-power-evidence-v2`, six-week context for eligible API-only rides,
file-backed precedence, honest HR-only/ineligible handling, and
exception-only Performance freshness banners.

STRAVA-004 remains `in_progress` pending final Analyst review.
Phase 3 has not begun.
