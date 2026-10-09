# Phase 4 Acceptance — Training State

**Status:** active design/implementation phase; Owner authorized on 2026-10-08  
**Phase goal:** Answer **“Where am I now?”** using transparent longitudinal training evidence before RideWorks attempts workout planning.

## 1. Roadmap decision

The Owner explicitly changed the roadmap order:

- **Phase 4:** Training State
- **Phase 5:** Workout intent/outcome and initial planning
- **Phase 6:** Adaptive planning

This supersedes the older Phase 4/5 ordering in historical planning material.

Reason: training-state assessment can be built and validated from completed training history that RideWorks already owns. Planning should then consume a state model that has already been tested against this rider rather than forcing state assumptions into a planner first.

Training state and planning remain separate concepts.

## 2. Phase 4 product question

Phase 4 is successful when RideWorks can answer, transparently:

> **What is my current training state, and what evidence is that based on?**

It is not yet required to answer:

> **What workout should I do next?**

That remains Phase 5/6 territory.

## 3. Controlling principles

Phase 4 inherits PR-007, PR-008, PR-010 through PR-012, STATE-001 through STATE-007, DATA-003 through DATA-006, and the accepted source/provenance model.

In particular:

- historical FTP/weight/zones are date-aware;
- no current FTP may be silently applied to old rides;
- missing load evidence is not zero load;
- power-derived and HR-derived load are not silently equivalent;
- outdoor power currently considered suspect for Performance must not be promoted into load merely for coverage;
- estimated outdoor power is excluded from the first implementation unless a later explicit eligibility decision is made;
- subjective tracking is optional, not required;
- important calculations must be explainable and recalculable;
- no mystery Fitness/Readiness score is required.

## 4. Two-stage Phase 4 delivery

Phase 4 begins with **P4-01 — Training-state model evaluation and athlete-state inventory**.

P4-01 is a research/design task. It must not commit RideWorks to a production training-state model before the evidence is compared.

After Owner approval of P4-01’s recommendation, a later P4-02 implementation task may implement the selected model and user-facing experience.

Phase 4 is **not accepted** merely because P4-01 finishes. Final Phase 4 acceptance requires a usable rider-facing current-state capability.

## 5. Candidate model families P4-01 must evaluate

At minimum compare:

1. **Classic power-based stress + short/long exponentially weighted load**
   - TSS/CTL/ATL/TSB-style concepts as the industry reference baseline;
   - normalized to historical FTP when valid historical FTP exists;
   - treat names/labels such as “fitness”, “fatigue”, and “form” as interpretations, not physiological ground truth.

2. **Simpler transparent short/long workload model**
   - use the same eligible daily load input where possible;
   - compare straightforward recent and longer-term rolling/EWMA workload without assuming the full fitness-fatigue interpretation;
   - determine whether simpler presentation is equally or more useful for this rider.

3. **Heart-rate-derived internal-load candidate for rides without eligible power**
   - evaluate only if the required historical HR reference evidence is available;
   - retain it as a different evidence class unless validation supports a mapping;
   - do not force HR load onto the same scale merely for completeness.

4. **External-load/context signals**
   - duration, work/kJ where genuinely known, hard-session spacing, recent races and Performance-v2 changes may be useful contextual inputs;
   - they are not automatically interchangeable “load points.”

P4-01 may recommend another transparent model if research and this rider’s data support it better.

## 6. Historical athlete-state gate

Before using any FTP-normalized load calculation across history, P4-01 must inventory whether RideWorks currently possesses trustworthy date-effective:

- FTP;
- weight when relevant;
- HR max/rest/thresholds when relevant;
- zones when relevant.

If historical FTP is absent or incomplete:

- do not infer a complete FTP history from current FTP;
- do not derive one from 20-minute Performance without an explicit Owner decision;
- quantify how much history could be evaluated with known values;
- compare minimal ways to supply missing historical athlete state, including simple manual dated entries;
- stop for Owner decision before production use if the chosen model materially depends on data RideWorks does not yet have.

### 6.1 New Owner-provided Strava historical FTP evidence

After the initial P4-01 research snapshot, the Owner supplied a private Strava
FTP-history screenshot transcribed as 66 dated values spanning July 2019 to
September 2026. The Owner explicitly approved treating each listed calendar
date as the effective start until the next listed date, with the last interval
open-ended and **no inferred value before the first date**.

This is **new evidence**, not a contradiction of the previous retained-source
inventory. Distinguish a reported Strava FTP setting from independently
validated physiological threshold. The Owner subsequently **approved
committing the 66 date/value entries** to the public RideWorks repo; PR #23
tracks them at `data/athlete/strava_ftp_history.csv` with a provenance README.
The original screenshot remains private. Do not treat this tracked dataset as
already persisted in the running RideWorks athlete-state store.

Before accepting P4-01's model recommendation, require a revised comparison
with this dated FTP series and a separate evaluation of recording-gap/timer
semantics. The original 693 complete one-second envelopes are a conservative
research floor, **not** the approved full-session load policy. Report FTP ×
eligible-power overlap and current gaps, and do not fill missing power or
missing whole-ride stress with zeros.

The Owner authorized further **research only**. P4-01 must return to HARD —
Owner for the revised model recommendation; no P4-02 or production FTP import is
authorized by this decision.

## 7. Current power-evidence boundary

For the first evaluation:

- accepted eligible Virtual Ride detailed power may be used where its evidence class is valid;
- FIT-backed power retains provenance;
- validated Strava API power streams remain API evidence;
- existing outdoor Ride power remains excluded from power-based load because its quality/provenance remains suspect;
- no estimated outdoor-power reconstruction is introduced in P4-01.

P4-01 must quantify the resulting coverage gap rather than hiding it.

A later Phase 4 decision may choose an HR/external-load fallback or eventually estimated outdoor power, but each must remain source/method distinguishable.

## 8. Evaluation against this rider

Do not choose a model because an industry platform uses it.

Use the accepted RideWorks history to evaluate:

- historical coverage;
- sensitivity to hard/easy/rest periods;
- stability;
- dependence on uncertain athlete-state inputs;
- interpretability;
- behavior around known recent races or demanding sessions where identifiable;
- relationship with existing 20-minute Performance history;
- behavior when evidence is missing;
- usefulness of short-vs-long workload and recovery-spacing views.

The aim is not to prove causality or optimize a predictive model from sparse outcomes.

Avoid overfitting model parameters to the rider’s historical best-20 observations.

## 9. External research baseline

P4-01 should verify current sources rather than relying on folklore.

Starting references:

- TrainingPeaks, **What Is TSS?**, updated 2026-06-12.
- TrainingPeaks, threshold / CTL / ATL / TSB documentation.
- Banister-style impulse-response literature and published limitations.
- Current research comparing or extending one-dimensional fitness-fatigue models, including recent cycling/power-based work.

Established industry practice is a reference implementation, not authority over RideWorks design.

## 10. P4-01 deliverables

P4-01 must produce:

- an inventory of available historical athlete-state evidence;
- a coverage census for candidate load inputs across RideWorks cycling history;
- reproducible exploratory calculations on a private/disposable copy of accepted history;
- comparison of candidate models;
- explicit limitations and missing-evidence behavior;
- recommendation for the first production RideWorks training-state model;
- proposed rider-facing terminology and explanation model;
- a decision document such as `docs/design/DESIGN-003-training-state-model.md`;
- verification/research report under `reports/P4-01/`.

No production schema migration, Home metric, Activity metric, or training recommendation is required in P4-01.

## 11. Final Phase 4 user-visible acceptance

A later implementation task must, at minimum:

- calculate a versioned/reproducible selected training-load metric for eligible evidence;
- preserve method, athlete-state context and source provenance;
- show daily/activity load history and missing/ineligible cases;
- show recent vs longer-term workload;
- provide a useful current-state view with transparent explanation;
- integrate selected state information into Home without reviving an opaque “Fitness Score” placeholder;
- permit navigation to underlying Activities/evidence;
- remain useful without subjective questionnaires;
- avoid workout prescriptions or plan changes.

The exact UI is deliberately not fixed before P4-01 model selection.

## 12. Phase boundary

Phase 5 planning must not begin automatically after P4-01 or Phase 4.

Workout completion/failure patterns were previously listed as a training-state candidate input. Because planning now follows Training State, they are **not a Phase 4 v1 dependency**. They may enrich the state model later after Phase 5 produces real planned-versus-actual evidence.
