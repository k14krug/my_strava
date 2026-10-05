# STATUS.md

**Product:** RideWorks. Phase 1 accepted; Phase 2 in progress.

**Accepted:** P2-01/P2-02/P2-03/P2-04 done; PR #16 merged.

**Current task:** P2-05 — in_progress.

**Branch / PR:** `task/p2-05-strava-sync` / [#17](https://github.com/k14krug/my_strava/pull/17) (draft).

**Implementation head:** `e4e77ffd5fa3e092038cecbba38f6d00446da084`; subsequent publication updates verification tooling/evidence/status.

**Implementation state:** awaiting_owner_review — /TASK corrections under Analyst JIT on main `e14c8c0` complete. Stopped at Gate 1 HARD — Owner. No Owner approval or Analyst acceptance claimed.

**Implemented:** normal in-app Settings Connect / Sync now / status / Disconnect; CLI secondary, shared OAuth/token/sync functions. API UTC `Z` dates now parse on Python 3.10 and participate in local display/sorting; View Activities links to the normal browser. Persistent app-wide Performance freshness reminder and explicit POST/nonce-protected Rebuild Performance use accepted atomic logic. Sync never rebuilds automatically.

**Verification:** 219 full / 33 focused tests pass. Actual Chromium synthetic OAuth, private state, refresh, restart, nonce/concurrency, LA/Tokyo dates/order, thin/rich provenance, phone/desktop, reminder persistence, failed rebuild rollback and successful explicit rebuild pass. Untouched accepted-copy HTTP/restart regression preserves 1,434 Activities / 1,022 eligible results. Live review: all 7 new API-only Activities have absolute chronological dates, are the newest seven and individually reachable; 4 overlaps enrich established identities without duplication. Guarded live restart reruns: 0 new Activities/observations, 3 unchanged per rerun; no native reads, archive reprocessing or hidden rebuild. Original sources/native evidence retained; integrity/foreign keys pass.

**Live review state:** 1,441 total / 1,417 cycling / 11 API observations. Initial web result: 7 new / 4 enriched / 0 unchanged. Explicit in-app rebuild evaluated 1,441 Activities, restored 1,022 eligible results and cleared 11 pending to zero. Reminder disappears across pages/restart; unchanged sync does not stale rebuilt history. Credentials/tokens remain private and locally configured.

**Review:** http://127.0.0.1:8771/settings and http://127.0.0.1:8771/ (Newest first). Server running; restart command: `.venv/bin/python -m rideworks --data-dir local_data/p2-05-review serve --port 8771`. Web callback uses this running port; Strava Callback Domain is host-only `127.0.0.1`. CLI connect/sync/disconnect/rebuild remain maintenance/recovery options in README.

**Evidence:** `reports/P2-05/verification.md`, `reports/P2-05/acceptance.json`, `rideworks/README.md`.

**Policy boundary:** the documented Strava durable-history/caching/deletion tension remains under JIT §4.6's Owner decision. Manual overlap does not guarantee old-edit/delete detection; public/unattended integration requires revisiting webhooks.

**Next action:** Owner reviews Settings, corrected newest-first Activities and explicit rebuild/reminder behavior. After explicit Owner approval, set ready_for_review and stop at HARD — Analyst / Phase 2 acceptance. Do not begin Phase 3.
