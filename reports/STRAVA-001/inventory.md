# Strava export inventory

Diagnostic inventory of local export metadata. No raw activity streams were parsed.

## What was received

- 2478 files, 1081019865 bytes total
- 1434 CSV activity rows
- Activity files: 1421 (1392 compressed)

| Format | Files | Bytes |
| --- | ---: | ---: |
| .fit.gz | 1264 | 57291252 |
| .gpx | 29 | 16820830 |
| .gpx.gz | 76 | 1725722 |
| .tcx.gz | 52 | 1652724 |

Top-level entries:

- activities (directory): 1421 files, 77490528 bytes
- activities.csv (file): 1 file, 632851 bytes
- applications.csv (file): 1 file, 72 bytes
- bikes.csv (file): 1 file, 243 bytes
- blocks.csv (file): 1 file, 30 bytes
- clubs (directory): 0 files, 0 bytes
- clubs.csv (file): 1 file, 105 bytes
- comments.csv (file): 1 file, 122 bytes
- components.csv (file): 1 file, 133 bytes
- connected_apps.csv (file): 1 file, 316 bytes
- contacts.csv (file): 1 file, 60 bytes
- email_preferences.csv (file): 1 file, 1717 bytes
- events.csv (file): 1 file, 41 bytes
- flags.csv (file): 1 file, 2032 bytes
- followers.csv (file): 1 file, 319 bytes
- following.csv (file): 1 file, 250 bytes
- general_preferences.csv (file): 1 file, 304 bytes
- global_challenges.csv (file): 1 file, 273 bytes
- goals.csv (file): 1 file, 486 bytes
- group_challenges.csv (file): 1 file, 25 bytes
- intercom_tickets.csv (file): 1 file, 44 bytes
- local_legend_segments.csv (file): 1 file, 55 bytes
- logins.csv (file): 1 file, 11370 bytes
- media (directory): 1007 files, 1002288308 bytes
- media.csv (file): 1 file, 59713 bytes
- memberships.csv (file): 1 file, 347 bytes
- messaging.json (file): 1 file, 333 bytes
- mobile_device_identifiers.csv (file): 1 file, 91 bytes
- monthly_recap_achievements.csv (file): 1 file, 206 bytes
- orders.csv (file): 1 file, 1110 bytes
- partner_opt_outs.csv (file): 1 file, 1316 bytes
- posts.csv (file): 1 file, 1271 bytes
- privacy_zones.csv (file): 1 file, 258 bytes
- profile.csv (file): 1 file, 261 bytes
- profile.jpg (file): 1 file, 93444 bytes
- reactions.csv (file): 1 file, 1154 bytes
- routes (directory): 9 files, 428129 bytes
- routes.csv (file): 1 file, 314 bytes
- segments.csv (file): 1 file, 459 bytes
- shoes.csv (file): 1 file, 57 bytes
- social_settings.csv (file): 1 file, 215 bytes
- starred_routes.csv (file): 1 file, 296 bytes
- starred_segments.csv (file): 1 file, 814 bytes
- structured_details.csv (file): 1 file, 129 bytes
- visibility_settings.csv (file): 1 file, 264 bytes

## CSV and history

- Date range: 2010-08-05 to 2026-09-29
- Years: 2010: 1, 2012: 6, 2014: 33, 2015: 17, 2016: 14, 2017: 6, 2018: 155, 2019: 185, 2020: 159, 2021: 129, 2022: 161, 2023: 119, 2024: 182, 2025: 154, 2026: 113
- CSV columns: 103; exact ordered names and positional counts are in inventory.json
- Entirely empty columns: Activity Private Note, Average Positive Grade, Average Negative Grade, Max Watts, Max Temperature, Number of Runs, Uphill Time, Downhill Time, Other Time, Type, Start Time, Total Weight Lifted, Gear, Jump Count, Total Grit, Average Flow, Newly Explored Distance, Newly Explored Dirt Distance, Activity Count, Total Steps, Pool Length, Timer Time, Total Cycles, Competition, Long Run, For a Cause, Downhill Distance, Total Sets, Total Reps
- Useful fields absent: sport_type, trainer, private

- activity_type: Ride: 146, Rowing: 1, Run: 22, Virtual Ride: 1264, Walk: 1

Exact-match activity formats by year:

| Year | Formats and counts |
| --- | --- |
| 2012 | .gpx.gz: 5, .tcx.gz: 1 |
| 2014 | .fit.gz: 1, .gpx.gz: 31, .tcx.gz: 1 |
| 2015 | .gpx: 11, .gpx.gz: 6 |
| 2016 | .gpx.gz: 14 |
| 2017 | .gpx.gz: 2, .tcx.gz: 4 |
| 2018 | .fit.gz: 100, .gpx: 1, .gpx.gz: 9, .tcx.gz: 45 |
| 2019 | .fit.gz: 175, .gpx.gz: 1 |
| 2020 | .fit.gz: 154, .gpx.gz: 4 |
| 2021 | .fit.gz: 127, .gpx: 1 |
| 2022 | .fit.gz: 158, .gpx: 2 |
| 2023 | .fit.gz: 117, .gpx: 2 |
| 2024 | .fit.gz: 178, .gpx: 4 |
| 2025 | .fit.gz: 151, .gpx: 1, .gpx.gz: 2 |
| 2026 | .fit.gz: 103, .gpx: 7, .gpx.gz: 2, .tcx.gz: 1 |

## CSV-to-file association

- Rows with/without a reference: 1421/13
- Exact existing/missing references: 1421/0
- Unreferenced activity files: 0
- Duplicate references/IDs: 0/0

## File sizes

- Minimum/median/p90/maximum bytes: 546, 42471, 75759, 1907556
- Zero byte/tiny (<1024 bytes): 0/4

## Anomalies

- row_without_file_reference: 13

## Candidate files for later inspection

These are deliberately diverse diagnostic samples, not statistical samples.

| File or path token | Activity ID | Format | Why selected |
| --- | --- | --- | --- |
| activities/11256451541.fit.gz | 10519675984 | .fit.gz | year 2024 |
| activities/1255575554.gpx.gz | 1150380329 | .gpx.gz | year 2017 |
| activities/133759711.gpx.gz | 122178660 | .gpx.gz | year 2014 |
| activities/133766879.gpx.gz | 122185017 | .gpx.gz | earliest dated activity, format .gpx.gz, year 2012 |
| activities/140124458.fit.gz | 127993934 | .fit.gz | format .fit.gz |
| activities/14130274713.fit.gz | 13249070901 | .fit.gz | year 2025 |
| activities/1447644322.tcx.gz | 1339479593 | .tcx.gz | year 2018 |
| activities/1705193620.gpx | 1705193620 | .gpx | largest matched file |
| activities/18010094080.fit.gz | 16917180034 | .fit.gz | year 2026 |
| activities/18919570078.gpx | 18919570078 | .gpx | power metadata absent, activity type Run |
| activities/21357825200.tcx.gz | 20205926508 | .tcx.gz | activity type Ride |
| activities/21415497232.tcx.gz | 20262354267 | .tcx.gz | format .tcx.gz |
| activities/21538875902.fit.gz | 20383280617 | .fit.gz | latest dated activity, power metadata present, activity type Virtual Ride |
| activities/2196956004.fit.gz | 2056153084 | .fit.gz | year 2019 |
| activities/255573617.gpx | 255573617 | .gpx | format .gpx |
| activities/266274304.gpx | 266274304 | .gpx | smallest matched file |
| activities/271715592.gpx.gz | 239883019 | .gpx.gz | year 2015 |
| activities/3169076193.fit.gz | 2974080526 | .fit.gz | year 2020 |
| activities/4869344930.fit.gz | 4557704835 | .fit.gz | year 2021 |
| activities/605191208.gpx.gz | 551907799 | .gpx.gz | year 2016 |
| activities/6861880619.fit.gz | 6453917995 | .fit.gz | year 2022 |
| activities/8936618361.fit.gz | 8333767642 | .fit.gz | year 2023 |

## Limits

- Power column presence is a CSV metadata proxy, not proof of measured power.
- CSV field presence and file association do not establish data quality inside activity streams.
- Matching uses exact relative paths; possible path variants remain anomalies.
