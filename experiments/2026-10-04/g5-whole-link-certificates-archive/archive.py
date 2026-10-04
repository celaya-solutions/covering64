# Document:    Lossless Fixed-g5 Certificate Archive Compression
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      dbb6f06608c4d11fd1ddbe2ea7276e953fe86df3f65a315b5d9398734c092a76
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compress the unchanged signed-row JSON bytes and verify exact restoration."""

import gzip
import hashlib
import json
import lzma
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORIGINAL = HERE.parent / "g5-whole-link-certificates/all-g5-cuts.compact.json.gz"
RAW = ROOT / "experiments/scratch/g5-whole-link-certificates-20261004/all-g5-cuts.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(payload):
    archive = json.loads(payload)
    assert archive["format"] == "g5-signed-row-compact-v1"
    rows, bundle = archive["unconditional_rows"], archive["bundle"]
    assert bundle["graph_index"] == 5 and len(rows) == 697
    for cut in bundle["cuts"]:
        ordinary, heavy = [0] * 1200, [0] * 276
        for row_index, weight in cut["dual"]["weights"]:
            ordinary_ids, heavy_ids, _, _ = rows[row_index]
            for index in ordinary_ids:
                ordinary[index] += weight
            for index in heavy_ids:
                heavy[index] += weight
        assert cut["ordinary_coefficients"] == "derived-from-signed-rows"
        assert cut["coefficients"] == "derived-from-signed-rows"
        cut["ordinary_coefficients"], cut["coefficients"] = ordinary, heavy
    restored = (json.dumps(bundle, indent=2) + "\n").encode()
    assert digest(restored) == archive["original_sha256"]
    assert len(restored) == archive["original_bytes"]
    return restored


def main():
    report_path = HERE / "result.json"
    target = HERE / "all-g5-cuts.compact.json.xz"
    assert not report_path.exists() and not target.exists()
    original = ORIGINAL.read_bytes()
    assert digest(original) == "22311f1f765e46a4ffb6a92b01a54474a6e8d96056d9a511ec096340fdb43ea8"
    payload = gzip.decompress(original)
    assert digest(payload) == "66fbb071a8df1b33c1e2e3cb153e8c1370742d07e8e94fc2d22e8c08133719da"
    before = time.monotonic()
    encoded = lzma.compress(payload, format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC64,
                            preset=9 | lzma.PRESET_EXTREME)
    seconds = time.monotonic() - before
    target.write_bytes(encoded)
    decoded = lzma.decompress(target.read_bytes())
    assert decoded == payload
    restored = restore(decoded)
    assert restored == RAW.read_bytes()
    assert ORIGINAL.read_bytes() == original
    report = {
        "source_sha256": digest(Path(__file__).read_bytes()),
        "original_path": str(ORIGINAL.relative_to(ROOT)),
        "original_sha256": digest(original), "original_bytes": len(original),
        "unchanged_payload_sha256": digest(payload), "payload_bytes": len(payload),
        "xz_path": str(target.relative_to(ROOT)), "xz_sha256": digest(encoded),
        "xz_bytes": len(encoded), "xz_format": "XZ", "xz_check": "CRC64",
        "lzma_preset": "9|PRESET_EXTREME", "compression_seconds": seconds,
        "under_5_million_bytes": len(encoded) <= 5000000,
        "full_bundle_path": str(RAW.relative_to(ROOT)),
        "full_bundle_sha256": digest(restored), "full_bundle_bytes": len(restored),
        "payload_byte_identical": True, "full_bundle_byte_identical": True,
        "original_gzip_unchanged": True, "optimization_calls": 0,
        "scope": "Lossless packaging only; no certificate or proof content changed.",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
