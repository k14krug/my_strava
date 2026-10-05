# P2-05 verification — Owner setup / live acceptance pending

**Date:** 2026-10-05.
**Branch / PR:** `task/p2-05-strava-sync` / [#17](https://github.com/k14krug/my_strava/pull/17).
**Implementation head:** `51c700c324deea7ca60a5b077055584e0f3d9300`; subsequent publication updates evidence/status only.
**Controlling main:** `e631f9c`; Analyst-authored `docs/tasks/P2-05.md`.
**State:** implementation and synthetic/copied-history verification complete; stopped at
Gate 1 **HARD — Owner** under JIT §21's missing-credentials provision. P2-05 is
`in_progress`; no real OAuth connection, sync or live idempotence is claimed.
Phase 3 has not begun.

## Implemented workflow and authoritative review

`strava-connect`, `sync-strava`, `strava-disconnect` use standard-library HTTP/OAuth,
a temporary loopback callback, and the existing Store/browser surfaces. Requested
scope is only **activity:read_all**. Granted scopes and athlete identity are checked;
scopes are kept locally. State is cryptographically random and checked before exchange.

Current sources re-read on 2026-10-05:

- [Authentication](https://developers.strava.com/docs/authentication/): code exchange,
  granted scope inspection, access/refresh rotation, loopback redirect and revoke.
- [API reference](https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities):
  SummaryActivity listing with after/before/page/per_page.
- [Rate limits](https://developers.strava.com/docs/rate-limits/): overall/read limits,
  response headers, 429 and single-player capacity.
- [Webhooks](https://developers.strava.com/docs/webhooks/): supported events and
  reachable subscription callback; manual operation is the controlling JIT slice.
- [API Agreement](https://www.strava.com/legal/api) and
  [API Policy](https://www.strava.com/legal/api_policy): effective June 1, 2026.

Endpoints are `GET /oauth/authorize`, `POST /oauth/token`,
`GET /api/v3/athlete/activities`, `POST /oauth/revoke`. No detail/stream/lap/zone/
segment/social/gear/profile endpoints are used. API requests use fixed HTTPS
endpoints, a RideWorks User-Agent, 20-second timeout, Bearer header for activity
listing, and reject redirects. Revoke uses client Basic authentication. JSON is
bounded to 2 MiB and observations are shape-checked/allowlisted.

Tokens live in a 0600 file under the private data directory, outside SQLite.
Atomic replacement/fsync retains the newest refresh token before another request.
Refresh runs within one hour of expiry. A per-store file lock prevents concurrent
rotation/sync. 401/invalid refresh clears unusable local authorization without
history deletion or retries. Disconnect attempts revoke and clears local tokens
even when remote revocation/credentials are unavailable. Callback request URLs
are never logged; normal results/errors never print secrets/tokens or activities.

## Window, pagination and transaction

Initial after = midnight UTC on the latest stored export calendar day minus
**three days**. This tolerates unknown export timezone placement. No usable date
means stop without an unbounded historical fallback. Later after = successful
sync request cutoff minus three days. Before = this request's start time;
that cutoff is the successful checkpoint only after the data transaction commits.

Page size is 100; sequential requests stop at a short/empty page. A 20-page safety
bound prevents an unexpected response volume becoming a crawler. Rate headers are
parsed on every response; an exhausted known limit stops before another request,
and 429 stops immediately without retry. All pages validate before a Store write
transaction applies observations and checkpoint. Page/network/auth/shape/SQL
failure leaves no partial observation application and no checkpoint advance.
Token rotation can correctly survive a later failed sync.

## Source association and display

Schema 5 adds specific API Source observations, a current Strava-ID association,
and single-rider successful-sync state. Credentials/tokens are absent from schema.
Observation hashes cover only allowlisted useful metadata. Identical re-fetches
reuse observations; differing versions remain inspectable. A current pointer also
handles reversion to an already seen observation without duplicating it.

Established export/API Strava ID enriches its Activity. Conflicting established
identities stop. Otherwise a unique unassociated local candidate must agree on
absolute start exactly, compatible classification, elapsed duration within one
second, and distance within one metre when both supply it. Ambiguous or conflicting
local evidence creates a new API-backed Activity; title alone never associates.
No Sources move between established Activities.

Current non-empty API title/type evidence is preferred in presentation, with
export and API observations retained in provenance. API-only review is thin;
enriched FIT review remains rich. API summaries, including watts, stay attributable
API evidence and cannot become native Performance candidates. Added/changed source
context invalidates affected results under the accepted signature boundary until
explicit rebuild. The conditional API signature extension preserves unchanged
historical signatures; no automatic native scan or Performance rebuild occurs.

## Automated verification

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_rideworks_strava.py'
.venv/bin/python -m unittest discover -s tests
```

**20 focused tests passed in 2.022 s; 206 full tests passed in 11.384 s.**
The 186 accepted tests remain intact; migration expectations advance to schema 5.
New tests use fake credentials/responses exclusively, including an actual
loopback callback with fake token exchange. State/scope/athlete, private token
storage/rotation/failure, refresh/revocation, endpoint/header/timeout/size rules,
window boundaries, pagination, exhausted limits/429, transaction rollback,
idempotence/reversion, association, source/native preservation, browser metadata,
API-only exclusion, no implicit rebuild, credential errors and atomic migration
are covered. Automated tests make no Strava requests.

## Copied full history and isolated synthetic acceptance

`local_data/p2-05-review` was copied from the accepted P2-04 store with immutable
originals and SQLite backup. No historical archive was opened/imported and none
of the 1,421 source artifacts were reprocessed. Source and copy fingerprints
stream all 13 historical tables: all rows, IDs, metadata, native records/laps/events,
extractions and persisted Performance rows remain identical through schema 5.
Original sizes/modification times remain unchanged. **1,434 Activities / 1,022
eligible persisted results / zero pending** remain in the unsynced copy. SQLite
integrity and foreign keys are clean.

```bash
.venv/bin/python tools/prepare_rideworks_strava_review.py \
  --data-dir '<accepted-history-copy>' --synthetic-dir '<new-synthetic-directory>'
.venv/bin/python tools/verify_rideworks_recent_context_http.py \
  --data-dir '<accepted-history-copy>' --representative '<representative.fit.gz>'
```

The preparation tool separately creates an **isolated synthetic** store; it does
not add fake observations/tokens to the real-history review copy. Synthetic FIT/
CSV setup builds its own tiny fixture history before sync. Fake API initial sync
observes two records: **1 new Activity + 1 established enrichment**, for three
synthetic Activities in total. After closing/reopening, rerun records **zero new
Activities / zero new observations / 2 unchanged observations**. SQL guards deny
native record/lap/event reads during sync; archive/reparse/rebuild calls are guarded.
Native FIT and persisted Performance rows remain unchanged. API enrichment reports
one rebuild recommendation while keeping old calculations untouched. This is
synthetic correctness evidence, not a real Strava acceptance result.

The accepted full-history HTTP/restart verifier passes on the schema 5 copy:
1,434 total / 1,410 cycling, search/type/date/sort/pagination, source titles,
FIT rich and TCX/GPX/CSV thin review, prior-context restart and no private native
comparison payload. Representative remains **120 W** best-20 / **118 W** FIT
source average with accepted prior context; saved Performance rows remain intact.

## Actual Chromium

```bash
.venv/bin/python -m rideworks --data-dir local_data/p2-05-synthetic-review serve --port 8773
.venv/bin/python tools/verify_rideworks_strava_ui.py --port 8773 --session rideworks-p2-05
```

Managed Chromium passes actual Activities-to-review navigation for synthetic
API-only thin and enriched-FIT rich cases, API title preference and retained export
title provenance, browser-local dates, unchanged 1,200-record native chart and
120 W best-20, explicit stale Performance context, API summary-watt exclusion,
search/type/sort and desktop/phone without overflow. Screenshots were visually
inspected. They and exact synthetic routes remain ignored under `output/playwright`.

## Real acceptance and Owner setup

Real credentials are **not configured**. Live connection, activity-list requests,
new/enriched/unchanged counts and live restart/idempotence are **pending**, not zero
or passed. The unsynced Owner review copy still contains exactly 1,434 Activities.

1. Register/use the Owner's Strava application at [API settings](https://www.strava.com/settings/api).
   Configure a loopback-capable callback domain, `127.0.0.1` or `localhost`.
2. Set `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` locally in exported environment
   or ignored `.env`. Keep values out of chat/GitHub. Use the Owner's Strava account.
3. Run the commands below and grant activity:read_all in the browser. The temporary
   callback is `http://127.0.0.1:8772/strava/callback`; use --callback-port if needed.
4. Inspect aggregate sync output, restart the review server and rerun sync for live
   idempotence. Review new/enriched Activities naturally in the existing browser.

```bash
.venv/bin/python -m rideworks --data-dir local_data/p2-05-review strava-connect
.venv/bin/python -m rideworks --data-dir local_data/p2-05-review sync-strava
.venv/bin/python -m rideworks --data-dir local_data/p2-05-review serve --port 8771
.venv/bin/python -m rideworks --data-dir local_data/p2-05-review sync-strava
```

The preserved-history review server is running at **http://127.0.0.1:8771/**.
The separate **synthetic** server at port 8773 supplies example behavior only.
Its private route file is `output/playwright/p2-05-synthetic-links.json`; screenshots:
`p2-05-synthetic-thin-phone.png`, `p2-05-synthetic-rich-desktop.png` in that directory.
Ordinary disconnect: `strava-disconnect` with the same --data-dir; history is retained.

## Policy/webhook limitations and privacy

The current policy limits caching to seven days, restricts persistent indexes,
and requires deletion following revocation/termination and prompt reflection of
upstream deletions. The implementation retains durable API evidence and leaves
history on disconnect under the explicit Owner decision carried in JIT §4.6.
This is a documented conflict, not a claim of policy compliance. No concealment,
rate-limit evasion or historical API harvesting mechanism is implemented.

Manual overlap cannot guarantee arbitrary old edits/back-dated uploads/deletions.
Absence from a list is never interpreted as deletion. Public/unattended integration
requires revisiting webhooks; no background polling/public hosting is introduced.

Published evidence is aggregate-only. Real source data/database, tokens, IDs/titles,
locations and screenshots remain local/ignored. API geometry/social/profile/notes
are outside the allowlist. No real secret, athlete/activity ID or source path is
published. **Stop at HARD — Owner for setup/live workflow acceptance**, then HARD —
Analyst / Phase 2 acceptance after Owner approval. P2-05 remains `in_progress`;
Phase 3 has not begun.
