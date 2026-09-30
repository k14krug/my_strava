# STRAVA-003 — Historical Data-Coverage Census

## 1. Purpose

Quantify the source-data characteristics discovered by STRAVA-001 and STRAVA-002 across Ken's complete Strava bulk-export activity history.

This is the final planned broad archive-discovery experiment before designing the durable historical activity/data-provenance representation. Its purpose is to distinguish common historical conditions from edge cases and to document the evidence that should constrain that design.

This remains research. It does not define the future importer, database schema, or canonical activity model.

## 2. Background / Questions Being Answered

STRAVA-001 established the archive structure: 1,434 CSV activity rows, 1,421 exact activity-file references, 13 rows without files, and a history spanning 2010–2026.

STRAVA-002 deeply inspected 23 deliberately diverse candidates and established that:

* FIT carries rich record/session/lap/device/developer-field evidence.
* GPX and TCX can also contain useful HR, cadence, temperature, power-related, and extension data.
* source-file and Strava CSV values are not guaranteed to be identical.
* presence of power fields or streams does not by itself establish measured/calculated/estimated provenance.
* recording behavior varies.
* the 13 no-file rows are structurally plausible activities, but their missing-file cause is unknown.

STRAVA-003 asks how prevalent those characteristics are across the complete archive.

Questions include:

* How many activities have source files of each format, by year and activity type?
* How many source files contain GPS/position, altitude, heart rate, cadence, power, temperature, distance, and speed evidence?
* How does signal availability change over time?
* For cycling specifically, how many Ride and Virtual Ride activities fall into useful signal combinations?
* How many Ride activities have HR but no source power? GPS/elevation but no source power? cadence but no source power?
* How often does source record-level power exist versus only source summary power versus only Strava CSV power metadata?
* How common are FIT device/session/lap/developer-field characteristics?
* Which developer fields or XML extensions discovered in STRAVA-002 recur enough to merit later attention?
* How common are irregular recording intervals, missing timestamps, duplicates, or large gaps under the STRAVA-002 diagnostic definitions?
* Are there parse failures, corrupt files, or structural outliers that a future history importer must explicitly tolerate?
* What historical eras or cohorts have materially different evidence availability?

The output should help decide what the durable history must represent; it must not make that design decision itself.

## 3. Requirements Used

Use:

* `AGENTS.md`
* `docs/tasks/STRAVA-001.md`
* `reports/STRAVA-001/inventory.json`
* `reports/STRAVA-001/inventory.md`
* `docs/tasks/STRAVA-002.md`
* `reports/STRAVA-002/sample_inspection.json`
* `reports/STRAVA-002/sample_inspection.md`
* `tools/inspect_strava_export.py`
* `tools/inspect_activity_samples.py`

Carry forward the project principles:

* preserve evidence separately from interpretation
* preserve provenance where it matters
* distinguish measured, known, calculated, estimated, inferred, and missing data
* do not manufacture precision
* do not treat field presence as proof of quality, accuracy, or provenance
* do not silently turn research findings into product architecture

Owner decision after STRAVA-002: continue this bounded discovery work, properly document findings, and then use the evidence to move into historical-data design rather than continuing open-ended archive inventory.

## 4. Scope

Create a reproducible whole-history coverage census over all activity files referenced by `activities.csv`.

The census may parse every referenced FIT/TCX/GPX file, but it should extract only compact structural/coverage evidence needed for this task. It must not emit or retain raw streams.

Reuse STRAVA-002 parsing/summarization behavior where appropriate rather than inventing incompatible definitions.

Include the 13 CSV-only rows in overall history counts as activities with no source file.

## 5. Explicit Non-goals

Do not:

* build the future importer
* design the database schema or canonical activity model
* import activities into a database
* preserve raw decoded streams in generated reports
* reconstruct or estimate outdoor power
* decide power provenance from field presence alone
* compare/reconcile every CSV numeric value against every source activity
* call the Strava API
* determine why the 13 no-file rows lack files unless explicit evidence in the existing export establishes it
* infer physical GPS capture merely from position fields, especially for Virtual Ride
* evaluate training load, fitness, fatigue, or workout quality
* redesign the legacy app
* turn the research parser into production architecture
* begin a subsequent design task automatically

## 6. Inputs and Local Data

Expected local source:

```text
local_data/strava-export.zip
```

or an already extracted copy of that same export.

`/local_data/` remains Git-ignored. Original files must not be modified.

The tool should accept an extracted Strava-export directory and an output directory. It may consume STRAVA-001/002 report files when useful, but the census of source-file contents must be derived reproducibly from the local export.

Do not hard-code Ken's absolute filesystem paths.

## 7. Required Experiment

Create a focused census tool, expected approximately as:

```text
tools/census_activity_coverage.py
```

Refactoring small shared parsing helpers out of STRAVA-002 is allowed only if it reduces duplication without turning research utilities into a proposed application architecture.

### A. Population accounting

Account for every CSV activity row and every exact referenced activity file.

At minimum report:

* total CSV rows
* source-file-backed rows
* no-file rows
* successfully parsed source files
* parse failures by format/reason category
* source format counts
* counts by year
* counts by Activity Type
* counts by year + Activity Type + source format where useful

Population totals must reconcile visibly.

### B. Source signal coverage

For each source-backed activity, derive presence/coverage evidence for:

* timestamps
* GPS/position
* altitude/elevation
* distance
* speed
* heart rate
* cadence
* record/point-level power
* source summary power
* temperature

Report aggregate counts and percentages with explicit denominators.

Do not use percentage precision that implies more certainty than simple file/row counts support.

Separate source-file evidence from CSV metadata.

### C. Cycling cohorts

At minimum separately summarize CSV Activity Type:

* `Ride`
* `Virtual Ride`
* non-cycling/other

For Ride and Virtual Ride, report useful combinations including:

* source power present / absent
* HR present + source power absent
* GPS/position + altitude + source power absent
* GPS/position + altitude + HR + source power absent
* cadence present + source power absent
* CSV power metadata present + source record power absent

These are evidence cohorts, not declarations of outdoor/indoor truth or estimated-power eligibility.

Use `Ride` and `Virtual Ride` as Strava Activity Type labels/proxies only.

### D. Historical evolution

Show signal/source-format availability by year, or by a small number of evidence-driven eras if a yearly table becomes unwieldy.

The committed machine-readable report should retain yearly counts even if Markdown uses compact eras.

Make transitions visible rather than smoothing them away.

### E. FIT structural coverage

Across FIT files, report prevalence of:

* session messages
* lap messages
* event messages
* device-info messages
* developer-data / field-description messages
* developer field names/descriptions, counted by files in which they occur
* important record fields discovered by STRAVA-002

Do not expose device serial numbers or other unnecessary identifiers.

### F. TCX/GPX structural coverage

Across TCX and GPX files, report:

* namespace/extension families
* useful extension field/tag names, counted by files in which they occur
* creator/device clues as presence flags only
* signal availability

Keep unknown/private namespace values privacy-safe using the existing hashing/redaction approach.

### G. Recording/timestamp characteristics

Using STRAVA-002 definitions, summarize prevalence of:

* common/median positive recording intervals
* files with missing/invalid timestamps
* duplicate timestamps
* backward/incompatible timestamps
* files with one or more large gaps

This is descriptive evidence. Do not repair streams or declare data quality good/bad solely from these flags.

For performance, do not retain per-point values beyond what is necessary to compute compact summaries.

### H. Power evidence matrix

Document, separately:

* source record-level power
* source summary power
* Strava CSV power metadata

Provide counts for their combinations, especially cycling cohorts.

Power provenance classification remains `unknown` unless a source contains explicit evidence supporting something stronger. Do not infer measured power because record-level power exists.

### I. Parse/outlier log

Any parse failure, structural exception, unusual encoding/XML condition, missing association, or other unexpected condition must appear in a compact diagnostic section with privacy-safe activity/file identifiers.

Do not silently skip files.

If the census encounters a class of files that the STRAVA-002 parser cannot interpret reliably, stop and report if continuing would make coverage counts misleading.

## 8. Required Outputs and Documentation

Produce:

```text
reports/STRAVA-003/
    coverage_census.json
    coverage_census.md
    findings.md
```

### `coverage_census.json`

Machine-readable evidence with:

* population/accounting totals
* aggregate coverage
* yearly coverage
* activity-type/cohort coverage
* format coverage
* structural-field prevalence
* power evidence matrix
* recording/timing prevalence
* parse/outlier diagnostics
* methodology/version metadata

Do not include raw streams, coordinates, serial numbers, activity names/descriptions, or unnecessary free text.

### `coverage_census.md`

Human-readable census. It should make denominators and limitations explicit and allow Analyst/Owner to verify the main quantitative findings without reading JSON.

### `findings.md`

This is a required durable research interpretation, not a duplicate dump of tables.

Organize it as:

1. **What we now know** — findings directly supported by STRAVA-001/002/003 evidence.
2. **What remains unknown** — especially provenance, semantic equivalence, missing-file causes, and any unresolved parsing issues.
3. **Historical cohorts that matter** — materially different evidence populations relevant to later app design.
4. **Implications for historical-data design** — constraints/questions the evidence creates, clearly labeled as implications rather than settled architecture.
5. **Implications for outdoor estimated-power research** — counts of evidence cohorts that may be useful later, without declaring them eligible or estimating power.
6. **Candidate next design decisions** — a concise list of decisions now ready to be discussed with Ken.
7. **Research boundary** — state explicitly that broad archive discovery is complete unless later design work identifies a specific unanswered evidence question.

Where STRAVA-003 confirms or contradicts an impression from the 23-file STRAVA-002 sample, say so explicitly.

Do not silently convert an implication into a requirement.

## 9. Dependencies

Reuse `fitdecode==0.11.0` unless the full corpus exposes a concrete parser limitation that requires reconsideration.

Use standard-library XML parsing for TCX/GPX unless a demonstrated issue requires something else.

Do not modernize unrelated legacy dependencies.

## 10. Verification / Tests

Use synthetic fixtures only; no personal raw activity data in tests.

Tests should cover at minimum:

* population totals reconcile across file-backed and no-file rows
* per-format and per-year aggregation
* Ride / Virtual Ride / other cohort aggregation
* signal-combination cohort logic
* power evidence matrix logic
* FIT structural/developer-field file prevalence
* TCX/GPX extension prevalence
* timing characteristic aggregation
* parse failure/outlier accounting
* privacy-safe output
* deterministic output ordering/content

Retain and run STRAVA-001/002 tests.

For the real-data run:

* account for all 1,434 CSV rows
* attempt all 1,421 exact referenced files
* record all failures/exceptions explicitly
* run twice against unchanged inputs
* confirm generated outputs are byte-identical

Record exact commands and dependency versions in the PR.

## 11. Acceptance Criteria

STRAVA-003 is acceptable when:

1. All 1,434 CSV rows are accounted for.
2. All 1,421 referenced activity files are attempted, with successes/failures explicitly reconciled.
3. Source-signal availability is quantified with clear denominators.
4. Ride and Virtual Ride evidence cohorts are quantified without overclaiming physical indoor/outdoor status.
5. Source record power, source summary power, and CSV power metadata remain distinct.
6. Historical/yearly evolution is visible.
7. FIT/TCX/GPX structural evidence is quantified.
8. Recording/timestamp characteristics are quantified without being overinterpreted.
9. Parse failures/outliers are not silently discarded.
10. `findings.md` clearly separates supported findings, unknowns, implications, and candidate design decisions.
11. The documentation explicitly closes broad archive discovery unless a later targeted question justifies reopening it.
12. Automated tests pass, including prior STRAVA-001/002 tests.
13. Real-data outputs are deterministic across two unchanged runs.
14. No raw personal activity data, coordinates, secrets, or unnecessary personal text are committed.
15. No importer/schema/production architecture is introduced.
16. Analyst review is complete.

## 12. Stop-and-report Conditions

Stop and report rather than producing misleading aggregate numbers if:

* source population cannot reconcile with STRAVA-001 without an explained source change
* a material class of files cannot be parsed reliably
* parser behavior appears to silently drop a signal/extension class discovered in STRAVA-002
* dependency changes would materially disrupt the legacy environment
* privacy-safe aggregation cannot be maintained
* runtime/memory behavior makes the census impractical without a materially different approach
* evidence contradicts a task assumption enough to change the experiment
* work begins expanding into importer/schema/product implementation

Preserve partial evidence, document the blocker, and wait for Analyst/Owner direction.
