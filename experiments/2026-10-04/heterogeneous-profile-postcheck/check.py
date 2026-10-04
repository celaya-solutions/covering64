# Document:    Independent Profile Pool Outcome Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e0c3e87db96c10a06ffa2025360050643e00bdf9deaebeae4eaf3e2287400404
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read saved artifacts only; independently count and verify every saved state."""

import hashlib
import json
import re
import subprocess
from collections import Counter
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = ROOT / "experiments/2026-10-04/heterogeneous-profile-pool"
RAW = ROOT / "experiments/scratch/heterogeneous-profile-pool-20261004"
BLOCKS = list(combinations(range(1, 17), 5))
TRIPLES = list(combinations(range(1, 17), 3))
RANK = {b: i for i, b in enumerate(BLOCKS)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def parse_seed(path):
    rows = [tuple(map(int, row.split())) for row in Path(path).read_text().splitlines()
            if row.strip() and not row.startswith("#")]
    require(len(rows) == len(set(rows)) == 64, "cardinality or duplicates")
    require(all(row in RANK for row in rows), "noncanonical or malformed block")
    return sorted(RANK[row] for row in rows)


def recount(ids):
    require(len(ids) == len(set(ids)) == 64, "bad selected cardinality")
    require(all(isinstance(i, int) and 0 <= i < 4368 for i in ids), "bad block ID")
    blocks = [BLOCKS[i] for i in ids]
    coverage = Counter(t for b in blocks for t in combinations(b, 3))
    missing = [t for t in TRIPLES if coverage[t] == 0]
    heavy = [t for t in TRIPLES if coverage[t] >= 6]
    obstructions = []
    for five in combinations(heavy, 5):
        if len(set().union(*map(set, five))) == 15 and sum(coverage[t] >= 7 for t in five) >= 2:
            obstructions.append(five)
    return {
        "holes": len(missing), "missing_triples": missing,
        "degree_histogram": sorted(Counter(sum(p in b for b in blocks)
                                           for p in range(1, 17)).items()),
        "pair_histogram": sorted(Counter(sum(set(p) <= set(b) for b in blocks)
                                         for p in combinations(range(1, 17), 2)).items()),
        "triple_histogram": sorted(Counter(coverage[t] for t in TRIPLES).items()),
        "heavy_triples": [(t, coverage[t]) for t in heavy],
        "all_disjoint_five_heavy_obstructions": obstructions,
    }, coverage


def in_domain(value, domain):
    return any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2))


def check_assignment(model, values):
    require(len(values) == len(model.variables), "solution length")
    for variable, value in zip(model.variables, values, strict=True):
        require(in_domain(value, variable.domain), "variable domain")
    for index, row in enumerate(model.constraints):
        active = all(values[literal] if literal >= 0 else not values[-literal - 1]
                     for literal in row.enforcement_literal)
        if not active:
            continue
        require(row.WhichOneof("constraint") == "linear", "unexpected row type")
        value = sum(values[i] * coefficient
                    for i, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True))
        require(in_domain(value, row.linear.domain), f"linear row {index}")


def derived_assignment(model, ids, manifest):
    chosen = set(ids)
    _, coverage = recount(ids)
    values = [int(i in chosen) for i in range(4368)]
    values.extend(int(coverage[t] == 0) for t in TRIPLES)
    for variable in model.variables[4928:]:
        match = re.fullmatch(r"partition_(\d+)_triple_(\d+)_at_least_([67])", variable.name)
        require(match is not None, "unknown threshold variable")
        partition, position, threshold = map(int, match.groups())
        triple = tuple(manifest["partitions"][partition][position])
        values.append(int(coverage[triple] >= threshold))
    return values


def verify(path, label, expected):
    outputs = {}
    for name, command in [
        ("package", ["uv", "run", "covering64", "verify", str(path), "--expected-blocks", "64"]),
        ("standalone", ["uv", "run", "python", "scripts/check_cover.py", str(path),
                        "--expected-blocks", "64"]),
    ]:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        require(result.returncode == (0 if expected == 0 else 1), "verifier exit")
        require(not result.stderr, "verifier error output")
        payload = json.loads(result.stdout)
        require(payload["blocks"] == 64 and payload["valid"] == (expected == 0), "verifier shape")
        covered = payload["covered"] if name == "package" else payload["covered_subsets"]
        require(covered == 560 - expected, "verifier coverage")
        out = HERE / "verifiers" / f"{label}-{name}.json"
        out.write_text(result.stdout)
        outputs[name] = {"path": str(out.relative_to(ROOT)), "sha256": sha(out),
                         "canonical_sha256": payload["canonical_sha256"]}
    require(outputs["package"]["canonical_sha256"] == outputs["standalone"]["canonical_sha256"],
            "verifier canonical hash mismatch")
    return outputs


def main():
    (HERE / "verifiers").mkdir(exist_ok=True)
    manifest_path = PRODUCER / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    result = json.loads((PRODUCER / "result.json").read_text())
    gate_path = ROOT / "experiments/2026-10-04/heterogeneous-profile-pool-independent/gate.json"
    gate = json.loads(gate_path.read_text())
    require(gate["passed"] and gate["manifest_sha256"] == sha(manifest_path), "preparation gate")
    require(result["manifest_sha256"] == sha(manifest_path), "result manifest")
    require(sha(PRODUCER / "run.py") == manifest["source_sha256"], "producer source drift")
    checked = []
    damaged = 0
    for offset, case in enumerate(result["cases"]):
        spec = manifest["cases"][offset]
        require(case["name"] == spec["name"], "case ordering")
        model_path = ROOT / spec["model_path"]
        require(sha(model_path) == spec["model_sha256"], "model binding")
        model = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
        require([v.name for v in model.variables[:4368]] == [f"block_{i}" for i in range(4368)],
                "global block ordering")
        require([v.name for v in model.variables[4368:4928]] == [f"hole_{i}" for i in range(560)],
                "triple ordering")
        parameters_path = RAW / f"{case['name']}-parameters.pbtxt"
        parameters = text_format.Parse(
            parameters_path.read_text(), sat_parameters_pb2.SatParameters()
        )
        require(parameters.max_time_in_seconds == 60 and parameters.num_search_workers == 4,
                "solver budget")
        require(parameters.random_seed == manifest["seed"] + offset, "solver seed")
        response_path = RAW / f"{case['name']}-response.pbtxt"
        response = text_format.Parse(response_path.read_text(), cp_model_pb2.CpSolverResponse())
        require(response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL), "response status")
        values = list(response.solution)
        check_assignment(model, values)
        final_ids = [i for i in range(4368) if values[i]]
        require(values == derived_assignment(model, final_ids, manifest), "auxiliary values")
        final_path = HERE / f"{case['name']}-final-response.txt"
        final_path.write_text("".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in final_ids))
        records = [(row["path"], row["ids"], row["objective"], row["sha256"])
                   for row in case["improvements"]]
        records.append((str(final_path.relative_to(ROOT)), final_ids, int(response.objective_value),
                        sha(final_path)))
        for index, (relative, ids, objective, expected_sha) in enumerate(records):
            path = ROOT / relative
            require(sha(path) == expected_sha and parse_seed(path) == ids, "witness binding")
            require(set(ids) <= set(spec["pool"]), "pool membership")
            check_assignment(model, derived_assignment(model, ids, manifest))
            facts, coverage = recount(ids)
            require(facts["holes"] == objective, "objective recount")
            facts["partition_counts"] = [[coverage[tuple(t)] for t in p]
                                         for p in manifest["partitions"]]
            facts["core_overlaps"] = [len(set(ids) & set(core)) for core in manifest["core_rows"]]
            outputs = verify(path, f"{case['name']}-{index:02d}", objective)
            checked.append({"case": case["name"], "path": relative, "sha256": sha(path),
                            "is_final_response": index == len(records) - 1,
                            "facts": facts, "verifiers": outputs})
        for variable in (final_ids[0], 4368, 4928):
            changed = values.copy()
            changed[variable] = 1 - changed[variable]
            try:
                check_assignment(model, changed)
            except ValueError:
                damaged += 1
            else:
                raise ValueError("damaged assignment accepted")
    require(damaged == 6, "damage-control count")
    audit = {"passed": True, "source_sha256": sha(__file__), "optimization_calls": 0,
             "producer_manifest_sha256": sha(manifest_path),
             "producer_result_sha256": sha(PRODUCER / "result.json"),
             "preparation_gate_sha256": sha(gate_path), "checked_states": checked,
             "damaged_controls_rejected": damaged,
             "scope": "Every saved callback and final response. Exhaustive five-heavy-set "
                      "scan applies to each checked state only, not all potential covers."}
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "states": len(checked), "verifier_calls": 2 * len(checked),
                      "audit_sha256": sha(HERE / "audit.json")}))


if __name__ == "__main__":
    main()
