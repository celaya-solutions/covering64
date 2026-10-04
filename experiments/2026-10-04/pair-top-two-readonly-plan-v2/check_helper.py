# Document:    Complete Top-Two Hint Helper Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3f791c29df8b9ee80889454288f210903e25dbf07f166fb4e8aca8f448ab6c42
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite arithmetic and rejection controls; no models, optimizer, or accepted hint."""

import hashlib
import importlib.util
import itertools
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCES = [
    ("H6", "experiments/2026-10-03/reduced-family-heuristic/penalty-2026100363/"
     "search-control_before-1-h6.txt", 6, 14, 62),
    ("H48", "experiments/2026-10-04/native-pair-penalty/seed-2026104401/"
     "search-final-qualified.txt", 48, 75, 175),
    ("H49", "experiments/2026-10-04/native-pair-penalty/seed-2026104402/"
     "search-final-qualified.txt", 49, 74, 170),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE / "helper-controls.json"
    if output.exists():
        raise SystemExit("receipt exists; do not overwrite")
    spec = importlib.util.spec_from_file_location("hint_helper", HERE / "derive_hint.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    rng = random.Random(2026104501)
    vectors = list(itertools.combinations_with_replacement(range(4), 14))
    vectors.extend(tuple(rng.randrange(65) for _ in range(14)) for _ in range(128))
    vectors.extend([(64,) * 14, (64,) + (0,) * 13, (64, 64) + (0,) * 12])
    for counts in vectors:
        ordered = sorted(counts, reverse=True)
        top_two = max(a + b for a, b in itertools.combinations(counts, 2))
        canonical_z = ordered[1]
        canonical_y = [max(0, t - canonical_z) for t in counts]
        assert 2 * canonical_z + sum(canonical_y) == top_two
        enumerated = min(2 * z + sum(max(0, t - z) for t in counts) for z in range(65))
        assert enumerated == top_two
        for budget in (top_two - 1, top_two, top_two + 1):
            explicit = all(a + b <= budget for a, b in itertools.combinations(counts, 2))
            assert explicit == (enumerated <= budget)
    records = []
    for name, relative, holes, d2max, d2sum in SOURCES:
        diagnostic, payload = helper.derive(ROOT / relative)
        assert payload is None and not diagnostic["qualified"]
        assert (diagnostic["holes"], diagnostic["D2max"], diagnostic["D2sum"]) == (
            holes, d2max, d2sum)
        assert diagnostic["rows_checked"] == 3605
        if name == "H6":
            assert diagnostic["core_overlaps"][3] == 59
        records.append({"name": name, "path": relative, "sha256": sha(ROOT / relative),
                        "diagnostics": diagnostic})
    text = (ROOT / SOURCES[1][1]).read_text()
    lines = text.splitlines()
    controls = {
        "malformed": "\n".join(lines[:-1]),
        "duplicate": "\n".join(lines[:-1] + [lines[0]]),
        "damaged": "\n".join(["0 " + " ".join(lines[0].split()[1:])] + lines[1:]),
        "valid_nonzero_D2": text,
    }
    rejection = []
    with tempfile.TemporaryDirectory(prefix="top-two-hint-controls-") as temporary:
        tmp = Path(temporary)
        for name, content in controls.items():
            candidate, destination = tmp / f"{name}.txt", tmp / f"{name}.json"
            candidate.write_text(content)
            run = subprocess.run([sys.executable, str(HERE / "derive_hint.py"), str(candidate),
                                  "--output", str(destination)], capture_output=True, text=True)
            result = json.loads(run.stdout)
            assert run.returncode == 2 and not destination.exists()
            assert not result["qualified"] and not result["hint_written"]
            rejection.append({"name": name, "returncode": run.returncode,
                              "output_absent": True, "result": result})
        candidate = tmp / "valid_nonzero_D2.txt"
        destination = tmp / "existing.json"
        destination.write_text("preserve\n")
        run = subprocess.run([sys.executable, str(HERE / "derive_hint.py"), str(candidate),
                              "--output", str(destination)], capture_output=True, text=True)
        assert run.returncode == 2 and destination.read_text() == "preserve\n"
    receipt = {
        "passed": True, "optimizer_calls": 0, "models_constructed": 0,
        "hints_written": 0, "source_sha256": sha(Path(__file__)),
        "helper_sha256": sha(HERE / "derive_hint.py"), "random_seed": 2026104501,
        "finite_vectors": len(vectors), "budget_checks": 3 * len(vectors),
        "integer_z_values_checked_per_vector": 65, "fixed_states": records,
        "rejection_controls": rejection, "existing_output_preserved": True,
        "limits": "No D2zero family among these inputs; accepted output unexercised.",
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "finite_vectors": len(vectors),
                      "receipt_sha256": sha(output), "hints_written": 0}))


if __name__ == "__main__":
    main()
