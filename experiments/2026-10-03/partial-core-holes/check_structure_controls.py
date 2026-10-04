#!/usr/bin/env python3
# Document:    Partial Cover Structure Screen Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Exercise complete relabeling witnesses, negative controls and damaged inputs."""

import hashlib
import importlib.util
import json
import random
import tempfile
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("structure", HERE / "screen_structure.py")
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


def write(path, blocks):
    path.write_text("".join(" ".join(map(str, b)) + "\n" for b in sorted(blocks)))


def main():
    core = screen.read(HERE / "core.txt", 60)
    original = screen.read(HERE / "input.txt", 64)
    rng = random.Random(2026103992)
    rows = []
    for index in range(5):
        labels = list(range(1, 17))
        if index:
            rng.shuffle(labels)
        target = {tuple(sorted(labels[p - 1] for p in b)) for b in original}
        result = screen.screen(target, core)
        assert result["contains_relabelled_core"] is True
        assert result["forbidden_five_heavy_profile"] is True
        permutation = result["mapping_images_of_1_to_16"]
        assert sorted(permutation) == list(range(1, 17))
        assert {tuple(sorted(permutation[p - 1] for p in b)) for b in core} <= target
        rows.append({"control": f"known-core-relabel-{index}", "report": result})
    random_blocks = set(rng.sample(list(combinations(range(1, 17), 5)), 64))
    result = screen.screen(random_blocks, core)
    assert result["contains_relabelled_core"] is False
    assert result["five_disjoint_heavy_families"] == 0
    rows.append({"control": "no-five-heavy-sets", "report": result})
    # A core plus arbitrary four extra blocks must also be recognized; the
    # detector does not depend on the original three-hole completion fringe.
    arbitrary = core | set(b for b in combinations(range(1, 17), 5) if b not in core)
    arbitrary = core | set(sorted(arbitrary - core)[:4])
    result = screen.screen(arbitrary, core)
    assert result["contains_relabelled_core"] is True
    rows.append({"control": "arbitrary-fringe", "report": result})
    damaged = 0
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "bad.txt"
        blocks = sorted(original)
        variants = [blocks[:-1], blocks + [blocks[0]], [blocks[0]] + blocks[:-1],
                    [(0, 2, 3, 4, 5)] + blocks[1:],
                    [(1, 1, 3, 4, 5)] + blocks[1:],
                    [(1, 2, 3, 4)] + blocks[1:]]
        for variant in variants:
            write(path, variant)
            try:
                screen.read(path, 64)
            except ValueError:
                damaged += 1
            else:
                raise AssertionError("damaged input accepted")
    report = {"passed": True, "positive_controls": 6, "negative_controls": 1,
              "damaged_inputs_rejected": damaged, "controls": rows,
              "screen_sha256": hashlib.sha256((HERE / "screen_structure.py").read_bytes())
              .hexdigest(), "source_sha256": hashlib.sha256(Path(__file__).read_bytes())
              .hexdigest()}
    (HERE / "structure-controls.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "controls"}), flush=True)


if __name__ == "__main__":
    main()
