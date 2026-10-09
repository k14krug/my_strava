# P4-01 Owner-policy reconciliation — Analyst handoff

**State:** `ready_for_review` at **HARD — Analyst**, JIT §16. TASKS remains
`in_progress`; Owner model/policy approval is recorded, Analyst acceptance pending.
**Branch / PR:** `task/p4-01-training-state` /
[draft PR #23](https://github.com/k14krug/rideworks/pull/23).
**Invocation:** `/TASK P4-01`, permitted by the refreshed JIT.

Refreshed main `20cfbb6`, JIT `36c72d0`, Phase 4 contract `67ad8ca` and TASKS
`151a48e` are integrated. Read the latest PR discussion and
[Analyst correction review](https://github.com/k14krug/rideworks/pull/23#pullrequestreview-5473101415).
No unresolved inline review comments existed. This revision addresses all four
Owner choices without changing production behavior or the historical experiment.

## Selected policy and coverage

[DESIGN-003](../../docs/design/DESIGN-003-training-state-model.md) now records:

- Separate 7-/42-day **observed work kJ** and FTP-normalized stress, with calculated
  recorded-interval, corrected **estimated** interval, partial observed-segment
  and unavailable classes. Whole-session labels require corroborated boundaries
  and verified calculation coverage. Show missing rides/time and no-record dates.
- Eligible dense 1 Hz **FIT-only** correction: each unexplained interior gap
  **≤15 missing seconds AND total missing ≤1% of recorded interval span**;
  ordered valid unique samples, no unresolved invalid/duplicates, no extrapolation
  beyond observed bounds and no correction across a proved pause.
- Accepted detailed API power stays eligible for **observed-only** work/stress;
  no API gap correction in v1. Larger/uncertain losses fall back to continuous
  ≥600 s observed segments, or unavailable when none qualifies.
- Validated FIT stop/restart events override movement heuristics. Split active
  intervals, reset NP at restart and sum labeled interval contributions. Never
  fill proved pauses with power or zeros. Missing/conflicting timing prohibits
  full-session claims. The old zero-marker `timer_aware` Sauce experiment is not
  the selected pause rule and its totals are not relabeled as that calculation.

The [reproducible source-specific audit](owner-policy-audit.json) independently
recomputes gaps from the private arrays for all **304 actual experiment cases**,
cross-checks experiment metadata and the hash-bound dated-FTP source results, and
confirms the 15 s / 1% screen yields **133 all-source intervals = 131 FIT + 2 API**.
Only **131 FIT** intervals enter the approved estimate screen. Five-second
comparison: 46 FIT + 1 API; thirty-second comparison: 150 FIT + 2 API. Historical
5/15/30 error results remain unchanged; the 15-second controlled maximum 2.88%
is not a universal accuracy bound. No production calculation was implemented.

**Correction to prior reporting:** one of the 131 FIT candidates (also in the
five-second set) has matching timer-summary/event duration and corroborating
session/start/end metadata. The earlier statement that none had that metadata
was incorrect. Its historical Sauce output used the recorded envelope, including
the sample at timer stop, not an independently verified timer-clipped corrected
calculation. **Zero new corrected whole-session calculations were verified**;
this remains distinct from the corrected count of one boundary/timer candidate.
No whole-session label is automatically assigned by this coverage audit.

## Recent coverage and time omissions

| Completed calendar window ending 2026-10-08 | 7 days | 42 days |
| --- | ---: | ---: |
| Recorded cycling / contributors | 6 / 4 | 38 / 31 |
| Complete recorded envelopes | 2 | 23 |
| FIT estimate-screen intervals | 0 | 2 |
| Remaining partial contributors | 2 | 6 |
| Omitted rides / no-record dates | 2 / 2 | 7 / 7 |
| Known interior missing seconds among contributors | 160 | 510 |
| Missing seconds within FIT estimate screens | 0 | 21 |
| Observed seconds excluded by historical ≥600 s comparator | 240 | 1,746 |

These are different kinds of omitted time, not additive estimates of total
missing training. Time outside recordings and within omitted rides is unknown.
No-record dates are not asserted rest. Work remains observed-only. The historical
segment versus unrestricted Sauce totals remain comparison evidence, not totals
under the newly selected timer-splitting policy. The 131 count screens unpaused
recorded envelopes; it does not claim new recovery of paused full sessions.

## Verification and reproducibility

- **311 full Python tests**, including **26 focused research tests**, pass.
  Added a synthetic validated-pause check: two 900 s active intervals at 100/300 W
  with a 60 s pause containing deliberately high records yield 360 observed kJ
  and 62.5 stress points at FTP 200 after timer exclusion and NP reset. The pause
  records contribute neither watts nor time; no new personal fixture is added.
- **52 Node adapter assertions** rerun successfully against the unchanged pinned
  Sauce source. The independent published-report verifier again passes **816
  distributions, four cutoff grids and both windows**. Previous full numerical
  verification of 2,127 cases / 8,508 variants remains valid for unchanged inputs,
  algorithms and outputs; it was not rerun solely for this documentation change.
- Full-store preservation verifier rerun: **20 production tables and 1,422 source
  artifacts** unchanged; snapshot byte hash unchanged, integrity `ok`, zero FK
  violations. It also rechecks 66 FTP intervals, 878 dated contributions, 2,718
  segment metrics and 70,908 rolling comparisons. Approved FTP CSV unchanged.
- Aggregate privacy scan, local report links and `git diff --check` pass.
  All source identities, streams, device strings and databases stay private.

```bash
.venv/bin/python tools/audit_training_state_policy.py \
  --input-dir '<private-sauce-experiment>' --ftp-results '<private-ftp-comparison>' \
  --output reports/P4-01/owner-policy-audit.json
.venv/bin/python -m unittest tests.test_research_training_state \
  tests.test_research_training_state_ftp tests.test_research_sauce_gaps -v
.venv/bin/python -m unittest discover -s tests -v
node tools/verify_sauce_adapter.mjs '<private-sauce-checkout>'
.venv/bin/python tools/verify_sauce_report.py \
  --input-dir '<private-sauce-experiment>' --report reports/P4-01/sauce-comparison.json \
  --output '<private-sauce-experiment>/owner-policy-report-verification.json'
.venv/bin/python tools/verify_training_state_ftp.py \
  --data-dir '<private-copy>' --input-dir '<private-ftp-comparison>' \
  --ftp data/athlete/strava_ftp_history.csv --live-dir '<accepted-store>' \
  --output '<private-sauce-experiment>/owner-policy-preservation.json'
git diff --check
```

The unchanged [Sauce methods/results](sauce-verification.md),
[error table](sauce-errors.md), [aggregate comparison](sauce-comparison.json),
[figure](sauce-gap-comparison.png), prior [dated-FTP verification](ftp-verification.md)
and [initial verification](initial-verification.md) remain historical evidence.
Current lifecycle and decision metadata: [acceptance.json](acceptance.json).

**Stop at HARD — Analyst:** accept or request corrections to this reconciled
research/design and boundary-count correction. No merge, task acceptance,
P4-02 implementation, production FTP import or later task is authorized here.
