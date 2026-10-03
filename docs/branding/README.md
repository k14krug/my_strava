# RideWorks Brand Direction

This directory contains the approved **RideWorks final brand direction** for product implementation.

## Canonical approved board source

The exact compact board bytes are stored as text-safe base64 because the GitHub connector used to populate this repository is not binary-safe for this asset.

- Encoded source: `docs/branding/rideworks-brand-direction-board.webp.b64`
- Restore/verify utility: `docs/branding/restore_board.py`
- Decoded format: WebP
- Decoded dimensions: **350 × 262**
- Decoded byte count: **6,888**
- Decoded SHA-256: `4dd937e2dc46f929e91fc201c32d138da6395d5c4c22fbbee8965e4b5376a81c`

Restore a verified viewing copy with:

```bash
python docs/branding/restore_board.py --output /tmp/rideworks-brand-direction-board.webp
```

The utility validates base64, SHA-256, RIFF/WebP identity, byte count, and the RIFF-declared size before writing the image. After restoration, inspect the resulting WebP with the normal image viewer/browser tooling.

The encoded repository source itself is authoritative. A future direct binary copy is equivalent only if it decodes to the exact checksum above.

## What the board establishes

The approved board establishes:

- the RideWorks primary symbol/mark direction;
- the RideWorks wordmark treatment;
- icon-only and app-icon treatments;
- light and dark monochrome use;
- the visual themes **Data**, **Motion**, **Personal**, and **Durable**.

The compact board is a visual-direction reference, not a source for sampling exact color values.

## Color palette

Use these values directly:

| Role | Hex |
| --- | --- |
| Navy | `#0F2A44` |
| Blue | `#2563EB` |
| Green accent | `#10B981` |
| Light gray | `#E5E7EB` |

Navy and blue are the primary identity colors. Green is an accent, not a generic signal that an analytical change is beneficial. RideWorks UI must continue to distinguish directional change from supported positive/negative interpretation.

## Identity language shown on the board

- **RideWorks**
- **Built for one rider.**
- **Measure / Understand / Ride Ahead**
- **A smarter way to ride ahead.**
- **Data + Motion / Hidden K²**

These are brand-direction elements, not requirements that every phrase appear in the application shell.

## P1-03 use

P1-03 must use this directory alongside the approved Activity Review mockup.

Dex should:

1. restore and inspect the board using `restore_board.py`;
2. use the mark/wordmark/app-icon direction shown there;
3. use the exact palette values in this README;
4. preserve the approved Activity Review mockup's layout hierarchy;
5. not invent a competing mark, palette, or brand direction.

Owner visual approval of the mark as actually applied in the RideWorks shell remains part of Phase 1 acceptance.
