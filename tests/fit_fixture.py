"""Privacy-safe synthetic FIT bytes, built with stdlib only.

Local definitions describe only a few public FIT fields. No device identifiers,
coordinates or personal data. This is a test fixture builder, not an exporter.
"""

import struct


def crc(data):
    value = 0
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
    return value


def make_fit(*, powers=(0, None, 180), heart_rates=(100, None, 110),
             timestamps=(1100000000, 1100000000, 1100000002),
             sessions=1, max_hr=150, elapsed=2, timer=1,
             file_type=4, num_sessions=1, file_ids=1):
    body = bytearray()

    def messages(number, fields, rows):
        # Local message 0 is redefined for each global message type.
        body.extend(struct.pack('<BBBH', 0x40, 0, 0, number))
        body.append(len(fields))
        for field_number, fmt, base_type in fields:
            body.extend(bytes((field_number, struct.calcsize('<' + fmt), base_type)))
        for row in rows:
            body.append(0)
            body.extend(struct.pack('<' + ''.join(f[1] for f in fields), *row))

    messages(0, [(0, 'B', 0)], [(file_type,)] * file_ids)
    messages(21, [(253, 'I', 0x86), (0, 'B', 0), (1, 'B', 0), (3, 'I', 0x86)],
             [(1100000000, 0, 0, 0), (1100000002, 0, 4, 0)])
    messages(20, [(253, 'I', 0x86), (7, 'H', 0x84), (3, 'B', 2)],
             [(0xFFFFFFFF if t is None else t, 0xFFFF if p is None else p,
               0xFF if h is None else h) for t, p, h in zip(timestamps, powers, heart_rates)])
    messages(19, [(2, 'I', 0x86), (253, 'I', 0x86), (7, 'I', 0x86), (8, 'I', 0x86)],
             [(1100000000, 1100000002, elapsed * 1000, timer * 1000)])
    messages(18, [(2, 'I', 0x86), (253, 'I', 0x86), (7, 'I', 0x86), (8, 'I', 0x86),
                  (5, 'B', 0), (6, 'B', 0), (17, 'B', 2)],
             [(1100000000, 1100000002, elapsed * 1000, timer * 1000, 2, 58,
               0xFF if max_hr is None else max_hr)] * sessions)
    messages(34, [(1, 'H', 0x84)], [(num_sessions,)])
    header = struct.pack('<BBHI4s', 14, 0x20, 2100, len(body), b'.FIT')
    header += struct.pack('<H', crc(header))
    artifact = header + body
    return artifact + struct.pack('<H', crc(artifact))
