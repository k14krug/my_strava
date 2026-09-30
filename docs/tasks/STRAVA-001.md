# STRAVA-001 — Inventory Latest Strava Bulk Export

## 1. Purpose

Build and run a small, reproducible local analysis tool that inventories Ken's latest Strava bulk export.

The goal is to establish what historical source material actually exists before designing the future application's historical importer, persistence model, or source-reconciliation behavior.

This is an evidence-gathering task, not an importer implementation task.

---

## 2. Background / Question Being Answered

Ken has downloaded a current Strava data export of roughly 1 GB. The archive is too large and too private to use as a normal GitHub artifact.

Before making historical-import design decisions, we need concrete answers about the export:

* What files and directories does Strava currently provide in this export?
* What columns and values are present in `activities.csv`?
* What activity file formats are present?
* What time period is covered?
* How well do CSV activity rows associate with exported activity files?
* Which rows/files appear missing, duplicated, malformed, unusual, or otherwise worth deeper inspection?
* Which representative activity files should we inspect next?

The tool must operate on Ken's local extracted export and emit compact results that can safely be reviewed through GitHub.

---

## 3. Requirements Used

This task is based on the Personal Cycling Training App project principles carried into `AGENTS.md`, especially:

* own a durable useful training history assembled from the best available sources
* preserve original source data and provenance
* distinguish known/measured/calculated/estimated/inferred/missing information
* inspect the actual Strava bulk export before committing to historical-import design
* expect overlapping sources and future enrichment rather than assuming one file equals one canonical activity
* avoid premature architecture
* use Strava as an important source, not as the product specification

Repository workflow and data-handling requirements come from:

* `AGENTS.md`
* `TASKS.md`
* `STATUS.md`

No existing legacy `my_strava` database schema or application behavior is a requirement for this task.

---

## 4. Scope

Create a standalone inventory utility for an **already extracted** Strava bulk-export directory.

The utility must inspect:

1. top-level and relevant nested export structure
2. `activities.csv`
3. activity files referenced by the CSV and/or present in the export
4. file extensions/formats and compression
5. basic historical/activity-type coverage
6. CSV-to-file association quality
7. obvious anomalies useful for choosing later representative samples

The tool should inspect metadata and filenames cheaply. It does **not** need to fully parse every FIT/TCX/GPX stream in this task.

---

## 5. Explicit Non-goals

Do not:

* design or implement the future application's historical importer
* design a database schema
* load the export into the legacy application's database
* redesign the old Flask application
* call the Strava API
* modify any original export file
* estimate cycling power
* calculate training metrics
* normalize activities into a proposed canonical production model
* attempt sophisticated duplicate-activity resolution
* deeply parse every FIT/TCX/GPX file
* add CI, containers, web UI, or infrastructure
* commit Ken's raw export or bulk activity files
* infer that the current Strava export format is a permanent API/contract

If a small parser dependency is useful merely to inspect a few representative headers, stop and report that as proposed follow-up rather than expanding this task automatically.

---

## 6. Inputs and Local-data Expectations

### Required input

A filesystem path to the root of Ken's **extracted** Strava export.

The tool must accept that path as a command-line argument. Do not hard-code Ken's local directory layout.

Expected example invocation:

```bash
python tools/inspect_strava_export.py /path/to/extracted/strava-export
```

If Python packaging in the legacy repository makes that exact invocation impractical, use an equally simple documented command.

### Source-data handling

The export is read-only input.

The tool must not:

* alter source files
* move/rename source files
* write generated output inside the source export unless Ken explicitly chooses an output path there
* copy raw activity files into the repository

The tool should work without network access.

### Privacy

Generated committed reports should avoid unnecessary personal/location data.

Do not dump full activity names, descriptions, GPS coordinates, route names, media metadata, or other free text merely because they exist.

It is acceptable to include limited filenames/row identifiers when needed to diagnose associations or anomalies, but prefer Strava activity IDs and sanitized structural information where practical.

If the export structure makes useful reporting impossible without exposing materially more personal data, stop and report the issue.

---

## 7. Required Implementation / Experiment

Create:

```text
tools/inspect_strava_export.py
```

and any small focused tests/supporting modules genuinely needed.

The script must validate its input and fail clearly if it cannot identify a plausible Strava export or cannot locate/read `activities.csv`.

### A. Export structure inventory

Report at minimum:

* total file count
* total byte size
* top-level files/directories
* counts by file extension, treating compound compressed extensions sensibly (for example `.fit.gz`, `.gpx.gz`)
* counts and byte sizes for activity-file formats
* count of compressed vs uncompressed activity files where identifiable

Do not enumerate thousands of files in the human-readable report.

### B. `activities.csv` inventory

Inspect the CSV without assuming a fixed historical schema.

Report:

* row count
* exact column names, preserving Strava's names
* which columns are entirely empty
* which columns have at least one value
* earliest/latest activity date that can be reliably derived from the CSV
* activity counts by year
* activity counts by Strava activity type/sport-type columns that actually exist in this export
* counts for relevant presence/absence fields when they exist, such as filename, distance, elapsed/moving time, elevation, power, heart rate, cadence, trainer/commute/private flags, etc.

Do not invent columns that are absent. The report should clearly say which expected/useful fields were not present.

Do not include full free-text field contents in committed reports.

### C. CSV-to-file association

Determine how activity rows relate to files using the filename/path information actually present in the export.

Report at minimum:

* CSV rows with a referenced activity filename/path
* CSV rows without one
* referenced files that exist
* referenced files that are missing
* activity files present in the export that are not referenced by a CSV row
* duplicate CSV references to the same file/path
* duplicate activity IDs if an activity-ID column is present and usable
* case/path/encoding oddities that interfere with straightforward matching

Do not silently “fix” mismatches. Record the evidence.

### D. Historical/file-format coverage

Where the CSV-to-file association is reliable enough, summarize file formats by:

* year
* activity type/sport type when available

The purpose is to expose transitions such as FIT vs TCX/GPX and indoor vs outdoor coverage.

If reliable association cannot be made, report that limitation instead of fabricating a table.

### E. File-size distribution

For activity files, report useful compact statistics:

* minimum
* median
* 90th percentile
* maximum
* counts of zero-byte or unusually tiny files

Use simple deterministic definitions and document them.

### F. Candidate representative files

Produce a **candidate list**, not copies of the files, for later deep inspection.

Aim for roughly 10–30 candidates when the dataset permits. Select candidates deterministically to cover useful diversity such as:

* earliest and latest activities
* different file formats
* indoor/trainer and outdoor cycling when distinguishable
* activities with and without measured-power indications when distinguishable from CSV metadata
* older and newer periods
* unusually small/large files
* rows/files involved in association anomalies
* non-cycling activities only when they reveal export-format behavior useful to importer research

For each candidate, record why it was selected.

Do not claim that these are statistically representative. They are intentionally diverse diagnostic samples.

### G. Determinism

Running the tool twice against unchanged input must produce semantically identical results.

Sort report collections deterministically.

---

## 8. Required Outputs / Artifacts

The tool should write to a caller-specified output directory, with a sensible default outside the source export if practical.

Produce:

```text
inventory.json
inventory.md
```

### `inventory.json`

Machine-readable evidence containing the structured inventory needed to reproduce or extend analysis.

Include:

* tool/report schema version
* source path represented safely (do not expose Ken's full home-directory path in committed output)
* generation/tool version information if practical
* structure counts
* CSV schema/presence statistics
* historical/type summaries
* file-format summaries
* association statistics
* anomaly records
* file-size statistics
* candidate representative-file records with selection reasons
* warnings/limitations

Do not include volatile generation timestamps if they would make otherwise identical runs differ unnecessarily. If a timestamp is included, keep it out of semantic comparison or document why.

### `inventory.md`

Concise human-readable summary of the same evidence.

It should make it easy for Ken and the Analyst to answer:

1. What did we receive?
2. Over what years?
3. In what formats?
4. How complete does CSV-to-file association appear?
5. What obvious gaps/anomalies exist?
6. Which files should we inspect next?
7. What limitations prevent stronger conclusions?

Avoid giant tables. Put exhaustive detail in JSON when necessary.

---

## 9. Tests and Verification

Add focused automated tests for reusable logic using **synthetic temporary data**, not Ken's real export.

Tests should cover at least:

* CSV schema discovery without a hard-coded exact schema
* compound extension classification such as `.fit.gz`
* matching referenced files
* missing referenced files
* unreferenced activity files
* duplicate references
* deterministic ordering
* representative-candidate selection behavior at a useful basic level
* privacy-safe source-path handling in generated output

Use the repository's existing test conventions if they are suitable. If none exist, use a minimal standard-library or pytest setup without modernizing the whole legacy dependency stack.

Dex must record:

* automated test command and result
* exact inventory command Ken should run locally
* any dependency installation required

### Real-data run

Because Dex may not have access to Ken's local export, Dex should first complete and verify the tool with synthetic fixtures.

If Dex cannot access the real export, the task may reach a **waiting_for_owner_run** handoff state in `STATUS.md` after code/tests are ready. In that state:

1. provide Ken one clear command to run against the extracted export
2. provide the output location
3. ask Ken to commit only `inventory.json` and `inventory.md` (or otherwise make those compact outputs available)
4. do not ask Ken to commit raw activity files

Once real-data reports are available, Dex should inspect them for obvious tool failures and update the PR for Analyst review.

For this task, `waiting_for_owner_run` is an allowed `STATUS.md` handoff value even though it is not a general `TASKS.md` status.

---

## 10. Acceptance Criteria

The Analyst can accept STRAVA-001 when:

1. A standalone command inventories an extracted Strava export without modifying it.
2. Synthetic automated tests cover the important matching/reporting behavior and pass.
3. The tool discovers the actual CSV schema rather than assuming a single fixed export version.
4. `inventory.json` and `inventory.md` are deterministic, compact, and privacy-conscious.
5. The reports describe structure, formats, dates, activity types, CSV/file association, size distribution, anomalies, and diagnostic candidate files.
6. Ken has successfully run the tool against the latest real export.
7. The real-data outputs contain enough evidence to choose the next deep-inspection experiment.
8. No raw bulk-export/activity data or credentials were committed.
9. The PR contains no unrelated legacy-application refactoring.
10. `TASKS.md` and `STATUS.md` reflect the lifecycle state.
11. The Analyst has reviewed and explicitly accepted the task.

---

## 11. Stop-and-report Conditions

Stop and report rather than guessing if:

* the supplied directory does not resemble an extracted Strava export
* `activities.csv` is missing or unreadable
* CSV encoding/dialect cannot be handled safely with a small explicit solution
* the export's filename association mechanism is materially different from what the task anticipates
* a large fraction of referenced paths cannot be matched and the cause is unclear
* useful analysis would require deeply parsing every activity file
* a new external dependency is needed for core task requirements and would materially complicate the legacy environment
* generated reports would expose sensitive personal/location information beyond what this brief permits
* existing repository state conflicts with this JIT
* the experiment reveals evidence that invalidates a material assumption in the brief

Report the evidence and wait for Ken/Analyst direction.
