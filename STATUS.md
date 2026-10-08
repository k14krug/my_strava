# STATUS.md

**Product:** RideWorks. Phase 1, Phase 2 and STRAVA-004 accepted / complete. Phase 3 active; Phase 4/5/6 not started.

**Current task:** P3-01, `in_progress` / `ready_for_review` at HARD — Owner in PR #19. Owner/Analyst task acceptance remains outstanding.

**Branch / PR:** `task/p3-01-dashboard` / [draft PR #19](https://github.com/k14krug/rideworks/pull/19). Refreshed main `23ac11d`; Analyst JIT `473a173` / Phase 3 contract `18fb186`; runtime `6d9160e`.

**Delivered:** Owner-approved Recent Mileage consolidates This Week and Last 7 Days, retaining neutral prior-seven-day comparison and unchanged calculations. Exactly three top cards; desktop mileage values side-by-side with an internal divider, phone stacked. Annual goal information stays in Mileage Progress.

**Verification:** 285 full / 24 focused dashboard tests pass. Fresh live and disposable synthetic Chromium check desktop/phone three-card geometry, LA/Tokyo boundaries, independent SQL/Decimal mileage/Performance, actual bars/needed line, tooltip behavior and restart. Exact goal tuple, 1,422 artifact hashes and 1,441 v1 rows preserved; integrity/FKs pass. Zero external API calls during this correction. Evidence: `reports/P3-01/verification.md` / `acceptance.json`.

**Preserved state:** Completed eight-ID enrichment; LA YTD 1,631.195462250 mi, 120 contributors / zero unavailable. Owner-confirmed 2,200-mi goal unchanged; Performance 1,028 eligible / zero pending. Current local This Week 26.3 mi / Last 7 Days 74.8 mi, 20.1 mi less than prior seven. Difference versus approximate 1,631-mi reference is within whole-mile rounding; exact current Strava equality remains unverified.

**Review app:** [Home](http://127.0.0.1:8771/), [Activities](http://127.0.0.1:8771/activities), [Settings goal](http://127.0.0.1:8771/settings#annual-goal).

**Next action:** HARD — Owner review of consolidation and desktop/phone readability under current JIT §8.3 / §15. Explicit Owner approval precedes Analyst acceptance. No merge, next task or Phase 4/5/6.
