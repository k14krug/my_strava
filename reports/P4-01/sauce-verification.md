# P4-01 Sauce challenge — verification and interpretation

**Historical stage:** §15 Sauce challenge, reviewed before the Owner's final
choice. JIT §16 now selects **15 s / 1%, FIT only**, validated timer splitting
and observed-only API inputs. See [current reconciliation](verification.md).
Five-second recommendations and pending-Owner statements below describe this
prior stage, not the current policy. The experiment outputs are unchanged.
Branch `task/p4-01-training-state`, [draft PR #23](https://github.com/k14krug/rideworks/pull/23).
Refreshed main `fb4761d`, JIT `fb5b9dd`, Phase 4 contract `f915bc6` integrated.
Allowed Invocation is explicitly `/TASK only`. Read Analyst source review and
Owner authorization comments; no outstanding inline comments or reviews existed.

The [revised DESIGN-003](../../docs/design/DESIGN-003-training-state-model.md),
[error table](sauce-errors.md), [aggregate results](sauce-comparison.json) and
[figure](sauce-gap-comparison.png) contain the evidence for Owner choice.
Prior [dated-FTP verification](ftp-verification.md) and
[initial retained-source verification](initial-verification.md) remain historical
evidence. Their earlier default segment-only recommendation is superseded.

## Exact reference code and explicit adaptations

Public source: [SauceLLC/sauce4strava](https://github.com/SauceLLC/sauce4strava/tree/4b6d4f42bf56d064507d694abd56e5f989530e03),
pinned commit `4b6d4f42bf56d064507d694abd56e5f989530e03`.
`src/common/lib.js` SHA-256:
`ca64ef21178be7f17bbbca630252243327241b69d495374d8f8c913f4ec611b1`.
The local checkout's HEAD and calculation file bytes must match the Git object;
any mismatch stops the adapter. The upstream code is MIT licensed and remains
in the disposable checkout with its [license](https://github.com/SauceLLC/sauce4strava/blob/4b6d4f42bf56d064507d694abd56e5f989530e03/LICENSE).
No production dependency or vendored library was added.

The Node VM loads the unmodified file and initializes only the `data` and `power`
namespaces. This runs exact functions on documented inputs, **not the full Sauce
application**. The following pinned source semantics were read and exercised:

| Source | Applied behavior / deliberate boundary |
| --- | --- |
| [`lib.js` active helpers](https://github.com/SauceLLC/sauce4strava/blob/4b6d4f42bf56d064507d694abd56e5f989530e03/src/common/lib.js#L124-L200) | Default positive timestamp gap <75 s plus power/movement/cadence/distance evidence. Trainer distance suppresses moving flags; trainer cadence can establish activity. `activeTime` sums original sample deltas whose active flag is true. Recommended ideal gap is the mode; maximum is rounded max(mode, median) ×4. |
| [`RollingAverage.add`](https://github.com/SauceLLC/sauce4strava/blob/4b6d4f42bf56d064507d694abd56e5f989530e03/src/common/lib.js#L430-L462) | Inactive gaps receive synthetic `Zero` markers, with compressed `Break` handling above 3,600 s. Other gaps repeat the **arriving value backward**, via `new Pad(value)`. Calling this previous-value forward fill would be incorrect. All marker counts are recorded separately. |
| [`correctedPower`, NP and TSS](https://github.com/SauceLLC/sauce4strava/blob/4b6d4f42bf56d064507d694abd56e5f989530e03/src/common/lib.js#L1227-L1313) | Whole corrected array; 30-second power means/fourth moments; default NP minimum 300 s. A drained zero-marker window is excluded from the NP denominator, while a real zero-watt sample remains distinct. |
| [`processors.mjs` activity stress](https://github.com/SauceLLC/sauce4strava/blob/4b6d4f42bf56d064507d694abd56e5f989530e03/src/bg/hist/processors.mjs#L484-L542) | Reproduce corrected kJ/active average/NP, then `calcTSS(np || power, activeTime, ftp)`. Do not import estimated outdoor watts, HR or athlete-state fallback. |
| [`lib.js` FTP lookup](https://github.com/SauceLLC/sauce4strava/blob/4b6d4f42bf56d064507d694abd56e5f989530e03/src/common/lib.js#L2691-L2709), [`data.mjs` daily aggregation](https://github.com/SauceLLC/sauce4strava/blob/4b6d4f42bf56d064507d694abd56e5f989530e03/src/site/performance/data.mjs#L5-L79) | **Not executed:** earliest-FTP prehistory fallback, missing-TSS-as-zero daily input and zero-seeded ATL/CTL conflict with this research's evidence boundary. |

Input adaptations are explicit:

- Accepted file/API source selection, FTP dates and existing 1,028-ride eligibility
  stay unchanged. No new Strava requests. Only dated, qualified inputs enter.
- Parse cadence, distance, speed and selected device context from the same
  original FIT records. Assert raw/extracted power count and ordering agreement.
  All selected FIT parses enforce CRC and original file hash/size checks.
- FIT lacks Strava's moving stream: derive moving from speed ≥0.447 m/s; missing
  speed supplies false. Missing auxiliary fields remain null. In trainer records
  with distance the upstream function ignores moving. Retained API auxiliary
  streams are used when present, otherwise an explicitly absent-moving adapter.
  This is not reconstructed Strava-side processing or a claim of app parity.
- Remove invalid/missing power and all duplicate-timestamp rows only from the
  disposable adapter view, preserving resulting timing gaps. Never pass unknown
  power as JavaScript `null`, which could coerce to zero. Do not sort backwards
  time or alter originals. The observed-only segment comparator is unchanged.
- Four upstream variants: default active heuristic; a **timer-aware adaptation**
  forcing inactive across explicitly known pauses; max-immobile-gap 30 s; and
  max-immobile-gap 120 s. Both latter options are sensitivity experiments, not
  accepted policy. No other upstream code changes.

## Reference set and controlled experiment

Use all **24 exact full-timer candidates**. Because 22 are from 2024 and most are
Rouvy/Wahoo recordings, supplement with **24 complete recorded envelopes** selected
by deterministic quantiles of duration, NP/FTP and NP/mean, then stable identity
order to fill the set. Supplemental intervals are all Zwift FIT and span 2019–2026;
they are reference truth only for their complete recorded intervals. Device and
source classes, duration/intensity/variability/zero fractions are aggregated in
`references` in the JSON; no device identifiers are published. Calibration is
FIT-only, indoors, one rider, nonrandom and correlated across interventions.

**1,823 controlled cases:** 48 pristine, 1,440 single-loss, 48 repeated-burst,
96 start/end truncations, 47 observed-zero losses, 144 constructed pauses.
Deterministic seed `4011500 + reference_index`; reference order is stable.
Each single-loss length (1, 5, 15, 30, 60, 73, 74, 75, 300, 600 s) is placed at
seeded-random, highest-power and lowest-power internal windows with 30 samples
reserved at both boundaries. No result-dependent placements or cherry-picked
successes. Bursts delete twelve equally spaced five-second windows; boundary
cases delete the first/last 30 samples. Zero cases delete a selected known zero.

Pause controls insert 5/60/300 s at the midpoint, shift later timestamps and add
known synthetic pause metadata, **without removing or changing source watts**.
Their target is the declared timer-aware NP-reset reference. They test convention
and active-time effects, not physiological ground truth during real pauses.

All deletion masks, seeds, input arrays and per-case NP/time/marker/stress results
remain private. For unexplained losses the unchanged complete original is the
reference. Strict coverage remains available only for pristine or wholly known
pause controls in the strict-reference group. A segment subtotal is compared to
that full reference to measure omitted contribution, not to imply its partial
label promised a full total. The Sauce pristine baseline is reported separately:
N−1 duration and active classification can differ from the existing half-open
N-bin reference. No rescaling hides this convention difference.

## Results and limits

- Across the 1-/5-second loss cases, Sauce's largest absolute error is **0.79%**;
  the segment method can omit over a third of reference stress after one lost
  second. For the twelve-burst pattern, segment stress is available in 1/48
  cases; Sauce returns all 48, signed error −0.70% to +0.29%.
- Long gaps are not reliable correction targets: a 60 s low-power loss produces
  +21.90% error; a 600 s high-power loss produces −87.59%. The exact 75 s heuristic
  transition and alternate 30/120 s settings expose sensitivity, not a universal
  recovery rule. Error and availability are reported jointly.
- A proposed **≤5 s gap / ≤1% total missing** screen admits 338/1,775 non-pristine
  controlled cases, worst absolute error 0.79%, versus 476 at 15 s / 2.88% and
  539 at 30 s / 3.03%. These are observed sample errors, not guarantees. A synthetic
  hidden five-second 1,000 W surge under otherwise 200 W yields identical remaining
  observations to steady power and a **−5.11%** reconstructed-stress error.
- All **281 actual interrupted dated contributors**, plus 23 complete recent
  envelopes, are compared separately (304 actual cases). There is no missing-
  signal ground truth. Median disagreement with partial stress is +2.39% for
  257 timing-discontinuous rides, +1.54% for 24 missing-power rides. Worst positive
  disagreement is +140.24% / +102.29%, respectively, not measured recovery accuracy.
- The narrow screen admits 47/281 actual interrupted intervals: 46 FIT and one
  API (API calibration remains unvalidated). **Correction in §16 audit:** one of these has consistent boundary/timer
  metadata; the earlier zero-corroboration claim was incorrect. Zero corrected
  whole-session calculations were verified by this envelope experiment. See
  [current audit](owner-policy-audit.json).
  Larger gaps remain partial; unavailable power/FTP stays unavailable.
- Latest 42 days: 31/38 contributors, 1,428.54 partial points versus 1,433.89
  unrestricted experimental points. The close sum does not validate missing
  signals. Candidate classes are 23 complete envelopes, one tentative small-gap
  API estimate, seven partial intervals, seven omitted rides; seven dates have
  no recorded cycling. Latest seven days: 4/6, 183.66 versus 185.69 points,
  two envelopes, two partials, two omitted rides and two no-record dates.

No whole-history TSS, full physiological load, readiness, FTP inference, outdoor
power admission, HR reference inference or default PMC follows from these data.
Five seconds/1% is a conservative candidate grounded in the tested tradeoff,
not a new accepted product rule or a bound on all possible missing efforts.

## Independent verification and preservation

**310 full Python tests pass**, including **25 focused research tests** (seven new
Sauce tests). The local Node adapter passes **52 analytical assertions** covering
constant power, endpoint convention, short/long gaps, exact threshold switching,
observed zeros, explicit pauses, invalid-input rejection, >3,600 s break handling
and arriving-value padding. Tests use synthetic values, not new personal fixtures.

An independent Python oracle does not import upstream math or the experiment's
segment functions. It reconstructs active flags/markers from source semantics,
uses integer prefix sums and Decimal powers/roots, and verifies:

- all **2,127** cases and their original arrays/deletion masks or pause shifts;
- all **8,508** upstream variant results: NP, stress, active duration, corrected
  duration, work, recommended gaps and observed/value/zero/break marker counts;
- every observed-only segment result, reference target and actual contribution;
- **816 published distribution checks**, four cutoff grids and both recent windows.

The oracle and upstream implementations agree within absolute 1e-7 or relative
1e-10 numerical tolerance; this verifies the scoped calculation, not Sauce-app
input equivalence or physiological validity. Publisher summaries carry exact
counts and source hash. The new figure was visually checked for units, reference
scope, omission/coverage and the actual-data “disagreement, not accuracy” label.

Before and after the experiment, the existing independent full-store verifier
checked all **20 production tables**, **1,422 original artifact hashes/sizes**,
unchanged snapshot byte hash, SQLite integrity `ok` and zero foreign-key errors.
It also rechecked the dated-FTP calculations and 70,908 rolling comparisons.
The 349 selected sensor-context sources were read from immutable originals;
none was rewritten. Production modules/schema/UI, source evidence, Performance
results and the 66-entry FTP CSV remain unchanged.

## Reproduction

Use existing Python/fitdecode environment plus Node (run used v20.19.3). Clone the
upstream repository into a disposable private directory, not into product code.
Run the prior dated-FTP verifier first to establish snapshot/source consistency.
Exact resolved commands/logs remain with ignored private artifacts.

```bash
git clone --filter=blob:none --no-checkout \
  https://github.com/SauceLLC/sauce4strava.git '<private-sauce-checkout>'
git -C '<private-sauce-checkout>' checkout --detach \
  4b6d4f42bf56d064507d694abd56e5f989530e03

node tools/verify_sauce_adapter.mjs '<private-sauce-checkout>'
.venv/bin/python tools/research_sauce_gaps.py \
  --data-dir '<private-copy>' --ftp-results '<private-ftp-comparison>' \
  --upstream '<private-sauce-checkout>' --output-dir '<private-sauce-experiment>'
# Optional repeat: --reuse-sensors requires matching snapshot/input hashes and method version.

.venv/bin/python tools/verify_sauce_gaps.py --input-dir '<private-sauce-experiment>'
PYTHONPATH='<private-plot-packages>' .venv/bin/python tools/report_sauce_gaps.py \
  --input-dir '<private-sauce-experiment>' --ftp-results '<private-ftp-comparison>' \
  --report-dir reports/P4-01 --plots
.venv/bin/python tools/verify_sauce_report.py \
  --input-dir '<private-sauce-experiment>' --report reports/P4-01/sauce-comparison.json \
  --output '<private-sauce-experiment>/report-verification.json'

.venv/bin/python tools/verify_training_state_ftp.py \
  --data-dir '<private-copy>' --input-dir '<private-ftp-comparison>' \
  --ftp data/athlete/strava_ftp_history.csv --live-dir '<accepted-store>' \
  --output '<private-sauce-experiment>/preservation-verification.json'
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

No new production dependency is needed; optional plotting uses the existing
private matplotlib 3.10.7 environment. All sensor streams, device strings,
source IDs, actual dates and intervention masks stay private. Public outputs
contain aggregates and an anonymized scatter, no source identities or raw values.
The already-approved FTP CSV is used through the independently checked interval
results; no duplicate dated FTP series or private screenshot is published.

**HARD — Owner:** choose the evidence-scoped stress direction, small-gap threshold,
API applicability and pause/missingness labels. Analyst acceptance follows that
choice. No merge, P4-02, production model, profile import or Phase 5/6 work.
