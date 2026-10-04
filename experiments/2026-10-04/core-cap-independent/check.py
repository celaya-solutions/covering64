# Document:    Independent Core Overlap Cap Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e936d471b8762294b5457327683a83df45768670d6e1028966a70aa666dcba88
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay the exact core certificate and bind its two current labelings."""

import copy
import gzip
import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHECKER = ROOT / "scripts/check_core_orbit_certificate.py"
CERTIFICATE = ROOT / "experiments/2026-10-03/core-orbit/core-remove-4.json.gz"
CORE = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
PILOT = ROOT / "experiments/2026-10-04/six-hole-pool-release/manifest.json"
MAPS = [list(range(1, 17)), [1, 7, 2, 10, 15, 3, 8, 11, 4, 9, 12, 16, 14, 6, 5, 13]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(path):
    command = [sys.executable, "-I", str(CHECKER), str(path)]
    before = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    elapsed = time.monotonic() - before
    assert not result.stderr
    return {
        "command": command,
        "exit_code": result.returncode,
        "seconds": elapsed,
        "stdout": result.stdout,
        "report": json.loads(result.stdout),
    }


def parse_blocks(path, expected):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == expected and blocks == sorted(blocks)
    assert all(
        len(b) == 5 and list(b) == sorted(set(b)) and 1 <= min(b) <= max(b) <= 16 for b in blocks
    )
    return blocks


def main():
    assert not (HERE / "audit.json").exists()
    assert sha(CERTIFICATE) == "9997df71457bd6f4ca5567032cd026e3956d29235515acc330f05fddc6d9c298"
    assert sha(CHECKER) == "5537b41e4447421e951d4f65c7f6d9ab0b9d629d06f259fd39dc4faceaf8d429"
    assert sha(CORE) == "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
    assert sha(PILOT) == "84eac4c5110c0f98c7f8e0b01b3cc29dcc1f51003fdad9aa1b8e502813e2be8c"
    certificate = json.loads(gzip.decompress(CERTIFICATE.read_bytes()))
    successful = replay(CERTIFICATE)
    report = successful["report"]
    assert successful["exit_code"] == 0 and report["valid_certificate"]
    assert report["complete_obstruction"] and report["removed_count"] == 4
    assert report["representatives"] == 8337 and report["all_removal_sets_checked"] == 487635
    assert report["subgroup_order"] == 60 and report["additional_blocks_allowed"] == 8
    assert not report["uncertified_representatives"]
    assert report["minimum_exact_dual_bound"] == [2035711, 250000]
    assert Fraction(*report["minimum_exact_dual_bound"]) > 8
    assert report["maximum_core_blocks_in_any_64_cover"] == 55
    core = parse_blocks(CORE, 60)
    assert [list(b) for b in core] == certificate["core_blocks"]
    assert certificate["core_sha256"] == sha(CORE)
    blocks = list(itertools.combinations(range(1, 17), 5))
    rank = {block: i for i, block in enumerate(blocks)}
    triples = list(itertools.combinations(range(1, 17), 3))
    manifest = json.loads(PILOT.read_text())
    translations = []
    for position, mapping in enumerate(MAPS):
        assert sorted(mapping) == list(range(1, 17))
        inverse = {image: original for original, image in enumerate(mapping, 1)}
        mapped_blocks = [tuple(sorted(mapping[p - 1] for p in b)) for b in blocks]
        mapped_triples = [tuple(sorted(mapping[p - 1] for p in t)) for t in triples]
        assert set(mapped_blocks) == set(blocks) and set(mapped_triples) == set(triples)
        mapped_core = sorted(tuple(sorted(mapping[p - 1] for p in b)) for b in core)
        recovered = sorted(tuple(sorted(inverse[p] for p in b)) for b in mapped_core)
        assert recovered == core
        ids = sorted(rank[b] for b in mapped_core)
        assert len(ids) == len(set(ids)) == 60 and ids == manifest["core_rows"][position]
        assert all(
            {tuple(sorted(mapping[p - 1] for p in t)) for t in itertools.combinations(block, 3)}
            == set(itertools.combinations(image, 3))
            for block, image in zip(blocks, mapped_blocks, strict=True)
        )
        translations.append(
            {
                "position": position,
                "map_images": mapping,
                "core_global_ids": ids,
                "recommended_upper_bound": 55,
                "universe_blocks_bijective": 4368,
                "universe_triples_bijective": 560,
                "incidences_preserved": 43680,
            }
        )
    controls = []
    mutations = (
        ("wrong_target", lambda d: d.__setitem__("target", 65)),
        ("wrong_core_hash", lambda d: d.__setitem__("core_sha256", "0" * 64)),
        (
            "nonpermutation_generator",
            lambda d: d["generators"][0].__setitem__(0, d["generators"][0][1]),
        ),
        ("duplicate_orbit", lambda d: d["cases"].append(copy.deepcopy(d["cases"][0]))),
        ("missing_orbit", lambda d: d["cases"].pop()),
        ("missing_strict_bound", lambda d: d["cases"][0].__setitem__("weights", [])),
        (
            "duplicate_dual_weight",
            lambda d: d["cases"][0]["weights"].append(d["cases"][0]["weights"][0]),
        ),
    )
    with tempfile.TemporaryDirectory(prefix="core-cap-controls-") as directory:
        for label, mutate in mutations:
            damaged = copy.deepcopy(certificate)
            mutate(damaged)
            path = Path(directory) / f"{label}.json"
            path.write_text(json.dumps(damaged))
            receipt = replay(path)
            assert receipt["exit_code"] == 2 and not receipt["report"]["valid_certificate"]
            controls.append({"label": label, "receipt": receipt})
    audit = {
        "passed": True,
        "optimizer_calls": 0,
        "python_version": sys.version,
        "sources": {
            str(p.relative_to(ROOT)): sha(p)
            for p in [Path(__file__), CHECKER, CERTIFICATE, CORE, PILOT]
        },
        "exact_replay": successful,
        "current_core_translations": translations,
        "damaged_controls_rejected": controls,
        "recommended_upper_bound": 55,
        "derivation": (
            "If a 64-block cover contains at least 56 core blocks, choose any 56 of them. "
            "The certificate for their four-block complement supplies positive rational weights "
            "on uncovered triples with total greater than 8 and load at most 1 on every possible "
            "added block. At most 8 other blocks cannot cover these triples. Therefore overlap "
            "is at most 55. Relabeling preserves the full block/triple incidence relation."
        ),
        "scope": (
            "Valid necessary inequality for either named core in any 64-block cover, and every "
            "other point-permutation image. No global nonexistence theorem; "
            "no cap of 54 is claimed."
        ),
    }
    (HERE / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    (HERE / "replay.json").write_text(successful["stdout"])
    print(
        json.dumps(
            {
                "passed": True,
                "recommended_upper_bound": 55,
                "audit_sha256": sha(HERE / "audit.json"),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
