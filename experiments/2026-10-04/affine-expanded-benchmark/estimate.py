# Document:    Expanded Affine Screen Runtime and Output Estimate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      840f52c310cedd38bb6bf82dc9ae993a3ed38fff443653730a466a1678174541
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Measure only mask preparation; estimate screening from the frozen sparse sample."""

import gzip
import json
import struct
import time
from collections import defaultdict
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CATALOG = HERE.parent / "affine-expanded-catalog"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def main():
    require(not (HERE / "estimate.json").exists(), "fresh estimate")
    benchmark = json.loads((HERE / "benchmark.json").read_text())
    catalog = json.loads((CATALOG / "summary.json").read_text())
    paths = {
        "benchmark.json": sha(HERE / "benchmark.json"),
        str((CATALOG / "summary.json").relative_to(ROOT)): sha(CATALOG / "summary.json"),
    }
    for path, expected in benchmark["raw_files"].items():
        require(sha(ROOT / path) == expected, "benchmark stream pin")
        paths[path] = expected
    cases_path = next(ROOT / p for p in paths if p.endswith("/cases.jsonl.gz"))
    survivors_path = next(ROOT / p for p in paths if p.endswith("/survivors.jsonl.gz"))
    case_compressed = cases_path.read_bytes()
    survivor_compressed = survivors_path.read_bytes()
    case_payload = gzip.decompress(case_compressed)
    survivor_payload = gzip.decompress(survivor_compressed)
    byte_counts = defaultdict(lambda: [0, 0])
    for line in case_payload.splitlines(keepends=True):
        row = json.loads(line)
        fiber = byte_counts[str(row["excess_link_id"])]
        fiber[0] += len(line)
        if row["outcome"] == "survives_single_pass":
            fiber[1] += len(line)
    weighted_screen, case_bytes, survivor_bytes = 0.0, 0.0, 0.0
    for key, row in benchmark["per_fiber"].items():
        weight = row["new_pair_population"] / row["sample_cases"]
        weighted_screen += weight * row["screen_seconds"]
        case_bytes += weight * byte_counts[key][0]
        survivor_bytes += weight * byte_counts[key][1]
    measured_overhead = (
        benchmark["elapsed_seconds"]
        - benchmark["loading_seconds"]
        - benchmark["screen_function_seconds"]
    )
    count_overhead = measured_overhead * 6543904 / 1000
    byte_overhead = (
        measured_overhead
        * (case_bytes + survivor_bytes)
        / (len(case_payload) + len(survivor_payload))
    )
    packed_path = ROOT / catalog["catalog_path"]
    require(sha(packed_path) == catalog["catalog_compressed_sha256"], "catalog pin")
    payload = gzip.decompress(packed_path.read_bytes())
    blocks = tuple(combinations(range(1, 17), 5))
    triple_rank = {triple: i for i, triple in enumerate(combinations(range(2, 17), 3))}
    prepared_digest = sha256()
    started = time.monotonic()
    for partial_id in range(catalog["families"]):
        ids = struct.unpack_from("<20H", payload, 40 * partial_id)
        indices = sorted(
            triple_rank[triple] for i in ids for triple in combinations(blocks[i][1:], 3)
        )
        require(len(indices) == len(set(indices)) == 80, "complete prepared partial rows")
        mask = sum(1 << row for row in indices)
        prepared_digest.update(mask.to_bytes(57, "little"))
    preparation = time.monotonic() - started
    estimated_total = weighted_screen + byte_overhead + preparation + benchmark["loading_seconds"]
    result = {
        "source_sha256": sha(__file__),
        "input_hashes": paths,
        "catalog_compressed_sha256": sha(packed_path),
        "measured": {
            "benchmark_pairs": 1000,
            "benchmark_total_seconds": benchmark["elapsed_seconds"],
            "benchmark_loading_seconds": benchmark["loading_seconds"],
            "benchmark_screen_function_seconds": benchmark["screen_function_seconds"],
            "benchmark_other_seconds": measured_overhead,
            "case_uncompressed_bytes": len(case_payload),
            "case_compressed_bytes": len(case_compressed),
            "survivor_uncompressed_bytes": len(survivor_payload),
            "survivor_compressed_bytes": len(survivor_compressed),
            "all_partial_masks_prepared_streaming": catalog["families"],
            "all_partial_mask_preparation_seconds": preparation,
            "prepared_57_byte_mask_stream_sha256": prepared_digest.hexdigest(),
            "all_masks_retained_in_memory": False,
        },
        "estimated_full_new_pairs": {
            "pairs": 6543904,
            "weighted_screen_function_seconds": weighted_screen,
            "writing_bookkeeping_seconds_by_pair_count": count_overhead,
            "writing_bookkeeping_seconds_by_emitted_bytes": byte_overhead,
            "case_uncompressed_bytes": case_bytes,
            "case_compressed_bytes": case_bytes * len(case_compressed) / len(case_payload),
            "survivor_uncompressed_bytes": survivor_bytes,
            "survivor_compressed_bytes": survivor_bytes
            * len(survivor_compressed)
            / len(survivor_payload),
            "total_seconds_with_streaming_preparation": estimated_total,
            "total_minutes_with_streaming_preparation": estimated_total / 60,
        },
        "method": {
            "screen": "sum of each fiber population times its measured mean screen-call time",
            "raw_bytes": "sum of each fiber population times its mean emitted JSONL bytes",
            "compressed_bytes": "estimated raw bytes times the respective sampled gzip ratio",
            "writing": "non-loading/non-screen overhead scaled by estimated emitted bytes",
            "startup": "add measured full streaming preparation and full sampled loading time",
            "startup_overlap": "the added sampled loading also includes its 1000 partial masks",
        },
        "limitations": [
            "Point estimate only; no statistical interval or guaranteed runtime bound.",
            "A short fixed sample may miss expensive cases and survivor-heavy regions.",
            "No full pair screen, full output stream, or all-mask memory retention was measured.",
            "File-system, memory, compression, scheduler, and thermal costs can change at scale.",
            "Streaming preparation is measured, including its check and hash overhead.",
        ],
        "additional_pair_screen_calls": 0,
        "optimizer_calls": 0,
    }
    (HERE / "estimate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
