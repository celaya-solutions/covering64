# Document:    Independent Heterogeneous Profile Pool Preparation Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Reconstruct both complete models, threshold truth tables and hinted assignments."""

import ast
import importlib.util
import itertools as it
import json
import subprocess
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "heterogeneous-profile-pool"
spec = importlib.util.spec_from_file_location(
    "independent_profile_core", DAY / "heterogeneous-core-pool-independent/check.py"
)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
basis = core.basis
LOW, HIGH = -(2**63), 2**63 - 1


def read(path):
    return json.loads(Path(path).read_text())


def expected(pool, hint, cores, partitions):
    model = core.expected(pool, hint, cores)
    proto = model.proto
    assert len(proto.variables) == 4928 and len(proto.constraints) == 1124
    chosen = set(hint)
    for p, partition in enumerate(partitions):
        for position, triple in enumerate(partition):
            support = basis.SUPPORT[basis.TRIPLES.index(tuple(triple))]
            for threshold in (6, 7):
                index = 4928 + 10 * p + 2 * position + threshold - 6
                var = proto.variables.add()
                var.name = f"partition_{p}_triple_{position}_at_least_{threshold}"
                var.domain.extend([0, 1])
                for domain, literal in (([threshold, HIGH], index),
                                        ([LOW, threshold - 1], -index - 1)):
                    row = proto.constraints.add()
                    row.linear.vars.extend(support)
                    row.linear.coeffs.extend([1] * 78)
                    row.linear.domain.extend(domain)
                    row.enforcement_literal.append(literal)
                proto.solution_hint.vars.append(index)
                proto.solution_hint.values.append(int(len(chosen & set(support)) >= threshold))
        row = proto.constraints.add()
        row.linear.vars.extend(range(4928 + 10 * p, 4938 + 10 * p))
        row.linear.coeffs.extend([5, 1] * 5)
        row.linear.domain.extend([LOW, 26])
    return model


def check_model(model, pool, hint, cores, partitions):
    assert not model.validate(), model.validate()
    assert str(model.proto) == str(expected(pool, hint, cores, partitions).proto)
    assert len(model.proto.variables) == 4948 and len(model.proto.constraints) == 1166
    assert list(model.proto.solution_hint.vars) == list(range(4948))
    values = list(model.proto.solution_hint.values)
    assert sum(values[:4368]) == 64 and sum(values[4368:4928]) == 17
    for row in model.proto.constraints:
        active = all(values[lit] if lit >= 0 else not values[-lit - 1]
                     for lit in row.enforcement_literal)
        if active:
            value = sum(values[v] * c for v, c in
                        zip(row.linear.vars, row.linear.coeffs, strict=True))
            assert row.linear.domain[0] <= value <= row.linear.domain[1]


def truth_tables(saved, partitions):
    local = []
    for count in range(79):
        valid = [[int(six), int(seven)] for six, seven in it.product((False, True), repeat=2)
                 if (count >= 6) == six and (count >= 7) == seven]
        assert len(valid) == 1
        local.append({"count": count, "unique_indicators": valid[0]})
    assert saved["local_counts"] == local
    reports = []
    for name, partition in partitions:
        assert len(partition) == 5 and len({p for triple in partition for p in triple}) == 15
        assert all(tuple(triple) in basis.TRIPLES for triple in partition)
        table = []
        mismatches = dict.fromkeys(
            ("bound_25", "bound_27", "six_coefficient_4", "unconditional_seven_cap"), 0
        )
        for categories in it.product(range(3), repeat=5):
            counts = [5 + category for category in categories]
            six, seven = [int(c >= 6) for c in counts], [int(c >= 7) for c in counts]
            forbidden = min(counts) >= 6 and sum(c >= 7 for c in counts) >= 2
            score = sum(5 * a + b for a, b in zip(six, seven, strict=True))
            assert (score <= 26) == (not forbidden)
            table.append({"category_representatives": counts, "six": six, "seven": seven,
                          "weighted_sum": score, "forbidden": forbidden})
            for label, value in {
                "bound_25": score <= 25, "bound_27": score <= 27,
                "six_coefficient_4": 4 * sum(six) + sum(seven) <= 26,
                "unconditional_seven_cap": sum(seven) <= 1
            }.items():
                mismatches[label] += value != (not forbidden)
        assert table == saved["table"]
        assert mismatches == saved["damaged_rule_mismatches"]
        forbidden_count = sum(row["forbidden"] for row in table)
        assert forbidden_count == saved["forbidden_cases"] == 26
        assert len(table) == saved["per_partition_cases"] == 243
        assert len(table) - forbidden_count == saved["allowed_cases"] == 217
        reports.append({"partition": name, "cases": 243, "forbidden": 26, "allowed": 217})
    return reports


def main():
    assert not (HERE / "gate.json").exists()
    manifest = read(SOURCE / "manifest.json")
    assert basis.digest(SOURCE / "run.py") == manifest["source_sha256"]
    assert basis.digest(SOURCE / "threshold-truth-table.json") == manifest[
        "threshold_truth_table_sha256"
    ]
    for path, digest in manifest["input_files"].items():
        assert basis.digest(ROOT / path) == digest
    previous = read(DAY / "heterogeneous-core-pool/manifest.json")
    prior_gate = read(DAY / "heterogeneous-core-pool-independent/gate.json")
    prior_post = read(DAY / "heterogeneous-core-pool-independent/postcheck.json")
    assert prior_gate["passed"] and prior_post["passed"]
    assert prior_gate["manifest_sha256"] == basis.digest(
        DAY / "heterogeneous-core-pool/manifest.json"
    )
    for field in ("sources", "core_rows", "random_additions", "seed", "ortools_version"):
        assert manifest[field] == previous[field]
    for source in manifest["sources"]:
        path = ROOT / source["path"]
        assert basis.digest(path) == source["sha256"]
        assert basis.parse_seed(path) == source["ids"]
        assert all(source[k] == value for k, value in basis.profile(source["ids"]).items())
    screen_path = DAY / "heterogeneous-five-heavy-screen/audit.json"
    screen = read(screen_path)
    original_partition = [[1, 3, 6], [2, 14, 15], [4, 8, 10], [5, 13, 16], [9, 11, 12]]
    mapped_partition = [sorted(core.MAPS[1][point - 1] for point in triple)
                        for triple in original_partition]
    assert manifest["partitions"] == screen["partitions"] == [
        original_partition, mapped_partition
    ]
    partitions = manifest["partitions"]
    names = ["original_saved_core", "mapped_saved_core"]
    assert manifest["partition_names"] == names
    assert manifest["partition_triple_ids"] == [
        [basis.TRIPLES.index(tuple(triple)) for triple in row] for row in partitions
    ]
    assert manifest["threshold_indicators"] == [
        {"variable_id": 4928 + 10 * p + 2 * i + threshold - 6,
         "partition": p, "position": i, "triple": triple, "threshold": threshold}
        for p, partition in enumerate(partitions) for i, triple in enumerate(partition)
        for threshold in (6, 7)
    ]
    assert manifest["profile_rule"] == {
        "six_coefficient": 5, "seven_coefficient": 1, "upper_bound": 26
    }
    for path, digest in manifest["proof_files"].items():
        assert basis.digest(ROOT / path) == digest
    proof_dir = ROOT / "experiments/2026-10-03/five-heavy-triples"
    proof = read(proof_dir / "result.json")
    assert proof["complete"] and proof["assignments_checked"] == 27040
    assert proof["feasible_two_sevenfold_assignments"] == 0
    assert proof["source_sha256"] == basis.digest(proof_dir / "check.py")
    tables = truth_tables(read(SOURCE / "threshold-truth-table.json"), zip(names, partitions))
    hint = manifest["hint"]
    assert hint == basis.parse_seed(ROOT / manifest["hint_source_path"])
    assert manifest["hint_source_path"].endswith("/g5-raw-17.txt")
    assert len(basis.profile(hint)["holes"]) == 17
    counts = [[len(set(hint) & set(basis.SUPPORT[basis.TRIPLES.index(tuple(t))])) for t in row]
              for row in partitions]
    assert counts == manifest["hint_partition_counts"] == [[1, 1, 1, 1, 2], [7, 7, 7, 7, 0]]
    reports, models = [], []
    for case, old_case, pool_size in zip(manifest["cases"], previous["cases"], (277, 337),
                                        strict=True):
        assert case["name"] == old_case["name"] and case["pool"] == old_case["pool"]
        assert case["support_histogram"] == old_case["support_histogram"]
        assert len(case["pool"]) == pool_size
        assert basis.digest(ROOT / case["model_path"]) == case["model_sha256"]
        model = cp_model.CpModel()
        model.proto.parse_text_format((ROOT / case["model_path"]).read_text())
        check_model(model, case["pool"], hint, manifest["core_rows"], partitions)
        models.append(model)
        reports.append({"name": case["name"], "pool_size": pool_size, "variables": 4948,
                        "rows": 1166, "hint_holes": 17, "model_sha256": case["model_sha256"]})
    tree = ast.parse((SOURCE / "run.py").read_text())
    run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    assignments = {ast.unparse(n.targets[0]): ast.unparse(n.value) for n in ast.walk(run)
                   if isinstance(n, ast.Assign)}
    assert assignments["solver.parameters.max_time_in_seconds"] == "60"
    assert assignments["solver.parameters.num_search_workers"] == "4"
    assert assignments["solver.parameters.random_seed"] == "SEED + offset"
    assert manifest["seed"] == 2026104091
    assert manifest["budget"] == {"cases": 2, "seconds_per_case": 60, "workers": 4}
    controls = []
    for label, mutate in (
        ("threshold", lambda p: p.constraints[1124].linear.domain.__setitem__(0, 7)),
        ("reverse_literal", lambda p: p.constraints[1125].enforcement_literal.__setitem__(0, 4928)),
        ("profile_bound", lambda p: p.constraints[1144].linear.domain.__setitem__(1, 27)),
        ("hint_indicator", lambda p: p.solution_hint.values.__setitem__(4928, 1)),
    ):
        damaged = cp_model.CpModel()
        damaged.proto.parse_text_format(str(models[0].proto))
        mutate(damaged.proto)
        assert basis.reject(lambda: check_model(
            damaged, manifest["cases"][0]["pool"], hint, manifest["core_rows"], partitions
        ))
        controls.append(label)
    verifiers = []
    for label, command in (("package", ["uv", "run", "covering64", "verify"]),
                           ("standalone", ["uv", "run", "python", "scripts/check_cover.py"])):
        proc = subprocess.run(command + [str(ROOT / manifest["hint_source_path"]),
                                         "--expected-blocks", "64"], cwd=ROOT,
                              capture_output=True, text=True, check=False)
        assert proc.returncode == 1 and not proc.stderr
        checked = json.loads(proc.stdout)
        assert not checked["valid"] and checked["blocks"] == 64
        uncovered = [list(basis.TRIPLES[i]) for i in basis.profile(hint)["holes"]]
        assert checked["uncovered"] == uncovered
        (HERE / f"hint-{label}.json").write_text(proc.stdout)
        verifiers.append({"name": label, "sha256": basis.digest(HERE / f"hint-{label}.json")})
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": basis.digest(Path(__file__)),
        "manifest_sha256": basis.digest(SOURCE / "manifest.json"),
        "source_sha256": basis.digest(SOURCE / "run.py"), "models": reports,
        "truth_tables": tables, "local_threshold_counts_checked": 79,
        "damaged_controls_rejected": controls, "hint_verifiers": verifiers,
        "scope": "Two frozen finite pools with the two existing core exclusions and two named "
        "five-heavy partition restrictions. No unrestricted or all-partitions exclusion claim.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
