# STATUS.md

**Product:** RideWorks.
**Current task:** P5-01 — Rolling Training Advisor.
**State:** ready_for_review — stopped at HARD — Analyst Gate 1 under `/AUTOTASK P5-01`.
**Branch:** `task/p5-01-rolling-advisor`; draft PR creation pending.
**Implementation:** Shared Home/Plan advisor through three future hard recommendations; two-date recovery and rolling seven-day cap; optional heavy-leg feedback, separate category corrections and explicit pre-ride date-level intent; honest Activity Review context. Schema 9 contains planning-only additions.
**Verification:** 405 Python / 22 focused tests; 71 Chromium assertions (desktop, 320/390 px, keyboard and Home/Plan parity); private representative VO2/race/Z2/source-uncertain checks, deterministic restart and source preservation. All 21 original tables, 1,422 originals, FTP/Elevate hashes and accepted Training State/Performance retained. [Report](reports/P5-01/verification.md).
**Limits for review:** Initial classifier describes observed Virtual Ride stimulus; race titles and HR stress alone remain uncertain until rider correction. Stale sync keeps quality projections provisional; private screenshots/data stay ignored.
**Running review copy:** `http://127.0.0.1:8773/plan` (disposable private store copy).
**Next action:** Analyst reviews Gate 1. After explicit release, demonstrate Home/Plan/Activity Review for Owner Gate 2. TASKS remains in_progress; no acceptance, merge or Phase 6.
