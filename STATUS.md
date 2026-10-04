# STATUS.md

**Product:** RideWorks

**Phase 1:** accepted / complete — P1-01/P1-02/P1-03 done.

**Current task:** P2-01 — in_progress

**Implementation state:** ready_for_review — stopped at HARD — Analyst.

**Branch / PR:** `task/p2-01-historical-import` / [#13](https://github.com/k14krug/my_strava/pull/13)

**Implementation head:** `c131092`; final publication changes contain documentation/evidence only.

**Implemented:** one ZIP/root bulk import; exact shared CSV snapshot and file preservation; actual titles/provenance; conservative enrichment; FIT/TCX/GPX native extraction; schema-1/2 → 3 migration; source-aware history read boundary. Analyst-authorized integer lap timestamps are retained losslessly with unknown interpretation and null absolute timestamps (`fit-v2`). Other FIT timing remains strict.

**Verification:** 123 tests passed. Clean seeded full export and restarted rerun passed: 1,434 Activities, 1,421 artifacts, 13 CSV-only Activities, zero failures/unresolved associations. All originals match received bytes/hash/size. Representative Activity enriched without duplication; IDs/extractions stable across rerun. All 18 integer lap fields across 17 Sources independently verified and reproduced by re-extraction. Real Phase 1 import/best-20 regressions and all 157 XML production parser checks passed.

**Runtime:** first bulk pass 616.55 seconds; restarted rerun 2.72 seconds.

**Evidence:** `reports/P2-01/verification.md`, `reports/P2-01/acceptance.json`. No personal source/runtime data or private titles published.

**Blockers:** none for implementation/verification; final Analyst acceptance pending.

**Next action:** Analyst reviews PR #13 against the updated P2-01 JIT and Phase 2 historical-import contract, then records explicit acceptance or actionable feedback on GitHub. Keep P2-01 `in_progress`; do not begin P2-02 automatically.
