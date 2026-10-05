# STATUS.md

**Product:** RideWorks. Phase 1 accepted; Phase 2 in progress.

**Accepted:** P2-01/P2-02/P2-03/P2-04 done; PR #16 merged as `16ef375434700ab7d2b5fb3a5c2cae000e049c12`.

**Current task:** P2-05 — in_progress.

**Branch / PR:** `task/p2-05-strava-sync` / [#17](https://github.com/k14krug/my_strava/pull/17) (draft).

**Implementation head:** `dea29b97622fcdd21a392e071932fbc8b9b83a9c`; subsequent publication adds evidence/status only.

**Implementation state:** awaiting_owner_setup_review — PR #17 credential setup correction complete under Analyst JIT `159b236`, invoked with /TASK. Stopped again at Gate 1 HARD — Owner under its missing-credentials provision.

**Implemented:** explicit connect/manual sync/disconnect; activity:read_all only; private atomic token rotation; sequential list endpoint with three-day export/checkpoint overlap and safe rate/error handling. Schema 5 API Source observations/current identity/checkpoint retain provenance and conservative association. API-only review thin; enriched FIT retains native summary/chart; stale Performance is explicit with no hidden rebuild. No historical API/archive crawl or source reprocessing.

**Verification:** 206 full / 20 focused tests rerun passed with fake HTTP only; actual example-copy configuration path, safe blanks and exported overrides verified. Prior runtime/copied-history/Chromium evidence retained unchanged. Actual loopback OAuth test. Full-history copy: all 13 historical tables, originals, 1,434 Activities and 1,022 current eligible results preserved; SQLite checks and accepted HTTP/restart regression pass. Isolated synthetic sync: 1 new + 1 enrichment; restart rerun 0 new Activities/observations and 2 unchanged; native-read/reparse/rebuild guards pass. Chromium synthetic thin/rich/provenance/native/stale-context/local-date/filter/desktop/phone checks pass.

**Live acceptance:** pending — client credentials not configured; no live connection/sync or live idempotence claimed. Real-history review copy still has 1,434 Activities. Keep tokens/credentials local.

**Evidence:** `reports/P2-05/verification.md`, `reports/P2-05/acceptance.json`, `rideworks/README.md`.

**Owner setup:** run `cp -n .env.example .env`, then fill STRAVA_CLIENT_ID / STRAVA_CLIENT_SECRET in ignored .env (preserve existing settings; exported values override). In Strava API settings, Authorization Callback Domain = `127.0.0.1` (host only); RideWorks redirect = `http://127.0.0.1:8772/strava/callback`. Connect: `.venv/bin/python -m rideworks --data-dir local_data/p2-05-review strava-connect`. Sync: same prefix + `sync-strava`. Review: http://127.0.0.1:8771/; startup same prefix + `serve --port 8771`. Restart/rerun sync for live idempotence. Port 8773 / local_data/p2-05-synthetic-review is isolated fake evidence only.

**Policy boundary:** current Strava caching/deletion restrictions conflict with the Owner's documented durable API-history decision; retained honestly under JIT §4.6. Manual overlap is not real-time or old-edit/delete detection. Webhooks deferred until public/unattended integration.

**Next action:** Owner configures/authorizes local Strava, completes real connect/sync/restart/rerun and reviews workflow/Activities. After explicit Owner approval, stop at HARD — Analyst / Phase 2 acceptance. Do not begin Phase 3 automatically.
