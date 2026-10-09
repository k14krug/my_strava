# P4-01 evidence coverage

Aggregate census of the accepted snapshot; timezone `America/Los_Angeles`. Source dates without timezone remain source-calendar dates, not guessed UTC. Years without retained rides are not asserted rest years.

P = unchanged Performance-v2 eligible power; X = preserved detailed power excluded by that policy; HR = stream or understood HR summary (including CSV bpm); D = understood elapsed-duration summary; W = known-unit source work summary; E = complete eligible one-second recorded envelope; F = usable supplied session-threshold candidate. W is not the calculated work count.

| Year | Type | Activities | P | X | HR | D | W | E | F |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | Ride | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2012 | Ride | 6 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 2014 | Ride | 30 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| 2014 | Run | 3 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| 2015 | Ride | 17 | 0 | 0 | 12 | 0 | 0 | 0 | 0 |
| 2016 | Ride | 14 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| 2017 | Run | 6 | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| 2018 | Ride | 53 | 0 | 44 | 48 | 0 | 0 | 0 | 0 |
| 2018 | Run | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 2018 | Virtual Ride | 101 | 90 | 11 | 101 | 100 | 0 | 50 | 0 |
| 2019 | Ride | 8 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 2019 | Rowing | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2019 | Run | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2019 | Virtual Ride | 175 | 144 | 31 | 175 | 175 | 0 | 102 | 0 |
| 2020 | Ride | 4 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| 2020 | Virtual Ride | 155 | 124 | 31 | 155 | 154 | 0 | 93 | 0 |
| 2021 | Ride | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 2021 | Virtual Ride | 128 | 88 | 40 | 128 | 128 | 0 | 60 | 0 |
| 2021 | Walk | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2022 | Ride | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2022 | Run | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 2022 | Virtual Ride | 157 | 127 | 30 | 157 | 157 | 0 | 97 | 0 |
| 2023 | Run | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| 2023 | Virtual Ride | 117 | 105 | 12 | 117 | 117 | 0 | 80 | 0 |
| 2024 | Run | 4 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| 2024 | Virtual Ride | 178 | 131 | 47 | 177 | 178 | 91 | 64 | 0 |
| 2025 | Ride | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 2025 | Run | 2 | 0 | 1 | 1 | 1 | 0 | 0 | 0 |
| 2025 | Virtual Ride | 150 | 127 | 23 | 150 | 150 | 0 | 78 | 0 |
| 2026 | Ride | 11 | 0 | 0 | 10 | 11 | 10 | 0 | 0 |
| 2026 | Run | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2026 | Virtual Ride | 109 | 92 | 17 | 109 | 109 | 11 | 69 | 1 |

## Cycling overlap

Bits below are P/HR/D/W in that order. They partition all 1,418 cycling Activities. Counts describe evidence presence, not guaranteed physiological validity.

| P HR D W | Activities |
| --- | ---: |
| 0000 | 60 |
| 0010 | 2 |
| 0011 | 2 |
| 0100 | 77 |
| 0110 | 213 |
| 0111 | 36 |
| 1110 | 954 |
| 1111 | 74 |

## Additional distinctions

- 1,352 cycling Activities have HR streams; 1,320 have file/API HR summaries; 1,333 have export average-HR summaries. These overlap; their union is 1,354.
- 1,263 have file timer durations; 1,397 have absolute-timestamp record spans. 124 of 137 missing understood duration summaries still have recorded spans. Spans are not automatically session duration.
- 93 cycling Activities have source dates with unknown timezone. No cross-timezone precision is manufactured.
- Native/API signal **presence** is not the same as complete timing, measured origin or load eligibility. Source-calculated work from an excluded outdoor ride remains excluded from the eligible power-work baseline.
- Eligible sources: 1,022 FIT / 6 API streams. Whole-envelope exclusions: 311 timing discontinuities and 24 missing/invalid power; 693 complete envelopes.
- Coverage is calculated across Activities after established source association, not by adding overlapping files and API observations.
- Complete-stream work uses one-second half-open sample bins, zero watts retained, no interpolation. It covers only the recorded interval. It does not establish complete session boundaries.
- All 1,421 file originals and the retained CSV passed hash/size verification. Unknown manufacturer fields remain preserved and uninterpreted.

Full aggregate fields: [acceptance.json](acceptance.json). Interpretation and Owner decisions: [DESIGN-003](../../docs/design/DESIGN-003-training-state-model.md).
