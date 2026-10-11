# STATUS.md

**Product:** RideWorks.
**Current task:** P5-01 — Rolling Training Advisor; JIT §10 review corrections.
**State:** ready_for_review — returned to HARD — Analyst Gate 1 under `/AUTOTASK P5-01`. Not accepted.
**Branch / PR:** `task/p5-01-rolling-advisor`; [draft PR #26](https://github.com/k14krug/rideworks/pull/26).
**Implemented:** Primary next ride advances after completed today across Home/Plan/Activity Review; historic Review labels live Current next ride. Plan v2 has separate completed/next cards, three milestones, compact complete daily rotation and shared context. Frequency is a soft preference with a supported-recovery exception; clear race confirmation remains separate from source data.
**Verification:** 412 full / 29 focused Python tests; 161 Chromium assertions (144 actual-case, 12 synthetic before-ride, 5 stale). Actual October 10 post-sync case now shows October 11 Race on all three pages; October 8/9 assumed planning rest. Confirmed-race before-ride third-in-seven, heavy legs, source uncertainty, normal sync regressions and midnight checks pass. 20 source tables / 1,422 originals, FTP/Elevate and accepted Training State/Performance preserved. [Follow-up report](reports/P5-01/review-followup.md); source-neutral screenshots committed, private screenshots ignored.
**Running review copy:** `http://127.0.0.1:8775/plan` (updated disposable private copy; primary source store unchanged).
**Next action:** Analyst reviews corrected JIT §10 behavior, soft-guideline implementation and visual evidence. After explicit Gate 1 release, present the running Home/Plan/Review at HARD — Owner Gate 2. PR stays draft; no merge, Phase 5 acceptance or Phase 6 work.
