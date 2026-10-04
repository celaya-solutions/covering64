# Document:    Independent Heterogeneous Pool Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      bf0775a8534dde4738dd172bcc61c345014b82883c7811519818dfdd7b972e68
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild both complete models and validate saved inputs without solving."""

import ast
import importlib.util
import json
import random
import subprocess
import tempfile
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TARGET = ROOT / "experiments/2026-10-04/heterogeneous-pool"
MANIFEST_SHA = "14667a9bde607660cc2bc4f2d38dc6464ae8ab975559b5f1e0b91a2b0d15564d"
BLOCKS = list(combinations(range(1, 17), 5))
RANK = {block: i for i, block in enumerate(BLOCKS)}
TRIPLES = list(combinations(range(1, 17), 3))
SUPPORT = [
    sorted(
        RANK[tuple(sorted(t + extra))]
        for extra in combinations([point for point in range(1, 17) if point not in t], 2)
    )
    for t in TRIPLES
]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


def parse_seed(path):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64
    assert all(b in RANK for b in blocks)
    return sorted(RANK[b] for b in blocks)


def profile(ids):
    blocks = [BLOCKS[i] for i in ids]
    counts = Counter(t for block in blocks for t in combinations(block, 3))
    degrees = Counter(point for block in blocks for point in block)
    pairs = Counter(pair for block in blocks for pair in combinations(block, 2))
    return {
        "holes": [i for i, triple in enumerate(TRIPLES) if counts[triple] == 0],
        "degree_histogram": [
            [n, c] for n, c in sorted(Counter(degrees[p] for p in range(1, 17)).items())
        ],
        "pair_histogram": [
            [n, c]
            for n, c in sorted(Counter(pairs[p] for p in combinations(range(1, 17), 2)).items())
        ],
        "triple_histogram": [
            [n, c] for n, c in sorted(Counter(counts[t] for t in TRIPLES).items())
        ],
    }


def expected_model(pool, hint):
    """Populate every protobuf field independently; do not call the runner builder."""
    model = cp_model.CpModel()
    proto = model.proto
    for i in range(4928):
        var = proto.variables.add()
        var.name = f"block_{i}" if i < 4368 else f"hole_{i - 4368}"
        var.domain.extend([0, 1])
    rows = [
        (list(range(4368)), [64, 64], []),
        ([i for i in range(4368) if i not in set(pool)], [0, 0], []),
    ]
    for i, support in enumerate(SUPPORT):
        rows.extend(
            [(support, [1, 9223372036854775807], [-4369 - i]), (support, [0, 0], [4368 + i])]
        )
    for variables, domain, enforcement in rows:
        row = proto.constraints.add()
        row.linear.vars.extend(variables)
        row.linear.coeffs.extend([1] * len(variables))
        row.linear.domain.extend(domain)
        row.enforcement_literal.extend(enforcement)
    proto.objective.vars.extend(range(4368, 4928))
    proto.objective.coeffs.extend([1] * 560)
    proto.objective.scaling_factor = 1
    missing = set(profile(hint)["holes"])
    proto.solution_hint.vars.extend(range(4928))
    proto.solution_hint.values.extend(
        [int(i in set(hint)) for i in range(4368)] + [int(i in missing) for i in range(560)]
    )
    return model


def check_model(model, pool, hint):
    assert not model.validate(), model.validate()
    expected = expected_model(pool, hint)
    assert str(model.proto) == str(expected.proto), "complete protobuf differs"
    # Check the complete hinted assignment against every enforced linear row.
    values = list(model.proto.solution_hint.values)
    for row in model.proto.constraints:
        active = all(
            values[lit] if lit >= 0 else not values[-lit - 1] for lit in row.enforcement_literal
        )
        if active:
            total = sum(
                values[v] * c for v, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            low, high = row.linear.domain
            assert low <= total <= high
    assert sum(values[4368:]) == 3


def reject(call):
    try:
        call()
    except (AssertionError, ValueError, KeyError):
        return True
    raise AssertionError("damaged control accepted")


def main():
    manifest_path = TARGET / "manifest.json"
    assert digest(manifest_path) == MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text())
    source_path = TARGET / "run.py"
    assert digest(source_path) == manifest["source_sha256"]
    assert manifest["ortools_version"] == ortools.__version__
    assert manifest["budget"] == {"cases": 2, "seconds_per_case": 30, "workers": 4}
    assert manifest["seed"] == 2026104091
    assert len(manifest["sources"]) == 10
    assert [c["name"] for c in manifest["cases"]] == ["elite", "expanded"]
    assert not (ROOT / "experiments/scratch/heterogeneous-pool-20261004/start.json").exists()
    # Inspect the actual executable solver settings, with no solver invocation.
    tree = ast.parse(source_path.read_text())
    run = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run"
    )
    assignments = {
        ast.unparse(n.targets[0]): ast.unparse(n.value)
        for n in ast.walk(run)
        if isinstance(n, ast.Assign)
    }
    assert assignments["solver.parameters.max_time_in_seconds"] == "30"
    assert assignments["solver.parameters.num_search_workers"] == "4"
    assert assignments["solver.parameters.random_seed"] == "SEED + offset"
    solves = [
        n
        for n in ast.walk(run)
        if isinstance(n, ast.Call) and ast.unparse(n.func) == "solver.solve"
    ]
    assert len(solves) == 1
    receipts = []
    sets = []
    profiles = []
    for source in manifest["sources"]:
        path = ROOT / source["path"]
        assert digest(path) == source["sha256"]
        ids = parse_seed(path)
        assert ids == source["ids"]
        counted = profile(ids)
        assert all(source[k] == value for k, value in counted.items())
        sets.append(set(ids))
        profiles.append(counted)
        for label, prefix in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
        ]:
            proc = subprocess.run(
                prefix + [str(path), "--expected-blocks", "64"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert proc.returncode == 1 and not proc.stderr
            report = json.loads(proc.stdout)
            assert report["blocks"] == 64 and not report["valid"]
            assert report["canonical_sha256"] == digest(path)
            assert report["uncovered"] == [list(TRIPLES[i]) for i in counted["holes"]]
            output = HERE / f"{path.stem}-{label}.json"
            output.write_text(proc.stdout)
            receipts.append({"path": str(output.relative_to(ROOT)), "sha256": digest(output)})
    assert len({tuple(sorted(s)) for s in sets}) == 10
    elite = set.union(*sets)
    assert len(elite) == 277
    extra = random.Random(2026104091).sample(sorted(set(range(4368)) - elite), 60)
    assert extra == manifest["random_additions"]
    assert len(set(extra)) == 60 and not (set(extra) & elite)
    hint = manifest["hint"]
    assert hint == manifest["sources"][0]["ids"]
    assert len(profile(hint)["holes"]) == 3
    model_reports = []
    models = []
    for case, expected_pool in zip(manifest["cases"], [elite, elite | set(extra)], strict=True):
        pool = case["pool"]
        assert pool == sorted(expected_pool)
        model_path = ROOT / case["model_path"]
        assert digest(model_path) == case["model_sha256"]
        model = cp_model.CpModel()
        model.proto.parse_text_format(model_path.read_text())
        check_model(model, pool, hint)
        histogram = [
            [n, c] for n, c in sorted(Counter(len(set(s) & expected_pool) for s in SUPPORT).items())
        ]
        assert histogram == case["support_histogram"]
        assert all(s <= expected_pool for s in sets)
        models.append(model)
        model_reports.append(
            {
                "name": case["name"],
                "pool_size": len(pool),
                "variables": 4928,
                "linear_rows": 1122,
                "hint_holes": 3,
                "support_histogram": histogram,
                "model_sha256": digest(model_path),
            }
        )
    controls = []
    mutations = [
        ("cardinality", lambda p: p.constraints[0].linear.domain.__setitem__(0, 63)),
        ("membership_coefficient", lambda p: p.constraints[1].linear.coeffs.__setitem__(0, 0)),
        ("membership_domain", lambda p: p.constraints[1].linear.domain.__setitem__(1, 1)),
        ("coverage_coefficient", lambda p: p.constraints[2].linear.coeffs.__setitem__(0, 0)),
        ("coverage_lower", lambda p: p.constraints[2].linear.domain.__setitem__(0, 0)),
        ("hole_zero_domain", lambda p: p.constraints[3].linear.domain.__setitem__(1, 1)),
        ("hole_polarity", lambda p: p.constraints[2].enforcement_literal.__setitem__(0, 4368)),
        ("hint_block", lambda p: p.solution_hint.values.__setitem__(0, 1)),
        ("hint_hole", lambda p: p.solution_hint.values.__setitem__(4368, 1)),
        ("objective_weight", lambda p: p.objective.coeffs.__setitem__(0, 2)),
        ("variable_domain", lambda p: p.variables[0].domain.__setitem__(1, 2)),
        ("block_order", lambda p: setattr(p.variables[0], "name", "block_1")),
    ]
    for name, mutate in mutations:
        damaged = cp_model.CpModel()
        damaged.proto.copy_from(models[0].proto)
        mutate(damaged.proto)
        assert reject(lambda: check_model(damaged, sorted(elite), hint))
        controls.append(name)
    spec = importlib.util.spec_from_file_location("gated_heterogeneous_runner", source_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original = (ROOT / manifest["sources"][0]["path"]).read_text().splitlines()
    seed_mutations = {
        "duplicate_block": [original[0]] + original[:-1],
        "missing_block": original[:-1],
        "extra_block": original + [original[0]],
        "duplicate_label": ["1 1 2 3 4"] + original[1:],
        "outside_label": ["1 2 3 4 17"] + original[1:],
        "short_block": ["1 2 3 4"] + original[1:],
        "noninteger_label": ["1 2 3 4 x"] + original[1:],
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "damaged.txt"
        for name, lines in seed_mutations.items():
            path.write_text("\n".join(lines) + "\n")
            assert reject(lambda: parse_seed(path))
            assert reject(lambda: runner.read_seed(path))
            controls.append(name)
    # Confirm the runner builder reproduces the saved models, still without solving.
    for case, saved in zip(manifest["cases"], models, strict=True):
        built, _, _ = runner.build_model(case["pool"], hint)
        assert str(built.proto) == str(saved.proto)
    gate = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "source_sha256": digest(source_path),
        "checker_sha256": digest(Path(__file__)),
        "optimizer_calls": 0,
        "models": model_reports,
        "verifier_receipts": receipts,
        "damaged_controls_rejected": controls,
        "source_holes": [len(p["holes"]) for p in profiles],
        "source_degree_histograms": [p["degree_histogram"] for p in profiles],
        "pairwise_common_blocks": [[len(a & b) for b in sets] for a in sets],
        "random_additions_replayed": True,
        "budget": manifest["budget"],
        "scope": "Two restricted block pools only; no unrestricted infeasibility claim.",
    }
    dump(HERE / "gate.json", gate)
    print(
        json.dumps(
            {"passed": True, "controls": len(controls), "sha256": digest(HERE / "gate.json")}
        )
    )


if __name__ == "__main__":
    main()
