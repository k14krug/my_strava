# STRAVA-002 sample inspection

Diagnostic evidence from STRAVA-001 candidates. No raw streams, coordinates, activity names, or absolute source paths are included.

## Candidate resolution

- Inventory candidates: 23
- Resolved and parsed: 23
- Status: complete

## Format and signal evidence

| Format | Samples | Points | Candidate files with signals |
| --- | ---: | ---: | --- |
| FIT | 11 | 31391 | altitude 11, cadence 10, distance 11, gps 11, heart_rate 10, power 10, speed 11, temperature 1, time 11 |
| GPX | 9 | 31569 | altitude 9, cadence 2, gps 9, heart_rate 1, temperature 2, time 9 |
| TCX | 3 | 7907 | altitude 2, cadence 1, distance 2, gps 2, heart_rate 2, power 1, speed 1, time 3 |

FIT message names seen: activity, developer_data_id, device_info, event, field_description, file_id, lap, record, session.
FIT sessions/laps: 11/22; files with device clues: 11.
FIT developer field descriptions: core_data_quality, core_reserved, heat_strain_index, skin_temperature, target_power.

- TCX: 14 laps; 96 extension tag names (ns1:AvgWatts, ns1:LX, ns1:MaxWatts, ns1:TPX, ns1:Watts, ns2:Speed, ns2:TPX, ns3:LX); full names in JSON.
- TCX XML namespaces encountered: 4; labels in JSON.
- GPX: 0 laps; 74 extension tag names (ns1:TrackPointExtension, ns1:atemp, ns1:cad, ns1:hr); full names in JSON.
- GPX XML namespaces encountered: 3; labels in JSON.

## Candidate-level evidence

Signal abbreviations: G GPS, H heart rate, C cadence, P power, T temperature. Counts are points with a value.

| Activity ID | Format | Points | G/H/C/P/T | Median delta (s) | Large gaps | Power source / CSV |
| --- | --- | ---: | --- | ---: | ---: | --- |
| 10519675984 | .fit.gz | 3832 | 3832/3832/3832/3832/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 1150380329 | .gpx.gz | 208 | 208/0/0/0/0 | 6.0 | 1 | record 0, summary 0, CSV 0 |
| 122178660 | .gpx.gz | 5401 | 5401/0/0/0/0 | 1.0 | 0 | record 0, summary 0, CSV 1 |
| 122185017 | .gpx.gz | 938 | 938/0/0/0/0 | 5.0 | 1 | record 0, summary 0, CSV 1 |
| 127993934 | .fit.gz | 432 | 432/0/0/0/432 | 6.0 | 2 | record 0, summary 0, CSV 1 |
| 13249070901 | .fit.gz | 3655 | 3655/3655/3655/3655/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 1339479593 | .tcx.gz | 3612 | 0/3600/3612/3612/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 1580824270 | .fit.gz | 3421 | 3421/3421/3421/3421/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 16917180034 | .fit.gz | 5444 | 5444/5444/5444/5444/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 1705193620 | .gpx | 16273 | 16273/0/0/0/0 | 1.0 | 21 | record 0, summary 0, CSV 1 |
| 18919570078 | .gpx | 5527 | 5527/0/0/0/0 | 1.0 | 0 | record 0, summary 0, CSV 0 |
| 20205926508 | .tcx.gz | 732 | 732/732/0/0/0 | 12.248 | 2 | record 0, summary 0, CSV 1 |
| 20262354267 | .tcx.gz | 3563 | 3563/0/0/0/0 | 4.0 | 7 | record 0, summary 0, CSV 1 |
| 20383280617 | .fit.gz | 3621 | 3621/3621/3621/3621/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 2056153084 | .fit.gz | 1084 | 1084/1084/1084/1084/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 239883019 | .gpx.gz | 451 | 451/0/451/0/451 | 2.0 | 0 | record 0, summary 0, CSV 1 |
| 255573617 | .gpx | 2277 | 2277/2277/2277/0/0 | 1.0 | 1 | record 0, summary 0, CSV 1 |
| 266274304 | .gpx | 1 | 1/0/0/0/0 | n/a | 0 | record 0, summary 0, CSV 1 |
| 2974080526 | .fit.gz | 694 | 694/694/694/694/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 4557704835 | .fit.gz | 2716 | 2716/2716/2716/2716/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 551907799 | .gpx.gz | 493 | 493/0/0/0/493 | 7.0 | 8 | record 0, summary 0, CSV 1 |
| 6453917995 | .fit.gz | 2676 | 2676/2676/2676/2676/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |
| 8333767642 | .fit.gz | 3816 | 3816/3816/3816/3816/0 | 1.0 | 0 | record 1, summary 1, CSV 1 |

The full per-message field counts, XML tag/extension names, signal coverage, timing distributions, and source summary values are in `sample_inspection.json`.

## CSV versus file

Comparison status counts (across candidate-field pairs):
- both_present_apparently_consistent: 88
- both_present_materially_different: 2
- csv_only: 69
- file_only: 24
- not_directly_comparable: 49
- unavailable: 44

Numeric comparisons use max(absolute floor, relative fraction): elapsed 5 s/1%, distance 100 m/1%, elevation 10 m/5%, heart rate 2 bpm/2%, cadence 2 rpm/3%, power 5 W/5%. CSV elapsed seconds and the last duplicate Distance as metre-like are explicit inferences from observed numeric scales; apparent agreement does not prove equivalent definitions.

- 2 candidate-field comparisons exceed those tolerances; numeric differences do not establish why values differ:
  - Activity 127993934 elevation_gain_m: CSV 178.7, source 147.0.
  - Activity 20262354267 elapsed_seconds: CSV 15775.0, source 13657.71.

## Power provenance

- Candidate files with record-level source power: 11
- Candidate files with source summary power: 11
- Candidate rows with Strava CSV power metadata: 21
- Provenance classification remains `unknown` for every candidate: these values do not identify a measured, calculated, or estimated origin.

## CSV rows without a filename

13 rows; years: {'2010': 1, '2019': 9, '2020': 1, '2021': 1, '2022': 1}; types: {'Ride': 10, 'Rowing': 1, 'Run': 1, 'Walk': 1}.

| Activity ID | Date | Type | Elapsed / distance / HR / cadence / power present |
| --- | --- | --- | --- |
| 6795134830 | 2010-08-05 | Ride | Y/Y/N/N/N |
| 2619452999 | 2019-02-05 | Ride | Y/Y/N/N/N |
| 2619177948 | 2019-02-11 | Ride | Y/Y/N/N/N |
| 2619608265 | 2019-04-22 | Ride | Y/Y/N/N/N |
| 2594373932 | 2019-08-05 | Ride | Y/Y/N/N/N |
| 2619111944 | 2019-08-13 | Ride | Y/Y/N/N/N |
| 2619120275 | 2019-08-13 | Ride | Y/Y/N/N/N |
| 2639333702 | 2019-08-19 | Ride | Y/Y/N/N/N |
| 2639337298 | 2019-08-19 | Run | Y/Y/N/N/N |
| 2788187826 | 2019-10-10 | Rowing | Y/Y/N/N/N |
| 3026653156 | 2020-01-18 | Ride | Y/Y/N/N/N |
| 5144713748 | 2021-04-17 | Walk | Y/Y/N/N/N |
| 7149991100 | 2022-04-27 | Ride | Y/Y/N/N/N |

Structural flags among those rows: From Upload field populated in 4; gear field populated in 10.
The missing filename is observed; the cause is not established.

## Limits and next questions

- This is a deliberately diverse sample of 23 files, not a whole-history prevalence estimate.
- FIT was decoded with `fitdecode==0.11.0` using strict CRC/error handling; TCX/GPX used ElementTree.
- GPS coordinates, raw points, serial numbers, route names, and CSV free text were excluded.
- CSV Activity Date lacks a timezone; source timestamps and CSV dates were not aligned as instants.
- CSV weather temperature is not directly comparable with a source temperature sensor.
- Source power fields do not by themselves establish power provenance.
- Position fields do not prove physical GPS capture, especially in virtual rides.
- Activity 1339479593: ignored 10 leading XML whitespace bytes before parsing; source file unchanged.
- Which file-only signals and developer fields merit a targeted next experiment?
- What evidence explains the CSV rows without activity-file references?
