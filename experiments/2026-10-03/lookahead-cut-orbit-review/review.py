#!/usr/bin/env python3
# Document:    Independent Review of Heavy-Cut Orbit Separation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Read-only mathematical replay and malformed/racing-input controls."""

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
from collections import deque
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIMARY = HERE.parent / "lookahead-cut-orbit/check.py"
LEGACY = ROOT / "experiments/scratch/lookahead-cut-orbit-v1.0.0/check.py"
CUT = HERE.parent / "lookahead-parametric-cut/cut.json"
WITNESS = HERE.parent / "four-seven-template-native-lookahead/performance-cycle-best.txt"
IDENTITY = tuple(range(1, 17))
ANCHORS = [set(range(s, s + 3)) for s in (1, 5, 9, 13)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image(block, mapping):
    return tuple(sorted(mapping[x - 1] for x in block))


def build_group():
    generators = []
    for group in range(4):
        start = group * 4
        for order in ((1, 0, 2), (1, 2, 0)):
            mapping = list(IDENTITY)
            mapping[start:start + 3] = [start + j + 1 for j in order]
            generators.append(tuple(mapping))
    for order in ((1, 0, 2, 3), (1, 2, 3, 0)):
        generators.append(tuple(4 * g + j + 1 for g in order for j in range(4)))
    group, todo = {IDENTITY}, deque([IDENTITY])
    while todo:
        current = todo.popleft()
        for generator in generators:
            new = tuple(current[p - 1] for p in generator)
            if new not in group:
                group.add(new)
                todo.append(new)
    assert len(group) == 31104
    return generators, group


def separate(heavy, group, coefficients, rhs):
    values = [(sum(coefficients[image(b, mapping)] for b in heavy), mapping)
              for mapping in sorted(group)]
    minimum, mapping = min(values)
    return {"minimum_lhs": minimum, "maximum_lhs": max(v for v, _ in values),
            "violated_maps": sum(v < rhs for v, _ in values), "worst_map": mapping}


def write(path, blocks):
    path.write_text("".join(" ".join(map(str, block)) + "\n" for block in blocks))


def main():
    before = {str(p.relative_to(ROOT)): sha(p) for p in (PRIMARY, LEGACY, CUT, WITNESS)}
    spec = importlib.util.spec_from_file_location("primary_orbit", PRIMARY)
    primary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(primary)
    cut = json.loads(CUT.read_text())
    blocks = [tuple(map(int, line.split())) for line in WITNESS.read_text().splitlines()]
    heavy_domain = {b for b in combinations(IDENTITY, 5)
                    if any(a <= set(b) for a in ANCHORS)
                    and all(len(a & set(b)) in (0, 1, 3) for a in ANCHORS)}
    ordinary = {b for b in combinations(IDENTITY, 5)
                if all(len(a & set(b)) <= 1 for a in ANCHORS)}
    coefficients = dict(zip(map(tuple, cut["heavy_blocks"]), cut["coefficients"], strict=True))
    assert set(coefficients) == heavy_domain and len(heavy_domain) == 276 and len(ordinary) == 1200
    heavy = [b for b in blocks if b in heavy_domain]
    generators, group = build_group()
    assert group == set(primary.maps())
    for mapping in group:
        assert tuple(sorted(mapping)) == IDENTITY
        for anchor in ANCHORS:
            transformed = {mapping[p - 1] for p in anchor}
            assert transformed in ANCHORS
            assert mapping[max(anchor)] == max(transformed) + 1
    for generator in generators:
        assert {image(b, generator) for b in heavy_domain} == heavy_domain
        assert {image(b, generator) for b in ordinary} == ordinary
    baseline = separate(heavy, group, coefficients, cut["rhs"])
    assert (baseline["minimum_lhs"], baseline["maximum_lhs"], baseline["violated_maps"]) == (
        98144, 156905, 19)
    archived = json.loads((HERE.parent / "lookahead-cut-orbit/baseline-v1.1.0.json").read_text())
    assert archived["checker_sha256"] == sha(PRIMARY)
    assert archived["witness_sha256"] == sha(WITNESS)
    assert archived["cut_sha256"] == sha(CUT)
    for field in ("minimum_lhs", "maximum_lhs", "violated_maps"):
        assert archived[field] == baseline[field]
    assert tuple(archived["worst_map_images_of_1_to_16"]) == baseline["worst_map"]
    pulled = [coefficients[image(tuple(b), baseline["worst_map"])] for b in cut["heavy_blocks"]]
    assert pulled == archived["pulled_back_coefficients_in_base_order"]
    relabel_controls = []
    damaged_rejected = []
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        path = directory / "candidate.txt"
        for i, mapping in enumerate((generators[1], generators[-1])):
            changed = sorted(image(b, mapping) for b in blocks)
            write(path, changed)
            parsed = primary.inspect_witness(path.read_bytes(), coefficients)
            result = separate(parsed, group, coefficients, cut["rhs"])
            for field in ("minimum_lhs", "maximum_lhs", "violated_maps"):
                assert result[field] == baseline[field]
            relabel_controls.append({"case": i, "mapping": mapping, **result})
        bad_point_map = list(IDENTITY)
        bad_point_map[0], bad_point_map[4] = bad_point_map[4], bad_point_map[0]
        bad_hub_map = list(IDENTITY)
        bad_hub_map[3], bad_hub_map[7] = bad_hub_map[7], bad_hub_map[3]
        cases = [
            ("missing-block", blocks[:-1]), ("extra-block", blocks + [blocks[0]]),
            ("duplicate-block", [blocks[0]] + blocks[:-1]),
            ("zero-label", [(0,) + blocks[0][1:]] + blocks[1:]),
            ("label17", [blocks[0][:-1] + (17,)] + blocks[1:]),
            ("repeated-label", [(1, 1, 2, 3, 4)] + blocks[1:]),
            ("wrong-width", [blocks[0][:-1]] + blocks[1:]),
            ("unsorted-block", [tuple(reversed(blocks[0]))] + blocks[1:]),
            ("cross-anchor-point-swap", sorted(image(b, bad_point_map) for b in blocks)),
            ("wrong-own-hub", sorted(image(b, bad_hub_map) for b in blocks)),
        ]
        for name, damaged in cases:
            write(path, damaged)
            try:
                primary.inspect_witness(path.read_bytes(), coefficients)
            except (AssertionError, ValueError):
                damaged_rejected.append(name)
            else:
                raise AssertionError(f"damaged witness accepted: {name}")
        # Deterministically emulate an external rewrite after witness parsing.
        # The primary file is untouched; the maps wrapper schedules a write to
        # the temporary candidate at the exact later-read boundary.
        old_spec = importlib.util.spec_from_file_location("legacy_orbit", LEGACY)
        legacy = importlib.util.module_from_spec(old_spec)
        old_spec.loader.exec_module(legacy)
        # Preserve the old checker's original data paths after loading its
        # separately archived source. No source file is modified.
        legacy.HERE, legacy.CUT = PRIMARY.parent, CUT
        race_summary = []
        for version, module in (("v1.0.0", legacy), ("v1.1.0", primary)):
            write(path, blocks)
            initial_sha = sha(path)
            original_maps = module.maps
            output = directory / f"race-{version}.json"

            def rewrite_then_maps():
                path.write_text("\n")
                yield from original_maps()

            module.maps = rewrite_then_maps
            old_argv = sys.argv
            try:
                sys.argv = [str(PRIMARY), str(path), str(output)]
                with contextlib.redirect_stdout(io.StringIO()):
                    module.main()
            finally:
                sys.argv = old_argv
                module.maps = original_maps
            race = json.loads(output.read_text())
            assert race["passed"] and path.read_text() == "\n"
            if version == "v1.0.0":
                assert race["witness_sha256"] == sha(path) != initial_sha
            else:
                assert race["witness_sha256"] == initial_sha != sha(path)
            race_summary.append({"version": version, "source_sha256": sha(Path(module.__file__)),
                                 "receipt_hash": race["witness_sha256"],
                                 "validated_bytes_sha256": initial_sha,
                                 "final_bytes_sha256": sha(path), "final_bytes": "LF only",
                                 "receipt_hash_matches_validated_bytes": version == "v1.1.0",
                                 "primary_source_modified": False})
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in (PRIMARY, LEGACY, CUT, WITNESS)}
    report = {
        "mathematical_replay_passed": True, "source_sha256": sha(Path(__file__)),
        "reviewed_inputs": before, "independent_generators": len(generators),
        "group_maps": len(group), "heavy_domain": len(heavy_domain),
        "ordinary_domain": len(ordinary),
        "baseline": baseline, "relabel_controls": relabel_controls,
        "damaged_witnesses_rejected": damaged_rejected,
        "race_control": race_summary,
        "findings": [{"severity": "evidence-integrity", "status": "resolved-in-v1.1.0",
                      "summary": "Version1.0 parsed input before enumeration but hashed fresh "
                      "bytes afterward. The controlled rewrite reproduced a passed receipt for "
                      "unvalidated final bytes. Version1.1 parses and hashes one captured byte "
                      "buffer, and passes the same rewrite control with the correct initial hash."
                      }],
        "unresolved_actionable_findings": 0,
        "current_frozen_baseline_affected": False, "solver_calls": 0,
        "claim_review": "A violated orbit cut rules out the fixed heavy tuple only in the "
        "regular four-sevenfold family. A passed orbit screen is not evidence of extendability. "
        "The31104-map orbit covers these anchor/hub relabelings, not all arbitrary16-point maps.",
    }
    (HERE / "review.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in (
        "reviewed_inputs", "relabel_controls")}), flush=True)


if __name__ == "__main__":
    main()
