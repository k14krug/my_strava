# P4-01 source register

Checked 2026-10-08 (Owner timezone). Primary sources and publisher documentation;
no Strava requests. This register distinguishes documented practice from empirical
support. Bibliographic dates below are publisher dates, not search-engine crawl dates.

| Source | Evidence used and limits |
| --- | --- |
| TrainingPeaks, [What Is TSS?](https://www.trainingpeaks.com/learn/articles/what-is-tss/), updated June 12, 2026 | Industry motivation: intensity and duration relative to an individual's threshold. Its broad physiological/fitness language is a vendor interpretation, not a RideWorks conclusion. |
| TrainingPeaks, [Estimating TSS](https://www.trainingpeaks.com/learn/articles/estimating-training-stress-score-tss/), updated April 13, 2026; [Intensity Factor](https://help.trainingpeaks.com/hc/en-us/articles/204071814-Intensity-Factor-IF) | Documented formula: `TSS = seconds × NP × IF / (FTP × 3600) × 100`, with `IF = NP / FTP`. Consequently `TSS = hours × (NP/FTP)² × 100`. Requires workout-specific threshold evidence. No cap at 100/hour is added: the formula permits higher rates above FTP; the simplified introductory article's wording is not an implementation specification. |
| TrainingPeaks, [Normalized Power calculations](https://www.trainingpeaks.com/coach-blog/normalized-power-how-coaches-use/) | Rolling 30-second means, fourth powers, mean, fourth root. The research implementation uses complete one-second samples and unpadded windows. Missing samples, pauses, boundary coverage and duration selection still require explicit handling; this is not a claim of exact vendor parity. The article cautions against interpreting very short NP intervals. |
| TrainingPeaks, [CTL](https://help.trainingpeaks.com/hc/en-us/articles/204071884-Fitness-CTL), [ATL](https://help.trainingpeaks.com/hc/en-us/articles/204071894-Fatigue-ATL), [TSB](https://help.trainingpeaks.com/hc/en-us/articles/204071764-Form-TSB) | Vendor recurrences use `previous + (today − previous)/tau`, defaults 42 and 7. TSB for today uses **yesterday's** CTL minus ATL. Exponential histories are not finite 42-/7-day windows. Do not silently substitute `1-exp(-1/tau)`, which is a different discretization. Initialization and missing evidence are separate research choices. |
| TrainingPeaks, [TSS methods explained](https://help.trainingpeaks.com/hc/en-us/articles/204071944-Training-Stress-Scores-TSS-Explained) | Power TSS requires time-series power and threshold; HR alternatives require appropriate HR reference state. Its tTSS discussion flags limitations for fluctuating effort. Vendor rankings of accuracy are not independent validation. |
| Banister & Calvert (1980), [Planning for future performance](https://pubmed.ncbi.nlm.nih.gov/6778623/), PMID 6778623 | Primary abstract establishes the TRIMP/fitness–fatigue modeling lineage in swimming. Bibliographic/abstract access only; no claim to have inspected the unavailable full original paper. |
| Hellard et al. (2006), [Assessing the limitations of the Banister model](https://pubmed.ncbi.nlm.nih.gov/16608765/), DOI 10.1080/02640410500244697 | Primary abstract: nine elite swimmers; good fitted relationships coexist with wide parameter intervals and correlated parameters. This supports caution about interpreting fitted time constants, not a finding about this rider. Abstract inspected; full paper not relied on. |
| Vermeire et al. (2021), [Training progression in recreational cyclists](https://biblio.ugent.be/publication/8628805), DOI 10.1519/JSC.0000000000003340 | Author-institution record/abstract: 11 recreational cyclists, 12 weeks; the tested TRIMP methods did not show significant linear associations with the reported fitness improvements. This small study does not establish universal failure of HR monitoring. It does argue against assuming that a convenient load sum predicts adaptation. |
| Kontro et al. (2026), [The three-dimensional impulse-response model](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0341721), PLOS ONE 21(2), e0341721, published February 6, 2026 | Recent peer-reviewed power/cycling model proposal, full article inspected. Separates energy-system-related strain using CP, W′ and maximal power. It explains the specificity lost in a single load scalar and acknowledges unvalidated assumptions and limited experimental validation. Examples/simulations are not independent proof of superiority. Authors disclose funding/shareholding relationships with Baron Biosystems. RideWorks lacks validated historical CP/W′/maximal-power state; this is a research reference, not a justified v1 replacement. HR lag, drift and contextual influences further limit simple HR-to-load mappings. |
| Garmin, [FIT SDK profile](https://github.com/garmin/fit-python-sdk/blob/main/garmin_fit_sdk/profile.py) ([raw](https://raw.githubusercontent.com/garmin/fit-python-sdk/main/garmin_fit_sdk/profile.py)) and [FIT protocol](https://developer.garmin.com/fit/protocol/) | Manufacturer definitions distinguish `zones_target`/`user_profile` reference fields from session HR maxima. `session.total_work` uses joules. Local parsing remains pinned to accepted `fitdecode==0.11.0`; a field's presence does not prove measured origin, correctness, or a date-effective interval. |

Research interpretation: a model can accurately summarize its chosen input without
validly predicting physiological readiness. Sparse best-20 outcomes are neither
standardized maximal tests nor a suitable target for aggressive parameter fitting.
The accepted best-20 method is therefore used only as a separate outcome/context
series. No model parameters are fitted in P4-01.

## Continuation check — 2026-10-09

Reopened the TrainingPeaks NP, estimating-TSS, CTL, ATL and TSB pages above.
Their formulas remain the cited industry baseline. The NP page specifically
motivates the **600-second candidate minimum**; the 30-second comparison is a
mathematical sensitivity, not equal physiological support. Vendor advice is not
validation of this rider's segmentation policy. Neither the docs nor this
research establishes exact vendor equivalence for gaps or partial sessions.

Garmin's primary [Decoding FIT Activity Files](https://developer.garmin.com/fit/articles/cookbook/decoding_activity_files.html),
particularly “Smart Recording,” distinguishes timestamped records from timer
start/stop evidence and warns that sparse sampling complicates pause detection.
Session start plus elapsed duration defines a summary span. This supports
checking timer pairs and boundaries separately; it does **not** establish that
a sample-count/timer match proves every missing second was paused. The current
[SDK profile](https://raw.githubusercontent.com/garmin/fit-python-sdk/main/garmin_fit_sdk/profile.py)
was also checked; retained parsing stays pinned to the accepted local parser.
The website's dynamic cookbook shell did not expose the duration article text;
no claim relies on that inaccessible text. The directly accessible decoding
article is the timer/record source used here.

The half-open one-second integration convention, segment stress sum, exact
active-bin gate, one-second summary sensitivity, and recommendation are explicitly
**RideWorks research candidates**. They are not implied Garmin or TrainingPeaks
requirements. The original published research/limitations register remains
applicable; no new physiological or predictive claim is made by the FTP expansion.

## Bounded Sauce challenge — 2026-10-09

Read and executed pinned [Sauce source revision
`4b6d4f42bf56d064507d694abd56e5f989530e03`](https://github.com/SauceLLC/sauce4strava/tree/4b6d4f42bf56d064507d694abd56e5f989530e03),
as directed by the [Analyst source review](https://github.com/k14krug/rideworks/pull/23#issuecomment-6084684860)
and [Owner authorization](https://github.com/k14krug/rideworks/pull/23#issuecomment-6084858539).
The [verification source table](sauce-verification.md#exact-reference-code-and-explicit-adaptations)
links exact active-time, padding, NP/stress, FTP and daily-aggregation code.
The unmodified calculation file is hash-checked; only its data/power namespaces
execute on documented adapted inputs. This is scoped function equivalence,
not full-app parity or physiological validation.

One correction to the review's informal gap description: the source repeats
**the arriving value backward**, not the previous value forward. Synthetic
value/zero/break markers remain distinct from measured zero. FTP prehistory
fallback, HR assumptions and zero-filled daily/PMC inputs are not executed.
The controlled evidence now challenges default 600-second segmentation for
small losses; its earlier external motivation does not establish that policy
as preferable to labeled estimates. No production implementation is accepted here; the subsequent Owner design
selection is recorded in JIT §16 and current verification.
