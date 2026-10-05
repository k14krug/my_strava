# P2-05 verification — HARD — Owner review

**Date:** 2026-10-05. **Branch / PR:** `task/p2-05-strava-sync` / [#17](https://github.com/k14krug/my_strava/pull/17).
**Runtime implementation:** `e4e77ffd5fa3e092038cecbba38f6d00446da084` (Settings foundation `c6c89f5`).
**Controlling main/JIT:** `e14c8c0`; includes `61d2ac7` explicit rebuild/reminder authorization.
P2-05 remains **in_progress**, stopped at **Gate 1 HARD — Owner**. Owner approval and Analyst acceptance are pending. Phase 3 has not begun.

## Normal workflow and action safety

Settings in the existing shell provides credential presence, connection/attention state,
Connect/Reconnect, Sync now, Disconnect, local last-successful time, compact outcome and
View Activities. CLI commands remain secondary. The running server receives the OAuth
callback; both paths share authorization URL generation, code exchange, scope/athlete
checks, token storage, sync and disconnect. Only **activity:read_all** is requested.

Actions require POST, a random one-use nonce and an allowed local Origin/Host. Repeated
submissions cannot reuse the nonce; controls disable while working. A local operation
lock and the per-store file lock reject overlapping operations. The loopback stdlib
server handles concurrent HTTP requests so browser preconnections and an in-flight
sync do not block unrelated requests; this does not introduce concurrent API fetching.

State expires after three minutes and is one-use. Callback completion/failure redirects
to clean `/settings`; callback URLs and exception text are not logged. Callback responses
use no-referrer; ordinary local forms use same-origin referrer policy, preserving the
Origin header Chromium needs. CSP restricts forms to this app/Strava authorization.
Private credentials/tokens never enter HTML or browser storage. A private 0600 derived
aggregate display file retains outcome/attention across restart; the SQLite successful
checkpoint remains authoritative and mismatched stale display counts are omitted.

## Authorized live-review corrections

The Owner's first live web result was **7 new / 4 enriched / 0 unchanged**. All seven
new Activities were API-only, but the browser originally placed them in its undated tail.
The cause was Python 3.10 rejecting Strava's RFC 3339 UTC **`Z`** in the presentation
parser. The fix accepts that UTC notation without changing original API evidence,
hashes, file-first source date precedence or timezone-unknown export dates.

Independent checks now prove:

- all seven are API-only, have absolute source dates and non-null chronological keys;
- all seven are later than the accepted cycling display baseline and form the newest seven;
- all seven individually open stable thin Activity Review routes;
- all four overlaps reuse established export Activity identities; none duplicates;
- **1,434 → 1,441 total / 1,410 → 1,417 cycling** is completely accounted for;
- LA/Tokyo Chromium contexts show correct local dates/times and Newest/Oldest ordering;
- focused mixed API `Z` + FIT/export + unknown-date tests preserve missing-date tails and local date filtering.

Current freshness also drives a neutral **Performance update needed** reminder on
Settings, Activities, Performance and Review. It includes affected count, explains
hidden affected results and retained ride data, cannot be dismissed and survives restart
without a reminder flag/table. **Rebuild Performance** is explicit, protected by the
same POST/nonce/origin rules, and calls accepted `rebuild_performance(store)` with its
atomic transaction. Sync does not call it. Failure retains previous results and the
reminder; zero pending after success clears it.

The live explicit web rebuild evaluated **1,441 Activities**, restored **1,022 eligible
results**, and cleared **11 pending → 0**. The reminder disappears across all pages and
restart. Original Sources/native records are unchanged; Performance rows are intentionally
replaced only by this explicitly requested accepted calculation.

## Forward sync, provenance and external boundary

Initial after = midnight UTC of the latest stored export calendar day minus **three
days**; later after = successful request cutoff minus three days. Before = request start,
committed as checkpoint only after observations commit. Missing boundaries stop without
a historical fallback. Sequential pages use 100 items, stop short/empty, and have a
20-page safety bound. Shape/network/rate/auth failures do not partially commit evidence
or advance the checkpoint. Exhausted limits/429 stop without retry.

Only authorization/token, activity-list and revoke endpoints are used. No detail, native
stream, lap, social, profile or historical archive crawl. Fixed HTTPS API endpoints,
20-second timeout, redirect rejection, bounded JSON and an evidence allowlist retain the
existing boundaries. Refresh within one hour of expiry atomically stores the newest
refresh token before further requests. Invalid authorization clears unusable tokens;
Disconnect attempts revoke and removes local tokens while retaining history.

Schema 5 keeps API observations/current identity/checkpoint separately from original
file/export evidence. Identical observations reuse Sources; changed observations retain
prior evidence. Established IDs enrich existing Activities. Otherwise association needs
one unique exact-time, compatible-type, duration-within-one-second and distance-within-
one-metre candidate when both distances exist. Title alone never associates; ambiguity
creates separate API evidence, established identity conflicts stop. API-only review stays
thin; enriched FIT retains native chart/summary. API watts never become native Performance.

Current authoritative documentation reviewed for the JIT/implementation on 2026-10-05:
[authentication](https://developers.strava.com/docs/authentication/),
[activity listing](https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities),
[rate limits](https://developers.strava.com/docs/rate-limits/),
[webhooks](https://developers.strava.com/docs/webhooks/),
[agreement](https://www.strava.com/legal/api), [policy](https://www.strava.com/legal/api_policy).
The documented current caching/persistent-index/deletion restrictions conflict with the
Owner's durable API-history/disconnect decision carried in JIT §4.6. This remains an
explicit policy tension, not a compliance claim. Manual overlap cannot guarantee arbitrary
old edits/back-dated uploads/deletions; absence is not deletion. Webhooks must be revisited
before public/unattended integration. No polling, evasion or public service was added.

## Tests and reproducible verification

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_rideworks_strava*.py'
.venv/bin/python -m unittest discover -s tests
```

**33 focused tests passed in 4.044 s; 219 full tests passed in 13.121 s.** Tests use fake
API credentials/responses, including real loopback callbacks and overlapping HTTP
requests. They cover private configuration/rotation, OAuth/CSRF/Origin/Host, restart,
refresh/revocation, paging/rates/failures, association/idempotence/native preservation,
API dates, app-wide reminder, accepted shared rebuild and transactional failure.

A fresh disposable accepted-history copy independently retains **1,434 Activities /
1,022 eligible / zero pending**, all 13 historical table fingerprints and originals,
clean integrity/foreign keys, and accepted bounded browsing/type/search/date/sort,
FIT rich and TCX/GPX/CSV thin, Performance/recent-context and process restart behavior.
The real review store had already received its initial live web sync while Dex was
verifying; it was preserved. The unsynced regression therefore uses the separate copy.

```bash
.venv/bin/python tools/prepare_rideworks_strava_review.py \
  --data-dir '<unsynced-accepted-copy>' --synthetic-dir '<new-synthetic-directory>'
.venv/bin/python tools/verify_rideworks_recent_context_http.py \
  --data-dir '<unsynced-accepted-copy>' --representative '<representative.fit.gz>'
.venv/bin/python tools/verify_rideworks_strava_settings_ui.py \
  --synthetic-dir '<new-settings-synthetic-directory>' --session rideworks-p2-05
.venv/bin/python tools/verify_rideworks_strava_live_ui.py \
  --data-dir '<authorized-live-copy>' --baseline '<unsynced-accepted-copy>' \
  --session rideworks-p2-05
.venv/bin/python tools/verify_rideworks_strava_surface_ui.py \
  --data-dir '<authorized-live-copy-with-11-pending>' --baseline '<unsynced-accepted-copy>' \
  --session rideworks-p2-05
```

The Settings verifier creates a fresh isolated fake store; intercepts the local POST's
303 authorization response before navigation and supplies a synthetic authorization page;
uses fake token/list/revoke responses; and exercises actual Chromium UI/callbacks. It
proves decline/reconnect/clean URL, sync/update, desktop/phone, LA/Tokyo date/order,
restart/refresh/idempotence, reminder on all four pages, failed rebuild retaining rows,
explicit rebuild clearing reminder, and Disconnect retaining history. API-only/rich/native
120 W/provenance/stale-context/Performance/filter regressions also pass. Early browser
probes exposed the Origin/referrer issue and a single-thread preconnection stall; both
were corrected. One early dummy-credential redirect reached Strava's logged-out login
page before interception was corrected; no Owner credentials were used, and no
token exchange or activity-list request occurred in that failed synthetic probe. The final synthetic verifier intercepts before navigation.
Screenshots were inspected and remain ignored locally.

Initial live OAuth/first sync interaction was performed outside Dex's browser automation;
its private connection and saved aggregate web outcome were observed, and Owner/Analyst
PR feedback independently confirmed that interaction. Dex then drove live manual Settings
reruns with native record/lap/event read denial and archive/reparse/rebuild guards.
Each restart rerun adds **0 Activities / 0 observations**, with **3 unchanged** from the
narrower rolling overlap. Initial calendar overlap and later checkpoint overlap are
intentionally different; the remaining initial observations persist. The final rerun
also preserves rebuilt Performance history, with **zero pending / 1,022 eligible**.
SQLite checks and accepted original Activity rows/Sources/native evidence remain intact.
No real login automation or live Disconnect was performed; synthetic coverage proves
Disconnect and the Owner's live connection is retained for review.

## Owner review

Server is running at **http://127.0.0.1:8771/settings**. Open **View Activities** or
**http://127.0.0.1:8771/** to inspect the corrected newest seven.

```bash
.venv/bin/python -m rideworks --data-dir local_data/p2-05-review serve --port 8771
```

Credentials are already configured locally. For a fresh setup: `cp -n .env.example .env`,
edit ignored STRAVA_CLIENT_ID/STRAVA_CLIENT_SECRET locally (exported overrides win), set
Strava Authorization Callback Domain to host-only `127.0.0.1`, then use Settings Connect.
Web callback is `http://127.0.0.1:8771/strava/callback` on this running server. CLI connect
uses secondary temporary port 8772 by default; CLI sync/disconnect/rebuild remain in README.

Published evidence is aggregate-only. Personal archives/DBs, credentials/tokens, private
IDs/titles/coordinates/routes/screenshots remain local/ignored. Review needed: Owner's
in-app workflow and corrected Activities/rebuild/reminder behavior. After explicit Owner
approval, record it and stop at **HARD — Analyst / Phase 2 acceptance**. No Phase 3 work.
