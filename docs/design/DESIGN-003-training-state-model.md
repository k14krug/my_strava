# DESIGN-003 — Training-state model evaluation

**Status:** revised research recommendation, **not accepted**. P4-01 returns to
**HARD — Owner** under JIT §§12/14. Analyst review follows Owner direction.
No production behavior, schema, source data or Performance policy changed.

**Requirements used:** [Product Requirements](../PRODUCT_REQUIREMENTS.md)
PR-007/008/010–012, STATE-001–007, DATA-003–006;
[Phase 4 acceptance](../PHASE_4_ACCEPTANCE.md), including §6.1;
[P4-01](../tasks/P4-01.md), including Owner continuation §14;
[DESIGN-001](DESIGN-001.md), [DESIGN-002](DESIGN-002.md), and unchanged
`virtual-power-evidence-v2` selection. Source research and independent checks:
[verification](../../reports/P4-01/verification.md),
[source register](../../reports/P4-01/sources.md).

## Revised recommendation

Recommend **separate 7-/42-day recorded-work and FTP-normalized segment-stress
summaries, with visible coverage and partial-session labels**. The new dated FTP
history makes normalized stress useful to compare now; collecting that history
is no longer a prerequisite. Work remains available before FTP history begins.
Neither input should be called physiological fitness, fatigue, form or readiness.

Use calculated work from observed power in kJ for physical workload. Beside it,
show an explicitly named **recorded segment stress** candidate, calculated from
continuous power intervals of at least 600 seconds and the approved historical
FTP setting. This is a proposed recording policy for Owner review. It is **not
full-session TSS**, vendor-compatible TSS, or a guaranteed lower bound on what a
complete nonlinear calculation would produce. Never scale partial stress up to
elapsed/timer duration, and never substitute zero for omitted rides or time.

The revised evidence supports **878 normalized activity contributions**, compared
with 597 using only complete recorded envelopes and one source-session candidate
in the original evidence. These are different scopes, not 878 proved complete
sessions. A deliberately strict timer/boundary candidate qualifies only 24;
a one-second *summary discrepancy* sensitivity qualifies 75 without filling any
missing active seconds. This distinction should remain visible in a first product.

If the Owner wants only full-session stress, defer the broader normalized display
and use the strict subset plus work; do not relax timer rules simply to populate
a chart. The proposed default is useful partial evidence with an honest label,
subject to Owner choice and a precise Analyst-authored P4-02 contract.

## New FTP evidence and date rules

The [66-row CSV](../../data/athlete/strava_ftp_history.csv) is version-controlled
source evidence with [provenance](../../data/athlete/README.md). Structural
validation finds 66 distinct increasing dates, each exclusive end exactly the
next start, and a final open interval. Repeated equal values remain separate
source observations. First date: **2019-07-18**; latest entry: **2026-09-24**.
The evidence class is **Owner-provided Strava UI historical FTP setting**,
not an independently measured threshold. No screenshot was newly inspected by
Dex; transcription authority is the Owner/Analyst-approved committed source.
The screenshot remains private. The CSV has not been imported into production.

The one previously usable FIT session threshold differs from the Owner's CSV
setting for that date. Both remain evidence; this continuation uses the CSV as
explicitly instructed, not a silent average or inferred compromise. That same
recording's stress changes from 68.99 under its source-session threshold to 71.49
under the Owner's interval. This is an input/provenance difference, not a change
to the original calculation or a claim that either setting was laboratory-tested.

An activity uses its accepted calendar date: absolute start timestamps converted
to the Owner's `America/Los_Angeles` calendar; offset-unknown sources retain their
source date. Start dates are inclusive, next dates exclusive, final interval
open, and prehistory unknown. No current FTP backfill, best-20 inference, or
interpolation between FTP settings. Private calculation context retains the
selected interval, source class, watts, segment NP, duration/work and exclusions.

There are 93 offset-unknown cycling Activities, **zero among the 1,028 eligible
power rides**. A conservative ±1-day source-date sensitivity would flag a source
interval change and withhold normalized calculation rather than invent a timezone;
no current cycling row triggers it. There are 67 cycling activities on listed
change dates, including 51 eligible power rides, resolved with the inclusive-start
rule. Date-level FTP evidence does not establish an exact within-day change time.

| Intersection | Dated FTP / denominator | FTP unavailable | Segment stress contributions |
| --- | ---: | ---: | ---: |
| All cycling | 1,121 / 1,418 (79.06%) | 297 | 878 / 1,418 |
| Virtual Ride | 1,097 / 1,270 (86.38%) | 173 | 878 / 1,270 |
| Eligible detailed power | 878 / 1,028 (85.41%) | 150 | 878 / 1,028 |
| Complete recorded envelopes | 597 / 693 (86.15%) | 96 | 597 / 693 |
| Incomplete eligible envelopes | 281 / 335 (83.88%) | 54 | 281 / 335 |
| Outdoor Ride (excluded) | 24 / 148 (16.22%) | 124 | 0 / 148 |

All 297 cycling FTP gaps precede the first supplied date; 150 have eligible power.
Within incomplete eligible envelopes, 257/311 timing-discontinuous rides and
24/24 missing-power rides have dated FTP. No FTP rule repairs their power.
File/API provenance remains separate: the selected eligible sources are 1,022
FIT and six API streams. The retained source-state census below remains correct
for what existed before this additional evidence.

## Recording candidates and diagnostic evidence

The methods are research candidates, not accepted production policy. Every
calculation starts from the existing eligible source. Source summaries, native
records, timer events and API moving flags remain separate evidence.

| Candidate | Work contributions | Dated stress contributions | Interpretation |
| --- | ---: | ---: | --- |
| Original complete 1-second envelope | 693 / 1,028 eligible | 597 / 1,028 | Conservative recorded-envelope floor; not proof of session boundaries |
| Continuous native segments, ≥30 s for stress | 1,028 / 1,028 | 878 / 1,028 | Mathematical NP minimum; short-interval interpretation weak |
| Continuous native segments, ≥600 s for stress | 1,028 / 1,028 for all observed work | 878 / 1,028 | Recommended **partial recorded stress** candidate; omitted short time remains visible |
| Exact timer, boundaries and complete active bins, ≥600 s per segment | Separate timer-scoped work | 24 / 1,028 | Narrow full-timer candidate; all qualifying recordings have one timer interval |
| Same, allowing ≤1 s timer-summary discrepancy | Separate sensitivity only | 75 / 1,028 | Adds 51, changes no samples; not permission to fill an active second |

**Native segments:** preserve record order. Split at any missing/invalid power,
missing timestamp or timestamp increment other than exactly one second. Exclude
both occurrences of a duplicate timestamp; reject backwards or subsecond timing
for this method. Zero watts remain observed zero. No interpolation, concatenation
across gaps, elapsed-time stretching or outdoor power admission. Integrate each
retained sample as a half-open one-second bin, the same explicit rectangular
integration convention as the original floor. This is calculated work from
recorded point power, not exact instrument-measured energy. Isolated valid bins
can contribute work; they cannot supply NP. Recorded-bin calculations do not
assume every recorded bin is timer-active.

**Stress:** each qualifying segment gets unpadded complete 30-second rolling
means, fourth-power averaging and fourth-root NP; segment points are
`segment_seconds / 3600 × (segment_NP / dated_FTP)² × 100`. Sum segment points,
without crossing gaps. Sum work over those *same segments and rides* for the fair
work-versus-stress comparison. Keep broader observed work separately. NP and its
stress transformation are nonlinear: pooling all within-segment fourth moments
before applying one duration produces a different candidate, up to **14.59%**
higher than the segment sum in one retained ride (ratio 1.145873). Neither is
claimed equivalent to a missing complete-session calculation.

**Why 600 seconds:** TrainingPeaks' NP guidance cautions about intervals shorter
than ten minutes; 30 seconds is merely the formula's mathematical minimum. This
is a conservative, externally motivated candidate, not a fitted cutoff or proof
of physiological validity. Moving from 30 to 600 seconds changes 163/878 dated
ride contributions, but loses no activity contributor. It reduces aggregate
segment stress from 55,393.86 to 54,707.01 points, a **1.24%** decrease relative to
the 30-second candidate. The 600-second rule omits 59,142 of 2,695,544 observed
seconds with dated FTP (**2.19%**); their observed work remains available.

**Full-timer candidate:** require valid ordered start/stop pairs, first start equal
to session start, all events within both the session timestamp and start-plus-
elapsed boundary, timer-event duration equal to the timer summary, and every
active second covered by an unambiguous valid power bin in a ≥600-second segment.
A sample exactly at stop is outside the half-open active interval. Reset NP at
restarts. A second candidate allows only a one-second *timer-summary mismatch*
while still demanding complete active-bin coverage. There is no arbitrary
“99% complete” promotion. Both candidates remain conditional on device summaries
and the bin convention; neither verifies the reported FTP physiologically.

The independent diagnostics explain why the rules matter:

- **Sample count is not pause proof.** 92/311 timing-discontinuous rides have
  timer-summary seconds equal to sample count. One has 2,836 samples and a 2,836 s
  timer summary, a 12 s internal gap, 2,847 s elapsed summary, and 2,950 s between
  timer events. The count match cannot authorize treating the gap as rest.
- **Boundary missingness can be harmless.** One recording has 1,753 rows, the only
  missing power at the stop timestamp, and exactly 1,752 valid active seconds.
  It qualifies without inventing a watt. Two of the 24 exact-timer candidates were
  excluded by the original missing-power envelope rule.
- **Proved pauses do not explain all missing power.** A recording has a 21 s
  stop/restart pause and timer summary/event duration of 2,491 s, but 481 active
  seconds lack valid bins. Its observed segments survive; its full stress does not.
- **Duplicates are not averaged or selected opportunistically.** One eligible
  recording has two rows at one timestamp. Both remain in the source and both are
  omitted from derived bins. It still contributes continuous-segment evidence.
- **Elapsed, timer and moving are different.** The earlier 166,891 s elapsed /
  5,998.72 s timer example still rules out elapsed-only load. Among eligible files,
  1,020 have usable timer pairs; two have missing/invalid pairs. Six API streams
  have no FIT timer events. Their moving flags include 2–9 false samples per
  stream; “not moving” neither proves zero power nor an exact paused timer.

## Revised 7-/42-day comparison

Use **2026-10-08** as the common completed-day endpoint, preserving the initial
comparison window. The unchanged store's latest activity is October 7; October 8
is a no-record date, not asserted rest. Complete windows are calendar windows,
not the last seven/42 rides. Subtotals with no contributors are unavailable,
not numeric zero. Actual observed zero remains numeric zero.

| Window | Cycling rides | Dated FTP | Eligible contributors | All observed work kJ | Matched ≥600 s work kJ | Segment stress points | Omitted rides / no-record dates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Latest 7 days | 6 | 6 / 6 | 4 / 6 | 1,465.90 | 1,449.91 | 183.66 | 2 / 2 |
| Latest 42 days | 38 | 38 / 38 | 31 / 38 | 11,075.38 | 10,930.67 | 1,428.54 | 7 / 7 |

The 42-day omissions are six outdoor rides and one Virtual Ride without eligible
power. The original floor contributes 23/38 rides: 8,111.38 kJ and 1,095.10 dated
stress points. Segment recovery adds eight contributors. The 30-second candidate
would yield 1,442.18 points, versus 1,428.54 with 600 seconds (0.95% lower).
There are **zero** exact full-timer candidates in either recent window; the
one-second summary sensitivity qualifies 13/38 in 42 days and 0/6 in seven days.
None of these partial numbers is the rider's complete training load.

The [revised figure](../../reports/P4-01/anonymized-ftp-model-comparison.png) places
matched work and stress on separate axes, using the same segments, dates and
coverage. Lines show rolling subtotals divided by seven/42, not means over only
contributing rides. Relative days omit ride identities and dates.

| Descriptive 42-day period | Rides / contributors | All observed work kJ | Matched work kJ | Segment stress points | No-record days |
| --- | ---: | ---: | ---: | ---: | ---: |
| A — latest | 38 / 31 | 11,075.38 | 10,930.67 | 1,428.54 | 7 |
| B — around highest observed best-20 | 26 / 0 stress; 22 work | 11,623.19 | unavailable | unavailable | 19 |
| C — highest elapsed subtotal | 24 / 0 stress; 19 work | 11,704.05 | unavailable | unavailable | 20 |
| D — highest matched 42-day work | 34 / 28 | 14,378.34 | 14,336.71 | 2,140.35 | 15 |
| E — around largest reported FTP reduction | 1 / 1 | 131.94 | 131.94 | 28.67 | 41 |

B/C precede the FTP series. Their historical best-20 evidence cannot validate a
normalized model that has no date-appropriate input there. D's best-20 range is
113.78–205.01 W versus A's 85.88–194.54 W: achieved efforts, not standardized tests.
A's third matched week has more work than its second (1,783.58 versus 1,592.71 kJ)
but fewer stress points (222.43 versus 238.36); intensity and changing FTP settings
make work and stress meaningfully different summaries. This is not evidence that
one predicts adaptation better. E contains only one ride and 41 no-record days;
no fitness loss, rest or recovery conclusion follows from that interval.

Selectors are descriptive, can overlap, and involve no fitted model parameters.
D maximizes matched rolling work; E ends 20 days after the largest proportional
FTP reduction. Neither is an independent validation sample. The older
[duration/Performance figure](../../reports/P4-01/anonymized-context-periods.png)
retains B/C context. Title-only race hints remain unconfirmed; no hard-session
threshold or race intensity is invented.

## Industry baseline and alternatives

The industry NP/stress formula motivates the candidate; no exact vendor pause or
boundary parity is asserted. CTL/ATL recurrences remain `previous + (today −
previous)/42` and `/7`, with today's TSB using yesterday's values. The
[same-input synthetic comparison](../../reports/P4-01/synthetic-model-comparison.png)
shows smoother exponential memory versus finite-window edges, build/rest response
and missing-data propagation. Its zero seed and known rest days are synthetic.

Dated FTP fixes a major input gap, but **does not establish actual CTL/ATL/TSB**:
most whole-session loads remain incomplete, 4,673/5,909 calendar dates have no
recorded cycling rather than confirmed rest, and no initial load state is known.
Running the strict candidate with unknown seed/missing days leaves the industry
series unavailable. An EWMA of observed contributions could be a descriptive
workload smoother, but must not be renamed complete CTL by assigning omitted
sessions or no-record dates zero. The finite 7/42 windows have simpler coverage
explanations; neither time constant has been validated as optimal for this rider.

| Alternative | Disposition |
| --- | --- |
| Work-only recent/longer summaries | Broadest eligible coverage, no FTP dependence; useful before July 2019, lacks relative-intensity normalization |
| Separate work + recorded segment stress | **Recommended for Owner choice**; adds historical setting context while exposing incomplete recordings |
| Full-session TSS + default PMC | Defer as default: unresolved full-session input, missing-day and initialization assumptions |
| HR/TRIMP fallback | Still unavailable: no usable dated cycling HR reference set; no mixing HR and power into one score |
| Elapsed-only load | Reject: pause/recording duration can dominate apparent workload |
| 3D/physiological predictive model | No validated historical CP/W′/maximal-power state or independent validation; no justified v1 expansion |

## Owner decision and proposed P4-02 boundary

1. Choose the **dual work/segment-stress view**, work-only, or strict full-timer
   stress subset. Approve or change the 600-second segment candidate and its
   explicitly partial label. Decide whether the one-second summary discrepancy
   candidate merits later adoption; this recommendation does not enable it.
2. Keep missing whole-session totals unavailable, display contributor counts and
   omitted time/reasons, and label no-record dates without claiming rest. Do not
   approve CTL/Fitness/Fatigue/Readiness merely by accepting FTP normalization.
3. If the dual view is selected, authorize the Analyst to specify the smallest
   dated-FTP ingestion/correction contract using the existing CSV, source/version
   provenance and inclusive/exclusive dates. **No further FTP entry is needed for
   the present recent windows.** Earlier than July 2019 requires separately
   supplied evidence only if retrospective normalized stress is wanted. Weight,
   zones and equipment input are unnecessary for these candidates.

After that choice, the Analyst should author P4-02: chosen versioned calculation,
precise recording/FTP policy, separate units, per-activity evidence and omissions,
7-/42-day history, evidence navigation and limited Home integration. Preserve
file/API distinctions and outdoor exclusion. A separate load rule for short
Virtual Rides would require explicit authorization; current Performance-v2 stays
unchanged. No generic profile engine, HR mapping, training prescriptions,
questionnaires, planning or adaptive recommendations are proposed.

**Stop here at HARD — Owner.** P4-01 remains `in_progress` / `ready_for_review`.
Owner choice, subsequent Analyst acceptance and all P4-02 implementation remain
outstanding. The following initial census is retained as historical evidence,
not as the current argument against FTP normalization.

## Initial retained-source evidence (before the new FTP dataset)

The frozen accepted store has **1,442 Activities**, including **1,418 cycling**:
1,270 Virtual Ride and 148 Ride. The census reads all 1,421 preserved activity
files (1,264 FIT, 105 GPX, 52 TCX), the original export CSV, all retained API
summary/stream observations, and the current application schema/settings.
No API fetch or historical crawl was performed.

| Cycling evidence | Virtual Ride | Ride | Total |
| --- | ---: | ---: | ---: |
| Activities | 1,270 | 148 | 1,418 |
| Eligible detailed power under unchanged Performance-v2 | 1,028 | 0 | 1,028 |
| Preserved detailed power excluded by that policy | 242 | 44 | 286 |
| HR stream or understood HR summary, including export HR | 1,269 | 85 | 1,354 |
| Understood elapsed-duration summary | 1,268 | 13 | 1,281 |
| Known-unit source work summary | 102 | 10 | 112 |
| Eligible power with complete one-second recorded envelope | 693 | 0 | 693 |
| Usable source-session threshold candidate | 1 | 0 | 1 |

All 1,028 eligible results have HR evidence and duration; 74 also have a known-unit
source work summary. The eligible sources are **1,022 FIT / 6 Strava API streams**.
Source work summaries and calculated recorded-envelope work remain distinct.
The full [year/type census and overlap definitions](../../reports/P4-01/coverage.md)
include the 24 noncycling Activities and each missingness category.

The current policy excludes **all 148 outdoor rides**, 44 despite preserved
point power. Another 242 Virtual Rides are excluded: 198 shorter than the accepted
20-minute window, 39 without a complete timestamp-contiguous window, and 5
without a complete power window. A load-specific policy for short rides might
later be useful, but this research does not change the authorized policy.

Of the 1,028 eligible rides, **311** have timing discontinuities somewhere in the
recorded envelope and **24** have missing/invalid power under the conservative
whole-envelope check. A good best-20 window is therefore insufficient evidence
for full-ride stress. The 693 complete envelopes are a **research coverage floor**,
not a decision to permanently discard all paused or irregularly recorded rides.
No gaps are interpolated, no gaps become zeros, and no outdoor watts are admitted.

There are 1,263 cycling Activities with a file timer summary and 1,397 with an
absolute-timestamp record span. Among 137 missing understood duration summaries,
124 still have such a span. “Summary unavailable” does not mean time evidence was
never recorded. Five cycling sessions have elapsed time more than twice timer
time; that diagnostic threshold is not an automatic exclusion rule. CSV elapsed,
moving, work and weight fields with unspecified units are not guessed.

## Initial athlete-state inventory

| State | Retained observations | Classification and usable scope |
| --- | --- | --- |
| FTP / threshold power | Three FIT session fields: one positive cycling value in 2026, one zero cycling value in 2024, one positive Run value in 2025; ten XML threshold fields, all zero | The positive cycling value is **source-supplied**, not proven measured/tested FTP. Used only for its own source session in the experiment. Eleven zeros are unusable thresholds. Run state is not transferred to cycling. |
| Body weight | 487 CSV rows, two distinct raw values; ten XML values, eight positive and two zero | Supplied observations with source-row/activity dates, unspecified units/effective intervals and unverified measurement origin. Not a validated dated weight history. No weight is required by the recommended kJ/rolling summaries or power TSS formula. |
| HR max / resting HR / threshold HR | No usable cycling reference set found in recognized retained fields | **Missing for cycling load calculation**. Session maximum HR is an activity outcome, not an athlete maximum reference. No age-based or observed-peak substitution. |
| HR zones | Five boundaries in one 2025 Run FIT | Supplied sport/session-local configuration; not cycling reference state. The open upper boundary is not physiological HR max. |
| Power zones | Six boundaries in the same Run FIT | Supplied configuration; no inference of historical cycling FTP from the boundaries. |
| Bike/equipment | 1,409 CSV bike-weight entries and retained equipment identifiers | Supplied metadata, not adopted date-effective configuration. Not required by the recommended methods, so no equipment model is proposed. |

The private inventory retains source IDs, artifact hashes, fields, units, raw
values and row/session context. It assigns **no cross-activity effective interval**.
There is no current application athlete-state table or dated profile to consult.
Record-zone values and time-in-zone summaries do not establish their underlying
thresholds. API `weighted_average_watts` is power summary evidence, not body weight.

Limit of absence claims: all artifacts were scanned with the accepted parser;
recognized fields and developer field names were inventoried. Opaque vendor
messages remain uninterpreted. No claim is made that every unknown byte cannot
encode further state, nor were unrelated local archives or external accounts
searched. The usable-state conclusion is about **established evidence**, not
impossibility of future recovery.

**Initial gap (now supplemented by the CSV):** 1,027 of 1,028 eligible power rides lack even a usable same-session
threshold candidate; zero independently Owner-confirmed historical FTP intervals
are retained. Current six-week coverage contains 31 eligible rides and **no**
usable threshold candidate. HR-derived cycling load cannot presently be evaluated.
