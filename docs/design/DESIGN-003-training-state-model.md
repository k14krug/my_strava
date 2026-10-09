# DESIGN-003 — Training-state model evaluation

**Status:** revised research recommendation, **not accepted**. P4-01 returns to
**HARD — Owner** under JIT §§12/14/15. Analyst review follows Owner direction.
No production behavior, schema, source data or Performance policy changed.

**Requirements used:** [Product Requirements](../PRODUCT_REQUIREMENTS.md)
PR-007/008/010–012, STATE-001–007, DATA-003–006;
[Phase 4 acceptance](../PHASE_4_ACCEPTANCE.md), including §§6.1/8.1;
[P4-01](../tasks/P4-01.md), including Owner continuations §§14–15;
[DESIGN-001](DESIGN-001.md), [DESIGN-002](DESIGN-002.md), and unchanged
`virtual-power-evidence-v2` selection. Source research and independent checks:
[verification](../../reports/P4-01/verification.md),
[source register](../../reports/P4-01/sources.md).

## Recommendation after the Sauce challenge

Recommend separate **7-/42-day work and stress views with explicit calculation
scope**, adding a narrow **small-gap stress estimate** candidate instead of making
600-second segmentation the default response to every dropped sample. Keep fully
observed calculations, estimated intervals and partial subtotals distinguishable.
The 66-entry FTP history and its approved date semantics remain unchanged.

The controlled experiment materially changes the earlier recommendation: deleting
one observed second can make the 600-second rule omit over a third of a recording's
reference stress. Exact pinned Sauce correction is substantially closer for short
losses. For the tested 1-/5-second losses its largest absolute error is 0.79%,
whereas long losses and hidden intensity changes can produce severe errors.
This is numerical reconstruction evidence, not physiological validation or a
universal error bound.

Proposed candidate, **pending Owner choice**: allow a labeled **recorded-interval
stress estimate** for nonnegative, uniquely time-ordered, dense 1 Hz eligible power with
interior gaps no longer than **5 missing seconds**, total missing time no more
than **1% of the recorded span**, no removed invalid/duplicate rows and no
explicit timer pause in that interval. Apply the documented Sauce active-time/
correction calculation with provenance for synthetic samples. Do not silently
rename it measured power, full-session TSS or verified training load.

This screen admits **47/281 interrupted rides** (46 FIT, one API). Calibration used
FIT references; the API case lacks independent complete-reference validation.
**None of those 47 has the corroborating session-boundary/timer evidence needed
for a whole-ride label.** The narrow rule recovers an interval estimate, not a
license to assume missing warmup/cooldown or complete session recording.

| Available evidence | Proposed display / calculation scope |
| --- | --- |
| Full timer/boundary evidence and complete active power | Calculated full-timer stress under the stated bin/NP convention; 24 prior candidates remain separate |
| Same boundary evidence, with only qualifying small interior losses | **Whole-ride stress estimate**, explicitly estimated; tested through controlled losses, but no newly qualifying actual interrupted ride established here |
| Complete observed envelope, session boundaries unproved | Calculated recorded-interval stress, not full-session TSS |
| Small eligible interior losses, boundaries unproved | **Recorded-interval stress estimate**, missing/padded seconds and source visible |
| Loss beyond the small-gap screen, ambiguous gaps or inconsistent timing | Observed ≥600 s segment subtotal, explicitly partial; work from shorter valid segments remains separately available |
| No qualifying power/FTP or no qualifying interval | Stress unavailable; known work/context retained where permitted |

Proved timer pauses must be handled explicitly, never mistaken for unknown
sensor dropout or measured zero. The timer-aware Sauce sensitivity still differs
from the existing reset-at-pause reference; do not adopt a new pause convention
without specifying it. Do not fill missing activities/dates with zero or adopt
CTL/Fitness/Fatigue/Readiness from this experiment.

## Bounded Sauce experiment — source and representation

Owner-authorized JIT §15 and Phase 4 §8.1 challenge the previous candidate using
[Sauce at the pinned revision](https://github.com/SauceLLC/sauce4strava/tree/4b6d4f42bf56d064507d694abd56e5f989530e03).
The research executes its **unmodified data/power functions** locally. Its source
hash and every numerical comparison are independently checked. No Sauce browser,
Strava request, athlete-state fallback, HR estimate or daily missing-as-zero
aggregation is executed. See [source details](../../reports/P4-01/sauce-verification.md).

The mathematics is exact upstream code on the supplied representation, **not a
claim of matching the full Sauce app**. FIT cadence/distance are parsed from the
same preserved records, with FIT speed ≥0.447 m/s supplying an explicitly derived
moving flag; trainer distance makes Sauce ignore that flag. Retained API streams
use their supplied auxiliary fields. Missing/invalid power and all duplicate
rows are removed only from the disposable adapter input, creating explicit gaps;
none becomes numeric zero. Originals and accepted Performance remain unchanged.

Important source detail: the gap pad uses the **arriving/next sample's value**,
repeated backward into the gap, not the last pre-gap watt. Its synthetic `Zero`
markers differ from actual zero-watt records. Default active detection requires
a positive timestamp gap **strictly less than 75 s** plus power/movement/cadence/
distance evidence. Thus losing 73 interior seconds gives a 74-second sample gap;
losing 74 gives 75 and can change the calculation abruptly. The 75-second setting
is a heuristic, not a verified error threshold.

## References, interventions and practical results

Use all **24 strict full-timer references**, supplemented by **24 complete recorded
envelopes** selected deterministically across duration, relative intensity and
variability. The strict set is narrow: 22 rides in 2024 and two in 2026, 23 files
reporting VirtualTraining/Rouvy and one development manufacturer; 23 contain Wahoo
power-device metadata. The supplement is 24 Zwift FIT recordings across 2019–2026,
with no retained power-device identification in that selected set. Platform
producer is not automatically the power sensor. These are one rider's indoor
recordings, not independent population validation or an outdoor/API calibration.

Strict reference durations range 1,233–5,071 s, NP/FTP 0.716–1.035 and NP/mean
1.014–1.138. Supplemental intervals range 1,203–16,240 s, NP/FTP 0.421–1.204 and
NP/mean 1.007–1.506. The supplement is recorded-interval reference truth only;
its session boundaries have not been verified.

There are **1,823 controlled cases**: 48 pristine controls, 1,440 single-loss
cases, 48 burst patterns, 96 boundary truncations, 47 known-zero sample losses
and 144 constructed timer pauses. Each reference receives 1/5/15/30/60/73/74/75/
300/600-second interior deletions at seeded-random, highest-power and lowest-power
locations. Bursts remove twelve five-second intervals; boundary cases remove the
first/last 30 s. Seeds, exact positions and context stay in reproducible private
outputs. Pauses insert 5/60/300 s of wall time with explicitly known synthetic
stop/restart events and **no deleted power**. Their target is the declared
timer-aware split-NP reference, not a measured physiological response.

| Loss | Strict set: segment worst absolute error | Strict set: Sauce worst absolute error | Supplemental set: segment worst | Supplemental set: Sauce worst |
| --- | ---: | ---: | ---: | ---: |
| 1 s | 36.21% | 0.15% | 32.75% | 0.66% |
| 5 s | 36.55% | 0.72% | 29.66% | 0.79% |
| 15 s | 37.43% | 2.12% | 39.07% | 2.88% |
| 30 s | 32.08% | 4.22% | 48.59% | 13.60% |
| 60 s | 35.99% | 21.90% | 54.75% | 19.56% |
| 600 s | 63.95% | 57.86% | 57.63% | 87.59% |

Each cell describes **72 cases = three placements × 24 references**, conditional
on method availability. At 600 s, the partial method is unavailable for 2/72
strict and 4/72 supplemental cases; Sauce returns an estimate for all 144.
The [full table](../../reports/P4-01/sauce-errors.md),
[aggregate JSON](../../reports/P4-01/sauce-comparison.json) and
[figure](../../reports/P4-01/sauce-gap-comparison.png) include medians, p95,
signed/absolute point and percent errors, omissions and placement strata.
Partial-method error against the full reference measures omitted contribution;
it does not mean a correctly labeled partial result asserted a false total.

For twelve five-second bursts, the 600-second method has a contribution in only
**1/48** cases; Sauce estimates all 48 with signed errors from −0.70% to +0.29%.
Most of those burst cases fail the proposed 1% total-loss screen. Tiny individual
gaps do not establish acceptable total missingness.

A 60-second low-power deletion produces **+21.90%** Sauce error in one strict
reference, because the arriving higher sample is extended backward. Deleting a
10-minute highest-power block from one supplemental interval produces **−87.59%**.
Lowering the immobile-gap option to 30 s suppresses the former overestimate but
makes all those strict 60-second cases underestimate by 0.98–9.42%. Raising it to
120 s removes the 75-second discontinuity but retains unsupported reconstruction.
No tested cutoff fixes unknown intensity in long missing intervals.

Known zeros, pauses and endpoints matter independently. Pristine Sauce controls
already differ from the common reference by up to 0.33% because its interval
accounting uses N−1 seconds and its active detection can exclude nonmoving zero
seconds. Reported deletion errors include this baseline difference; no concealed
rescaling makes it disappear. For constructed pauses, default Sauce differs from
the declared timer-aware reference by −1.53% to +13.98%; passing explicit pause
information reduces the upper deviation to +4.81% but does not make the NP
conventions identical. Boundary truncation remains undetectable from interior
correction alone; all 96 truncated cases are barred by the proposed known-loss
screen in the controlled experiment.

## Candidate cutoff tradeoff and actual interruptions

| Maximum missing gap, with total loss ≤1% | Admitted controlled loss cases / 1,775 non-pristine cases | Worst absolute error among admitted | Potential estimates / 281 actual interrupted rides |
| --- | ---: | ---: | ---: |
| 5 s | 338 / 1,775 | 0.79% | 47 / 281 |
| 15 s | 476 / 1,775 | 2.88% | 133 / 281 |
| 30 s | 539 / 1,775 | 3.03% | 152 / 281 |

The 1% screen intentionally limits cumulative loss; it is a proposed conservative
budget, not an optimized or physiologically established limit. Wider thresholds
trade coverage for larger observed errors. These repeated interventions are
correlated; percentiles are descriptive, not confidence bounds.

Even the five-second screen cannot guarantee small error. A clearly synthetic
30-minute 200 W example with an unobserved five-second 1,000 W surge has exactly
the same remaining observations as steady 200 W after deletion. Correction cannot
distinguish them and underestimates the surged reference by **5.11%**. This is an
identifiability limit, not a claim this rider produced that missing surge. No
reconstructed interval is relabeled measured or guaranteed within 1%.

Separately evaluate **all 281** actual interrupted dated-FTP contributors, plus
23 complete recent envelopes (304 actual comparisons). There is **no reference
signal inside real gaps**. Sauce-versus-partial median disagreement is +2.39%
for 257 timing-discontinuous rides and +1.54% for 24 missing-power rides; maxima
are +140.24% and +102.29%. Those increases do not establish recovered accuracy.
The adapter identifies 7,007 synthetic value pads and 34,805 synthetic zero pads
across the actual set, rather than silently treating them as observations.

In the latest 42 days both methods cover the same **31 contributors among 38 recorded cycling rides**:
partial sum 1,428.54 points versus unrestricted Sauce experimental sum 1,433.89.
That close aggregate is not validation; seven recorded rides remain omitted and
seven dates have no recorded ride. Under the five-second candidate, the 31 split
into **23 complete envelopes, one tentative API interval estimate and seven
partial recordings**. Latest seven days: 4/6 contributors, 183.66 partial versus
185.69 unrestricted experimental points; two envelopes and two partials, with no
new small-gap estimate. No full-timer recent total is established. Never combine
these categories into an unlabeled whole-history TSS total.

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
| Continuous native segments, ≥600 s for stress | 1,028 / 1,028 for all observed work | 878 / 1,028 | Initial **partial recorded stress** candidate; omitted short time remains visible |
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
| Separate work + evidence-scoped stress | **Recommended for Owner choice**; distinguish complete intervals, narrow estimates and partial segment subtotals |
| Full-session TSS + default PMC | Defer as default: unresolved full-session input, missing-day and initialization assumptions |
| HR/TRIMP fallback | Still unavailable: no usable dated cycling HR reference set; no mixing HR and power into one score |
| Elapsed-only load | Reject: pause/recording duration can dominate apparent workload |
| 3D/physiological predictive model | No validated historical CP/W′/maximal-power state or independent validation; no justified v1 expansion |

## Owner decision and proposed P4-02 boundary

1. Choose whether the first view should distinguish complete recorded work/stress,
   narrow small-gap **estimates**, and partial segment stress. The experiment
   supports correction for short losses; it does not support blanket Sauce
   correction, automatic whole-ride labels or default CTL/ATL/TSB.
2. Approve/change the **5 s / 1% candidate**, auxiliary-sensor assumptions,
   API applicability and evidence labels. Retain 600-second segments as a
   conservative fallback, not automatic rejection of otherwise useful short-gap
   interval estimates. Resolve pause conventions explicitly; the timer-aware
   sensitivity is not accepted production policy.
3. Authorize the Analyst, after that choice, to specify narrow P4-02 calculation,
   dated-FTP ingestion/provenance, activity/daily evidence categories, distinct
   7-/42-day subtotals, coverage/navigation and limited Home integration.
   Existing FTP is sufficient for recent windows. No generic profile engine,
   FTP inference, outdoor power admission, short-ride eligibility change,
   HR mapping, planning or prescriptions are proposed.

**Stop at HARD — Owner, JIT §15.** Owner model/policy choice and subsequent Analyst
acceptance remain outstanding. No merge or P4-02 implementation is authorized.
The dated-FTP and original retained-source findings below remain evidence; the
new recommendation supersedes the earlier default segment-only direction.

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
