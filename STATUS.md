# STATUS.md

**Product:** RideWorks. Phase 1 and Phase 2 accepted / complete; Phase 3 not started.

**Current task:** STRAVA-004 — `in_progress`, invoked with `/TASK PR18`; Owner correction complete, awaiting **Gate 1 — HARD — Owner** review again.

**Branch / PR:** `task/strava-004-streams` / [PR #18](https://github.com/k14krug/my_strava/pull/18) (draft). Verified correction implementation: `c84b74dd16edb64dd22dc54e6181277f18698163`; Analyst JIT refreshed from `main` `d88033b`.

**Behavior:** Seven API-only reviews now have normal summary cards, chart, ride-local Best 20-minute power, Ride summary, and collapsed provenance. Summary values remain current Strava summary evidence; five qualifying best-20 results use returned streams, two HR-only results show Unavailable. Local results never enter trusted Performance or prior-six-week context. FIT-backed review unchanged.

**Verification:** 243 full / 57 focused tests passed. Live/synthetic Chromium independently checked local means/windows/rounding, all seven chart payloads, summary hierarchy, HR-only unavailability, FIT precedence, LA/Tokyo dates, phone/desktop, and restart/idempotence. P2-05 Settings/OAuth/rebuild regression passed. All 16 accepted tables and source originals unchanged: 1,441 Activities / 11 stream observations / 1,022 eligible Performance / 0 pending; integrity/FKs passed. Correction made no new live API requests; total stream GETs remain 11. Original Stage A: four overlaps / 13,076 exact power+HR timestamp pairs per signal / 100% agreement; cadence comparison unavailable. [Evidence and reproduction](reports/STRAVA-004/verification.md).

**Review:** App running final code at `http://127.0.0.1:8771/`. Private `output/playwright/strava-004-review-links.json` identifies newest API-only / FIT overlap / HR-only rides; targeted links supplied directly to Ken. Expand Calculation details, Summary source, and Strava API stream evidence to inspect methods/provenance.

**Next action:** Owner reviews whether the API-only Activity Review as a whole is useful, structurally complete enough, and honest about source/eligibility, per JIT Gate 1. After explicit Owner approval, Gate 2 is Analyst review. Task is not accepted; no next task is authorized.
