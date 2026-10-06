# STRAVA-004 verification

Initial Stage A/B verification completed October 5, 2026 (America/Los_Angeles), from Analyst JIT on refreshed `main` at `719db85`. The October 6 Owner Activity Review correction is implemented from updated JIT `d88033b`, merged into the existing PR branch. Invocation: `/TASK PR18`. Stage A supported proceeding to Stage B under the JIT's evidence gate. Stopped at **Gate 1 — HARD — Owner**; task remains `in_progress`. Phase 3 has not begun.

## Result and limits

All four accepted Strava/FIT overlap rides supported power/heart-rate Activity Review: 13,076 exact timestamp pairs per signal, 100% pairing and exact value agreement, no missing-pattern differences, and zero maximum/mean absolute differences. Independent experimental best-20 means and selected windows also matched for all four qualifying rides.

The bounded catch-up added usable charts for all **7 known post-export API-only cycling Activities**: **5 have power and HR; 2 have HR only**. Absent power stays unavailable, including a sparse 22-sample HR observation. Four additional stream observations came from the existing Stage A cache, with no repeat overlap requests. Supported FIT review remains authoritative; its additional API stream provenance is inspectable separately.

This evidence supports visual review of the tested power/heart-rate streams. It does not establish measured origin, fidelity across all Activities/signals, or trusted analytical eligibility. Cadence could not be compared because the accepted FIT extraction has no sample cadence; FIT average cadence is not a sample series. Moving values were retained as API evidence, without inventing equivalent FIT flags. Similarity warrants a separate future eligibility investigation; **no trusted Performance policy changed**. Accepted Performance remains **1,022 eligible / 0 pending**, and all accepted database tables, including existing results/signatures, remained unchanged.

The [Owner correction](https://github.com/k14krug/my_strava/pull/18#issuecomment-6008558160) authorizes normal Activity Review structure and ride-local API-stream best-20. All seven API-only rides now have summary cards and a Ride summary panel. **Five qualifying rides have a calculated local best-20; two HR-only rides show Unavailable.** These results are for individual Activity Review and are never persisted into trusted Performance. The correction reused retained observations and made **zero additional live API requests**.

## Authoritative API check

Reviewed official Strava documentation October 5, 2026. The existing `activity:read_all` authorization and private token file were reused; no additional scope or second connection was needed. Requests use `GET https://www.strava.com/api/v3/activities/{id}/streams`, exactly `time,watts,heartrate,cadence,moving`, and `key_by_type=true`. The documented stream metadata includes `original_size`, `resolution`, and `series_type`. [Streams reference](https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams), [authentication](https://developers.strava.com/docs/authentication/).

Live stream access was limited to **4 Stage A GETs + 7 catch-up GETs = 11 total**. Restart/idempotent rerun made **0 stream GETs** and created **0 observations**. Rate headers were inspected by the client, but no rate-limit values were observed/exposed in these live responses (`rate_limits: {}`); remaining budget/usage is therefore unavailable, not zero. Synthetic tests verify known exhaustion and HTTP 429 stop without busy retry. Fetches are sequential, retain existing refresh locking/rotation, use a 20-second timeout, fixed HTTPS endpoints, no redirects, and a finite 16 MiB stream response limit. The metadata/token limit remains 2 MiB. [Rate limits](https://developers.strava.com/docs/rate-limits/).

No coordinates, maps, segments, laps, zones, athlete history crawl, or background polling were requested. Normal Sync now uses only its existing bounded forward/recent window for API-only cycling candidates. Missing or failed optional streams can be retried on a later explicit sync; metadata commits survive stream failures.

## Stage A comparison

Every overlap returned all five requested types. For **each type** in each row below, metadata was `resolution=high`, `series_type=distance`, and `original_size=returned_length=sample count`. Returned metadata is evidence, not an assertion of one-second sampling: actual time offsets were checked independently.

| Anonymous overlap | API/FIT samples | Elapsed offset range (s) | API and FIT consecutive deltas | Power zeros | HR zeros |
| --- | ---: | --- | --- | ---: | ---: |
| overlap-1 | 2,836 | 0–2,847 | 2,834 × 1 s; 1 × 13 s | 49 | 45 |
| overlap-2 | 3,135 | 0–3,134 | 3,134 × 1 s | 18 | 165 |
| overlap-3 | 3,484 | 0–3,483 | 3,483 × 1 s | 25 | 0 |
| overlap-4 | 3,621 | 0–3,620 | 3,620 × 1 s | 17 | 0 |

All API summary starts equaled their FIT session starts (difference 0 seconds). Pairing used **API summary `start_date` + returned offset versus original FIT record timestamp**, with no fitted time shift, index-only pairing, interpolation, or normalization. No duplicate/backward offsets or missing FIT timestamps occurred. Power and HR each had zero missing samples, 100% timestamp coverage, 100% exact agreement, and identical zero counts/patterns. No mismatches needed examples; the 13-second gap in overlap-1 exists in both sources.

The independent experiment segments exact one-second runs and enumerates complete 1,200-sample windows using prefix sums. Gaps or missing power split runs. It uses the accepted complete-window semantics and earliest equal maximum, independently of the production best-20 result. These experimental outputs are not persisted as trusted results.

| Overlap | Best-20 raw mean (W), API = FIT | Rounded W | Elapsed window [start, end) s | Sum W / 1,200 samples | Eligible windows |
| --- | ---: | ---: | --- | ---: | ---: |
| overlap-1 | 93.32166666666667 | 93 | [13, 1,213) | 111,986 | 1,040 |
| overlap-2 | 181.08583333333334 | 181 | [71, 1,271) | 217,303 | 1,936 |
| overlap-3 | 100.155 | 100 | [480, 1,680) | 120,186 | 2,285 |
| overlap-4 | 120.11916666666667 | 120 | [204, 1,404) | 144,143 | 2,422 |

Raw API-minus-FIT mean difference was 0 W for each; absolute window alignment was identical. No analytical eligibility inference was made from this result. Full anonymous per-signal statistics and stream metadata are in [acceptance.json](acceptance.json).

## Stage B behavior and preservation

Schema 6 adds three narrow stream observation/current/attempt tables. Each durable observation retains exact allowed arrays/order, returned metadata, requested keys, retrieval time, mapping version, content digest, and related API summary Source. It stays separate from native records and API summary values. Identical observations reuse a Source; changed observations retain prior evidence. A changed summary start invalidates the older chart mapping until another fetch.

API-only charts use returned elapsed offsets directly. Nulls remain unavailable; zeros remain zero; missing samples and gaps longer than one second break paths. Presentation date/time uses the related summary start plus the retained offset, documented in the review. The new chart header uses compact browser-local date/time without a GMT suffix and does not split the timestamp across lines. Summary watts never become chart samples or trusted best-20. API evidence has an explicit source label and expandable provenance/stream metadata. Unsupported or ambiguous file-backed Activities do not substitute API charts for native review.

The accepted schema-5 database was backed up locally before stream persistence, without copying authorization tokens. Fingerprints of all 16 pre-existing tables matched after enrichment and again after final UI verification. Live state: **1,441 Activities / 11 stream observations / 7 usable API-only graphs (5 power+HR, 2 HR-only)**. Source original sizes/mtimes were unchanged. The catch-up denied native records/laps/events reads and guarded import, re-extraction, and Performance rebuild paths; none occurred. SQLite integrity and foreign-key checks passed. Existing cohort, cached calculations, and input signatures remained unchanged, with 1,022 eligible / 0 pending after restart.

The existing P2-05 accepted retention decision still governs local API history. This task introduced no new retention-policy decision. Raw responses, token state, databases, private routes/titles/identifiers, and live screenshots remain ignored local artifacts; no raw personal arrays are committed.

API-only reviews now follow the normal summary-cards → chart → local best-20 hierarchy with Ride summary beside it and collapsed provenance below. The four cards and Ride summary use the **current Strava API summary Source**, including elapsed/moving duration, distance/ascent, supplied power/HR averages/maxima, cadence, and energy where present. Missing fields show Unavailable; no FIT timer duration is invented and supplied averages are not calculated from streams.

The local calculation is labeled **RideWorks-calculated from Strava API stream evidence** and uses `best-average-power-v1` semantics directly on returned offsets. It searches exact one-second, complete 1,200-sample windows; zero watts count, gaps/duplicate/backward edges or missing power invalidate affected windows. Raw maximum wins, exact ties choose the earliest window, and display rounding is integer half-up. Details expose offset bounds, raw mean, sample/window counts, stream Source, related summary Source, retrieval and mapping. It creates no native record indices/timestamps, no result rows, no trusted enrollment, and no prior-six-week context.

After the correction, all 16 accepted schema-5 table fingerprints again matched the original backup. The Chromium verifier also checks that **all current schema-6 tables** are unchanged across review/calculation and restart/idempotent reuse. Originals, integrity/FKs, 1,441 Activities, 11 stream observations, and 1,022 eligible / zero pending remain intact.

## Verification and reproduction

**243 full tests / 57 focused Strava tests passed** on final runtime code. Tests cover strict endpoint/key/type/size validation, non-finite and malformed values, absent/zero signals, timing gaps/duplicates, independent complete windows, shared token rotation, atomic schema migration, changed/identical observations, restart, FIT precedence, failed/rate-limited/unauthorized optional enrichment, and successful metadata retention. Seven correction tests add exact local-window boundaries, legitimate zeros, raw selection/ties, half-up rounding, missing/short/downsampled/ambiguous input, affected timing edges, comparison with the independent prefix-sum verifier, current-summary versus stream values, HR-only unavailability despite summary watts, and unchanged persisted tables. Existing metadata-only fixtures remain focused on metadata; integration tests exercise the stream HTTP endpoint and Settings path.

Actual Chromium checks passed against both the live local store and synthetic fake-HTTP fixtures:

- All 7 live API-only charts: exact complete browser payload hashes, returned counts/offsets, power/HR points, source metadata, keyboard inspection, and no native/trusted Performance claims. All seven have normal summary cards and Ride summary; five local best-20 means, rounded values, returned-offset bounds and eligible-window counts match the independent prefix-sum verifier; two HR-only results are unavailable with explicit reasons.
- FIT overlap: unchanged native chart points and best-20, with additional stream provenance inspectable.
- Synthetic normal Settings Sync now: a newly discovered API-only Activity gains its graph in one explicit workflow; zeros, missing values, and gap path breaks verified.
- Desktop/phone layouts and Los Angeles/Tokyo browser-local dates; graph, local review result, summaries, and connection survive server restart. Idempotent rerun reuses all seven observations with zero stream GETs, zero new observations, and all persisted tables unchanged.
- Full P2-05 Settings/OAuth/reconnect/refresh/disconnect and explicit Performance rebuild regression, including persistent reminder and failed rebuild preservation.

Executed commands (paths are ignored local data, not repository inputs). The Stage A fetch and catch-up lines below ran once during initial implementation; the correction reran the focused/full suites and browser verifiers using retained streams only:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_rideworks_strava*.py'
.venv/bin/python -m unittest discover -s tests
.venv/bin/python tools/compare_rideworks_strava_streams.py --data-dir local_data/p2-05-review --cache-dir local_data/strava-004-stage-a --fetch
.venv/bin/python tools/verify_rideworks_strava_enrichment.py --data-dir local_data/p2-05-review --baseline local_data/strava-004-baseline --stage-a-cache local_data/strava-004-stage-a
.venv/bin/python tools/verify_rideworks_strava_stream_ui.py --data-dir local_data/p2-05-review --session rideworks-strava-004 --live
.venv/bin/python tools/verify_rideworks_strava_stream_synthetic.py --synthetic-dir local_data/strava-004-correction-synthetic --session rideworks-strava-004
.venv/bin/python tools/verify_rideworks_strava_settings_ui.py --synthetic-dir local_data/strava-004-correction-settings --session rideworks-p2-05
```

The fetch command requires a fresh private cache and performs the four explicitly bounded live requests. Omit `--fetch` to recompute comparisons from the retained cache without network access. The one-time enrichment verifier requires a fresh accepted baseline/store and asserts unchanged accepted tables before starting; do not use it to repeat the completed live catch-up. Its built-in restart rerun proves reuse without fetching. Browser verifiers make no external API requests; they require an open Playwright CLI Chromium session. Synthetic fixtures use fake HTTP and disposable local stores.

The final 16-table baseline check uses the same `fingerprint` helper, with read-only connections. Reproduce it without opening token state or calling the API:

```bash
.venv/bin/python - <<'PY'
import sqlite3, sys
sys.path.insert(0, 'tools')
from compare_rideworks_strava_streams import fingerprint
with sqlite3.connect('file:local_data/strava-004-baseline/rideworks.sqlite3?mode=ro', uri=True) as db:
    accepted = fingerprint(db)
with sqlite3.connect('file:local_data/p2-05-review/rideworks.sqlite3?mode=ro', uri=True) as db:
    current = fingerprint(db)
assert all(current[table] == digest for table, digest in accepted.items())
print(len(accepted), 'accepted tables unchanged')
PY
```

## Owner handoff

Branch: `task/strava-004-streams`; draft [PR #18](https://github.com/k14krug/my_strava/pull/18); verified correction implementation head `c84b74dd16edb64dd22dc54e6181277f18698163`. Existing review app: `http://127.0.0.1:8771/`. Private local `output/playwright/strava-004-review-links.json` identifies the newest API-only ride and a FIT-backed overlap; targeted links are supplied directly to the Owner, rather than published here. Expand **Strava API stream evidence** to inspect provenance. The newest ride shows the four summary cards, API graph, qualifying local best-20, and Ride summary; the overlap keeps native review. The private route file also includes both HR-only rides for unavailable-result review.

The required decision is whether the API-only Activity Review as a whole is **useful, structurally complete enough, and honest** about its source, timing, gaps, and eligibility. The JIT explicitly requires stopping here for Owner review. After explicit Owner approval, Gate 2 is Analyst review of evidence and implementation; there is no automatic acceptance or next task.
