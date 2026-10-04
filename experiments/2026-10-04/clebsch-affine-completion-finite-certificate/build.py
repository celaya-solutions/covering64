# Document:    Seven Fixed Affine Link Completion Exclusion Certificates
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e0a99930621ddc0b81d7bcf1106ac7a1586edce347da4de9b45597eb66a4f701
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Bounded failed-literal deductions over exact residual rows; no solver."""

import hashlib
import importlib.util
import itertools
import json
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent / "clebsch-affine-link-completion-pilot"
PROPAGATOR = HERE.parent / "clebsch-neighborhood-cycle-certificate/build.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = HERE / "certificate.json"
    assert not destination.exists()
    spec = importlib.util.spec_from_file_location("checked_bounds", PROPAGATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = json.loads((BASE / "manifest.json").read_text())
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    containing = {t: set() for t in triples}
    for i, block in enumerate(blocks):
        for triple in itertools.combinations(block, 3):
            containing[triple].add(i)
    started = time.monotonic()
    deadline = started + 20
    certificates = []
    for case in manifest["cases"]:
        assert time.monotonic() < deadline
        profile_path = ROOT / case["profile"]
        partial_path = ROOT / case["partial"]
        profile = set(map(tuple, json.loads(profile_path.read_text())))
        partial = [tuple(map(int, line.split())) for line in partial_path.read_text().splitlines()]
        assert len(profile) == 80 and len(set(partial)) == len(partial) == 20
        covered = Counter(t for block in partial for t in itertools.combinations(block, 3))
        domain = {i for i, block in enumerate(blocks) if case["point"] not in block}
        assert len(domain) == 3003
        rows = [
            {"support": sorted(containing[t] & domain), "lower": 1 + (t in profile) - covered[t],
             "upper": 1 + (t in profile) - covered[t]}
            for t in triples
        ]
        assert all(row["lower"] >= 0 for row in rows)
        rows.append({"support": sorted(domain), "lower": 44, "upper": 44})
        yes, no, initial_trace, bad = module.propagate(rows, set(), set())
        deductions = []
        probes = 0
        while bad is None:
            found = False
            for variable in sorted(domain - yes - no):
                assert time.monotonic() < deadline, "finite certificate budget exceeded"
                probes += 1
                branch_yes, _, branch_trace, branch_bad = module.propagate(
                    rows, yes | {variable}, no
                )
                if branch_bad is None:
                    continue
                no.add(variable)
                yes, no, base_trace, bad = module.propagate(rows, yes, no)
                deductions.append({
                    "assume_selected": variable, "forced_value": 0,
                    "branch_trace": branch_trace, "branch_contradiction_row": branch_bad,
                    "branch_selected": sorted(branch_yes),
                    "base_trace": base_trace, "base_contradiction_row": bad,
                })
                found = True
                break
            assert found, "failed-literal pass did not close this case"
        certificates.append({
            "case": case["case"], "profile_seed": case["profile_seed"], "point": case["point"],
            "profile": case["profile"], "profile_sha256": sha(profile_path),
            "partial": case["partial"], "partial_sha256": sha(partial_path),
            "initial_trace": initial_trace, "deductions": deductions,
            "final_selected": sorted(yes), "final_removed": sorted(no),
            "final_contradiction_row": bad, "probes": probes,
        })
    result = {
        "scope": "These seven exact20-block partials and exact excess profiles only.",
        "all_seven_closed": len(certificates) == 7,
        "does_not_exclude_all_links_in_any_class_or_profile": True,
        "solver_calls": 0, "wall_budget_seconds": 20,
        "elapsed_seconds": time.monotonic() - started,
        "source_sha256": sha(Path(__file__)), "propagator_sha256": sha(PROPAGATOR),
        "manifest_sha256": sha(BASE / "manifest.json"),
        "row_order": "560 lex global triples with exact residual demands, then sum44",
        "variable_ids": "Global lex five-block IDs, restricted to3003 avoiding the fixed point",
        "cases": certificates,
    }
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"certificate_sha256": sha(destination), "cases": len(certificates),
                      "failed_literals": [len(c["deductions"]) for c in certificates],
                      "seconds": result["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
