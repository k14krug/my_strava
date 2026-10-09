# P4-02 — Training-state direction and decision record

**Recorded:** 2026-10-09  
**Status:** Owner-confirmed goals/source choices and agreed P4-02 design direction; **not a finalized algorithm, P4-02 JIT, or implementation authorization**.  
**Purpose:** Preserve the rider's recent decisions, the supporting Elevate/Sauce research, and unresolved details for the next design and implementation brief.

## 1. Rider goal and standard of usefulness — confirmed

RideWorks is a personal application for one recreational cyclist riding for enjoyment, fitness, and health. Consistent, useful approximations and comparisons with the rider's **own history** matter more than laboratory-level precision or a model optimized for competitive racing. **"Close counts."**

A Fitness, Fatigue, or Form value is a trend indicator, not a literal measurement of physiology or health. Provide practical context and explain important input choices without burdening the rider with warnings on every estimated value.

This preference for pragmatism does **not** remove existing source-quality, provenance, historical-state, or missing-data requirements.

## 2. Source choices — confirmed by the Owner

- **Historical FTP:** Use the Owner-provided and approved **66-entry dated Strava FTP history**, `data/athlete/strava_ftp_history.csv`, with its approved date-effective semantics and unknown prehistory. Elevate's athlete FTP history was not maintained and must not be used as RideWorks authority.
- **Reliable measured power:** Prefer power-based stress calculated with the dated FTP for Zwift/virtual rides **when their power evidence qualifies**. "Virtual" is a practical tendency, not sufficient proof of recording quality. The accepted P4-01 rules on FIT corrections, pauses, observed-only API streams, and calculated/estimated/partial/unavailable evidence still govern.
- **Outdoor Strava estimated watts:** The Owner has established that Strava's outdoor cycling power estimates are especially unreliable for this rider. Do **not** promote those estimates to primary stress merely to fill coverage gaps. Retain useful source evidence for comparison and later research.
- **Future improvement:** Better outdoor-power reconstruction remains a **separate future research topic**. Preserve calculation inputs, method labels, and versions so history can be recalculated coherently if outdoor estimates improve.

## 3. HR-based fallback — agreed direction, details open

An **Elevate-style heart-rate-derived stress (HRSS)** is the practical preferred *candidate* for rides lacking trustworthy measured power **when usable HR exists**, notably outdoor rides. Consistency and a meaningful approximation are the goal; do not demand exact correspondence to measured-power stress.

Before first implementation, do a **modest sanity check** of recording quality and historically applicable resting HR, max HR, and cycling threshold HR. The values shown by Elevate and its threshold fallback are reference settings, **not** approved RideWorks athlete state. Choose a transparent initial policy for missing or uncertain HR reference state without inventing certainty.

Do **not** automatically apply a universal multiplier to HRSS: preliminary paired virtual-ride comparisons showed variation by ride type and period. Extensive calibration is not required to make the initial P4-02 useful.

Where no defensible power- or HR-derived stress exists, keep stress **unavailable**, distinct from a true zero and from a no-record day. P4-02 must decide and explain how days containing unknown stress influence a numeric longitudinal trend, rather than silently treating those rides as rest.

## 4. Longitudinal model and interface — accepted direction, details open

- The familiar **42-day Fitness (CTL) / 7-day Fatigue (ATL)** exponentially weighted daily-stress model is the preferred **working basis**. Elevate and Sauce use equivalent 42-/7-day update mathematics. Self-comparison and stability, not physiological exactness, justify this choice.
- Favor an **interactive Fitness / Fatigue / Form longitudinal chart**, inspired by useful parts of Elevate and Sauce, with the daily load and measurement/estimate/missing quality inspectable. Neither reference application is the product specification.
- **Form timing is undecided:** Elevate displays today's Form as *yesterday's* CTL minus ATL; Sauce displays today's CTL minus ATL. Choose, document, and clearly label the convention when P4-02 is designed.
- Elevate's fixed Form training-zone thresholds are **reference material only**, not validated medical, readiness, or overtraining judgments. Subjective ride experience and recovery context can improve later training interpretation without being compulsory inputs.
- Preserve the distinction between **observed work (kJ)** and **FTP-normalized training stress** from P4-01. The exact placement of these alongside the new Fitness Trend chart remains a P4-02 presentation choice; earlier work/stress display concepts are not a mandate to use large dashboard cards.

## 5. Supporting reference research — not approved source truth

- The Owner's local-only Elevate Fitness Trend CSV (exported 2026-10-09) provides daily selected stress, HRSS, PSS, and Fitness/Fatigue/Form. **Do not commit the CSV or original activity records** as part of this decision.
- Elevate's 42-/7-day series was reproducible from its daily stress; its **lagged Form** convention was confirmed. Reproducibility validates the arithmetic, **not** the accuracy of its stress inputs.
- On one unusually long and hard outdoor effort reported by the rider, Elevate produced approximately **151 HRSS versus 59 estimated-power PSS**. The rider's description reinforces concern that Strava estimated power understates some outdoor efforts. It does **not** prove the HRSS value is exact; recording quality and historical HR settings remain relevant.
- Preliminary comparisons of paired virtual-ride HRSS and power PSS showed useful broad correlation, but meaningful disagreement on individual workouts. This supports preferring qualifying measured power when available and treating HRSS as approximate, without requiring extensive calibration before v1.
- Sauce remains a **targeted implementation reference**. Further broad Sauce-versus-Elevate matching is not necessary for the next design step.

## 6. Relationship to P4-01 and still-open decisions

**P4-01 is accepted as research/design** in [DESIGN-003](DESIGN-003-training-state-model.md) and [P4-01 verification](../../reports/P4-01/verification.md). In particular, retain the approved dated FTP evidence, separate observed-work and normalized-stress measures, short FIT-gap screen (each internal loss ≤15 s and total missing ≤1%), validated timer stop/restart precedence, API observed-only rule, and calculated / estimated / partial / unavailable labels.

**Explicit follow-on change in direction:** P4-01 deliberately did **not** approve HR mapping, CTL/ATL/TSB interpretation, or outdoor-power admission. The Owner's later conversation now supports **investigating an HRSS-style fallback and a 42-/7-day Fitness/Fatigue/Form chart for P4-02**. This is a later **P4-02 design direction**, not a retroactive claim that P4-01 validated an HR model, nor an override of P4-01's measured-power evidence rules. Outdoor **estimated power** remains excluded as the primary basis.

**Still open for the P4-02 JIT/design:** exact HRSS formula and dated HR settings; HR-data eligibility; mixed/incomplete ride treatment; the missing-load convention within ATL/CTL; initialization; Form timing; future projection; final chart interactions and the presentation of kJ versus stress; any interpretation or zone labels.

**Not authorized here:** production changes, importing FTP/HR data into the running app, creating a P4-02 JIT that assumes unmade choices, implementing P4-02, or starting Phase 5/6.

## 7. Next step

Prepare a modest P4-02 design and JIT around qualified measured-power stress, a transparent approximate HR fallback, reproducible daily stress, and an interactive 42-/7-day Fitness/Fatigue/Form view. Resolve only the missing-data, threshold-setting, and Form-convention decisions needed for an honest v1. Revisit outdoor reconstructed power and elaborate HR calibration only if they prove useful.

---

**Provenance:** Owner priorities and source choices: October 2026 RideWorks conversation. Elevate/Sauce formulas and source selection: reference-code research; paired-stress and daily-series observations: exploratory comparison of local-only Elevate export. Candidate implementation mechanisms and remaining choices: proposals, **not Owner-approved algorithms**.
