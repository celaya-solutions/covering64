# Document:    Independent Gate for Two Point-Star Repair Models
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4f742204f6f5f81cbb6b23703eb4bb0967112868c117aa4f3901e460fffb8821
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reconstruct both complete protobufs and the seed counts without solving."""

import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAX_INT = 2**63 - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row(model, variables, domain, enforcement=None):
    constraint = model.constraints.add()
    if enforcement is not None:
        constraint.enforcement_literal.append(enforcement)
    constraint.linear.vars.extend(variables)
    constraint.linear.coeffs.extend([1] * len(variables))
    constraint.linear.domain.extend(domain)


def main():
    assert not (HERE / "gate.json").exists(), "preserve completed gate"
    metadata_path = HERE / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    checked = {
        str(path.relative_to(ROOT)): sha(path)
        for path in (
            metadata_path,
            HERE / "run.py",
            HERE / "initial.txt",
            HERE / "initial.audit.json",
        )
    }
    assert sha(HERE / "run.py") == metadata["source_sha256"]
    assert sha(HERE / "initial.txt") == metadata["initial_sha256"]
    for relative, expected in metadata["dependencies"].items():
        assert sha(ROOT / relative) == expected
        checked[relative] = expected
    assert metadata["runs"] == [
        {"point": p, "seed": s, "seconds": 30, "workers": 1}
        for p, s in [(2, 2026104001), (2, 2026104002), (15, 2026104003), (15, 2026104004)]
    ]
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    ids = {block: i for i, block in enumerate(blocks)}
    tids = {triple: i for i, triple in enumerate(triples)}
    supports = [[] for _ in triples]
    for i, block in enumerate(blocks):
        for triple in itertools.combinations(block, 3):
            supports[tids[triple]].append(i)
    assert len(blocks) == 4368 and len(triples) == 560 and all(len(s) == 78 for s in supports)
    seed = [
        tuple(map(int, line.split())) for line in (HERE / "initial.txt").read_text().splitlines()
    ]
    assert (
        len(seed) == len(set(seed)) == 64 and seed == sorted(seed) and all(b in ids for b in seed)
    )
    selected = {ids[block] for block in seed}
    counts = Counter(triple for block in seed for triple in itertools.combinations(block, 3))
    missing = [triple for triple in triples if counts[triple] == 0]
    assert missing == [(2, 7, 14), (2, 7, 15), (7, 14, 15)]
    package = verify_cover(seed)
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "scripts/check_cover.py"),
            str(HERE / "initial.txt"),
            "--expected-blocks",
            "64",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 1 and not process.stderr
    standalone = json.loads(process.stdout)
    assert package["uncovered"] == missing
    assert [list(t) for t in missing] == standalone["uncovered"]
    assert (
        package["canonical_sha256"] == standalone["canonical_sha256"] == metadata["initial_sha256"]
    )
    assert not package["valid"] and not standalone["valid"]
    assert len(metadata["models"]) == 2
    summaries = []
    for item, point in zip(metadata["models"], (2, 15), strict=True):
        assert item["point"] == point
        removed = sorted(i for i in selected if point in blocks[i])
        retained = sorted(selected - set(removed))
        assert item["removed_ids"] == removed and item["retained_ids"] == retained
        assert item["weight"] == len(removed) + 1
        model_path = Path(item["model_file"])
        assert model_path.is_relative_to(ROOT) and sha(model_path) == item["model_sha256"]
        checked[str(model_path.relative_to(ROOT))] = sha(model_path)
        actual = cp_model_pb2.CpModelProto()
        text_format.Parse(model_path.read_text(), actual)
        expected = cp_model_pb2.CpModelProto()
        for i in range(4928):
            variable = expected.variables.add()
            variable.name = f"block_{i}" if i < 4368 else f"missing_{i - 4368}"
            variable.domain.extend([0, 1])
        row(expected, list(range(4368)), [64, 64])
        for i in retained:
            row(expected, [i], [1, 1])
        for tid, support in enumerate(supports):
            row(expected, support, [0, 0], 4368 + tid)
            row(expected, support, [1, MAX_INT], -(4368 + tid) - 1)
        expected.objective.vars.extend(removed + list(range(4368, 4928)))
        expected.objective.coeffs.extend([1] * len(removed) + [len(removed) + 1] * 560)
        expected.objective.scaling_factor = 1
        hint = [int(i in selected) for i in range(4368)] + [int(not counts[t]) for t in triples]
        expected.solution_hint.vars.extend(range(4928))
        expected.solution_hint.values.extend(hint)
        assert actual.SerializeToString(deterministic=True) == expected.SerializeToString(
            deterministic=True
        ), point
        for constraint in actual.constraints:
            if constraint.enforcement_literal:
                literal = constraint.enforcement_literal[0]
                active = hint[literal] if literal >= 0 else not hint[-literal - 1]
                if not active:
                    continue
            activity = sum(
                hint[i] * c
                for i, c in zip(constraint.linear.vars, constraint.linear.coeffs, strict=True)
            )
            assert constraint.linear.domain[0] <= activity <= constraint.linear.domain[1]
        remaining_counts = Counter(
            t for i in retained for t in itertools.combinations(blocks[i], 3)
        )
        deficit_after_star_deletion = [t for t in triples if remaining_counts[t] == 0]
        summaries.append(
            {
                "point": point,
                "removed": len(removed),
                "retained": len(retained),
                "variables": len(actual.variables),
                "constraints": len(actual.constraints),
                "complete_proto_matches_independent_reconstruction": True,
                "initial_holes": len(missing),
                "initial_objective": 3 * item["weight"] + len(removed),
                "holes_after_deleting_star": len(deficit_after_star_deletion),
                "model_sha256": sha(model_path),
            }
        )
    assert all(sha(ROOT / relative) == expected for relative, expected in checked.items())
    gate = {
        "passed": True,
        "metadata_sha256": sha(metadata_path),
        "source_sha256": sha(__file__),
        "verified_inputs": checked,
        "models": summaries,
        "solver_calls": 0,
        "scope": "Only the two recorded retained-block neighborhoods. Hole variables are exact; "
        "objective prefers fewer holes before changed-star size. No unrestricted lower bound.",
    }
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    print(json.dumps(gate))


if __name__ == "__main__":
    main()
