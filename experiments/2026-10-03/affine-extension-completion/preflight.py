# Document:    Fixed Circle Completion Preflight and Positive Control
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools
import json
import random
import subprocess
from pathlib import Path

from build import construct
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-extension-completion-control-68"


def bits(block):
    return sum(1 << (p - 1) for p in block)


def check(model, meta):
    proto = model.proto
    all_blocks = list(itertools.combinations(range(1, 17), 5))
    extensions = list(map(tuple, meta["extensions"]))
    retained = list(map(tuple, meta["retained_circles"]))
    assert extensions == sorted(set(extensions)) and len(extensions) == 240
    assert len(proto.variables) == 240
    assert [v.name for v in proto.variables] == [f"block_{all_blocks.index(b)}" for b in extensions]
    assert all(list(v.domain) == [0, 1] for v in proto.variables)
    e_masks = list(map(bits, extensions))
    fixed = list(map(bits, retained))
    missing = [t for t in itertools.combinations(range(1, 17), 3)
               if not any(bits(t) & b == bits(t) for b in fixed)]
    assert missing == list(map(tuple, meta["missing_triples"]))
    assert len(proto.constraints) == 1 + len(missing)
    expected = [(list(range(240)), [meta["target"] - len(retained)] * 2)]
    expected += [([i for i, b in enumerate(e_masks) if bits(t) & b == bits(t)],
                  [1, 2**63 - 1]) for t in missing]
    for row, (ids, domain) in zip(proto.constraints, expected, strict=True):
        assert not row.enforcement_literal
        assert list(row.linear.vars) == ids
        assert list(row.linear.coeffs) == [1] * len(ids)
        assert list(row.linear.domain) == domain


def main():
    rng = random.Random(2026104251)
    for count in [0, 1, 4, 9, 14, 24, 48]:
        for _ in range(3):
            removed = sorted(rng.sample(range(48), count))
            model, meta = construct(removed, 64)
            check(model, meta)
    invalid = [[0, 0], [-1], [48], [True], [2, 1]]
    for removed in invalid:
        try:
            construct(removed)
        except ValueError:
            continue
        raise AssertionError("invalid deletion set accepted")
    model, meta = construct([], 68)
    check(model, meta)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 2026104251
    status = solver.solve(model)
    assert status in (cp_model.FEASIBLE, cp_model.OPTIMAL)
    chosen = [b for i, b in enumerate(meta["extensions"])
              if solver.value(model.get_bool_var_from_proto_index(i))]
    witness = sorted(map(tuple, meta["retained_circles"] + chosen))
    assert len(witness) == len(set(witness)) == 68
    witness_path = RAW / "positive-control.txt"
    witness_path.write_text("".join(" ".join(map(str, b)) + "\n" for b in witness))
    checks = []
    for name, command in [
        ("package", ["uv", "run", "covering64", "verify", str(witness_path),
                     "--expected-blocks", "68"]),
        ("standalone", ["uv", "run", "python", "scripts/check_cover.py", str(witness_path),
                        "--expected-blocks", "68"]),
    ]:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        (RAW / f"{name}.json").write_text(result.stdout)
        (RAW / f"{name}.err").write_text(result.stderr)
        checks.append({"checker": name, "returncode": result.returncode,
                       "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest()})
    report = {"passed": True, "model_reconstructions": 22,
              "invalid_deletion_sets_rejected": len(invalid), "seed": 2026104251,
              "positive_control_blocks": 68, "control_verifiers": checks,
              "builder_sha256": hashlib.sha256((HERE / "build.py").read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "Model preparation and known 68-block positive control; "
                       "target64 is unsolved"}
    (HERE / "preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
