# Document:    Independent Clebsch Neighborhood Cycle Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f3a9571106cc5edf5787f963807a0c84fe29a702de31fd476087d3023d43f467
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild the complete finite geometry and matrix; never run an optimizer."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import itertools
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "clebsch-neighborhood-cycle-pilot"
RAW = ROOT / "experiments/scratch/clebsch-neighborhood-cycle-pilot-20261004"
MANIFEST_SHA = "909498955fe3f595465c364f97dd5b938ff333f23ccbf027ec611a4d472fc968"
SOURCE_SHA = "092c5c8a7ee693adadfd5a2bdd9a443fa3a95d1feeb6d3906b0e1ec662ed1d2b"
POINTS = tuple(range(1, 17))
BLOCKS = tuple(itertools.combinations(POINTS, 5))
TRIPLES = tuple(itertools.combinations(POINTS, 3))
PAIRS = tuple(itertools.combinations(POINTS, 2))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry():
    # Four-cube plus antipodal edges, transported to the producer's labels.
    vertices = tuple(itertools.product((0, 1), repeat=4))
    labels = {v: 1 + sum((bit ^ (sum(v) % 2)) * 2**i for i, bit in enumerate(v)) for v in vertices}
    edges = {
        tuple(sorted((labels[u], labels[v])))
        for u, v in itertools.combinations(vertices, 2)
        if sum(a != b for a, b in zip(u, v, strict=True)) in (1, 4)
    }
    adjacent = {p: {q for q in POINTS if tuple(sorted((p, q))) in edges} for p in POINTS}
    assert len(edges) == 40 and all(len(v) == 5 for v in adjacent.values())
    assert all(len(adjacent[a] & adjacent[b]) == (0 if (a, b) in edges else 2) for a, b in PAIRS)
    kinds = [sum(pair in edges for pair in itertools.combinations(t, 2)) for t in TRIPLES]
    assert Counter(kinds) == {0: 160, 1: 240, 2: 160}
    fixed = {tuple(sorted(v)) for v in adjacent.values()}
    independent = {t for t, k in zip(TRIPLES, kinds, strict=True) if k == 0}
    cycles = {b for b in BLOCKS if all(len(set(b) & adjacent[p]) == 2 for p in b)}
    no_independent = {b for b in BLOCKS if not any(set(t) <= set(b) for t in independent)}
    assert no_independent == cycles and len(cycles) == 192 and len(fixed) == 16
    assert fixed.isdisjoint(cycles)
    assert all(
        sum(set(t) <= set(b) for b in fixed) == (1 if k == 0 else 0)
        for t, k in zip(TRIPLES, kinds, strict=True)
    )
    assert all(
        sum(set(t) <= set(b) for b in cycles) == [0, 4, 6][k]
        for t, k in zip(TRIPLES, kinds, strict=True)
    )
    assert all(
        Counter(kinds[TRIPLES.index(t)] for t in itertools.combinations(b, 3)) == {1: 5, 2: 5}
        for b in cycles
    )
    # Sum the six exact-one rows through each pair. Per-cycle coefficients
    # are one on edges and two on nonedges, forcing cycle loads six/three.
    for pair in PAIRS:
        rows = [t for t, k in zip(TRIPLES, kinds, strict=True) if k == 1 and set(pair) <= set(t)]
        assert len(rows) == 6
        coefficient = 1 if pair in edges else 2
        assert all(
            sum(set(t) <= set(b) for t in rows) == (coefficient if set(pair) <= set(b) else 0)
            for b in cycles
        )
        assert sum(set(pair) <= set(b) for b in fixed) == (0 if pair in edges else 2)
    return edges, fixed, cycles, kinds


def expected_proto(fixed, cycles, kinds):
    expected = cp_model_pb2.CpModelProto()
    for i, b in enumerate(BLOCKS):
        v = expected.variables.add(name=f"block_{i}")
        v.domain.extend([int(b in fixed), int(b in fixed or b in cycles)])
    cardinality = expected.constraints.add().linear
    cardinality.vars.extend(range(len(BLOCKS)))
    cardinality.coeffs.extend([1] * len(BLOCKS))
    cardinality.domain.extend([64, 64])
    for triple, kind in zip(TRIPLES, kinds, strict=True):
        row = expected.constraints.add().linear
        carriers = [i for i, b in enumerate(BLOCKS) if all(p in b for p in triple)]
        assert len(carriers) == 78
        row.vars.extend(carriers)
        row.coeffs.extend([1] * len(carriers))
        row.domain.extend([1, 2 if kind == 2 else 1])
    return expected


def damage_controls(proto, expected, fixed, cycles, kinds):
    fixed_id = next(i for i, b in enumerate(BLOCKS) if b in fixed)
    free_id = next(i for i, b in enumerate(BLOCKS) if b in cycles)
    zero_id = next(i for i, b in enumerate(BLOCKS) if b not in fixed | cycles)
    cases = {
        "fixed_one_relaxed": lambda p: p.variables[fixed_id].domain.__setitem__(0, 0),
        "free_cycle_fixed": lambda p: p.variables[free_id].domain.__setitem__(1, 0),
        "excluded_block_allowed": lambda p: p.variables[zero_id].domain.__setitem__(1, 1),
        "variable_name": lambda p: setattr(p.variables[0], "name", "block_1"),
        "missing_variable": lambda p: p.variables.pop(),
        "cardinality_bound": lambda p: p.constraints[0].linear.domain.__setitem__(1, 65),
        "missing_row": lambda p: p.constraints.pop(),
        "extra_row": lambda p: p.constraints.add(),
        "hidden_enforcement": lambda p: p.constraints[1].enforcement_literal.append(0),
        "objective": lambda p: p.objective.vars.append(0),
        "hint": lambda p: p.solution_hint.vars.append(0),
    }
    for kind in range(3):
        index = kinds.index(kind) + 1
        cases[f"kind_{kind}_bound"] = lambda p, i=index: p.constraints[i].linear.domain.__setitem__(
            1, 3
        )
        cases[f"kind_{kind}_support"] = lambda p, i=index: p.constraints[i].linear.vars.pop()
        cases[f"kind_{kind}_coefficient"] = lambda p, i=index: p.constraints[
            i
        ].linear.coeffs.__setitem__(0, 2)
    controls = {}
    for name, mutate in cases.items():
        damaged = copy.deepcopy(proto)
        mutate(damaged)
        assert damaged != proto and damaged != expected, name
        controls[name] = "rejected"
    return controls


def wrapper_controls():
    # Execute only the wrapper against fake processes and disposable directories.
    # Importing producer definitions cannot invoke solve: this guard spans import
    # and every synthetic wrapper run.
    spec = importlib.util.spec_from_file_location("cycle_gate_producer", PRODUCER / "run.py")
    module = importlib.util.module_from_spec(spec)
    outcomes = {}
    with patch.object(cp_model.CpSolver, "solve", side_effect=AssertionError("solver forbidden")):
        spec.loader.exec_module(module)
        for mode in ("normal", "terminate", "kill"):
            with tempfile.TemporaryDirectory(prefix="clebsch-gate-") as directory:
                root = Path(directory)
                module.ROOT = module.HERE = root
                module.RAW = root / "raw"
                module.RAW.mkdir()
                manifest = {"pins": {}, "ortools": ortools.__version__}
                module.dump(root / "manifest.json", manifest)
                gate = {
                    "passed": True,
                    "launch_permitted": True,
                    "manifest_sha256": sha(root / "manifest.json"),
                }
                module.dump(root / "gate.json", gate)

                class FakeProcess:
                    def __init__(self, *args, **kwargs):
                        self.returncode = 0
                        self.calls = []

                    def communicate(self, timeout=None):
                        self.calls.append(("communicate", timeout))
                        if timeout == 35 and mode != "normal":
                            raise subprocess.TimeoutExpired("fake", timeout)
                        if timeout == 5 and mode == "kill":
                            raise subprocess.TimeoutExpired("fake", timeout)
                        return "synthetic stdout", "synthetic stderr"

                    def terminate(self):
                        self.calls.append(("terminate", None))
                        self.returncode = -15

                    def kill(self):
                        self.calls.append(("kill", None))
                        self.returncode = -9

                fake = FakeProcess()
                with patch.object(module.subprocess, "Popen", return_value=fake) as popen:
                    with contextlib.redirect_stdout(io.StringIO()):
                        module.execute(root / "gate.json")
                    assert popen.call_count == 1
                    result = json.loads((root / "result.json").read_text())
                    assert result["watchdog"] == (mode != "normal")
                    assert result["terminated"] == (mode != "normal")
                    assert result["killed"] == (mode == "kill")
                    assert result["child"] is None
                    before = popen.call_count
                    try:
                        module.execute(root / "gate.json")
                    except AssertionError:
                        pass
                    else:
                        raise AssertionError("duplicate launch accepted")
                    assert popen.call_count == before
                    outcomes[mode] = {
                        "passed": True,
                        "calls": fake.calls,
                        "duplicate_launch": "rejected",
                    }
    return outcomes


def main():
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(PRODUCER / "run.py") == SOURCE_SHA
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    for path, digest in manifest["pins"].items():
        assert sha(ROOT / path) == digest, path
    assert manifest["ortools"] == ortools.__version__
    assert {
        key: manifest[key]
        for key in (
            "calls",
            "seed",
            "workers",
            "native_seconds",
            "watchdog_seconds",
            "termination_grace_seconds",
            "relaunch",
            "hint",
            "objective",
        )
    } == {
        "calls": 1,
        "seed": 2026106201,
        "workers": 1,
        "native_seconds": 30,
        "watchdog_seconds": 35,
        "termination_grace_seconds": 5,
        "relaunch": False,
        "hint": None,
        "objective": None,
    }
    edges, fixed, cycles, kinds = geometry()
    expected_geometry = {
        "edges": [list(pair) for pair in sorted(edges)],
        "triple_kinds": kinds,
        "fixed_neighbor_ids": [i for i, b in enumerate(BLOCKS) if b in fixed],
        "free_cycle_ids": [i for i, b in enumerate(BLOCKS) if b in cycles],
    }
    assert json.loads((PRODUCER / "geometry.json").read_text()) == expected_geometry
    expected = expected_proto(fixed, cycles, kinds)
    proto = text_format.Parse((RAW / "model.pbtxt").read_text(), cp_model_pb2.CpModelProto())
    assert proto == expected
    actual_parameters = text_format.Parse(
        (RAW / "parameters.pbtxt").read_text(), sat_parameters_pb2.SatParameters()
    )
    wanted_parameters = sat_parameters_pb2.SatParameters(
        random_seed=2026106201,
        max_time_in_seconds=30,
        num_search_workers=1,
        log_search_progress=True,
        log_to_stdout=False,
    )
    assert actual_parameters == wanted_parameters
    gate = {
        "passed": True,
        "launch_permitted": True,
        "manifest_sha256": MANIFEST_SHA,
        "producer_source_sha256": SOURCE_SHA,
        "checker_sha256": sha(Path(__file__)),
        "pins_checked": len(manifest["pins"]),
        "scope": "Only the fixed sixteen Clebsch neighborhoods plus forty-eight cycle pentads.",
        "variables": len(proto.variables),
        "rows": len(proto.constraints),
        "coefficients": sum(len(c.linear.vars) for c in proto.constraints),
        "domains": {
            str(k): v for k, v in Counter(tuple(v.domain) for v in proto.variables).items()
        },
        "geometry": {
            "edges": len(edges),
            "neighborhoods": len(fixed),
            "cycles": len(cycles),
            "triple_kinds": dict(Counter(kinds)),
            "carriers_by_kind": [0, 4, 6],
            "fixed_independent_carriers": 1,
            "pair_implication_checked": True,
            "all_no_independent_triple_pentads_are_cycles": True,
        },
        "damage_controls": damage_controls(proto, expected, fixed, cycles, kinds),
        "wrapper_controls": wrapper_controls(),
        "optimizer_calls": 0,
        "outcome_rules": (
            "UNKNOWN is inconclusive; INFEASIBLE is not an independently checked proof."
        ),
    }
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(PRODUCER / "run.py") == SOURCE_SHA
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "damage_controls": len(gate["damage_controls"]),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
