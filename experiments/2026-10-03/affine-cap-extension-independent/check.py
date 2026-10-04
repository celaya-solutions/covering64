# Document:    Independent Affine Cap and Extension Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      75483d1adc5fb5f6296ea3a13f2d139398290bbed7a4c044b9a3b54ef0af684b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild the full cap/extension pool and every model coefficient independently."""

import copy
import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "affine-cap-extension-pool"
PRIOR = HERE.parent / "affine-extension-independent"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct(lines):
    points = list(range(1, 17))
    require(len(lines) == len(set(lines)) == 20, "affine line count")
    require(
        all(len(line) == 4 and tuple(sorted(set(line))) == line for line in lines), "line shape"
    )
    require(
        Counter(pair for line in lines for pair in it.combinations(line, 2))
        == {pair: 1 for pair in it.combinations(points, 2)},
        "line pair partition",
    )
    collinear = set(t for line in lines for t in it.combinations(line, 3))
    triples = list(it.combinations(points, 3))
    universe = list(it.combinations(points, 5))
    counts = [sum(t in collinear for t in it.combinations(block, 3)) for block in universe]
    require(Counter(counts) == {0: 288, 1: 2400, 2: 1440, 4: 240}, "full partition")
    extension_set = {
        tuple(sorted((*line, point))) for line in lines for point in points if point not in line
    }
    require(
        {b for b, n in zip(universe, counts) if n == 4} == extension_set, "extension equivalence"
    )
    ids = [i for i, n in enumerate(counts) if n in (0, 4)]
    pool = [universe[i] for i in ids]
    supports = [
        [i for i, block in enumerate(pool) if set(triple) <= set(block)] for triple in triples
    ]
    point_rows = [[i for i, block in enumerate(pool) if point in block] for point in points]
    pairs = list(it.combinations(points, 2))
    pair_rows = [[i for i, block in enumerate(pool) if set(pair) <= set(block)] for pair in pairs]
    require(Counter(map(len, supports)) == {9: 480, 12: 80}, "triple support sizes")
    require(all(len(row) == 165 for row in point_rows), "point incidence sizes")
    require(all(len(row) == 44 for row in pair_rows), "pair incidence sizes")
    payload = {
        "affine_lines": lines,
        "collinear_triples": sorted(collinear),
        "full_universe_collinear_count_distribution": dict(Counter(counts)),
        "pool": [
            {
                "local_id": i,
                "global_id": global_id,
                "block": universe[global_id],
                "kind": "cap" if counts[global_id] == 0 else "line_extension",
            }
            for i, global_id in enumerate(ids)
        ],
        "triples": triples,
        "supports": supports,
        "point_labels": points,
        "point_rows": point_rows,
        "pair_labels": pairs,
        "pair_rows": pair_rows,
    }
    return json.loads(json.dumps(payload))


def expected_model(payload, cuts):
    model = cp_model_pb2.CpModelProto()
    for block in payload["pool"]:
        variable = model.variables.add()
        variable.name = f"block_{block['global_id']}"
        variable.domain.extend([0, 1])
    rows = [(list(range(528)), 64, 64)]
    rows += [(support, 1, 2**63 - 1) for support in payload["supports"]]
    if cuts:
        rows += [(support, 19, 2**63 - 1) for support in payload["point_rows"]]
        rows += [(support, 5, 2**63 - 1) for support in payload["pair_rows"]]
    for variables, lower, upper in rows:
        row = model.constraints.add().linear
        row.vars.extend(variables)
        row.coeffs.extend([1] * len(variables))
        row.domain.extend([lower, upper])
    return model


def check_model(actual, expected):
    require(actual == expected, "complete model differs from independent reconstruction")


def model_controls(model, expected, cuts):
    mutations = []

    def add(name, mutation):
        damaged = copy.deepcopy(model)
        mutation(damaged)
        mutations.append((name, damaged))

    add("missing variable", lambda p: p.variables.pop())
    add("duplicate block identity", lambda p: setattr(p.variables[1], "name", p.variables[0].name))
    add("nonBoolean variable", lambda p: p.variables[0].domain.__setitem__(1, 2))
    add("missing coverage row", lambda p: p.constraints.pop(100))
    add("wrong cardinality", lambda p: p.constraints[0].linear.domain.__setitem__(0, 63))
    add("wrong coefficient", lambda p: p.constraints[1].linear.coeffs.__setitem__(0, -1))
    add("wrong support", lambda p: p.constraints[1].linear.vars.__setitem__(0, 527))
    add("vacuous coverage", lambda p: p.constraints[1].linear.domain.__setitem__(0, 0))
    add("extra upper bound", lambda p: p.constraints[1].linear.domain.__setitem__(1, 1))
    add("enforced coverage", lambda p: p.constraints[1].enforcement_literal.append(0))
    add("extra hint", lambda p: p.solution_hint.vars.append(0))
    add("extra strategy", lambda p: p.search_strategy.add())
    add("extra row name", lambda p: setattr(p.constraints[1], "name", "altered"))
    if cuts:
        add("degree equality20", lambda p: p.constraints[561].linear.domain.__setitem__(0, 20))
        add("weakened pair cut", lambda p: p.constraints[577].linear.domain.__setitem__(0, 4))
        add("stronger pair cut", lambda p: p.constraints[577].linear.domain.__setitem__(0, 6))
    result = []
    for name, damaged in mutations:
        try:
            check_model(damaged, expected)
        except ValueError as error:
            result.append({"name": name, "rejected": str(error)})
        else:
            raise ValueError("damaged model accepted: " + name)
    return result


def main():
    prior = json.loads((PRIOR / "construction-audit.json").read_text())
    require(prior["passed"] and sha(PRIOR / "pool.json") == prior["pool_sha256"], "prior pool gate")
    require(sha(PRIOR / "construct.py") == prior["source_sha256"], "prior constructor gate")
    independent = json.loads((PRIOR / "pool.json").read_text())
    expected_pool = reconstruct(list(map(tuple, independent["lines"])))
    manifest = json.loads((INPUT / "manifest.json").read_text())
    require(sha(INPUT / "build.py") == manifest["builder_sha256"], "builder hash")
    pool_path = ROOT / manifest["pool"]
    require(sha(pool_path) == manifest["pool_sha256"], "pool hash")
    pool = json.loads(pool_path.read_text())
    require(pool == expected_pool, "complete pool payload differs")
    pool_controls = []
    for field in ["pool", "supports", "point_rows", "pair_rows", "affine_lines"]:
        damaged = copy.deepcopy(pool)
        damaged[field].pop()
        require(damaged != expected_pool, "damaged pool accepted")
        pool_controls.append({"removed_from": field, "rejected": True})
    reports = []
    protos = []
    for entry in manifest["models"]:
        require(entry["name"] in ["base", "incidence-cuts"], "unknown model")
        path = ROOT / entry["path"]
        require(sha(path) == entry["sha256"], "model hash")
        proto = text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())
        cuts = entry["name"] == "incidence-cuts"
        expected = expected_model(expected_pool, cuts)
        check_model(proto, expected)
        controls = model_controls(proto, expected, cuts)
        reports.append(
            {
                "name": entry["name"],
                "model_sha256": sha(path),
                "passed": True,
                "variables": len(proto.variables),
                "rows": len(proto.constraints),
                "damaged_controls": controls,
            }
        )
        protos.append(proto)
    require([r["name"] for r in reports] == ["base", "incidence-cuts"], "model ordering")
    stripped = copy.deepcopy(protos[1])
    del stripped.constraints[561:]
    require(stripped == protos[0], "cuts changed the base model")
    report = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(INPUT / "manifest.json"),
        "pool_sha256": sha(pool_path),
        "prior_pool_sha256": sha(PRIOR / "pool.json"),
        "prior_gate_sha256": sha(PRIOR / "construction-audit.json"),
        "models": reports,
        "pool_controls": pool_controls,
        "universe_blocks": 4368,
        "caps": 288,
        "extensions": 240,
        "base_unchanged_after_stripping_cuts": True,
        "cut_argument": "Each pair needs ceil(14/3)=5 blocks. For a point, 15 pair "
        "incidences sum to four times its degree; hence ceil(75/4)=19.",
        "solver_calls": 0,
        "scope": "Exact models within the 528-block pool only. No symmetry, fixed "
        "degree or cap/extension split. No global exclusion or proof claim.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "model_controls": sum(len(r["damaged_controls"]) for r in reports),
                "pool_controls": len(pool_controls),
            }
        )
    )


if __name__ == "__main__":
    main()
