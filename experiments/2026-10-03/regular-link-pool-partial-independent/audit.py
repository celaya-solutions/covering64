# Document:    Independent Partial Pooled Link Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      27c462d1ccdccde39ea8cf7ddef4f7857065a3e333cb3451133b3a537be81df9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit the archived fixed-source partial-cover pool, without solving it."""

import gzip
import hashlib
import importlib.util
import itertools as it
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "experiments/scratch/regular-link-pool-partial-20261003"
SUPPORT = ROOT / "experiments/2026-10-03/regular-link-pool-independent/audit.py"
SPEC = importlib.util.spec_from_file_location("independent_pool_support", SUPPORT)
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
require, canonical, sha = BASE.require, BASE.canonical, BASE.sha


def check_model(families, source, pair_counts, missing, metadata):
    count = len(families)
    fixed = metadata["fixed_family_index"]
    require(families[fixed] == source, "fixed family index mismatch")
    universe = list(it.combinations(range(1, 17), 5))
    outside_ids = [i for i, b in enumerate(universe) if b[0] >= 4]
    outside = [tuple(x - 4 for x in universe[i]) for i in outside_ids]
    first_hole = count + 1287
    expected_vars = [(f"family_{i}", [0, 2]) for i in range(count)]
    expected_vars += [(f"block_{i}", [0, 1]) for i in outside_ids]
    expected_vars += [(f"uncovered_{i}", [0, 1]) for i in range(286)]
    model = cp_model.CpModel()
    require(model.proto.parse_text_format((ARCHIVE / "model.pbtxt").read_text()), "parse failed")
    require([(v.name, list(v.domain)) for v in model.proto.variables] == expected_vars,
            "variable domains or ordering differ")
    rows = [({i: 1 for i in range(count)}, (2, 2), []),
            ({count + i: 1 for i in range(1287)}, (18, 18), [])]
    family_triples = [{t for b in family for t in it.combinations(b, 3)} for family in families]
    for tid, triple in enumerate(BASE.TRIPLES):
        coefficients = {i: 1 for i, ts in enumerate(family_triples) if triple in ts}
        coefficients.update({count + i: 1 for i, b in enumerate(outside) if set(triple) <= set(b)})
        constant = int(triple in family_triples[fixed])
        hole = first_hole + tid
        rows.extend([(coefficients, (-constant, -constant), [hole]),
                     (coefficients, (1 - constant, BASE.LIMIT), [-hole - 1])])
    for point in range(13):
        degree = 6 if point == 0 else 7
        rows.append(({count + i: 1 for i, b in enumerate(outside) if point in b},
                     (degree, degree), []))
    for pair in BASE.PAIRS:
        coefficients = {i: values[pair] for i, values in enumerate(pair_counts) if values[pair]}
        coefficients.update({count + i: 1 for i, b in enumerate(outside) if set(pair) <= set(b)})
        lower = 5 - int(pair in BASE.EDGES) - pair_counts[fixed][pair]
        rows.append((coefficients, (lower, BASE.LIMIT), []))
    for spoke in [(0, 1), (0, 2)]:
        lower = 1 - int(spoke in missing[fixed])
        rows.append(({i: 1 for i, holes in enumerate(missing) if spoke in holes},
                     (lower, BASE.LIMIT), []))
    require(len(rows) == len(model.proto.constraints) == 667, "row count mismatch")
    for index, (actual, (coefficients, bounds, enforcement)) in enumerate(
            zip(model.proto.constraints, rows)):
        require(dict(zip(actual.linear.vars, actual.linear.coeffs)) == coefficients
                and len(actual.linear.vars) == len(coefficients)
                and list(actual.linear.domain) == list(bounds)
                and list(actual.enforcement_literal) == enforcement,
                f"model row mismatch {index}")
    objective = model.proto.objective
    require(dict(zip(objective.vars, objective.coeffs)) ==
            {first_hole + i: 1 for i in range(286)}, "wrong hole objective")
    require(objective.offset == 0 and objective.scaling_factor == 1, "wrong objective direction")
    # Exhaustive arithmetic truth table for both fixed-source constant cases.
    truth_table = []
    for constant, remaining, flag in it.product(range(2), range(6), range(2)):
        represented = ((remaining == -constant) if flag else (remaining >= 1 - constant))
        require(represented == (flag == (remaining + constant == 0)), "hole iff mismatch")
        truth_table.append([constant, remaining, flag, represented])
    return {"rows": 667, "variables": len(expected_vars), "fixed_family_index": fixed,
            "fixed_family_count": 1, "remaining_family_count": 2, "outside_block_count": 18,
            "objective_hole_variables": 286, "hole_truth_table": truth_table,
            "exact_hole_flag_reification": True}


def candidate_check():
    path = ARCHIVE / "candidate.txt"
    result_path = ARCHIVE / "result.json"
    if not result_path.exists():
        return {"state": "run_still_in_progress"}
    result = json.loads(result_path.read_text())
    if not path.exists():
        require(result["status"] not in ["OPTIMAL", "FEASIBLE"], "missing feasible candidate")
        return {"state": "no_feasible_candidate", "solver_status": result["status"]}
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    require(len(blocks) == len(set(blocks)) == 64, "candidate block count or duplicates")
    require(all(len(b) == len(set(b)) == 5 and tuple(sorted(b)) == b
                and all(1 <= p <= 16 for p in b) for b in blocks), "malformed candidate")
    require(Counter(p for b in blocks for p in b) == {p: 20 for p in range(1, 17)},
            "candidate degrees differ")
    covered = {t for b in blocks for t in it.combinations(b, 3)}
    absent = sorted(set(it.combinations(range(1, 17), 3)) - covered)
    require(len(absent) == result["holes"], "reported holes differ")
    checks = []
    for prefix in [["uv", "run", "covering64", "verify"],
                   [sys.executable, "scripts/check_cover.py"]]:
        process = subprocess.run(prefix + [str(path), "--expected-blocks", "64"], cwd=ROOT,
                                 capture_output=True, text=True, check=False)
        data = json.loads(process.stdout)
        require(process.returncode == int(bool(absent)), "verifier return code differs")
        require(sorted(map(tuple, data["uncovered"])) == absent, "verifier holes differ")
        checks.append(data)
    require(checks[0]["canonical_sha256"] == checks[1]["canonical_sha256"], "hash disagreement")
    return {"state": "independently_checked", "holes": len(absent), "blocks": 64,
            "all_degrees": 20, "canonical_sha256": checks[0]["canonical_sha256"],
            "checks": checks}


def main():
    metadata = json.loads((ARCHIVE / "metadata.json").read_text())
    for filename, key in [("source.py", "source_sha256"), ("helper.py", "helper_sha256"),
                          ("pool.json.gz", "pool_sha256"), ("model.pbtxt", "model_sha256")]:
        require(sha(ARCHIVE / filename) == metadata[key], "archive hash mismatch")
    pool = json.loads(gzip.decompress((ARCHIVE / "pool.json.gz").read_bytes()))
    families = [canonical(family) for family in pool["families"]]
    source = canonical(pool["source_template"])
    inspected = [BASE.inspect(family) for family in families]
    pair_counts, missing = zip(*inspected)
    expected, first_count = BASE.normalized_maps(source)
    swapped = canonical(tuple({0: 3, 3: 0, 1: 4, 4: 1}.get(x, x) for x in b) for b in source)
    second, second_count = BASE.normalized_maps(swapped)
    require(not expected.intersection(second), "two source-edge map families unexpectedly overlap")
    expected |= second
    require(expected == {f for f, holes in zip(families, missing) if holes},
            "two-edge pool mismatch")
    require(len(expected) == first_count + second_count == 30720, "spoke pool count mismatch")
    require(families == sorted(set(families)) and len(families) == 30976,
            "pool uniqueness mismatch")
    body = {"status": "PASS", "scope": "Archived finite two-source-edge family pool only",
            "audit_source_sha256": sha(Path(__file__)), "support_source_sha256": sha(SUPPORT),
            "archive_hashes": {k: v for k, v in metadata.items() if "sha256" in k},
            "spoke_families": 30720, "plane_families": 256,
            "model": check_model(families, source, pair_counts, missing, metadata),
            "candidate": candidate_check()}
    header = {"Document": "Independent Partial Pooled Link Model Audit", "Version": "v1.0.0",
              "Author": "Celaya Solutions", "Contact": "hello@celayasolutions.com",
              "Date": "2026-10-03", "SHA256": hashlib.sha256(json.dumps(body, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest(), "Chain": "n/a",
              "Tx": "[not anchored]", "License": "All Rights Reserved / Celaya Solutions"}
    Path(__file__).with_name("result.json").write_text(
        json.dumps({"document_header": header, "body": body}, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "rows": 667, "families": 30976,
                      "candidate_state": body["candidate"]["state"]}))


if __name__ == "__main__":
    main()
