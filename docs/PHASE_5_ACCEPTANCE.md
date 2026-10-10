# Phase 5 Acceptance — Workout Intent, Outcome and Rolling Training Plan

**Status:** Product direction established 2026-10-10; implementation not yet started.
**Source of direction:** Owner's current FTP-oriented training description and explicit **"Plan should show the rotation from today through the next 3 planned hard days"** decision. [Design baseline](design/P5-01-rolling-training-plan.md).
**Dependency:** [Phase 4 complete](PHASE_4_ACCEPTANCE.md).

## 1. Product question

Phase 5 should answer **"What kind of ride should I do today, and what's the upcoming rotation through the next three hard sessions?"**, while starting to connect **recommendation/explicit intent** to **what was actually ridden**. Phase 4 asks *where am I now?*; Phase 5 recommends the next few rides. Full autonomous adaptation and FTP-progression planning remain later Phase 6 concerns.

## 2. Minimum rider-facing outcomes

1. **Home:** prominent next-ride category, useful intensity/duration and short explanation, linked to Plan, without removing existing accepted Home features.
2. **Plan:** a *rolling daily timeline starting today and ending on the third upcoming recommended hard day*, including every intervening easy/recovery/Z2 day. Exactly three prospective hard-session recommendations are visible. It is **not** restricted to three days or a fixed week. Today counts as hard recommendation #1 if that is the proposed uncompleted ride; an **already completed** hard session today remains context, not one of the three future hard recommendations.
3. **Categories:** Race, Threshold, VO2, Recovery, Easy and Z2. **Never recommend No ride/Rest**; the lowest recommendation is an easy recovery spin. No Zwift custom workout-file transfer, race selection or fixed weekday schedule.
4. **Recovery:** first day after any hard session ~45–60 min @90–100 W; second day after Race/Threshold ~45–75 min @105–120 W if legs feel normal, after VO2 ~45–60 min @100–110 W; heavy legs downgrade to recovery intensity and postpone hard efforts. The hard recommendation generally waits until two recovery *calendar dates* have passed. A third automatic recovery day is not mandatory.
5. **Rotation:** typically one Race plus one structured Threshold/VO2 hard session in approximately seven days, without accidentally recommending three hard days in seven. The next planned hard type after a race is structured; after structured quality, generally race. Don't mechanically mandate which structured workout without considering recent type and the stated FTP goal.
6. **Actual behavior:** synced actual race/structured/easy rides and elapsed dates recalculate the rotation; past unrecorded synced days count as **assumed rest** for planning, not a recommended no-ride day and not proof of rest in source/training history. If the rider doesn't ride on a planned hard day, do not count that hard session as completed, impose a missed-workout penalty or restart the recovery sequence.
7. **Transparency:** show the latest actual hard ride/date/type, why the next hard session is eligible or delayed, and any confidence caveat if activity classification, sync freshness or subjective recovery is uncertain. The rider can flag heavy legs and correct a materially wrong activity classification using a minimal interaction.
8. **Review:** reflect the suggested or explicit intended ride beside actual RideWorks Activity Review evidence where supported, without fabricating acceptance of a recommendation or blindly labeling a different ride a failure.
9. **Data preservation:** preserve original FIT/TCX/GPX/API evidence, historical athlete settings and existing Performance and Training State methods; store only minimal separate planning-specific facts as needed. No personal original activity files, local Zwift files, private paths or secrets committed.

## 3. Verification examples

- Race yesterday: recommend recovery today and low-Z2 tomorrow if feeling normal; next hard recommendation structured, no earlier than after two recovery dates and respecting the rolling-week hard-session cap.
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
