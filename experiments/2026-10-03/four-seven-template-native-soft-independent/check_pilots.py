# Document:    Independent Soft-Score Native Pilot Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ae176ef72bb226240cbce6775b8884897eff078cfa58d8f5124cc23042375f38
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import json
from pathlib import Path

from check import BASE, HERE, INPUT, RAW, ROOT, SOURCE_SHA, audit_run, require, sha


def main():
    gate = json.loads((HERE / "audit.json").read_text())
    require(gate["passed"] and gate["checker_sha256"] == sha(HERE / "check.py"), "gate changed")
    require(
        sha(ROOT / "scripts/four_seven_template_soft_heuristic.cpp") == SOURCE_SHA, "source changed"
    )
    encoding = json.loads((BASE.ENCODING / "independent-audit.json").read_text())
    cases = json.loads((INPUT / "seeds.json").read_text())["cases"]
    reports = []
    for case in cases:
        name = case["name"]
        maps = BASE.catalogs(case, next(c for c in encoding["cases"] if c["case"] == name))
        report = audit_run(RAW / "pilots" / name, name, maps)
        require(report["final"]["event"] == "finished", "pilot incomplete")
        reports.append({"case": name, **report})
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "gate_sha256": sha(HERE / "audit.json"),
        "source_sha256": SOURCE_SHA,
        "cases": reports,
        "scope": "Saved native pilot states, score fields and operations only; "
        "no cover or exclusion.",
    }
    (HERE / "pilot-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "states": sum(len(c["states"]) for c in reports),
                "operations": sum(len(c["operations"]) for c in reports),
                "damaged_fields": sum(len(c["damaged_fields"]) for c in reports),
                "best_holes": {c["case"]: c["final"]["best_holes"] for c in reports},
            }
        )
    )


if __name__ == "__main__":
    main()
