# P4-01 revised verification — dated FTP and interrupted recordings

**State:** `ready_for_review` at **HARD — Owner**, not accepted.
**Branch / PR:** `task/p4-01-training-state` /
[draft PR #23](https://github.com/k14krug/rideworks/pull/23).
**Invocation:** `/TASK P4-01`; the JIT's missing Allowed Invocation declaration
uses AGENTS.md's `/TASK only` fallback. No execution controls were edited.

Fetched origin and fast-forwarded the existing task branch, then integrated main
`91842f7` with Analyst JIT `645cb48`, Phase 4 contract `a74c97c` and FTP privacy
exception `a288dfd`. Read all four PR comments; there were no review/inline
comments. The latest Owner comment supersedes the earlier FTP privacy hold.
Transient STATUS/TASKS merge conflicts were resolved to the latest authorization.
CSV source `46be978` and provenance `a1d10cc` remain unchanged.

## Revised findings and deliverables

- [DESIGN-003](../../docs/design/DESIGN-003-training-state-model.md) now recommends
  separate 7-/42-day work and **partial recorded segment stress**, subject to
  Owner choice of model and recording policy. Dated FTP collection is no longer
  the prerequisite it was in the initial recommendation.
- [FTP coverage](ftp-coverage.md) and [acceptance.json](acceptance.json) include
  all intersections, year/type counts, recent windows, sensitivity and verification.
  JSON separates `initial_research` from `continuation`; old absence claims are
  about the retained-source evidence before the new CSV.
- [Revised figure](anonymized-ftp-model-comparison.png) compares matched work and
  stress on the same ≥600 s segments, relative days and distinct units. Prior
  [synthetic](synthetic-model-comparison.png), [duration/Performance](anonymized-context-periods.png)
  and [original-envelope work](anonymized-work-periods.png) figures remain initial
  reference evidence. The original [verification](initial-verification.md) is
  retained explicitly as historical evidence, with its old review question superseded.
- New disposable tools: `research_training_state_ftp.py`, independent
  `verify_training_state_ftp.py`, and aggregate-only `report_training_state_ftp.py`.
  Ten new synthetic tests supplement the eight existing research tests.

**FTP input:** all 66 rows validate as positive watts, distinct sorted dates,
consecutive exclusive ends and a final open interval. Repeated values stay
separate. Source class is Owner-provided Strava UI historical setting, not
laboratory measurement. Dex did not re-inspect the private screenshot; the
committed Owner/Analyst transcription is the authorized research source. Its
SHA-256 is retained in the public aggregate, without duplicating the dated series.

**Coverage:** 1,121/1,418 cycling Activities have dated FTP; 878/1,028 eligible
power rides intersect it. Of the 693 original complete envelopes, 597 have FTP;
another 281/335 incomplete eligible recordings yield dated segment contributions.
All 297 cycling FTP gaps precede the first date, including 150 eligible rides.
No historical current-FTP backfill, best-20 inference or outdoor power admission.

**Recording policies:** observed-bin work expands from 693 to 1,028 contributors;
≥600 s segment stress expands from 597 complete envelopes to 878 contributors.
Only 24 qualify under the exact full-timer candidate, versus 75 with a one-second
summary discrepancy sensitivity. The sensitivity fills no missing active time.
Two exact-timer candidates recover missing-power records at the exclusive stop
boundary. Native segments preserve gaps, invalid power and duplicate evidence.
The numerical minimum (30 s) versus conservative 600 s candidate changes stress
by 1.24% in aggregate and 0.95% in the latest 42 days. Source timing contradictions
and incomplete power remain reportable evidence, not silently repaired input.

**Recent comparison:** as of 2026-10-08 (the same completed-day anchor as before),
31/38 rides in 42 days contribute 11,075.38 kJ observed work; the same segments used
for normalized stress provide 10,930.67 kJ and 1,428.54 segment-stress points.
Seven days: 4/6 rides, 1,465.90 kJ observed, 1,449.91 kJ matched, 183.66 points.
Full-timer stress is unavailable for these recent windows under the exact rule.
Omitted rides, omitted within-ride seconds and no-record dates are distinct.
Unknown dates/sessions are not zero, and partial stress is not a full TSS total.

## Verification performed

The original snapshot was reused **only after** independently comparing every
production table with the accepted live store. All 20 tables still match. The
prior raw census is bound to the snapshot byte hash; no stale/newly synced data
are mixed into it. The independent initial verifier was rerun successfully:
1,442 Activity checks, 693 work results, one source-session stress calculation,
5,909 days and 23,636 rolling comparisons. The continuation verifier rechecks
all 1,422 original artifact sizes and hashes. No original parse was silently
assumed to apply to a changed database.

Continuation checks use direct SQL and an independent algorithm:

- all **1,442** activity dates/classifications and their linear FTP interval lookup;
- **66** structurally validated intervals; no prehistory value or future backfill;
- all **1,028** eligible power sources; all excluded rows retain unavailable load;
- **878** dated segment-stress contributions and **24** exact-timer candidates;
- **2,718** segment-metric comparisons across 30-/600-second candidates, with
  direct integer 30-s sums and Decimal fourth powers/roots rather than the
  research rolling-sum implementation;
- independent source-row/time grouping, duplicate exclusion, timer-event pair
  interpretation, active-bin completeness and session-boundary checks;
- **5,909** daily rows and **70,908** direct-date 7-/42-day Decimal subtotal checks
  across six work/stress candidates, including contributor and omission counts;
- aggregate, year/type and recent-window coverage checks;
- unknown-seed CTL/ATL/TSB remains unavailable; no fabricated decay through gaps;
- all **20 live tables** still equal the snapshot after research; all **1,422**
  original hashes/sizes pass; snapshot byte hash unchanged; SQLite integrity
  `ok`, zero foreign-key violations.

**Tests:** 303 full tests passed, including 18 focused research tests (ten new).
Synthetic cases cover inclusive/exclusive FTP boundaries, repeated entries,
no backfill, malformed source rejection, unknown timezone boundaries, real zero
versus missing, gap/duplicate/backwards/subsecond handling, short-segment omission,
timer stop/restart boundaries, nonlinear segment versus pooled stress, separate
units, finite rolling edges and unknown-seed/missing-day behavior. Test fixtures
are generated synthetic values, not additional personal source files.

The independent verifier initially exposed a zero-duration timer pair its oracle
had assumed absent. The research method already withheld it. The oracle was
corrected to verify that exclusion; it does not reinterpret the pair or change
the candidate policy. The corpus also has a file without usable timer pairs and
six API streams without FIT timer evidence.

The revised plot was visually inspected for units, partial labels, missing/no-record
markers and privacy. Public evidence uses aggregate counts, synthetic data and
anonymized relative-day figures. No ride IDs, source IDs, activity dates/streams,
private paths, coordinates, credentials or screenshot are added. Only the
explicitly approved FTP source CSV contains the full dated FTP series.

## Reproduction

Use the accepted environment (`fitdecode==0.11.0`). The original census/snapshot
commands are in [initial verification](initial-verification.md). The continuation
requires that same snapshot, its hash-bound census, and the committed FTP CSV.
Paths below are placeholders; exact resolved commands/logs remain local-only.
The common `--as-of 2026-10-08` permits direct before/after comparison. A later
anchor is a new comparison, not proof that no rides occurred after the snapshot.

```bash
# Establish that the retained snapshot still represents the accepted live store.
.venv/bin/python tools/verify_training_state.py \
  --data-dir '<private-copy>' --input-dir '<private-census>' \
  --comparison-dir '<initial-private-comparison>' --live-dir '<accepted-store>' \
  --output '<private-census>/continuation-baseline-verification.json'

# Optional plot packages remain outside production dependencies:
# matplotlib==3.10.7, NumPy 2.2.6 in a disposable directory.
PYTHONPATH='<private-plot-packages>' .venv/bin/python tools/research_training_state_ftp.py \
  --data-dir '<private-copy>' --input-dir '<private-census>' \
  --ftp data/athlete/strava_ftp_history.csv \
  --output-dir '<private-ftp-comparison>' --as-of 2026-10-08 --plots

.venv/bin/python tools/verify_training_state_ftp.py \
  --data-dir '<private-copy>' --input-dir '<private-ftp-comparison>' \
  --ftp data/athlete/strava_ftp_history.csv --live-dir '<accepted-store>' \
  --output '<private-ftp-comparison>/independent-verification.json'

.venv/bin/python -m unittest discover -s tests -p 'test_research_training_state*.py' -v
.venv/bin/python -m unittest discover -s tests -v

# Publish only reviewed aggregate/relative-day artifacts after verification.
.venv/bin/python tools/report_training_state_ftp.py \
  --input-dir '<private-ftp-comparison>' --report-dir reports/P4-01 --test-count 303

git diff --check
```

Private outputs retain selected source IDs, FTP interval/source/value, segment
indices/NP/work/stress, native gaps/invalid counts, timer evidence and daily
missingness. Do not copy these outputs wholesale into the repository. The
publisher explicitly selects aggregate diagnostics; it does not publish private
activity or dated daily rows. Production modules, schema, UI, dependencies,
Performance-v2 and originals are unchanged. No Strava requests, profile import,
P4-02 implementation, planning or merge occurred.

## Review boundary

The continuation fulfills JIT §14's source validation, FTP intersections,
recording-policy comparison, normalized stress, separate 7/42 models and revised
recommendation. Current primary sources were rechecked for formula and timer
semantics; [the source register](sources.md) separates documented practice from
our candidate choices. HR normalized load remains unavailable without cycling
reference state. Recorded contributions are not physiological validation.

**HARD — Owner:** choose the dual work/partial-segment-stress direction versus
work-only or strict full-timer stress, and approve/change the 600-second recording
candidate and missingness presentation. No additional FTP entry is required for
the recent windows. After Owner choice, the Analyst reviews calculations/design
and authors a narrow P4-02 JIT. No acceptance or P4-02 implementation is inferred
from this research or its passing tests.
