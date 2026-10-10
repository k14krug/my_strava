# P4-02 — Training State: product requirements and design decisions

**Status:** Approved core calculation model, data-source principles and [screen design](P4-02-training-state-screen.md); implementation underway in [draft PR #24](https://github.com/k14krug/rideworks/pull/24). **HARD — Analyst Gate 1 remains open.**
**Decision context:** P4-01 accepted evidence policy; P4-02 design decisions dated 2026-10-09; source-eligibility clarification informed by the 2026-10-10 running-app review. [Current JIT](../tasks/P4-02.md).

## 1. Product goal and acceptance standard

RideWorks should provide a **credible, interpretable account of the rider's training history and current modeled training load**. It should recognize the contribution of substantial training sessions using the best defensible information available, including approximate HR-based load where qualified measured power is absent. Fitness, Fatigue and Form should reflect changes in recent versus accumulated training effort, rather than primarily reflecting gaps in detailed source recordings.

Interpretability and longitudinal consistency matter more than laboratory-level precision. Fitness/Fatigue/Form are **model outputs**, not measured physiological fitness, fatigue, health or readiness. Source limitations should be visible where relevant without overwhelming ordinary use.

**External behavioral reference:** Elevate is useful for checking whether major sessions produce plausible changes in training load and whether the longitudinal patterns are broadly credible. Its individual scores, athlete settings and FTP history are **not** RideWorks source truth, numerical calibration targets or requirements for exact agreement. Explain material differences by eligible input evidence, historical settings and method—not by forcing numerical parity.

**Acceptance checks:** Inspect representative high-load, ordinary and low-load days across recent windows. Where a ride has eligible power or suitable recorded HR/duration, it must contribute its independently calculated stress and produce the expected daily Fitness/Fatigue update and next-day Form effect. Do not silently suppress a material ride solely because a detailed HR stream fails a completeness check if a defensible *independently eligible* same-source HR summary is available. Require real-rider date-level behavioral checks **in addition to** unit arithmetic tests; compare against the external reference as a plausibility check, not as an oracle.

## 2. Training stress sources

- **Measured power:** Prefer eligible recorded power for virtual/other rides using the approved dated [Strava FTP history](../../data/athlete/strava_ftp_history.csv). Respect P4-01's FIT-only internal gap screen (≤15 seconds per gap, ≤1% total), timer pause/restart handling, API observed-only power, and calculated/estimated/partial/unavailable evidence labels. Being a Virtual Ride alone does not establish trustworthy wattage.
- **Strava outdoor estimated watts:** Do not use as the primary stress input; their rider-specific agreement with experienced effort has been poor. Retain as reference information where appropriate, not authoritative measured power.
- **HR fallback:** When qualified power cannot adequately score the activity, estimate load from eligible measured HR information and a supported duration. For v1, use a threshold-normalized, Elevate-inspired approximate HRSS calculation. No universal HRSS↔power-stress multiplier.
- **Stream versus summary:** A timestamped HR stream with suitable duration/coverage is preferred. Detailed-stream completeness requirements apply to *that stream's* reliability; they do not automatically invalidate a separate source-reported average HR and compatible same-source moving/active duration. Such a pairing can qualify for an **HR summary estimate** even if the detailed stream is defective, provided validity/compatibility checks pass. Preserve the failed-stream reason, duration basis, coverage uncertainty and approximate method label. A summary is not independently verified full-session coverage; pauses may be uncertain. Do not invent active time, fill unknown HR samples, assume CSV duration units, or silently choose among conflicting candidates.
- **Partials:** If neither full recorded power nor suitable HR estimate exists, eligible partial observed-power stress may contribute with its limited scope disclosed. A partial-HR candidate is **not** approved as a trusted default v1 replacement without separate evaluation. Never add power and HR scores for a single ride.

**Selected HR parameter assumptions (v1):** Resting HR **58 bpm**, approximate max HR **158 bpm**, modeled threshold **143 bpm** using the specified fallback. Apply as **retrospective modeling assumptions**, not asserted historical measurements, when accepted dated HR state is absent. Use accepted date-effective settings where genuinely available. Retain source/date/method version and recalculate when better settings become available. The JIT specifies the fixed 1.92 response coefficient; do not infer sex or treat the threshold as clinically measured.

**Unavailable stress:** Preserve `unavailable` in evidence and inspection, but use a numerical zero contribution to daily model stress for an unscored ride; dates with no recorded rides have zero *recorded* model contribution. Neither situation proves a rest day. This pragmatic curve convention is not permission to reject otherwise suitable approximate evidence. Scored coverage should be shown so substantial gaps are not confused with stable training.

## 3. Longitudinal calculations and presentation

- **Fitness:** 42-day exponential update of daily selected stress.
- **Fatigue:** 7-day exponential update of daily selected stress.
- **Form:** Beginning-of-day value based on **previous day's** Fitness minus Fatigue. This is an indicator, not an individualized readiness or overtraining diagnosis.
- **Initialization:** Zero before the earliest usable recorded stress, with the early modeled period identified as provisional. Do not extrapolate a current FTP into dates before its known effective history.
- **Not in v1:** Future training projections, fixed Form readiness/overload zones, prescriptions or extensive HR calibration.

The [approved Training State screen](P4-02-training-state-screen.md) contains a dominant interactive chart, independently selectable Fitness/Fatigue/Form series, synchronized daily stress strip, compact summary metrics, hover and keyboard/date inspection, persistent selected-day ride/source details, and separate 7-/42-day stress and observed-work (kJ) evidence. Home links to this view. Work in kJ is measured observed power, **not** a substitute for or conversion from HR stress.

## 4. Implementation evidence and regression examples

The first P4-02 implementation correctly applied the 42-/7-day arithmetic and preserved original data, but **overrestricted HR input selection**: at least 99% stream coverage, adjacent HR intervals ≤15 s and suppression of summary estimation whenever an invalid detailed stream was present. The resulting outdoor coverage was 7/148 scored rides despite additional source-reported HR information. These conditions are useful evidence screens for fully recorded streams, **not a general veto** on separately qualified HR-summary estimates.

The diagnostic identified three recent outdoor rides with potentially usable same-source HR/duration summaries. The **2026-09-16 Springwater Corridor Trail** ride is a mandatory *private* regression example: the initial model marked it unavailable (zero numeric contribution) while Elevate reported approximately 151 HRSS. The correction must derive an independent score from eligible RideWorks inputs and demonstrate the resulting daily/longitudinal response. Neither 151 nor the displayed Elevate graph is an imported model target. More historical outdoor activities still lack defensible duration/coverage and may remain unavailable; do not manufacture data to improve coverage statistics.

**Verification:** Source-selection cases (including defective stream + eligible summary), source/version provenance and unknown scope; impact on representative actual rides, daily trends and next-day Form; existing P4-01 power rules; browser chart inspection; source/original preservation. See the [P4-02 JIT](../tasks/P4-02.md) and [diagnostic report](../../reports/P4-02/review-followup.md).

## 5. Authority, provenance and execution gates

**Owner-approved design decisions:** practical trend model, approximate HR baseline/settings, source preference (measured power; HR fallback; partial power), unavailable-stress numeric convention, Form timing, and screen direction. **Analyst technical specification:** fixed versioned HRSS coefficient, exact source-summary eligibility and labeling, regression checks. They are separate from claims about historical measurements or physiological validation.

Earlier P4-01 research did not approve HRSS or CTL/ATL for production; the later P4-02 selections supersede that *scope limitation* without changing P4-01 power-evidence rules. Sauce and Elevate are comparative research material, not normative source truth.

The Owner separately authorized committing only the unchanged [Elevate Fitness Trend export](../../data/reference/elevate/fitness_trend_export.2026.10.9-15.58.52.csv), documented in its [README](../../data/reference/elevate/README.md). Exclude its 14 projected days from completed-ride comparisons. Do not commit personal original FIT/TCX/GPX, private screenshots/mockup HTML, stores, credentials or further exports without specific authorization.

**Execution status:** P4-02 has been invoked and is in draft PR #24. The clarified source-summary correction can be implemented within the existing task, but **HARD — Analyst Gate 1 stays closed** pending evidence review; Owner's running-app usefulness/visual acceptance is a separate Gate 2. No automatic merge, Phase 4 acceptance or Phase 5/6 start.
