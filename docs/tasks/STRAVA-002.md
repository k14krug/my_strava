# STRAVA-002 — Deep Inspect Representative Activity Files

## 1. Purpose

Deeply inspect the representative activity files identified by STRAVA-001 and compare their contents with the corresponding `activities.csv` metadata.

The goal is to learn what evidence is actually available from FIT, TCX, and GPX across Ken's history before designing historical import, canonical activity representation, or broad corpus scanning.

This is a diagnostic research task, not an importer task.

## 2. Questions Being Answered

For the STRAVA-001 diagnostic candidates:

* What messages, fields, streams, and metadata are actually present in FIT files?
* What data survives in TCX and GPX files?
* Which important values exist in source files but not `activities.csv`?
* Which values exist in Strava CSV but not source files?
* Where values overlap, do they appear equivalent, transformed, summarized, or otherwise different?
* Which files contain GPS, altitude, heart rate, cadence, temperature, and power evidence?
* What device/session/lap/event information exists?
* What recording intervals and gaps are visible?
* What can we say about measured versus calculated/estimated power from the evidence, without overclaiming?
* What are the 13 CSV rows with no filename reference?

## 3. Requirements Used

Use:

* `AGENTS.md`
* `TASKS.md`
* `STATUS.md`
* `docs/tasks/STRAVA-001.md`
* `reports/STRAVA-001/inventory.json`
* `reports/STRAVA-001/inventory.md`

STRAVA-001 established 1,434 CSV rows, 1,421 exactly matched activity-file references, 13 rows without filenames, and 23 deliberately diverse candidate files spanning historical years/formats and useful diagnostic conditions.

Project principles remain controlling: preserve provenance, distinguish measured/calculated/estimated/inferred/missing information, avoid manufactured precision, and do not turn research results into architecture silently.

## 4. Scope

Create a reproducible inspection utility that deeply parses the STRAVA-001 candidate files available in Ken's local export.

Inspect FIT, TCX, and GPX candidates using format-appropriate parsing.

Also inspect the 13 `activities.csv` rows without filename references using CSV metadata only.

Compare parsed file evidence with the corresponding CSV row where association exists.

## 5. Explicit Non-goals

Do not:

* design or implement the historical importer
* design a database schema or canonical activity model
* scan/deep-parse all 1,421 activity files
* calculate training load or training state
* reconstruct or estimate outdoor power
* classify CSV power as measured merely because a value exists
* modify source files
* call the Strava API
* redesign the legacy app
* commit raw personal activity files
* infer unsupported device/sensor provenance
* add infrastructure unrelated to this experiment

If candidate inspection demonstrates that a whole-corpus scan would be valuable, record that as follow-up rather than doing it here.

## 6. Inputs and Local Data

The existing local archive is expected at:

```text
local_data/strava-export.zip
```

`/local_data/` remains Git-ignored.

Dex may reuse a safely extracted temporary copy or create one under a Git-ignored local-data path. The ZIP must remain untouched.

The tool should accept:

1. an extracted Strava-export directory
2. the STRAVA-001 `inventory.json`
3. an output directory

Do not hard-code Ken's absolute filesystem path.

## 7. Required Implementation / Experiment

Create a focused tool, expected approximately as:

```text
tools/inspect_activity_samples.py
```

Small support modules/tests are allowed when useful.

### A. Candidate resolution

Read the candidate list from STRAVA-001 `inventory.json` rather than duplicating the 23 filenames in code.

Resolve candidates against the extracted export and corresponding CSV rows.

Report missing/unresolvable candidates explicitly.

### B. FIT inspection

For candidate FIT/FIT.GZ files, inventory available FIT messages and fields without dumping every record.

At minimum, where present, inspect:

* file/session/activity metadata
* session messages
* lap messages
* record messages
* event messages
* device/device-info messages
* developer-data/field-description information
* timestamps and duration evidence
* position/GPS
* altitude/enhanced altitude
* distance
* speed/enhanced speed
* heart rate
* cadence
* power
* temperature
* accumulated values where relevant
* any other field that appears materially useful for later activity reconstruction

For record-level fields, report presence/count/coverage and compact descriptive evidence rather than raw streams.

Preserve enough field/message naming information to understand what the FIT file actually contains.

### C. TCX inspection

For TCX/TCX.GZ candidates, inspect structure and presence/count/coverage for useful activity/lap/trackpoint data including, where present:

* activity/sport metadata
* time
* GPS
* altitude
* distance
* heart rate
* cadence
* speed
* power extensions
* creator/device information
* lap summaries

Do not assume all TCX namespaces/extensions are identical.

### D. GPX inspection

For GPX/GPX.GZ candidates, inspect:

* metadata/track/segment/point structure
* timestamps
* GPS
* elevation
* heart rate/cadence/temperature/power extensions when present
* creator/device clues when present
* namespaces/extensions encountered

Do not treat plain GPX as necessarily GPS-only; report what is actually present.

### E. Stream timing evidence

For each candidate with time-series points/records, summarize:

* first/last timestamp
* record/point count
* positive timestamp-delta distribution compactly
* common/median recording interval where meaningful
* duplicate timestamps
* large gaps using a simple documented rule

This is evidence about recording behavior, not an attempt to repair streams.

### F. CSV comparison

For each matched candidate, compare source-file evidence with corresponding `activities.csv` metadata.

Focus on semantically useful overlaps such as:

* date/time
* elapsed/moving duration
* distance
* elevation
* activity type
* heart rate
* cadence
* power
* temperature where available
* device/filename metadata

Classify comparisons conservatively, for example:

* file-only
* CSV-only
* both-present and apparently consistent
* both-present but materially different
* not directly comparable
* unavailable

Document comparison tolerances where numeric comparison is used.

Do not imply that CSV and source fields share identical definitions merely because labels look similar.

### G. Power provenance evidence

For every candidate, report separately:

* whether record-level power exists in the source file
* whether FIT/TCX/GPX summary power exists
* whether Strava CSV power-related fields exist
* any explicit metadata that supports a measured/calculated/estimated interpretation

Use labels such as `measured`, `calculated`, or `estimated` only when supported by explicit evidence. Otherwise use `unknown` or similarly conservative wording.

The purpose is to establish what evidence we have for later power work, not to solve power provenance now.

### H. Thirteen no-file rows

Produce a compact diagnostic table for the 13 CSV rows without filename references.

Include only privacy-safe fields useful for understanding their nature, such as:

* activity ID
* date/year
* activity type
* duration/distance presence
* power/HR/cadence presence
* other structural flags useful to explain why a file may not exist

Do not include activity names, descriptions, routes, coordinates, or other unnecessary free text.

State observed patterns without guessing the cause.

## 8. Required Outputs

Produce:

```text
reports/STRAVA-002/
    sample_inspection.json
    sample_inspection.md
```

The JSON should contain detailed structured evidence suitable for later programmatic analysis.

The Markdown should concisely summarize:

1. candidate resolution
2. format-specific findings
3. signal/field availability
4. CSV-versus-file observations
5. power-provenance evidence
6. recording/timing observations
7. the 13 no-file rows
8. important format/history differences
9. limitations
10. concrete questions suggested for the next experiment

Do not embed raw time-series streams.

## 9. Dependencies

Prefer mature, focused parsers over writing a FIT decoder from scratch.

A small FIT parsing dependency is acceptable for this task if needed. Dex must:

* identify the chosen library and version
* explain briefly why it was selected
* keep dependency changes scoped
* avoid modernizing the legacy application dependency stack merely to accommodate this research tool

Use Python standard-library XML parsing where adequate for TCX/GPX. Add an XML dependency only if clearly justified.

## 10. Tests and Verification

Use synthetic fixtures generated by tests or tiny deliberately constructed fixtures that contain no personal activity data.

Tests should cover at minimum:

* gzip and uncompressed input handling as applicable
* candidate resolution from STRAVA-001 inventory
* TCX field/extension discovery
* GPX field/extension discovery
* timing summary behavior
* CSV/file comparison classification
* conservative power-provenance classification
* privacy-safe no-file-row output
* deterministic output ordering/content

For FIT, use a synthetic/generated fixture if practical with the chosen parser/tooling. If generating a valid FIT fixture would require disproportionate complexity, isolate and test FIT summarization logic with synthetic parsed-message structures and verify the real candidate parsing during Ken's local run. Document that limitation.

Record exact test and real-data commands.

Run the tool twice against unchanged real inputs and confirm output stability.

## 11. Acceptance Criteria

STRAVA-002 is acceptable when:

1. All 23 STRAVA-001 candidates are resolved or any exceptions are explicitly explained.
2. FIT, TCX, and GPX candidates are deeply inspected at the metadata/field/coverage level.
3. Source-file versus CSV evidence is compared conservatively.
4. Power evidence clearly distinguishes record-level source power, summary/source power, CSV power metadata, and unknown provenance.
5. Recording/timing characteristics are summarized without altering streams.
6. The 13 no-file rows are characterized using privacy-safe metadata without unsupported causal claims.
7. Outputs are compact, deterministic, and do not contain raw streams or unnecessary personal/location information.
8. Automated tests pass.
9. Ken's real export has been successfully inspected.
10. No raw activity files or secrets are committed.
11. No importer/schema/product architecture is introduced.
12. Analyst review is complete.

## 12. Stop-and-report Conditions

Stop and report rather than guessing if:

* any STRAVA-001 candidate cannot be safely resolved
* parsing a candidate requires unsupported/corrupt-file recovery beyond a small explicit handling step
* a parser silently drops unknown/developer fields needed to answer the task
* dependency installation would materially disrupt the legacy app environment
* CSV/source comparisons require assumptions about units/definitions that cannot be established
* privacy-safe reporting cannot be maintained
* the candidate evidence suggests the task's assumptions are materially wrong
* implementation starts expanding into a full-corpus importer or scanner

Preserve the evidence and wait for Analyst/Owner direction.
