# Document:    Independent Radius Four V2 Execution Gate
# Version:     v2.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import itertools
import json
from pathlib import Path

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = ROOT / "experiments/2026-10-04/radius-four-feasibility-repair-v2"
BASE = ROOT / "experiments/2026-10-04/soft-pair-hole-priority/manifest.json"
BASE_MODEL_SHA = "b4d49337d5dc3fd330c84145817b1b00f52877924aabf6614ce4b573ddea4900"
FAMILY_SHA = "44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_model(path):
    model = cp_model.CpModel()
    assert model.proto.parse_text_format(path.read_text())
    assert not model.validate()
    return model


def parse_family(text):
    blocks = []
    for line in text.splitlines():
        if not line.strip():
            continue
        block = tuple(map(int, line.split()))
        assert len(block) == 5 and len(set(block)) == 5
        assert all(1 <= v <= 16 for v in block)
        blocks.append(tuple(sorted(block)))
    assert len(blocks) == len(set(blocks)) == 64
    return sorted(blocks)


def row_signature(row):
    assert not list(row.enforcement_literal)
    assert row.has_linear()
    return (
        dict(zip(list(row.linear.vars), list(row.linear.coeffs), strict=True)),
        list(row.linear.domain),
    )


def row_failures(model, values):
    assert len(values) == len(model.proto.variables)
    for value, variable in zip(values, model.proto.variables, strict=True):
        assert type(value) is int
        domain = list(variable.domain)
        assert any(a <= value <= b for a, b in zip(domain[::2], domain[1::2], strict=True))
    failed = []
    active = 0
    for index, row in enumerate(model.proto.constraints):
        if not all(values[lit] if lit >= 0 else 1 - values[-lit - 1]
                   for lit in row.enforcement_literal):
            continue
        active += 1
        assert row.has_linear()
        total = sum(values[i] * c for i, c in zip(
            row.linear.vars, row.linear.coeffs, strict=True))
        domain = list(row.linear.domain)
        if not any(a <= total <= b for a, b in zip(domain[::2], domain[1::2], strict=True)):
            failed.append(index)
    return failed, active


def main():
    manifest_path = PRODUCER / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    base_manifest = json.loads(BASE.read_text())
    base_path = ROOT / base_manifest["model_path"]
    model_path = ROOT / manifest["model_path"]
    parameter_path = ROOT / manifest["parameters_path"]
    assert sha(base_path) == BASE_MODEL_SHA
    assert sha(model_path) == manifest["model_sha256"]
    assert sha(parameter_path) == manifest["parameters_sha256"]
    family_path = ROOT / manifest["candidate_path"]
    assert sha(family_path) == FAMILY_SHA == manifest["candidate_sha256"]
    family = parse_family(family_path.read_text())
    universe = list(itertools.combinations(range(1, 17), 5))
    pairs = list(itertools.combinations(range(1, 17), 2))
    triples = list(itertools.combinations(range(1, 17), 3))
    lookup = {block: i for i, block in enumerate(universe)}
    ids = {lookup[block] for block in family}
    assert sorted(ids) == manifest["baseline_ids"]
    base = read_model(base_path)
    model = read_model(model_path)
    assert len(base.proto.variables) == len(model.proto.variables) == 5728
    assert len(base.proto.constraints) == 14405
    assert len(model.proto.constraints) == 14407
    assert not model.has_objective()
    assert not model.proto.has_solution_hint()
    base.clear_objective()
    base.clear_hints()
    prefix = cp_model.CpModel()
    prefix.proto.copy_from(model.proto)
    prefix.proto.constraints.clear()
    prefix.proto.constraints.extend(list(model.proto.constraints)[:14405])
    assert str(prefix.proto) == str(base.proto), "unrequested model change"
    signatures = [row_signature(row) for row in list(model.proto.constraints)[14405:]]
    expected = [({i: 1 for i in ids}, [60, (1 << 63) - 1]),
                ({i: 1 for i in range(5048, 5608)}, [-(1 << 63), 11])]
    assert all(signature in signatures for signature in expected)
    assert len(signatures) == len(expected)
    params = cp_model.CpSolver().parameters
    assert params.parse_text_format(parameter_path.read_text())
    assert params.max_time_in_seconds == 300
    assert params.num_search_workers == 4
    assert params.random_seed == 2026105201
    prior_params = cp_model.CpSolver().parameters
    assert prior_params.parse_text_format((ROOT / base_manifest["parameters_path"]).read_text())
    prior_params.random_seed = 2026105201
    assert str(prior_params) == str(params), "unrequested parameter change"
    block_sets = [set(block) for block in family]
    pair_counts = [sum(set(pair) <= block for block in block_sets) for pair in pairs]
    triple_counts = [sum(set(triple) <= block for block in block_sets) for triple in triples]
    triple_map = dict(zip(triples, triple_counts, strict=True))
    deficits = []
    for pair, count in zip(pairs, pair_counts, strict=True):
        counts = sorted((triple_map[tuple(sorted((*pair, v)))]
                         for v in range(1, 17) if v not in pair), reverse=True)
        deficits.append(max(0, 12 - 3 * count + counts[0] + counts[1]))
    values = ([int(i in ids) for i in range(4368)] + pair_counts + triple_counts
              + [int(c == 0) for c in triple_counts] + deficits)
    assert sum(c == 0 for c in triple_counts) == 12 and sum(deficits) == 29
    assert row_failures(base, values)[0] == []
    failures, active = row_failures(model, values)
    hole_row = 14405 + signatures.index(expected[1])
    assert failures == [hole_row], "baseline should fail only the eleven-hole bound"
    overlap_coeffs, overlap_domain = expected[0]
    hole_coeffs, hole_domain = expected[1]
    outside = sorted(set(range(4368)) - ids)
    for radius in range(65):
        selection = set(sorted(ids)[radius:]) | set(outside[:radius])
        total = sum(c for index, c in overlap_coeffs.items() if index in selection)
        assert (overlap_domain[0] <= total <= overlap_domain[1]) == (radius <= 4)
    for holes in range(561):
        total = sum(c for index, c in hole_coeffs.items() if index < 5048 + holes)
        assert (hole_domain[0] <= total <= hole_domain[1]) == (holes <= 11)
    bad_controls = 0
    raw = family_path.read_text()
    for damaged in [raw + raw.splitlines()[0] + "\n", "", raw.replace("1", "17", 1)]:
        try:
            parse_family(damaged)
        except (AssertionError, ValueError):
            bad_controls += 1
    assert bad_controls == 3
    for category in ("sources", "input_files"):
        for path, expected_sha in manifest.get(category, {}).items():
            assert sha(ROOT / path) == expected_sha, path
    review_path = ROOT / "experiments/2026-10-04/radius-four-runner-review/review.json"
    review = json.loads(review_path.read_text())
    assert review["passed"] is True and review["decision"] == "RUNNER_GO"
    assert review["optimizer_calls"] == 0 and review["unresolved_issues"] == []
    assert review["runner_sha256"] == sha(PRODUCER / "execute.py")
    assert review["producer_manifest_sha256"] == sha(manifest_path)
    assert review["producer_controls_sha256"] == sha(PRODUCER / "runner-controls.json")
    for path, expected_sha in review["files"].items():
        assert sha(ROOT / path) == expected_sha, path
    scan_path = ROOT / "experiments/2026-10-04/weak-pair-two-swap-scan-v2/result.json"
    scan = json.loads(scan_path.read_text())
    assert scan["validation_passed"] is True
    assert scan["final"]["best_rank"][0] >= 12
    assert scan["cover_found"] is False
    gate = {
        "passed": True, "decision": "GO", "manifest_sha256": sha(manifest_path),
        "model_sha256": sha(model_path), "parameters_sha256": sha(parameter_path),
        "runner_sha256": sha(PRODUCER / "execute.py"), "checker_sha256": sha(Path(__file__)),
        "baseline_family_sha256": FAMILY_SHA, "baseline_holes": 12,
        "baseline_D2max": 29, "baseline_fails_only_new_hole_bound": True,
        "unchanged_prefix_variables": 5728, "unchanged_prefix_rows": 14405,
        "new_rows": 2, "active_baseline_rows": active,
        "radius_row_scalar_controls": 65, "hole_row_scalar_controls": 561,
        "malformed_family_controls": bad_controls,
        "controls_are_not_cover_witnesses": True, "optimizer_calls": 0,
        "runner_review_sha256": sha(review_path),
        "two_swap_terminal_sha256": sha(scan_path),
        "fallback_condition_met": True,
        "scope": "At most four replacements of the pinned family; no global inference",
    }
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    print(json.dumps(gate))


if __name__ == "__main__":
    main()
