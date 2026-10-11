# Phase 5 Acceptance — Workout Intent, Outcome and Rolling Training Plan

**Status:** **Phase 5 v1 accepted/complete 2026-10-10**, via accepted P5-01 after implemented JIT §10, code and behavioral verification, and the Owner's positive running-app assessment; [PR #26](https://github.com/k14krug/rideworks/pull/26).
**Source of direction:** Owner's current FTP-oriented training description and explicit **"Plan should show the rotation from today through the next 3 planned hard days"** decision. [Design baseline](design/P5-01-rolling-training-plan.md).
**Dependency:** [Phase 4 complete](PHASE_4_ACCEPTANCE.md).

## 1. Product question

Phase 5 should answer **"What kind of ride should I do today, and what's the upcoming rotation through the next three hard sessions?"**, while starting to connect **recommendation/explicit intent** to **what was actually ridden**. Phase 4 asks *where am I now?*; Phase 5 recommends the next few rides. Full autonomous adaptation and FTP-progression planning remain later Phase 6 concerns.

## 2. Minimum rider-facing outcomes

1. **Home:** prominent next-ride category, useful intensity/duration and short explanation, linked to Plan, without removing existing accepted Home features.
2. **Plan:** a *rolling daily timeline starting today and ending on the third upcoming recommended hard day*, including every intervening easy/recovery/Z2 day. Exactly three prospective hard-session recommendations are visible. It is **not** restricted to three days or a fixed week. Today counts as hard recommendation #1 if that is the proposed uncompleted ride; an **already completed** hard session today remains context, not one of the three future hard recommendations.
3. **Categories:** Race, Threshold, VO2, Recovery, Easy and Z2. **Never recommend No ride/Rest**; the lowest recommendation is an easy recovery spin. No Zwift custom workout-file transfer, race selection or fixed weekday schedule.
4. **Recovery:** first day after any hard session ~45–60 min @90–100 W; second day after Race/Threshold ~45–75 min @105–120 W if legs feel normal, after VO2 ~45–60 min @100–110 W; heavy legs downgrade to recovery intensity and postpone hard efforts. The hard recommendation generally waits until two recovery *calendar dates* have passed. A third automatic recovery day is not mandatory.
5. **Rotation:** typically one Race plus one structured Threshold/VO2 hard session in approximately seven days. This is a **soft coaching target**, not an absolute blocker: after two recovery dates the advisor may recommend another hard workout if otherwise appropriate, clearly explaining when that implies three hard days in seven; it must not make three-hard weeks the default. The next planned hard type after a race is structured; after structured quality, generally race. Don't mechanically mandate which structured workout without considering recent type and the stated FTP goal.
6. **Actual behavior:** synced actual race/structured/easy rides and elapsed dates recalculate the rotation; past unrecorded synced days count as **assumed rest** for planning, not a recommended no-ride day and not proof of rest in source/training history. If the rider doesn't ride on a planned hard day, do not count that hard session as completed, impose a missed-workout penalty or restart the recovery sequence.
7. **Transparency:** show the latest actual hard ride/date/type, why the next hard session is eligible or delayed, and any confidence caveat if activity classification, sync freshness or subjective recovery is uncertain. The rider can flag heavy legs and correct a materially wrong activity classification using a minimal interaction.
8. **Review:** reflect the suggested or explicit intended ride beside actual RideWorks Activity Review evidence where supported, without fabricating acceptance of a recommendation or blindly labeling a different ride a failure.
9. **Data preservation:** preserve original FIT/TCX/GPX/API evidence, historical athlete settings and existing Performance and Training State methods; store only minimal separate planning-specific facts as needed. No personal original activity files, local Zwift files, private paths or secrets committed.

## 3. Verification examples

- Race yesterday: recommend recovery today and low-Z2 tomorrow if feeling normal; next hard recommendation structured, no earlier than after two recovery dates; explain the normal two-hard-week target when the next appropriate quality day would exceed it.
- VO2 yesterday: recovery today, easy 100–110 W tomorrow; a threshold/race choice is based on the agreed race-versus-structured rotation, not an automatic third hard in seven.
- Threshold yesterday: same two-day recovery as race; next hard normally race.
- Two recovery dates then a **past day without a recorded activity and with up-to-date sync**: count it as assumed rest; today can be an eligible quality day if other guardrails permit. Do not restart the recovery timer or mark a workout missed.
- Missed current-day recommended ride: today's recommendation is still a recommendation until the day is over; next day does not inherit a falsely completed hard workout.
- Unplanned race during easy days: it is an actual hard stimulus; future sequence resets recovery and next hard type.
- Fresh sync not available: don't claim missing past rides are proven rest or unconditionally assert readiness; disclose that projections are provisional.
- Starting on a projected hard day, after a completed hard day, and midway through recovery: in all cases Plan terminates at **the third upcoming projected hard-day recommendation** while showing each intervening day.
- Home and Plan show the same today's recommendation at the same time and input state; desktop/mobile and keyboard operation pass.
- No algorithm automatically suggests "Rest" or "No ride" in any tested state.

## 4. Delivery and gates

**P5-01** may implement the compact Home and Plan recommendations with an evidence-aware first Activity Review connection; further workout prescription engines, complex calendar editors, external Zwift-file management and Phase 6 autonomous adaptation remain separate.

Dex executes only under the controlling [P5-01 JIT](tasks/P5-01.md) and a valid explicit invocation. **HARD — Analyst Gate 1** requires code, test and behavioral/source-preservation review. **HARD — Owner Gate 2** requires the actual running Plan/Home experience and usefulness review. A pushed branch or passing tests alone do not accept Phase 5; do not merge or start Phase 6 without acceptance.

## 5. Post-running-app correction — 2026-10-10 (controlling)

The Owner observed a newly synced completed Recovery ride but Home still labeled **another Easy ride for that same date** as **Next Recommended Ride**. **After a ride exists today, the primary Next Ride is the first future date (typically tomorrow); an additional spin today is optional context, never the primary next session.** Before any ride today, the primary recommendation can still be today's. Show the future next ride with date/type on the just-completed Activity Review too. A current Plan begins with Today's Completed Ride and Next Planned Ride, but still displays the complete daily timeline through three future hard milestones.

**Visual acceptance:** use the [Plan v2 HTML reference](mockups/plan-rotation-v2.html), not the initial plain-text list layout. Include 3 prominent hard-session milestones, chronological compact easy-day rows, context/freshness once near the top, and consistent RideWorks design. Do not repeat the same provisional warning in every row. The owner expects the two synced unrecorded days after a VO2 workout to count toward recovery, and expects a quality recommendation to become eligible after that interval; if a third hard session falls in a rolling seven days, disclose this nonstandard load instead of treating the two-hard-session guideline as an automatic veto. Classification of a race title remains evidence-qualified, with easy rider confirmation.

**Resolved:** JIT §10 was implemented in PR #26 and source/behavior/UI checks rerun. Both HARD — Analyst Gate 1 and HARD — Owner Gate 2 are accepted. The v2 Plan mockup direction was implemented; full adaptive planning remains a separate Phase 6 task.

## 6. Final acceptance disposition — 2026-10-10

**P5-01 / Phase 5 v1 accepted.** [Final behavior report](../reports/P5-01/review-followup.md) verifies shared first-future next-ride semantics on Home, Plan and recent Activity Review after today's synced ride; visible completed-ride context; every daily recommendation through three upcoming hard milestones; a compact redesigned Plan; source-qualified quick Race correction; explicit leg feedback and conditional hard-session frequency exceptions. October 7 VO2, two assumed-rest dates and October 10 Recovery lead to October 11 Race next. A before-ride counterfactual permits October 10 hard training after supported recovery, without mandating three hard days in every week. Nothing in the Plan's projections becomes a completed activity or observed Training State stress.

Dex reported **412 passing Python tests and 161 browser assertions** (144 on the actual synced case, 12 synthetic before-ride, five stale-sync), verified no browser errors and source preservation of all 20 original tables, 1,422 original artifacts, unchanged FTP/reference and accepted Performance/Training State. Analyst reviewed pushed implementation and privacy-safe regression aggregates; the Owner reviewed the revised experience and said **P5-01 looks good**, resolving the product/visual gate. The actual private screenshots/store remain local to the implementation environment; no claim is made that Analyst independently reran the private store.

**Known limitations:** The initial stimulus classifier is a fallible observed-power heuristic; some race-like titles lack independent evidence and require manual confirmation, and readiness suggestions are conditional on ordinary legs and sync accuracy. These are disclosed v1 limitations, not evidence of fully measured racing or physiological readiness. Phase 6 adaptive planning remains **pending**, not implicitly started or accepted.
