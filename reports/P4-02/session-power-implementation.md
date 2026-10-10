# P4-02 — Installed estimated session-power stress

**Implemented under approved JIT §14; ready at HARD — Analyst Gate 1.** Branch
refreshed through `fc5e405` and [Analyst implementation authorization](https://github.com/k14krug/rideworks/pull/24#issuecomment-6102096016).
The §13 method decision is resolved. Subsequent branch refresh through `5d21678` includes the Analyst-committed final Form default. This report verifies the installed selector
and actual running review page, rather than a substituted diagnostic curve.
PR #24 remains draft. The Owner’s final acceptance is conditional on verified §14 implementation and Form’s initial unchecked state, per [the latest decision](https://github.com/k14krug/rideworks/pull/24#issuecomment-6102260559). No merge or Phase 4 completion.

## Calculation and selection

Training State **v4** adds `elevate-time-buffer-session-pss-v1` and the approved
`distributed-observations-v1` screen. The estimator shares the recorded-power
evaluator's native extraction integrity, source ambiguity, native/API precedence
and confirmed measured-device/high-resolution API checks. No Performance best-20
gate is used and no outdoor estimated watts become trusted inputs.

Available non-null measured watts use the pinned Elevate nonoverlapping time
buffer, with its check-before-time-add convention, arithmetic sample means and
discarded unfinished final buffer. Known timer stops exclude stopped samples and
reset weighting. No API gap fill, invented watts or extrapolated observed work.
Session stress is `100 * supported_moving_or_active_seconds / 3600 * (weighted_power / dated_FTP)^2`,
using unrounded intermediates and the existing approved historical FTP.

The screen requires >=80% total observed timeline, >=50% in **every sliding
300-second window**, and a >=600-second contiguous observed segment. It includes
missing starts/endings. Only independently verified active timer boundaries can
compress the screening clock; otherwise it uses the same-source full elapsed
timeline and supported origin. Formula duration remains the separately reported
moving/timer value. Contradictory/unclosed timers, unsupported duration, missing
FTP, impossible timing, ambiguous/untrusted sources and independently known
omitted effort retain explicit exclusions. Unknown small-gap intensity remains
the already accepted approximation limitation, not inferred recovery or rest.

Selection is deterministic: **complete/corrected recorded power → qualifying
estimated session power → HR estimate → observed partial power → unavailable**.
It never adds power and HR or selects their maximum. Existing recorded/corrected/
partial candidates, observed kJ and all HR candidates remain separately intact.
The new `session_estimate` class is labeled **Estimated session power**, with
source, duration, FTP, weighted power, screen, omissions and uncertainty available
in the persistent inspection and hover. Workload source counts include it.
The help text explains its distinction from measured complete effort. Fitness/Fatigue lines are visible on first load; Form is initially unchecked, with all three independently toggleable.

Version, estimator, screen, selection policy, upstream pin and parameters enter
cache signatures. Current caches recalculate under v4; all 1,418 cached records
are v4, fresh source recalculation matches each one, and restart/repeat reuse is
identical. No source-store migration or unrelated Performance change.

## Actual behavior

The independently selected mandatory interval case **now selects the qualifying
session-power estimate in the running app**, replacing its HR contribution.
Actual same-day Fitness and Fatigue increase; following-day Form derives from
that day's recalculated Fitness minus Fatigue. Source inspection still exposes
the original observed partial and HR alternatives. The mandatory outdoor case
retains its corrected HR selection and observed-power exclusion. Exact values,
source references, before/after state, isolated contribution and screenshots are
in the private handoff, not committed activity-level artifacts.

**28 rides change:** 27 HR estimates and one partial-power selection become
estimated session power. **No previously unavailable ride is newly scored.**
Overall coverage remains **1,150/1,418**, outdoor coverage **10/148**, with 268
unavailable. Current selected classes: 642 calculated, 150 corrected FIT,
183 HR estimates, 147 partial power, 28 estimated session power, 268 unavailable.

Every old recorded-power candidate, observed work value, HR candidate, HR setting
and FTP object is identical across all 1,418 rides. Complete/corrected selections
remain identical. Of the separately diagnosed 117 formerly best-20-blocked cases,
the actual selection is now **53 calculated / 19 corrected / 34 partial /
7 session estimates / 4 HR**. All original decoupling outcomes remain traceable.

At the frozen completed-day endpoint `2026-10-10T00:30:00+00:00`:

| Window | Previous v3 selected stress | Installed v4 stress | Completed Elevate reference | Changed rides |
|---|---:|---:|---:|---:|
| 7 days | 170.86 | 187.89 | 216.75 | 2 |
| 42 days | 1,747.97 | 1,793.46 | 1,920.45 | 3 |
| 90 days | 3,034.25 | 3,079.73 | 3,127.50 | 3 |
| 365 days | 8,289.61 | 8,335.10 | 8,869.08 | 3 |

Endpoint Fitness/Fatigue/Form changes approximately **+0.927 / +2.846 / −2.333**.
These are actual recalculated historical results; the running page additionally
includes the current rider-local calendar day. Selected-day card changes compare
seven days earlier; the private behavioral checks separately calculate exact
day-over-day changes and following-day Form.

Of 13 independently predeclared cases, **12 agree with the reference's direction
of both daily Fitness and Fatigue change**. The remaining deliberately sparse
case has unsupported duration/timer evidence and lacks a qualifying contiguous
power interval; it stays unscored, while the reference reports training load.
That is an explained retained-source limitation. Other numerical disagreement
includes missing historical load, different prior model state/seeds, approved
FTP versus exported FTP, HR assumptions and weighted-power method/scope.
Reference comparison is descriptive; no multiplier or score is fitted.

160 chosen source session candidates are eligible; 132 retain complete/corrected
recorded-power priority. Other estimator exclusions include 671 timer/reported-
duration conflicts, 198 unsupported durations, 172 unknown FTP cases and 148
outdoor exclusions; distribution/continuous-segment/clock failures remain named.
An estimate-specific rejection does not invalidate a separately supported
recorded-interval result. The accepted screen still cannot prove unknown gap
intensity; its uncertainty stays visible rather than relabeling inferred load as
complete measured effort.

## Verification

- **383 Python tests pass**, including 10 new production session tests. They
  exercise pinned buffer math, unrounded stress, equal-count clustered/dispersed
  recordings, sliding minima/edges, null watts, endpoint clipping, duration/FTP,
  verified and unverified pause scope, known effort omissions, source conflicts,
  complete/corrected priority, a higher-HR alternative, fallback and cache
  version/parameter invalidation. Four older selection tests were updated for
  the explicitly approved power-before-HR behavior, preserving their original
  interval/work/HR and no-double-count checks.
- **506 general Chromium assertions and 614 private representative assertions**
  pass: 13 activities / 32 date-range inspections. The actual new source/stress,
  same-day model math, following-day Form readout, uncertainty, exact dates,
  three line toggles, persistent source inspection, hover, keyboard and touch
  are verified. 3-/12-month views retain **600/400 CSS-pixel actual plots**;
  desktop and 320-/390-pixel phones pass. Private screenshots were inspected.
- **32 source/distribution/formula checks** pass; **41 actual pinned upstream
  buffer executions** independently match current candidate weighted power,
  including timer reset and dropped groups with no finished buffer.
- **All 1,418 fresh source calculations match the installed v4 caches**. Repeat
  and reopened-store results are identical. The verifier starts with already
  recomputed caches (zero additional misses), not a simulated old-cache result.
- Independent **3,053 daily model / 1,263 observed-power / 874 HR formula checks**
  pass on actual selected contributions. All **20 original tables / 1,422 source
  originals** remain intact; integrity is `ok`, foreign-key violations zero.
  Home outside its intentional Training State snapshot and Performance match at
  identical clocks; Activities body matches at the same timezone. Stable
  Activity Review routes pass in-browser.
- Historical FTP/package copies and the original **496,966-byte Elevate CSV**
  retain their hashes. Its final **14 projection days** are excluded. No
  original files, benchmark settings or vendor results are imported or modified.

Safe outputs: [selection and behavior](session-power-selection.json),
[verification](session-power-verification.json),
[reference sanity comparison](session-power-elevate-sanity.json).
Private source-level handoff:
`local_data/p4-02-session-implementation/verification-private.md` and
`behavior-private.json`; screenshots remain under ignored `output/playwright/`.
The updated running review page uses the existing private copy at
`http://127.0.0.1:8772/training-state`.

## Reproduce / review

```sh
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python tools/verify_training_state_session_selection.py \
  --data-dir local_data/p4-02-baseline/store \
  --baseline-dir local_data/p2-05-review \
  --before local_data/p4-02-session-implementation/before-private.json \
  --cases local_data/p4-02-session-implementation/cases-private.json \
  --blocked-cases local_data/p4-02-interval-diagnosis/diagnosis-private.json \
  --reference data/reference/elevate/fitness_trend_export.2026.10.9-15.58.52.csv \
  --reference-source local_data/p4-02-power-followup/activity-computer.ts \
  --as-of 2026-10-10T00:30:00+00:00 \
  --after-output local_data/p4-02-session-implementation/after-private.json \
  --private-output local_data/p4-02-session-implementation/behavior-private.json \
  --aggregate-output reports/P4-02/session-power-selection.json
.venv/bin/python tools/verify_training_state_production.py \
  --data-dir local_data/p4-02-baseline/store \
  --baseline-dir local_data/p2-05-review \
  --as-of 2026-10-10T00:30:00+00:00 \
  --output local_data/p4-02-session-implementation/production-verification.json
.venv/bin/python tools/compare_training_state_elevate.py \
  --data-dir local_data/p4-02-baseline/store \
  --reference data/reference/elevate/fitness_trend_export.2026.10.9-15.58.52.csv \
  --as-of 2026-10-10T00:30:00+00:00 \
  --aggregate-output reports/P4-02/session-power-elevate-sanity.json \
  --private-output local_data/p4-02-session-implementation/elevate-private.json
npx --yes --package @playwright/cli playwright-cli -s=p402 run-code \
  "$(cat tools/verify_training_state_browser.js)"
npx --yes --package @playwright/cli playwright-cli -s=p402 run-code \
  "$(cat local_data/p4-02-session-implementation/browser-private.js)"
```

Private prior v3 results, declared cases and accepted source stores must already
be available. The reference code's commit/hash/download procedure is recorded in
the prior method report; its hash is checked before executing the oracle. Open
the skill-managed Chromium session before browser commands. No activity fetching
or source-file modification occurs.

**Next review:** Analyst reviews the implemented §14 estimator/selector,
recalculated actual behavior, source disclosures, verification and preserved
invariants at **HARD — Analyst Gate 1**. The Owner’s conditional Gate 2 acceptance requires Analyst verification of §14
and the Form default; no further open-ended design round is requested. TASKS remains `in_progress`; STATUS is `ready_for_review`.
