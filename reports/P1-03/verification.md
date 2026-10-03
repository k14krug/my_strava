# P1-03 pre-implementation verification — blocked

**Date:** 2026-10-03

**Branch:** `task/p1-03-activity-review`

**PR:** [#12 — draft blocker handoff](https://github.com/k14krug/my_strava/pull/12)

**Evidence commit:** `02f7f8b`

**Refreshed main:** `d21a9fa`

**State:** blocked before UI implementation; no Owner acceptance requested yet.

## Required approved branding source is damaged

P1-03 permits `/AUTOTASK`, and accepted P1-02 is merged. The task requires
inspection and faithful use of `docs/branding/rideworks-brand-direction-board.webp`
before implementing the mark. The Activity Review mockup is available and was
inspected successfully. The brand board cannot be decoded.

| Check | Result |
| --- | --- |
| Documented board SHA-256 | `4dd937e2dc46f929e91fc201c32d138da6395d5c4c22fbbee8965e4b5376a81c` |
| Committed/worktree SHA-256 | `29e8d909255622a718a82511898a5b7e82b4fd490bfba52938d49e3cd06230b1` |
| Actual byte count | 6,887 |
| RIFF-declared total byte count | 6,888 |
| Git blob matches worktree | Yes |
| Image viewer | Unable to decode the WebP |
| Pillow | `OSError: could not create decoder object` |
| Appending one byte reproduces the documented checksum | No, for any possible byte |

The mismatch is in the committed source, not an uncommitted edit. The last
board commit is `a41adf6` (`Store RideWorks brand board as repository image`).
The byte-count discrepancy suggests truncation; it does not establish what the
correct missing bytes or approved image should be. No reconstructed or invented
mark has been substituted, and no branding/JIT source has been changed.

Exact integrity commands:

```bash
file docs/branding/rideworks-brand-direction-board.webp
sha256sum docs/branding/rideworks-brand-direction-board.webp
```

The committed bytes were also read via `git show
HEAD:docs/branding/rideworks-brand-direction-board.webp`, compared with the
worktree and hashed with Python `hashlib`. The RIFF size was read using
`struct.unpack('<I', blob[4:8])[0] + 8`.

The image-decode attempt used:

```bash
python3 - <<'PY'
from PIL import Image
im=Image.open('docs/branding/rideworks-brand-direction-board.webp')
im.resize((1050,789)).save('/tmp/rideworks-brand-board.png')
PY
```

Opening failed before any preview was written. The approved source was untouched.

## Required next action

Restore a valid, decodable approved brand board from the authoritative image and
ensure `docs/branding/README.md` records its actual checksum/dimensions. Do not
replace it with a newly designed mark. Refresh the task branch after that repair
before implementing P1-03.

This stop follows AGENTS.md's required-source/conflict rules and P1-03's branding
requirements in sections 3 and 8.12. Dex cannot establish the approved mark's
visual direction from the damaged file or infer it from the palette/taglines.

Only task/status and this blocker evidence are changed. No production code,
runtime dependency, branding source, personal data or JIT controls were modified.
No new automated test-suite or representative browser acceptance run is claimed.
P1-03 remains incomplete; Owner Gate 1 and Analyst Gate 2 remain outstanding.
