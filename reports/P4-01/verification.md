# P4-01 current verification and Owner handoff

**State:** `ready_for_review` at **HARD — Owner**, JIT §15. TASKS remains
`in_progress`; no Owner model acceptance or Analyst acceptance.
**Branch / PR:** `task/p4-01-training-state` /
[draft PR #23](https://github.com/k14krug/rideworks/pull/23).
**Invocation:** `/TASK P4-01`, explicitly permitted by the refreshed JIT.

The Owner-authorized Sauce challenge is complete as research. Main `fb4761d`,
JIT `fb5b9dd` and Phase 4 contract `f915bc6` are integrated. The latest Analyst
source review and Owner continuation were read; no unresolved inline review
comments existed.

[DESIGN-003](../../docs/design/DESIGN-003-training-state-model.md) now recommends
keeping complete calculations, narrow small-gap **estimates**, and partial
segment subtotals distinct in separate 7-/42-day work/stress views. Correction
outperforms the 600-second rule for small injected losses; longer gaps have
severe failure cases. The proposed ≤5 s / ≤1% screen is for Owner choice, not
accepted production behavior.

- **48 reference rides / 1,823 controlled cases**, using all 24 strict timer
  references and 24 explicitly limited complete recorded envelopes.
- **281 actual interrupted rides + 23 recent complete envelopes** compared for
  disagreement, with no claim of accuracy inside real missing signals.
- **47/281 potential small-gap interval estimates**; none establishes a newly
  qualifying whole-ride estimate from the available boundary evidence.
- **310 full tests / 25 focused research tests** and **52 Node assertions** pass.
- Independent numerical verification: **2,127 cases, 8,508 upstream variants,
  816 published distribution checks**, four cutoff grids and both recent windows.
- All **20 production tables** and **1,422 originals** preserved; snapshot byte
  hash unchanged, integrity `ok`, no FK violations. Production behavior,
  Performance-v2 and the FTP CSV remain unchanged.

Detailed methods, source equivalence/adaptations, limitations and exact commands:
[Sauce verification](sauce-verification.md). Results:
[error table](sauce-errors.md), [aggregate comparison](sauce-comparison.json),
[anonymized figure](sauce-gap-comparison.png), [acceptance metadata](acceptance.json).
Prior [dated-FTP](ftp-verification.md) and [initial inventory](initial-verification.md)
verification remain preserved as earlier evidence, not current model decisions.

**Stop at HARD — Owner:** approve/change the evidence categories and five-second/
one-percent candidate, including API applicability and pause conventions.
Analyst review and a separately authored P4-02 brief follow Owner choice.
No merge, acceptance, production implementation or later task is authorized.
