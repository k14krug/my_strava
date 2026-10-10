# P4-02 — Training-state direction and decision record

**Recorded:** 2026-10-09  
**Status:** Owner-confirmed source, HR modeling assumptions, longitudinal defaults, and approved Training State screen (2026-10-09). The [P4-02 JIT](../tasks/P4-02.md) is Analyst-finalized but **implementation is not yet authorized**.  
**Purpose:** Preserve the rider's recent decisions, the supporting Elevate/Sauce research, and unresolved details for implementation. The Owner has since **approved the dedicated Training State screen** described in [P4-02 screen design](P4-02-training-state-screen.md) (2026-10-09). The [finalized P4-02 JIT](../tasks/P4-02.md) awaits a separate explicit `/TASK P4-02` start.

## 1. Rider goal and standard of usefulness — confirmed

RideWorks is a personal application for one recreational cyclist riding for enjoyment, fitness, and health. Consistent, useful approximations and comparisons with the rider's **own history** matter more than laboratory-level precision or a model optimized for competitive racing. **"Close counts."**

A Fitness, Fatigue, or Form value is a trend indicator, not a literal measurement of physiology or health. Provide practical context and explain important input choices without burdening the rider with warnings on every estimated value.

This preference for pragmatism does **not** remove existing source-quality, provenance, historical-state, or missing-data requirements.

## 2. Source choices — confirmed by the Owner

- **Historical FTP:** Use the Owner-provided and approved **66-entry dated Strava FTP history**, `data/athlete/strava_ftp_history.csv`, with its approved date-effective semantics and unknown prehistory. Elevate's athlete FTP history was not maintained and must not be used as RideWorks authority.
- **Reliable measured power:** Prefer power-based stress calculated with the dated FTP for Zwift/virtual rides **when their power evidence qualifies**. "Virtual" is a practical tendency, not sufficient proof of recording quality. The accepted P4-01 rules on FIT corrections, pauses, observed-only API streams, and calculated/estimated/partial/unavailable evidence still govern.
- **Outdoor Strava estimated watts:** The Owner has established that Strava's outdoor cycling power estimates are especially unreliable for this rider. Do **not** promote those estimates to primary stress merely to fill coverage gaps. Retain useful source evidence for comparison and later research.
- **Future improvement:** Better outdoor-power reconstruction remains a **separate future research topic**. Preserve calculation inputs, method labels, and versions so history can be recalculated coherently if outdoor estimates improve.

## 3. HR-based fallback — Owner-approved modeling direction

An **Elevate-style heart-rate-derived stress (HRSS)** is the practical preferred *candidate* for rides lacking trustworthy measured power **when usable HR exists**, notably outdoor rides. Consistency and a meaningful approximation are the goal; do not demand exact correspondence to measured-power stress.

**Owner-approved practical HR settings for P4-02 v1 (2026-10-09):** Resting HR **58 bpm**, probable maximum HR **158 bpm**, and modeled threshold HR **143 bpm** by Elevate's 85%-of-heart-rate-reserve fallback. They are approximate **retrospective modeling assumptions**, explicitly allowed on older rides when no accepted date-effective HR evidence exists; **not historical measurements**. Use accepted dated HR settings if truly known for a date. Preserve the assumed source/date span, method version, and ability to recalculate. Modest HR-data quality checks remain necessary, but extensive calibration is not.

Do **not** automatically apply a universal multiplier to HRSS: preliminary paired virtual-ride comparisons showed variation by ride type and period. Extensive calibration is not required to make the initial P4-02 useful.

**Owner-approved pragmatic handling of rare unscored rides (2026-10-09):** Preserve the ride and its **unavailable** stress status in activity/source evidence, but use a **zero contribution for the missing stress in the numerical daily Fitness/Fatigue model**, as Elevate effectively does. Also use zero recorded training stress for calendar days with no recorded activity, without claiming they were confirmed rest days. Do not block or break the chart, invent a ride score, or make the rare case a major UI feature. A selected-day detail can distinguish an unscored activity from no recorded activity. The chart is explicitly a pragmatic estimate that may understate load after an unscored ride. **This P4-02 calculation convention does not rewrite P4-01's assertion that missing observed stress is not a true measured zero.**

## 4. Longitudinal model and interface — calculation defaults approved; interface details open

- **Owner-approved for P4-02 v1:** **42-day Fitness (CTL) / 7-day Fatigue (ATL)** exponentially weighted daily selected stress. Elevate and Sauce use equivalent 42-/7-day update mathematics. Self-comparison and stability, not physiological exactness, justify this choice.
- **Owner approved the visual/interaction direction**: a dedicated Training State screen with a dominant interactive Fitness/Fatigue/Form chart, aligned daily-stress strip, persistent selected-day ride details, distinct 7-/42-day stress and observed-work context, new navigation and compact Home link. See [screen design](P4-02-training-state-screen.md). Elevate/Sauce remain references, not specifications.
- **Owner-approved for P4-02 v1:** Follow **Elevate's prior-day Form convention**: today's Form = yesterday's Fitness − yesterday's Fatigue, representing the modeled start-of-day condition. Document the timing clearly in the UI/tooltips; this is not a directly observed recovery measurement.
- **Owner-approved simple v1 defaults:** Initialize the series to **zero before the first usable historical stress date**, with the early build-up treated as provisional; **omit future projections** in the first release; **do not adopt Elevate's fixed Form training-zone labels/thresholds yet**. Such zones are reference material only, not validated medical, readiness, or overtraining judgments. Subjective recovery context may enrich later interpretation but must not be compulsory.
- Preserve the distinction between **observed work (kJ)** and **FTP-normalized training stress** from P4-01. The exact placement of these alongside the new Fitness Trend chart remains a P4-02 presentation choice; earlier work/stress display concepts are not a mandate to use large dashboard cards.

## 5. Supporting reference research — not approved source truth

- The Owner's local-only Elevate Fitness Trend CSV (exported 2026-10-09) provides daily selected stress, HRSS, PSS, and Fitness/Fatigue/Form. **Do not commit the CSV or original activity records** as part of this decision.
- Elevate's 42-/7-day series was reproducible from its daily stress; its **lagged Form** convention was confirmed. Reproducibility validates the arithmetic, **not** the accuracy of its stress inputs.
- On one unusually long and hard outdoor effort reported by the rider, Elevate produced approximately **151 HRSS versus 59 estimated-power PSS**. The rider's description reinforces concern that Strava estimated power understates some outdoor efforts. It does **not** prove the HRSS value is exact; recording quality and historical HR settings remain relevant.
- Preliminary comparisons of paired virtual-ride HRSS and power PSS showed useful broad correlation, but meaningful disagreement on individual workouts. This supports preferring qualifying measured power when available and treating HRSS as approximate, without requiring extensive calibration before v1.
- Sauce remains a **targeted implementation reference**. Further broad Sauce-versus-Elevate matching is not necessary for the next design step.

## 6. Relationship to P4-01 and still-open decisions

**P4-01 is accepted as research/design** in [DESIGN-003](DESIGN-003-training-state-model.md) and [P4-01 verification](../../reports/P4-01/verification.md). In particular, retain the approved dated FTP evidence, separate observed-work and normalized-stress measures, short FIT-gap screen (each internal loss ≤15 s and total missing ≤1%), validated timer stop/restart precedence, API observed-only rule, and calculated / estimated / partial / unavailable labels.

**Explicit later Owner decision:** P4-01 deliberately did **not** approve HR mapping, CTL/ATL/TSB, or outdoor-power admission. The Owner subsequently approved a **pragmatic HRSS-style fallback with approximate current HR values used as historical assumptions** and the **42-/7-day chart** for P4-02. For a ride with materially partial power but adequate whole-ride HR, choose HR-derived stress for its primary trend contribution, retaining power partials separately. This P4-02 direction does **not** retroactively claim P4-01 validated HR load or override P4-01 power eligibility; outdoor **estimated power** stays excluded as primary input.

**Selected for P4-02 v1:** 42-/7-day model; prior-day Form; zero initialization before usable data; no projections/fixed training zones; rare unscored rides keep **unavailable evidence** but add **zero to the numeric model**; use approximate retrospective HR 58/158/143 and prefer adequately covering HRSS to materially partial power. The approved [screen design](P4-02-training-state-screen.md) settles the high-level chart and interactions. **Analyst technical specification** in the [final JIT](../tasks/P4-02.md) uses a fixed, versioned 1.92 HR-response coefficient for a simple Elevate-inspired normalized-average-HR model; this is an implementation choice, not a rider sex/gender claim nor a physiological measurement. Dex must verify real recording coverage and stop for material eligibility issues. Avoid unnecessary missing-state/calibration infrastructure.

**Not authorized here:** production changes, importing FTP/HR data into the running app, implementing P4-02, or starting Phase 5/6. The [P4-02 JIT](../tasks/P4-02.md) now records the Owner HR/model gate as resolved. The Owner-approved design/model direction is **not an explicit implementation start**; Dex still requires a separate permitted `/TASK P4-02` invocation.

## 7. Next step

The Owner approved the [screen design](P4-02-training-state-screen.md) and HR retrospective-model assumption/source-choice direction. The Analyst has finalized the [P4-02 JIT](../tasks/P4-02.md). **Next: request a separate explicit `/TASK P4-02` authorization and have Dex implement under its Analyst and Owner review gates.** Revisit reconstructed outdoor power and elaborate HR calibration only if useful.

---

**Provenance:** Owner priorities, source choices, explicit retrospective HR assumptions, selection of HR over materially partial power, and longitudinal-model/missing-stress defaults: October 9, 2026 RideWorks conversation. Elevate/Sauce formula details: reference-code research; paired-stress/daily-series observations: exploratory local-only Elevate export analysis. Versioned fixed-coefficient HRSS recipe and specific recording-quality checks: **Analyst's transparent v1 implementation specification**, not a measured HR threshold or vendor-parity guarantee.
