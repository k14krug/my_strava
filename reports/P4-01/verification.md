# P4-01 verification and Owner review handoff

**State:** `ready_for_review` at JIT §12 **HARD — Owner**, not accepted.
**Branch / PR:** `task/p4-01-training-state` / [draft PR #23](https://github.com/k14krug/rideworks/pull/23), research head `d4a4619`.
**Invocation:** `/TASK P4-01`. Main refreshed to `84e7048`; Analyst JIT `e04d0ca`.
The JIT omits Execution Control / Allowed Invocation; AGENTS.md's explicit
missing-declaration fallback permits `/TASK only`. The brief was not modified.
Its later Owner/Analyst boundaries remain controlling.

## Delivered

- [DESIGN-003](../../docs/design/DESIGN-003-training-state-model.md): evidence,
  calculations, comparison, limitations, recommendation and exact Owner decisions.
- [Coverage](coverage.md): year/type census and power/HR/duration/work intersections.
- [Sources](sources.md): current primary research and vendor documentation.
- [Aggregate machine-readable evidence](acceptance.json).
- [Synthetic comparison](synthetic-model-comparison.png),
  [anonymized duration/Performance periods](anonymized-context-periods.png),
  [anonymized recorded-work periods](anonymized-work-periods.png),
  and [synthetic checkpoints](synthetic.json).
- Reproducible, disposable tools under `tools/`; eight scientific/regression tests.

Production modules, schema, accepted eligibility, source files, credentials,
settings and Home remain unchanged. No Strava calls, rebuild, migration, CI,
new production dependencies or later-phase implementation.

## Main findings

1. **1,442 Activities / 1,418 cycling**, with **1,028 eligible power results**:
   1,022 FIT and 6 API. Outdoor power remains excluded.
2. Only **one** usable same-session cycling threshold candidate. Supplied 170 W,
   2,762 complete seconds → NP 161.2048301769 W → candidate stress
   68.9889335508. It is not adopted as an independently verified FTP, a present-day
   FTP, or authority for any other activity/date. **1,027 eligible rides lack a
   same-session candidate**. No valid longitudinal FTP or cycling HR-reference
   history was established.
3. **693** complete eligible recorded power envelopes yield calculated work;
   **311** eligible rides have timing discontinuities and **24** missing/invalid
   power in the whole-envelope check. No recording repair or zero filling.
4. Latest six weeks: **38 rides**, **32.29 known elapsed hours**, no missing
   duration summary, but only **23** complete eligible work contributions;
   **15** rides lack this work contribution. No recent threshold candidate.
5. An elapsed-time-only model is misleading: the largest elapsed example contains
   166,891 seconds elapsed versus 5,998.72 seconds timer. Both source values are
   preserved. Its example period is a semantic/outlier diagnostic, not a hard
   training block. Resolving a future production duration policy belongs to the
   Owner/Analyst, not this experiment.
6. Recommendation: transparent separate 7-/42-day workload with coverage;
   FTP-normalized stress remains conditional on date-valid reference inputs and
   session timing. No Fitness/Fatigue/Form truth claim or workload-to-performance
   prediction is established.

The sparse state and duration discrepancy are within the inventory/model-
comparison questions of this research brief. They limit the recommendation;
no policy was invented to “fix” them or expand the experiment into production.

## Method and independent checks

Inventory reads a **private SQLite backup plus copied, hash-verified originals**.
Only DB-referenced artifacts are copied, not OAuth files. The accepted store is
opened with SQLite `mode=ro`; the research read boundary also sets `query_only`.
No `Store` initializer/migration runs. Every source is accounted for; FIT CRCs,
artifact sizes and SHA-256 hashes are checked. Original XML and the original CSV
are inspected, including fields not exposed by the application extraction.

Current Performance signatures must be fresh; pending results cause a stop.
The complete-record-envelope method requires at least 30 paired samples,
nonnegative finite power and exact one-second timestamp increments. Applied only
to the already eligible source, it preserves file precedence and API provenance.
For a contiguous envelope, each sample covers its half-open one-second bin;
`work_kJ = sum(watts) / 1000`. It does **not** claim that the recorded envelope
covers unrecorded session boundaries or pauses. The sole threshold stress
candidate also requires sample seconds = source elapsed seconds = timer seconds.
Its FTP field comes from that same source session and is never propagated.

The independent verifier uses direct SQL selection and Decimal arithmetic rather
than the new census presentation/calculation functions. It separately reconstructs
classification/date/duration, checks full power timing against consecutive
expected timestamps, sums powers, and directly enumerates all 30-s means for the
isolated stress result. It uses direct 7-/42-day sums as the rolling oracle.

Verified:

- **1,442 Activity** identities/classifications/dates/durations;
- all **693** calculated recorded-work results, with no ineligible source used;
- **one** source-scoped stress result, independently by Decimal;
- **5,909 daily rows / 23,636 rolling Decimal comparisons** (duration and work);
- all **20 production tables** match the snapshot by full row fingerprints,
  including native records, both Performance policies, API observations, sync
  state and the existing goal;
- **1,422 original artifact** hash/size checks;
- snapshot database byte hash unchanged; integrity `ok`, zero foreign-key errors;
- no current FTP applied backward; no inferred FTP/HR state; no fabricated load.

The scientific tests independently verify threshold-hour = 100, half-threshold-
hour = 25, real zero watts, variable-power NP by direct window enumeration,
quadratic FTP sensitivity, gap/missing rejection, EWMA impulse/step closed forms,
previous-day balance timing, rolling-window cutoffs, unknown-seed behavior,
unknown-day propagation, and incomplete duration/work subtotals.

**Final test run:** 293 full tests passed, including 8 focused research tests.
The application suite is a regression check, not proof of model validity.
No UI acceptance run is necessary because no product UI was changed. All three
research figures were visually inspected for labels, missingness, and privacy.

## Reproduction

Run from the repository root, with the accepted Python environment containing
`fitdecode==0.11.0`. The **snapshot destination must not already exist**. These
commands use path placeholders because private local paths must not be committed.
Exact resolved invocations and logs remain with the ignored private outputs.

```bash
.venv/bin/python tools/research_training_state.py \
  --snapshot-from '<accepted-store>' \
  --data-dir '<new-private-copy>' \
  --output-dir '<private-census>'

# Optional rerun after changes to the comparison code: reuse the completed raw
# parse only after its database/version match and every artifact hash rechecks.
.venv/bin/python tools/research_training_state.py \
  --data-dir '<private-copy>' --output-dir '<private-census>' --reuse-raw

# Plotting packages are installed only into a disposable local directory.
.venv/bin/python -m pip install --target '<private-plot-packages>' matplotlib==3.10.7
PYTHONPATH='<private-plot-packages>' .venv/bin/python tools/compare_training_state.py \
  --input-dir '<private-census>' --output-dir '<private-comparison>' \
  --as-of 2026-10-08 --plots

.venv/bin/python tools/verify_training_state.py \
  --data-dir '<private-copy>' --input-dir '<private-census>' \
  --comparison-dir '<private-comparison>' --live-dir '<accepted-store>' \
  --output '<private-census>/independent-verification.json'

.venv/bin/python -m unittest discover -s tests -p test_research_training_state.py -v
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

The optional live comparison reads but never writes the accepted store. If the
Owner syncs new history after the snapshot, its preservation equality must fail;
use a fresh snapshot for a new experiment rather than weakening the check.
The aggregate calculations require no plotting packages; omit `--plots` to run
with the existing application environment only. Plotting run used matplotlib
3.10.7 / NumPy 2.2.6. No scientific fitting package is required.

Private outputs: `raw-inventory.json` (raw state/source pointers), `activities.json`
(per-Activity facts/provenance), `daily-private.json` (dated context), copied store
and originals. **Do not commit them.** The public report selects aggregate census
fields, comparison summaries, independent check counts and synthetic checkpoints.
Only relative-day anonymized plots are committed. No IDs, titles, source hashes,
raw streams, local paths, coordinates, athlete tokens or original files are in
these reports. Individual source-supplied threshold context is reported only to
explain the one isolated calculation.

## Requirement mapping and limits

| JIT requirement | Evidence / result |
| --- | --- |
| §4 power/HR/duration/work inventory and overlap | Entire snapshot, year/type table and four-way overlap; source vs calculated work separated |
| §5 dated athlete-state inventory | Original FIT/XML/CSV and retained API fields; usable threshold scoped to one session; weight/HR/zones limitations explicit |
| §6A industry model | Current documented formula, isolated source-state candidate, synthetic decay comparisons; real longitudinal model unavailable |
| §6B simpler model | Same-input synthetic comparison; actual recorded-work and duration context windows with contributor/missing counts |
| §6C HR candidate | Not evaluated numerically because appropriate reference state is missing; no invented fallback |
| §6D context | Actual anonymized periods, timer/elapsed discrepancy, Performance context, title-only race hints not promoted to confirmed hard sessions |
| §7 evidence policy | Existing v2 selection unchanged; outdoor and short/incomplete exclusions counted |
| §8 comparison | Coverage, state dependence, explainability, response/noise, unknown-day behavior and sparse outcome limitations; no parameter fitting |
| §9 primary sources | Current TrainingPeaks docs, Banister lineage/limitations, 2026 peer-reviewed cycling model, primary HR/cycling findings |
| §10 deliverables | DESIGN-003, this report, aggregate JSON, figures and reproducible scripts |
| §11 production boundary | No production files/schema/UI changed |
| §12 Owner gate | Direction, required manual data and P4-02 proposal ready; **approval outstanding** |
| §13 Analyst gate | Follows Owner decision; independent verifier supplied, Analyst acceptance outstanding |

Limitations: completeness of the rider's full life/training calendar is not
established; no recorded cycling is not proven rest. Date-only sources do not
support exact local-time placement. Opaque vendor fields may contain as-yet
uninterpreted context. Source threshold and weight settings are not proven
measurements. Whole-envelope filtering is conservative and not a final pause
policy. Periods are selected for illustration and may overlap. TSS/CTL/ATL and HR
load lack enough historical reference evidence for a fair real longitudinal
comparison. No readiness, optimality or causality claim follows from these data.

**Decision needed:** choose the workload-first direction or require dated FTP
collection first; then authorize the Analyst to settle the narrow timing and
missingness contract. The brief says **“Stop for Owner decision.”** No P4-02,
Phase 5/6 work or substantive task acceptance is authorized by this handoff.
