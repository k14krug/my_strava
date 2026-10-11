# P5-01 — Rolling training advisor: product direction

**Status:** Owner-directed Phase 5 design baseline, 2026-10-10. No implemented Plan feature yet.
**Role:** This document establishes user-facing behavior and training-policy boundaries; it does not mandate a database schema, scheduling algorithm, UI framework or file integration.
**References:** [Product requirements](../PRODUCT_REQUIREMENTS.md), [Phase 5 acceptance](../PHASE_5_ACCEPTANCE.md), accepted [Phase 4 Training State](../PHASE_4_ACCEPTANCE.md). P4-02's Training State remains distinct from future planning.

## 1. The core experience

RideWorks should answer **"What kind of ride should I do today, why, and what comes next?"** The user has no fixed weekdays and does not want a conventional recurring calendar, exercise video selector or race finder.

- **Home:** a prominent **Next Recommended Ride** card (category, useful duration/intensity, plain-English reason, and link to Plan). Place in the dashboard's intended next-workout area beside Recent Activities; keep existing dashboard features.
- **Plan:** a dedicated navigation page showing the **daily rolling rotation from today through the next three *upcoming recommended hard-session days***, inclusive. Show all intervening recovery/easy/Z2 days, not just the three hard-day cards. The horizon is event-based, **not a fixed 3-, 5- or 7-day calendar range**. A hard session recommended for today counts as the first of three; one already **completed** today does not count as a future recommended hard day. Include the current day's completed training and explanation, where relevant, without double-counting it.
- **Activity Review:** contextual, truthful "recommended/intended versus actual" interpretation after an activity, linked to the Plan where appropriate. A recommendation is **not automatically proof the rider committed to that plan**. If optional user-confirmed workout intent is introduced, store it separately and label it accurately; never rewrite what a ride actually was.

The recommendations are *suggestions*, not prescribed obligations. Future cards are **projections conditional on the expected recovery/ride pattern**, refreshed when actual activities, subjective feedback or days without recorded rides alter the inputs. Explain why a hard day was projected and why it moves.

## 2. Owner-confirmed training choices

**Primary goal:** recover approximately 186 W FTP toward >=195 W and eventually >200 W; rider weight about 77 kg. These are the owner's current coaching context, **not historical measurements or permanent fixed FTP settings**. Historical FTP stays date-effective and source-traceable.

**Ride frequency:** 5–7 days/week commonly, though the rider is comfortable riding daily when easy days are truly easy. **Never suggest "Rest", "No ride" or an unstructured day off as the recommended activity.** Even on a light/recovery day, recommend a *minimum easy spin*; the rider independently decides whether to skip.

**Hard sessions:** Race, Threshold, VO2. Usually **two hard sessions in approximately seven days**, normally **one race and one structured (Threshold or VO2)**. A race is a full hard training session, not an extra to add to two structured workouts. After a race, the next planned hard *type* is structured; after a structured session, the next is normally a race. The choice between Threshold and VO2 should be sensitive to recent structured work and the FTP goal, with no arbitrary rigid alternation imposed as an owner requirement.

**Recovery:** two *calendar* days after each hard-session day, whether actually ridden or not; a missed/no-record past day may count as **assumed rest** only once sync is current enough to trust the absence of a record. Never create a fictitious recovery *ride*. A third recovery day is **not a default required pause**; if an additional day passes without riding after two recovery days, it counts as more elapsed recovery time, not a new two-day requirement.

- After **Race or Threshold**: day +1 recommend **Recovery, 45–60 min at ~90–100 W**; day +2 recommend **Easy/low Z2, 45–75 min at ~105–120 W**, conditional on feeling normal. If legs are heavy, day +2 remains ~90–100 W.
- After **VO2**: day +1 recommend **Recovery, 45–60 min at ~90–100 W**; day +2 recommend **Easy, 45–60 min at ~100–110 W**. Return to ordinary Z2 ~115–120 W when feeling normal.
- Other non-hard days: Z2 typically **60–75 min at ~115–120 W**; if freshness does not justify it, use an easier 100–110 W ride. All watts/durations are current approximate coaching targets and should not imply medically validated recovery zones.
- **Warmup/recovery override:** if legs feel unusually heavy or recovery is questionable, postpone a hard session and recommend an easy ride instead. The rider should be able to flag this simply; do not infer physical readiness confidently from Fitness/Fatigue/Form alone.
- **Hard-session frequency guideline (revised after running-app review):** aim for roughly two hard days per rolling seven dates, but **do not treat two as an absolute veto** when two valid recovery dates have elapsed and the rider is ready for quality. Disclose when a proposed hard session would be a third within seven dates, considering genuine race evidence and the rider's legs; three-hard weeks are not a new default. This explicitly supersedes the earlier hard cap. Correct race classification separately without treating a title alone as certain.

**Workout progression** is background for selecting appropriate types, not required Zwift file management:
- Threshold ~175–180 W: accumulate 2x12, 2x15, 2x18, 2x20 with ~5 min easy between; increase duration before watts.
- VO2 30/15: ~30s @223 W / 15s @93–100 W; recent success 13+13+5; progress toward 13+13+6–8, rather than escalating power; 3x13 is an eventual option, not success criterion.
- Race: user independently finds and joins a race.
- Only two custom Zwift workout names are used routinely: `90_Z2_workout` and `V02max_30-15s_x13_x3`. Files currently exist in two Zwift folder locations, but **no .zwo discovery, syncing, editing, path configuration, file de-duplication or Zwift integration is needed for Phase 5 v1**. The rider chooses the appropriate named workout in Zwift; "Threshold" does not require a known local file.

## 3. Actual-history and inference boundaries

- Plan consumes *the best current RideWorks evidence*: synced completed activities and source-provenanced Training State, rather than Strava titles or modeled stress alone. Derive race/Threshold/VO2/hard/easy classification from credible available evidence; when ambiguous, disclose uncertainty and permit a simple human correction. **Do not choose high-load regression examples using RideWorks' selected stress only**; short hard intervals may have modest averaged HR.
- Use rider-local date boundaries and as-of/sync timestamps. On a **past day with no activity**, when current synchronization supports it, planning can label **Assumed rest (no recorded ride)** and count it toward elapsed recovery; Training State and its original evidence continue to say **no recorded activity**, not proven rest. A future day must never be labeled completed rest; today's absence is not yet a finished rest day.
- An unrecognized ride should not be silently classified as Recovery/Threshold/VO2 solely to make the recommended rotation advance. Prefer an explicit "classification uncertain" state with a simple override.
- No implicit conversion of measured/estimated/unavailable stress into physiological readiness. Explain recent workload as supporting context, not a proven fatigue threshold.
- Suggested hard session on a day does not prove it was performed. Only actual synced/manual activity may advance the **actual** completed hard-session history. Recompute future suggestions from new actual evidence, not from pretending projected future hard sessions already happened.
- Store/retain a separate, inspectable **recommendation or explicit intent** if comparing with actual outcome; do not rewrite original activity data, fabricate adherence, or penalize a skipped day.
- If source sync is stale/unknown, label the recommendation as **provisional based on available history** and do not silently assert a no-ride date is a rest date. Allow the rider to refresh/sync normally.

## 4. Rolling-horizon example (illustrative, not fixed weekdays)

Assume today follows a recently completed race and there is no confirmed heavy-leg report. Show today's recommendation, every day onward and **exactly three future hard recommendations**, for example:

`Today Recovery → Easy → Threshold (hard 1) → Recovery → Easy → Z2 → Z2 → Race (hard 2) → Recovery → Easy → [further Z2 as needed] → VO2 (hard 3)`.

The precise number of low-intensity days depends on rolling seven-day hard-session count, activity history, current date and later evidence. The display should make the three hard sessions easy to identify and explain any delay. It **must not truncate after a fixed week** or schedule a third hard session too early merely to fill the horizon.

## 5. Initial interface outline (not pixel specification)

**Home**: compact Next Recommended Ride card with type, approximate duration/target where useful, "because ..." explanation and `View Plan`. Use the same recommendation engine as Plan.

**Plan**: prominent Today's Ride, a daily timeline down to the **third upcoming hard day** with distinguishable Hard/Recovery/Easy/Z2 cards, relative plus explicit rider-local dates, projected status and reasoning for at least the hard recommendations. Show last actual hard-session type/date, recent hard count, sync freshness and whether the rider reported heavy legs. Optional small control to flag legs heavy / normal and to correct ambiguous actual classifications or capture intent; avoid a large questionnaire or extensive settings. Accessible desktop/mobile, keyboard and readable contrast. No hard-stop after a normal viewport height; scrolling is fine.

**Activity Review**: can show a light-touch recommendation-context/outcome section only when supported; distinguish an **unaccepted suggestion** from a rider-confirmed intended workout. Never call a ride "failed" solely because it differs from a prior suggestion.

## 6. Known open implementation choices / non-decisions

- Exact ride-category classification rules, minimal correction UX and persistence location are **engineering proposals to be justified and reviewed against actual evidence**; don't prematurely choose a schema.
- Choice of Threshold versus VO2 after a race is an **initial recommendation heuristic**, not an owner mandate to alternate them mechanically.
- Percentage thresholds for "elevated fatigue" or automatic readiness conclusions are **not established**; keep v1 guardrails explainable and subjective-heavy-legs overrides explicit.
- Full autonomous AI coaching, FTP progression scheduling, Zwift .zwo integration, race-finding, goals engine, arbitrary calendar editing and Phase 6 adaptive programming are **not accepted v1 scope**.

## 7. Owner acceptance focus

The running app must demonstrate: no Rest recommendation; assumed past no-ride handling with synced evidence; race/structured hard-day alternation and two post-hard recovery dates; appropriate VO2 versus Race/Threshold second recovery; two-hard-days-per-seven guardrail; skipped day does not restart recovery or mark a failed workout; Plan spans **today through third *future* hard recommendation**; Home/Plan agree; actual ride of different type updates next recommendation; contextual honesty about missing evidence/subjective readiness. Use real privately selected rides alongside deterministic simulations. Owner Gate 2 remains a distinct running-app review before completion.

## 8. Running-app review correction and approved visual reference (2026-10-10)

**This section supersedes the earlier assumption that Home always describes a ride for today.** When a ride is *already completed today*, the primary next ride is **the first future recommended ride**, usually tomorrow; today's actual ride appears as a separate completed card, and an optional second spin is subordinate. Before today's ride, today may be the primary next recommendation. Activity Review of a just-completed ride must also show the upcoming ride/date, while never fabricating a retrospective accepted intent. After sync, Home, Plan and Activity Review must agree.

The Plan layout in draft PR #26 was rejected as a long undifferentiated wall of text. Use [editable Plan v2 HTML visual reference](../mockups/plan-rotation-v2.html) for hierarchy: completed/next headline cards; **three upcoming hard-day milestone cards**; full but compact dated rotation with low-intensity days grouped and hard days highlighted; a single visible context/sync disclosure; detailed diagnostic reasoning below. All projected daily dates remain represented. The mockup uses illustrative dates and categories, not live recommendations.

With Oct 7 VO2, no rides Oct 8/9 and a synced Recovery ride on Oct 10, the primary next suggestion should target the next available future ride, not a second optional Oct 10 Easy. Prior to the Oct 10 ride, quality can become eligible after two assumed-rest dates, subject to transparent current-history/subjective guards. See [P5-01 JIT §10](../tasks/P5-01.md).
