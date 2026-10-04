# Document:    Restore Compact Fixed-g5 Certificate Bundles
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6f7b5b20fd3078f3e1429be0ef8e4174464b2324894337f6af34a0bbf733cacf
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Restore exact frozen bytes by rebuilding coefficient sums from signed rows."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def restore(path):
    archive = json.loads(gzip.decompress(Path(path).read_bytes()))
    assert archive["format"] == "g5-signed-row-compact-v1"
    rows = archive["unconditional_rows"]
    bundle = archive["bundle"]
    assert bundle["graph_index"] == 5 and len(rows) == 697
    for cut in bundle["cuts"]:
        ordinary = [0] * 1200
        heavy = [0] * 276
        for row_index, weight in cut["dual"]["weights"]:
            ordinary_ids, heavy_ids, _, _ = rows[row_index]
            for index in ordinary_ids:
                ordinary[index] += weight
            for index in heavy_ids:
                heavy[index] += weight
        assert cut["ordinary_coefficients"] == "derived-from-signed-rows"
        assert cut["coefficients"] == "derived-from-signed-rows"
        cut["ordinary_coefficients"] = ordinary
        cut["coefficients"] = heavy
    data = (json.dumps(bundle, indent=2) + "\n").encode()
    assert hashlib.sha256(data).hexdigest() == archive["original_sha256"]
    assert len(data) == archive["original_bytes"]
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = restore(args.archive)
    if args.output:
        assert not args.output.exists()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
    print(
        json.dumps(
            {
                "passed": True,
                "restored_sha256": hashlib.sha256(data).hexdigest(),
                "restored_bytes": len(data),
                "wrote_output": args.output is not None,
                "optimization_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
