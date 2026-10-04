# Document:    Independent Native Template Malformed-Input Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exercise damaged seed/catalog parsing and bind saved smoke budget/outcome claims."""

import importlib.util
import itertools
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("template_native_gate", HERE / "check.py")
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)


def main():
    audit = json.loads((HERE / "audit.json").read_text())
    G.require(
        audit["passed"] is True and audit["checker_sha256"] == G.sha(HERE / "check.py"),
        "gate source changed",
    )
    binary = G.OWN / "search-sanitize"
    G.require(G.sha(binary) == audit["binary_sha256"], "sanitized binary changed")
    cases = json.loads((G.INPUT / "seeds.json").read_text())["cases"]
    smoke = []
    for c in cases:
        prefix = G.RAW / (c["name"] + "-smoke")
        events = list(map(json.loads, prefix.with_suffix(".log").read_text().splitlines()))
        G.require(
            events[0]["seed"] == c["seed"]
            and events[0]["seconds"] == 3
            and events[0]["workers"] == 1
            and events[0]["catalog"] == c["name"],
            "wrong smoke budget",
        )
        G.require(events[-1]["event"] == "finished", "smoke unfinished")
        best = next(
            s
            for a in audit["cases"]
            if a["case"] == c["name"]
            for s in a["saved_states"]
            if s["path"].endswith("-smoke-best.txt")
        )
        G.require(best["holes"] == events[-1]["best_holes"], "saved final claim differs")
        smoke.append(
            {
                "case": c["name"],
                "final": events[-1],
                "log_sha256": G.sha(prefix.with_suffix(".log")),
            }
        )
    c = cases[0]
    seed = G.ROOT / c["seed_path"]
    catalog = G.ROOT / c["catalog_path"]
    rows = G.read(seed)
    ordinary_slot = next(i for i, b in enumerate(rows) if G.ordinary(b))
    changed = rows.copy()
    changed[ordinary_slot] = next(
        b for b in itertools.combinations(range(1, 17), 5) if G.ordinary(b) and b not in rows
    )
    forbidden = rows.copy()
    forbidden[ordinary_slot] = next(
        b
        for b in itertools.combinations(range(1, 17), 5)
        if not G.ordinary(b) and b not in rows and not any(a <= set(b) for a in G.ANCHORS)
    )
    malformed = {
        "duplicate_block": rows[:-1] + [rows[0]],
        "missing_block": rows[:-1],
        "point_outside": [(1, 2, 3, 4, 17)] + rows[1:],
        "repeated_point": [(1, 2, 3, 4, 4)] + rows[1:],
        "changed_degree": sorted(changed),
        "forbidden_ordinary": sorted(forbidden),
    }
    directory = G.OWN / "damaged"
    directory.mkdir(exist_ok=True)
    controls = []
    for name, blocks in malformed.items():
        path = directory / (name + ".txt")
        path.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
        controls.append((name, catalog, path))
    lines = catalog.read_text().splitlines()
    header = lines.copy()
    words = header[0].split()
    words[2] = "1"
    header[0] = " ".join(words)
    repeated_edge = lines.copy()
    words = repeated_edge[1].split()
    words[4:6] = words[2:4]
    repeated_edge[1] = " ".join(words)
    for name, damaged in [
        ("wrong_catalog_count", header),
        ("duplicate_catalog_edge", repeated_edge),
    ]:
        path = directory / (name + ".txt")
        path.write_text("\n".join(damaged) + "\n")
        controls.append((name, path, seed))
    reports = []
    for name, pack, initial in controls:
        argv = [str(binary), str(pack), str(initial), "7", "0.1", str(directory / name)]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)
        G.require(
            result.returncode == 2 and result.stderr and not result.stdout,
            "malformed control accepted or sanitizer failed",
        )
        reports.append({"name": name, "exit": result.returncode, "error": result.stderr.strip()})
    report = {
        "passed": True,
        "checker_sha256": G.sha(Path(__file__)),
        "gate_sha256": G.sha(HERE / "audit.json"),
        "smoke_claims": smoke,
        "malformed_controls_rejected": reports,
    }
    (HERE / "controls-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "controls_rejected": len(reports)}))


if __name__ == "__main__":
    main()
