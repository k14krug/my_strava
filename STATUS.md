# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete — P1-01/P1-02/P1-03 done.

**Current task:** P2-01 — in_progress

**Implementation state:** blocked — mandatory source-timing stop; not ready for acceptance.

**Branch / PR:** `task/p2-01-historical-import` / [#13](https://github.com/k14krug/my_strava/pull/13) (draft)

**Implementation head:** `dd05905`; subsequent handoff changes contain documentation/evidence only.

**Implemented foundation:** bulk ZIP/root import; shared exact CSV snapshots and source titles/provenance; FIT/TCX/GPX originals/native extraction; safe schema-1 migration; conservative enrichment; source-aware history reads.

**Verification:** 113 tests passed (94 prior + 19 new). Known 1,434/1,421/13 population passed preflight. Disposable real-data import stopped with 241 Activities/CSV Sources and 233 completed file Sources. Representative seed Activity was enriched with actual title evidence; FIT remains 3,621 native records / 118 W average. All 233 completed artifact hashes/sizes verify. Full-population and restart/rerun acceptance remain pending.

**Blocker:** seven diagnosed files strictly decode but supply an integer `lap.timestamp`; accepted `fit-v1` requires absolute UTC and rejects them. Native record timestamps in those files are absolute. No FIT timing interpretation/repair was invented. One additional row was interrupted; no whole-export failure prevalence is claimed.

**Evidence:** `reports/P2-01/verification.md`, `reports/P2-01/stop-evidence.json`.

**Next action:** Analyst reviews PR #13 and specifies/authorizes lossless handling or an explicit disposition for non-absolute FIT lap timing under the P2-01 JIT and accepted Phase 1 contract. Dex has stopped. Keep P2-01 `in_progress`; do not start P2-02.
