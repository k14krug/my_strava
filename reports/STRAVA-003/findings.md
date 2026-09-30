# STRAVA-003 findings and design questions

This document interprets the whole-export census alongside STRAVA-001 and STRAVA-002. Counts refer to this one local Strava export, not a general population or permanent export contract. The reproducible counts and denominators are in `coverage_census.json` and `coverage_census.md`.

## What we now know

- STRAVA-001 found 1,434 CSV activity rows. The whole-history parse attempted and decoded all 1,421 exactly referenced files; 13 rows have no filename. This supports a complete source-coverage census for this export, while the 13 no-file rows remain CSV-only evidence.
- Format prevalence differs sharply from the deliberately diverse STRAVA-002 sample. The full file-backed population is 1,264 FIT.GZ, 105 GPX/GPX.GZ, and 52 TCX.GZ files. STRAVA-002's 23 selected files contained 11 FIT, 9 GPX, and 3 TCX and were never a prevalence sample.
- A source point/record power value exists in 1,309 parsed files. Source summary power evidence occurs in 1,314 files, including nine GPX files with numeric non-point summary-shaped tags. CSV power-related metadata is populated in 1,399 of 1,434 rows. These are different evidence channels. STRAVA-002's 11/23 source-power count substantially understates whole-export prevalence because its candidates were deliberately diverse.
- CSV Activity Type creates sharply different evidence cohorts. All 1,264 `Virtual Ride` rows have a file and point/record power; 1,262 are FIT.GZ and two are GPX.GZ. Of 146 `Ride` rows, 136 have files, and 44 of those have point/record power. The remaining 92 file-backed Ride rows have position and altitude evidence without point/record power; 39 also have heart rate, 13 have cadence, and 91 have CSV power metadata. These combinations describe available evidence only.
- Coverage changes visibly around 2018. Earlier source-backed history is predominantly GPX/TCX, with little record power. In 2018, FIT.GZ appears in 100 of 155 CSV rows, alongside 45 TCX.GZ. From 2019 onward, FIT.GZ dominates the yearly source mix. This is a feature of this export and its Activity Type mix, not proof of a device or training change.
- FIT is structurally rich across this archive: session messages occur in 1,264/1,264 parsed FIT files; laps in 1,259; events in 1,264; device-info in 1,254. Developer-data IDs occur in 236 files and field descriptions in 235. Recurrent developer field names include `target_power` and several quality/temperature/strain labels, but their presence does not establish meaning or reliability without field-level interpretation.
- XML extensions are not negligible. TCX activity extensions recur, and GPX contains Garmin TrackPointExtension tags as well as other hashed namespace families. Nine GPX files contain numeric `avgPower`/`maxPower`-like tags outside track points; those are source summary metadata candidates with uncertain semantic equivalence to FIT or TCX summaries.
- All 1,421 parsed files contain points and at least one timestamped point. Under the STRAVA-002 timing rule, 83 files contain duplicate timestamps and 238 contain one or more large gaps. No parsed file has missing/invalid or backward/incompatible timestamps under that implementation. Fifty of 52 TCX files have ten leading whitespace bytes before XML content; the parser removes them in memory only. No file failed strict parsing in this run.

## What remains unknown

- A point-level power stream, source summary field, or Strava CSV power field does not identify measured, calculated, or estimated origin. The census does not establish a stronger provenance classification for the population; that question needs a targeted examination of explicit source and device evidence.
- Source summaries and Strava CSV values may use different units, boundaries, corrections, or sample selection. STRAVA-002 found two material numeric differences in 23 candidates; STRAVA-003 deliberately did not reconcile every numeric value.
- The missing-file cause for 13 rows is unknown. A CSV-only row is an activity in the population, while its source signals are unknown rather than proven absent.
- Position fields do not establish physical GPS capture. `Ride` and `Virtual Ride` are Strava labels used as cohort proxies; neither is proof of physical riding conditions. Field presence does not establish accuracy, continuity, sensor source, or trustworthiness.
- The meaning and usefulness of the numerous FIT developer fields and private XML extension tags remain open. The census records file prevalence and safe tag names, not decoded vendor-specific semantics.
- The sampled and full-archive parsing results are reproducible for this local extraction; behavior on future exports or changed libraries remains untested.

## Historical cohorts that matter

1. **Early GPX/TCX history (2012–2017):** source formats and signal coverage differ from the later FIT-heavy years. The one 2010 row has no source file.
2. **2018 transition:** FIT and TCX coexist in substantial counts, so a single-format assumption would lose evidence.
3. **2019–2026 FIT-heavy `Virtual Ride` history:** source point power is widespread, but power provenance and physical GPS meaning are still unresolved.
4. **File-backed `Ride` without source point power:** 92 files carry position and altitude; 39 also carry heart rate. They are an evidence cohort for later targeted research, not an estimated-power eligibility set.
5. **CSV-only rows:** 13 activities retain metadata but cannot contribute observed source streams from this export.

## Implications for historical-data design

These are constraints and questions suggested by evidence, not settled product architecture:

- The durable history will need a way to retain original-source association and distinguish CSV metadata, record/point evidence, and source summaries. Those channels overlap without guaranteed equivalence.
- Activity data can be partially populated: a CSV row may have no file, a file may lack a given signal, and a source summary may exist without a matching stream. Missing, unobserved, and explicitly absent states merit separate discussion.
- Historical interpretation may need to retain the source format, original field or extension context, and the rule/version used to compute derived summaries. The design discussion should decide the right granularity rather than importing this research JSON as a schema.
- Time-series analysis must expect variable recording intervals, duplicates, and gaps even when every file parses. These findings do not by themselves call any activity good or bad.
- Activity Type and physical riding context should be represented or assessed separately when a later analysis requires that distinction.

## Implications for outdoor estimated-power research

The 92 file-backed `Ride` rows with position and altitude but no source point power are a broad evidence cohort; 39 also have heart rate, and 13 have cadence. CSV power metadata is populated for 91 of the 92, but that does not prove a measured power source. Whether any of these activities support outdoor estimated-power work depends on later checks of physical context, signal quality, bike/rider history, weather, calibration, and source provenance. No power was estimated here, and no activity was declared eligible.

## Candidate next design decisions

1. Which original-source artifacts and field-level provenance must the durable history preserve?
2. How should CSV-only activities and unknown versus missing signals be represented?
3. Which source/CSV values should coexist versus be chosen for a particular calculation, and how should that choice be versioned?
4. How should `Ride` and `Virtual Ride` labels relate to verified physical context in analysis?
5. What evidence and historical rider/bike state would be required before a targeted outdoor estimated-power experiment?

## Research boundary

Broad archive discovery is complete for this export unless later design work identifies a specific unanswered evidence question. The next phase is discussion with Ken about durable historical activity and provenance representation. No importer, canonical schema, or estimated-power model was selected by this census.
