# Document:    Frozen Declared-Partition Core Transport Witness
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      cca423a395b2acf4599fcdd4a35ca455d26d8ed9fc38d3a1b4ecbdd69fab8899
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run finite point-map enumeration and save the complete transported-core witness."""

import hashlib
import itertools
import json
import subprocess
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/six-hole-relabeled-core-transport-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def main():
    assert not RAW.exists() and not (HERE / "result.json").exists()
    post_path = DAY / "six-hole-strong-core-release-independent/postcheck.json"
    result_path = DAY / "six-hole-strong-core-release/result.json"
    core_path = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
    core_audit_path = DAY / "core-cap-independent/audit.json"
    post, result, audit = read(post_path), read(result_path), read(core_audit_path)
    assert post["passed"] and post["result_sha256"] == sha(result_path)
    assert audit["passed"] and audit["recommended_upper_bound"] == 55
    assert sha(core_path) == "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
    final = post["cases"][1]["final"]
    ids = final["ids"]
    assert ids == result["cases"][1]["final"]["ids"]
    assert len(ids) == len(set(ids)) == 64 and ids == sorted(ids)
    assert all(type(i) is int and 0 <= i < 4368 for i in ids)
    blocks = list(itertools.combinations(range(1, 17), 5))
    rank = {block: i for i, block in enumerate(blocks)}
    candidate = [blocks[i] for i in ids]
    core = [tuple(map(int, line.split())) for line in core_path.read_text().splitlines()]
    assert len(core) == len(set(core)) == 60 and all(block in rank for block in core)
    counts = Counter(t for b in core for t in itertools.combinations(b, 3))
    source = sorted(t for t, count in counts.items() if count >= 6)
    assert len(source) == 5 and all(counts[t] == 6 for t in source)
    assert len(set(itertools.chain.from_iterable(source))) == 15
    necessary = final["relabeled_core_screen"]["necessary_partitions"]
    assert len(necessary) == 1
    target = necessary[0]["triples"]
    assert target == [[1, 2, 3], [5, 6, 7], [8, 12, 16], [9, 10, 11], [13, 14, 15]]
    counts = Counter(t for b in candidate for t in itertools.combinations(b, 3))
    assert [counts[tuple(t)] for t in target] == [7, 7, 7, 7, 6]
    response_path = ROOT / final["path"]
    assert sha(response_path) == final["sha256"]
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in (
        Path(__file__), HERE / "transport.cpp", post_path, result_path, core_path,
        core_audit_path, response_path,
    )}
    payload = "60 64\n" + "\n".join(" ".join(map(str, row)) for row in (
        core + candidate + source + [tuple(t) for t in target]
    )) + "\n"
    (HERE / "input.txt").write_text(payload)
    manifest = {"input_files": inputs, "input_sha256": sha(HERE / "input.txt"),
                "source_triples": source, "target_triples": target,
                "expected_label_maps": 933120, "optimization_calls": 0,
                "tie_rule": "Maximize overlap, then maximize the 16-label map lexicographically.",
                "scope": "Only maps carrying the declared source partition "
                "to the target partition."}
    dump(HERE / "manifest.json", manifest)
    RAW.mkdir()
    binary = RAW / "transport"
    version = subprocess.check_output(["/usr/bin/clang++", "--version"], text=True)
    subprocess.run(["/usr/bin/clang++", "-std=c++17", "-O3", str(HERE / "transport.cpp"),
                    "-o", str(binary)], check=True, capture_output=True, text=True)
    started = time.monotonic()
    completed = subprocess.run([str(binary)], input=payload, text=True,
                               capture_output=True, check=True, timeout=120)
    seconds = time.monotonic() - started
    (RAW / "stdout.json").write_text(completed.stdout)
    (RAW / "stderr.txt").write_text(completed.stderr)
    scan = json.loads(completed.stdout)
    mapping = scan["map_images"]
    assert sorted(mapping) == list(range(1, 17))
    transported = sorted(tuple(sorted(mapping[p - 1] for p in block)) for block in core)
    transformed_ids = sorted(rank[block] for block in transported)
    intersection = sorted(set(transformed_ids) & set(ids))
    assert len(transported) == len(set(transported)) == 60
    assert len(intersection) == scan["best_overlap"]
    assert scan["label_maps_checked"] == sum(scan["overlap_histogram"]) == 933120
    witness = {"map_images": mapping, "transported_core_blocks": transported,
               "transported_core_global_ids": transformed_ids, "candidate_global_ids": ids,
               "intersection_global_ids": intersection, "overlap": len(intersection),
               "valid_transported_core_cap": 55,
               "violates_transported_core_cap": len(intersection) > 55}
    dump(HERE / "witness.json", witness)
    report = {**scan, "manifest_sha256": sha(HERE / "manifest.json"),
              "witness_sha256": sha(HERE / "witness.json"), "source_sha256": sha(__file__),
              "enumerator_sha256": sha(HERE / "transport.cpp"), "binary_sha256": sha(binary),
              "compiler_version": version, "enumeration_seconds": seconds,
              "optimization_calls": 0, "independent_map_replay_pending": True,
              "scope": "Exhaustive only among the 933120 maps carrying the declared five-triple "
              "partition to the target partition. Not an enumeration of all16! point maps. "
              "A witnessed overlap above55 yields a translated necessary core-cap row; "
              "it makes no unrestricted infeasibility claim."}
    dump(HERE / "result.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "overlap_histogram"}, indent=2))


if __name__ == "__main__":
    main()
