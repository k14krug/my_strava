# STRAVA-003 historical data-coverage census

Source: local extracted export; no raw streams, coordinates, names, descriptions, serials, or absolute paths.

## Population

| CSV rows | File-backed | No file | Attempted | Parsed | Failed |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1434 | 1421 | 13 | 1421 | 1421 | 0 |

Source formats (file-backed rows): .fit.gz 1264, .gpx 29, .gpx.gz 76, .tcx.gz 52.

## Source signal coverage

A signal is present when at least one decoded source point has a value. Percentages use parsed files as denominator; presence does not establish quality or provenance.

| Signal | Files | Parsed-file denominator | % | Points with value |
| --- | ---: | ---: | ---: | ---: |
| time | 1421 | 1421 | 100.0 | 3661469 |
| gps | 1358 | 1421 | 95.6 | 3483737 |
| altitude | 1353 | 1421 | 95.2 | 3482547 |
| distance | 1278 | 1421 | 89.9 | 3379571 |
| speed | 1278 | 1421 | 89.9 | 3382856 |
| heart_rate | 1351 | 1421 | 95.1 | 3553732 |
| cadence | 1316 | 1421 | 92.6 | 3501974 |
| power | 1309 | 1421 | 92.1 | 3492130 |
| temperature | 42 | 1421 | 3.0 | 32486 |

## Historical evolution

Yearly counts include no-file rows; source-signal columns use parsed files in that year.

| Year | CSV | FIT | TCX | GPX | No file | Parsed | GPS | HR | Cadence | Record power |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 2012 | 6 | 0 | 1 | 5 | 0 | 6 | 6 | 0 | 0 | 0 |
| 2014 | 33 | 1 | 1 | 31 | 0 | 33 | 33 | 2 | 0 | 0 |
| 2015 | 17 | 0 | 0 | 17 | 0 | 17 | 17 | 12 | 13 | 0 |
| 2016 | 14 | 0 | 0 | 14 | 0 | 14 | 14 | 9 | 0 | 0 |
| 2017 | 6 | 0 | 4 | 2 | 0 | 6 | 6 | 0 | 0 | 0 |
| 2018 | 155 | 100 | 45 | 10 | 0 | 155 | 111 | 148 | 139 | 145 |
| 2019 | 185 | 175 | 0 | 1 | 9 | 176 | 176 | 176 | 175 | 175 |
| 2020 | 159 | 154 | 0 | 4 | 1 | 158 | 158 | 157 | 155 | 155 |
| 2021 | 129 | 127 | 0 | 1 | 1 | 128 | 128 | 128 | 127 | 127 |
| 2022 | 161 | 158 | 0 | 2 | 1 | 160 | 160 | 159 | 158 | 158 |
| 2023 | 119 | 117 | 0 | 2 | 0 | 119 | 119 | 119 | 117 | 117 |
| 2024 | 182 | 178 | 0 | 4 | 0 | 182 | 165 | 179 | 178 | 178 |
| 2025 | 154 | 151 | 0 | 3 | 0 | 154 | 152 | 152 | 151 | 151 |
| 2026 | 113 | 103 | 1 | 9 | 0 | 113 | 113 | 110 | 103 | 103 |

Full yearly signal, type, and year/type/format counts are in `coverage_census.json`.

## Cycling evidence cohorts

Counts below use parsed source files within each CSV Activity Type cohort. Activity Type does not prove physical riding context.

| Cohort | CSV rows | Parsed | Source power | HR, no source power | Position + altitude, no source power | Position + altitude + HR, no source power | Cadence, no source power | CSV power, no source power |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ride | 146 | 136 | 44 | 39 | 92 | 39 | 13 | 91 |
| Virtual Ride | 1264 | 1264 | 1264 | 0 | 0 | 0 | 0 | 0 |
| Other | 24 | 21 | 1 | 6 | 14 | 5 | 0 | 0 |

## Power evidence

Source record power: 1309 parsed files; source summary power: 1314 parsed files; CSV power metadata: 1399 rows.
The matrix covers all CSV rows; source flags are false when a source is absent or could not be parsed. Such rows remain separately counted in population status. No provenance classification stronger than unknown is supported by these flags.

| Record | Summary | CSV | Rows |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 33 |
| 0 | 0 | 1 | 83 |
| 0 | 1 | 0 | 1 |
| 0 | 1 | 1 | 8 |
| 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 3 |
| 1 | 1 | 1 | 1305 |

## Structural coverage

FIT parsed files: 1264; session 1264, lap 1259, event 1264, device_info 1254, developer_data_id 236, field_description 235. Device clues: 1264.
FIT developer field names by file: air_speed 1, air_speed_avg 1, air_speed_wind_time_in_zone 1, air_speed_wind_zone 1, ant_device_num 1, ascent 1, auto_lap_distance 1, auto_lap_duration 1, avg_smoothness_x 1, avg_smoothness_y 1, avg_smoothness_z 1, calibration 1, charge 1, core_data_quality 187, core_reserved 187, crank_length 1, descent 1, fit_date_time 1, glucose 1, heat_strain_index 187, lap_distance_before_snap 1, lat_gps 1, lev_travel_assist_level_time_in_zone 1, lon_gps 1, name-sha256:1978472fe10ecdfa 1, name-sha256:878b843b9c8332a2 1, name-sha256:b24f1532d1ff2be9 1, name-sha256:c7fc7966da5a1a20 1, reanalyzer_lap_motion_type 1, rpe_value 18, running_smoothness 1, running_stress_score 1, serial_number 1, skin_temperature 187, target_power 216, time_ms 1, travel_assist_level 1, wind_adj_speed 1, wind_adj_speed_avg 1, wind_grade_power_ratio 1, wind_speed 1, wind_time_in_zone 1, workout_type 1.
TCX: 52 parsed; 4 namespace families, 97 extension tags; device clues in 45. Full file-prevalence counts are in JSON.
GPX: 105 parsed; 5 namespace families, 220 extension tags; device clues in 105. Full file-prevalence counts are in JSON.
GPX files with numeric avgPower/maxPower-like tags outside track points: 9; these are summary metadata evidence, not verified measurement or equivalent definitions.

## Recording and timestamp evidence

Parsed-file denominator: 1421. Files with missing/invalid timestamps: 0; duplicate timestamps: 83; backward/incompatible timestamps: 0; one or more large gaps: 238.
Large gap means a positive interval greater than max(30 seconds, 5 × the file's median positive interval). Common/median interval distributions are in JSON; they are per-file summaries, not pooled stream estimates.

## Parse and structural diagnostics

Categories: leading_xml_whitespace 50.
- Activity 1339479593 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1341007772 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1347476119 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1350737163 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1363642262 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1370220376 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1381931171 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1404562797 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1404664295 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1428843988 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1429544046 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1438109215 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1439697140 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1442936353 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1451405093 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1461337715 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1473433028 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1473533505 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1475223773 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1484621224 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1486061857 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1491364382 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1495624319 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1500917515 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1501056827 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1506567280 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1511317006 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1512707436 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1514592011 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1523561145 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1533626519 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1544142760 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1545836766 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1547922749 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1554844204 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1556538544 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1558722433 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1562846901 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1572166111 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1589311892 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1593843273 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1617475485 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1848487773 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1884547398 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1884547480 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1884547653 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1884547711 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1884547804 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1884547902 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes
- Activity 1894802809 (.tcx.gz): leading_xml_whitespace, 10 leading whitespace bytes

## Limits

- File/field presence does not prove measurement quality, physical GPS capture, or measured power; Virtual Ride positions are especially ambiguous.
- CSV power metadata, source record power, and source summary power remain distinct; provenance is unknown without explicit evidence.
- CSV/source numeric reconciliation was intentionally outside this census; see STRAVA-002 for diagnostic comparisons and uncertainty.
- A missing file reference has no established cause. Parse failures, if any, reduce source-coverage denominators and are reported above.
- FIT uses fitdecode 0.11.0 with strict CRC/error handling. TCX/GPX use ElementTree and STRAVA-002 signal/timing definitions.
