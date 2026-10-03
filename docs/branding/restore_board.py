#!/usr/bin/env python3
"""Restore and verify the approved RideWorks brand direction board.

The repository stores the exact compact WebP bytes as base64 text because the
current GitHub connector path is not binary-safe for this asset.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
from pathlib import Path
import struct
import tempfile

EXPECTED_SHA256 = "4dd937e2dc46f929e91fc201c32d138da6395d5c4c22fbbee8965e4b5376a81c"
EXPECTED_BYTES = 6888
EXPECTED_WIDTH = 350
EXPECTED_HEIGHT = 262
SOURCE = Path(__file__).with_name("rideworks-brand-direction-board.webp.b64")


def restore(output: Path) -> Path:
    encoded = SOURCE.read_text(encoding="ascii").strip()
    payload = base64.b64decode(encoded, validate=True)

    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"brand board checksum mismatch: {digest}")
    if len(payload) != EXPECTED_BYTES:
        raise SystemExit(f"brand board byte-count mismatch: {len(payload)}")
    if payload[:4] != b"RIFF" or payload[8:12] != b"WEBP":
        raise SystemExit("brand board is not a RIFF/WebP payload")

    declared_total = struct.unpack("<I", payload[4:8])[0] + 8
    if declared_total != len(payload):
        raise SystemExit(
            f"brand board RIFF size mismatch: declared {declared_total}, actual {len(payload)}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(f"restored: {output}")
    print(f"bytes: {len(payload)}")
    print(f"sha256: {digest}")
    print(f"documented dimensions: {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(tempfile.gettempdir()) / "rideworks-brand-direction-board.webp",
    )
    args = parser.parse_args()
    restore(args.output)


if __name__ == "__main__":
    main()
