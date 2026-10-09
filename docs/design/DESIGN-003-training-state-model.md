# DESIGN-003 — Training-state model evaluation

**Status:** recommendation, **not an accepted design decision**. P4-01 is at
**HARD — Owner**; Analyst review follows Owner direction. No production changes.

**Requirements used:** [Product Requirements](../PRODUCT_REQUIREMENTS.md)
PR-007/008/010–012, STATE-001–007, DATA-003–006;
[Phase 4 acceptance](../PHASE_4_ACCEPTANCE.md);
[P4-01](../tasks/P4-01.md); accepted [DESIGN-001](DESIGN-001.md) and
[DESIGN-002](DESIGN-002.md); current `virtual-power-evidence-v2` policy.

## Recommendation and its evidentiary limit

Recommend **transparent 7-day / 42-day rolling workload summaries**, with
**recorded eligible power work, duration context, and Performance kept separate**.
Show available contributions and missing/excluded evidence beside every subtotal.
Use descriptive language such as “recent workload” and “longer-term workload,”
not an asserted measurement of fitness, fatigue, form, or readiness.

Initially, recorded power work in kJ is the reproducible external-workload input
that requires no invented historical athlete state. It describes work over a
qualified recorded interval, not physiological stress or necessarily an entire
session. Duration must name its semantics: timer, moving, recorded span and
elapsed time are not interchangeable. **Elapsed duration alone is not recommended
as the load input.** The evidence contains substantial pauses, including one
46.36-hour elapsed session with only 1.67 hours of source timer time.

FTP-normalized power stress is a useful **conditional addition** after the Owner
provides or confirms dated FTP intervals and the Analyst specifies full-session
timing eligibility. Prefer the same transparent rolling summaries if that input
becomes available. The present evidence cannot establish whether such stress
outperforms simpler work summaries for this rider: there is only **one** usable
source-session threshold candidate, not a longitudinal FTP history.

This is an inference/design recommendation based on data coverage, explainability
and modest assumptions, **not empirical proof that 7/42 days are optimal**.
The Owner must choose whether this conservative external-workload start meets the
intended first Training State experience or whether dated FTP collection should
precede it. Phase 4 remains incomplete either way.

## Historical evidence

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

## Athlete-state inventory

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

**Gap:** 1,027 of 1,028 eligible power rides lack even a usable same-session
threshold candidate; zero independently Owner-confirmed historical FTP intervals
are retained. Current six-week coverage contains 31 eligible rides and **no**
usable threshold candidate. HR-derived cycling load cannot presently be evaluated.

## Candidate calculations and comparison

The [source register](../../reports/P4-01/sources.md) records current primary
research and vendor documentation with explicit access/validation limits.

### A — Industry baseline

Research formula: complete one-second power → 30-second rolling means → fourth
power → mean → fourth root (`NP`); `stress = hours × (NP / FTP)² × 100`.
Use the supplied threshold only for the session to which it belongs.

The isolated 2026 cycling candidate has 2,762 complete seconds, equal source timer
and elapsed duration, and a supplied 170 W threshold. Calculated NP is **161.20 W**;
candidate stress is **68.99**. An independent direct Decimal calculation agrees.
These are calculated values conditional on supplied source state, not validation
of the threshold itself. It is not carried forward or backward to any other ride.

Documented recurrences are `CTL[t] = CTL[t−1] + (load[t]−CTL[t−1])/42` and the
analogous ATL `/7`; `TSB[t] = CTL[t−1] − ATL[t−1]`. No alternate exponential
coefficient is silently substituted. **No real historical CTL/ATL/TSB series is
available**: missing loads and initial state are not replaced with zero.

### B — Transparent recent / longer workload

For a fair mechanics comparison, A's same synthetic daily stress inputs feed both
EWMA and complete 7-/42-day rolling means. The
[synthetic figure](../../reports/P4-01/synthetic-model-comparison.png) includes
steady input, concentrated weekly input, a build/rest transition and a missing day.
The zero initial state and rest days are explicit **synthetic facts** only.

Both methods react to a larger input; seven-day summaries react faster. Rolling
means have visible window-edge changes; EWMAs decay smoothly but retain old input
and initialization assumptions. A missing day prevents an exact EWMA thereafter
unless a justified new initial state is supplied. Complete rolling means recover
after 7/42 fully known days. Neither response establishes real fatigue or recovery.
A 10% threshold error changes stress nonlinearly: for the same 200 W hour,
180/200/220 W FTP yields **123.46 / 100 / 82.64** points. Reconstructing FTP casually
would materially change the comparison.

The real-history alternative sums eligible complete-envelope `watts × 1 second`
as calculated recorded power work in kJ. It yields 693 activity contributions,
with FIT/API provenance retained. These are physical external-work subtotals,
**not TSS-equivalent scores**. Known contributions and missing/excluded activity
counts are shown together. No full-history total is asserted from partial data.

### C — HR internal load

Not numerically evaluated for cycling: no usable date-effective HR reference set
exists. Banister/zone-based TRIMP candidates require different reference inputs;
none should be manufactured from activity maxima or borrowed running zones.
HR remains useful source evidence. It is not mapped into power stress to complete
a chart. See the primary cycling study and limitations in the source register.

### D — Context and actual periods

The [duration/Performance figure](../../reports/P4-01/anonymized-context-periods.png)
and [recorded-work figure](../../reports/P4-01/anonymized-work-periods.png) use
relative days without ride identities or actual dates. Selectors are fixed:
latest 42 days; 42 days ending seven days after the greatest observed best-20;
and greatest known 42-day elapsed-duration subtotal. Windows can overlap and are
**descriptive selections, not independent validation samples**.

| Period | Rides | Known elapsed h / rides missing duration | Recorded eligible work kJ / contributors | Rides without work contribution | Observed best-20 range W |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: latest | 38 | 32.29 / 0 | 8,111.38 / 23 | 15 | 85.88–194.54 |
| B: around highest best-20 | 26 | 20.19 / 2 | 6,322.44 / 13 | 13 | 146.74–218.40 |
| C: greatest elapsed subtotal | 24 | 65.59 / 3 | 5,911.72 / 11 | 13 | 173.87–218.40 |

C is dominated by the 46.36-hour elapsed / 1.67-hour timer observation. It is a
recording/semantic caution, not evidence of an extraordinary training block.
A's six successive weekly elapsed subtotals are 5.58, 5.40, 6.71, 3.87, 5.96 and
4.78 hours. The displayed best-20 values vary within these periods; they are
achieved efforts, not standardized maximal capacity tests. No correlation claim,
parameter fitting, recovery verdict or causal conclusion is justified here.

231 cycling titles contain the word “race,” but titles alone do not establish
confirmed races, demanding efforts or their intensity. No hard-session threshold
or race classification is invented. Days with no recorded cycling are labeled
as such, not “rest” or “recovered.” There are 4,673 such dates in the 5,909-day
observed calendar; history completeness outside recorded sessions is unproven.

## What the alternatives trade off

| Candidate | Coverage today | Benefit | Main limitation / disposition |
| --- | --- | --- | --- |
| TSS-style stress + 42/7 EWMA + balance | One session-context stress candidate; no complete longitudinal input | Familiar relative-intensity summary | FTP, whole-session timing, unknown-day and initialization gaps; defer physiological labels and default PMC |
| Separate 7/42 rolling workload | 693 recorded-power-work contributions; duration evidence separately | Simple units, explicit windows, no inferred athlete history; finite missingness dependency | Partial coverage and no intensity normalization; **recommended first direction, pending Owner** |
| HR/TRIMP fallback | Zero usable cycling reference sets | Potential outdoor internal-load context later | HR state missing; method/context sensitivity; defer numeric fallback |
| Elapsed-time-only load | 1,281 cycling summaries | Broad and easy to reproduce | Includes pauses/overnight recording; reject as load proxy |
| 3D power/impulse-response models | Required historical CP/W′/maximal-power state unavailable | Explicit intensity specificity | More unvalidated assumptions and inputs; retain as research, not v1 |

No comparison establishes which model predicts this rider's performance best.
The preference is for an explainable first product with visible coverage, not a
claim of predictive superiority.

## Owner decisions and proposed P4-02 boundary

1. **Approve or change the proposed first direction:** separate rolling external
   workload with coverage and Performance context, without Fitness/Fatigue/Form
   claims. Explicitly decide whether this is useful enough before normalized
   stress, or whether supplying dated FTP is a prerequisite.
2. **If adding normalized power stress:** supply FTP watts, effective-from date,
   effective-to date or explicit validity interval, source/basis (test, device
   setting, or remembered/manual value), and uncertainty where applicable.
   Confirming the single retained session value would authorize only its stated
   scope. To evaluate a recent 42-day window, provide the historically valid
   interval(s) covering that window, including each change; no need to invent a
   complete lifetime profile. A current value with today's date starts today.
3. **Timing and missingness:** authorize the Analyst to specify a narrow workload
   eligibility/boundary policy, distinguishing complete recorded work, verified
   session timer duration, partial samples and pauses. All unknown full totals
   stay unavailable; known subtotals carry contributor/omission counts. Do not
   automatically call unrecorded dates rest. A later short-Virtual-Ride load policy
   requires a separate explicit decision; current eligibility remains unchanged.
4. **HR fallback, only if wanted later:** provide dated sport-appropriate HR max
   and resting HR for a reserve-based method, or dated threshold/zone boundaries
   and the zone-system definition for a zone-based method. Do not request all
   inputs for every model. Weight and equipment entry are **not needed** for the
   recommended first model or power stress.

Manual dated entries are the smallest candidate approach for normalized load.
Alternatives are importing trustworthy dated test/settings records, or starting
prospectively and leaving older history unknown. Reconstructing state from
best-20, extending today's FTP backward, and reverse-engineering zones are not
approved options. None of these proposals establishes a schema.

After Owner direction, the **Analyst**, not Dex, should author P4-02's JIT: the
chosen versioned calculation and timing rules, date-state input if selected,
coverage-aware daily/activity history, 7-/42-day view, evidence navigation and
limited Home integration. It must retain file/API classes and outdoor exclusion,
and independently verify calculations and missingness before user-visible
acceptance. No training prescriptions, questionnaires, generic profile engine,
Phase 5 planning or adaptive recommendations are proposed here.

**Next gate:** Owner chooses direction and required manual inputs; Analyst then
reviews sources/calculations and accepts DESIGN-003 or requests corrections.
P4-01 and Phase 4 are not declared accepted by this report.
