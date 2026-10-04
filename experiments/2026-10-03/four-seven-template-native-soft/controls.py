# Document:    Soft-Score Complete Template Native Damaged Input Controls
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      565ce9b07dede3bcf7b636e87f8cfcaac80c72bd1e7911de4afd2b84ba751d11
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Reject damaged catalog, seed, ordinary family and argument inputs."""

import hashlib
import itertools as it
import json
import subprocess
from pathlib import Path

from audit import analyze, ordinary

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-native-v1.1.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    case = json.loads((HERE / "seeds.json").read_text())["cases"][0]
    pack, seed = ROOT / case["catalog_path"], ROOT / case["seed_path"]
    out = RAW / "damaged-controls"
    out.mkdir(exist_ok=True)
    seed_rows = seed.read_text().splitlines()
    damaged_seeds = {
        "missing_block": seed_rows[:-1],
        "duplicate_block": seed_rows[:-1] + seed_rows[:1],
        "repeated_label": ["1 1 3 4 5"] + seed_rows[1:],
        "outside_label": ["1 2 3 4 17"] + seed_rows[1:],
        "extra_token": [seed_rows[0] + " 16"] + seed_rows[1:],
    }
    candidate = [tuple(map(int, row.split())) for row in seed_rows]
    forbidden = None
    for i, j in it.combinations(range(64), 2):
        a, b = set(candidate[i]), set(candidate[j])
        if not ordinary(a) or not ordinary(b):
            continue
        for x, y in it.product(a - b, b - a):
            fresh = [tuple(sorted(a - {x} | {y})), tuple(sorted(b - {y} | {x}))]
            if (
                any(not ordinary(row) for row in fresh)
                and len(set(fresh)) == 2
                and not any(row in set(candidate) - {candidate[i], candidate[j]} for row in fresh)
            ):
                changed = candidate.copy()
                changed[i], changed[j] = fresh
                forbidden = sorted(changed)
                break
        if forbidden is not None:
            break
    require(forbidden is not None, "cannot build ordinary-family damage control")
    damaged_seeds["degree_preserving_forbidden_family"] = [" ".join(map(str, b)) for b in forbidden]
    try:
        analyze(forbidden, case)
    except ValueError:
        pass
    else:
        raise ValueError("independent audit accepted forbidden ordinary family")
    records = []

    def reject(name, bad_pack=pack, bad_seed=seed, override=None):
        command = [str(RAW / "search"), str(bad_pack), str(bad_seed), "7", "0.01", str(out / name)]
        if override is not None:
            position, value = override
            command[position] = value
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        require(
            result.returncode == 2 and not (out / f"{name}-initial.txt").exists(),
            "damaged input accepted",
        )
        records.append({"name": name, "exit": result.returncode, "error": result.stderr.strip()})

    for name, rows in damaged_seeds.items():
        path = out / f"{name}.txt"
        path.write_text("\n".join(rows) + "\n")
        reject(name, bad_seed=path)
    pack_rows = pack.read_text().splitlines()
    duplicate_edge = pack_rows.copy()
    row = duplicate_edge[1].split()
    row[4:6] = row[2:4]
    duplicate_edge[1] = " ".join(row)
    wrong_group = pack_rows.copy()
    row = wrong_group[1].split()
    row[0] = "2"
    wrong_group[1] = " ".join(row)
    for name, rows in {
        "missing_template": pack_rows[:-1],
        "extra_template": pack_rows + pack_rows[-1:],
        "duplicate_edge": duplicate_edge,
        "wrong_group": wrong_group,
        "wrong_count": ["C64T1 matching 12041 12042 12042 12042"] + pack_rows[1:],
    }.items():
        path = out / f"{name}.catalog"
        path.write_text("\n".join(rows) + "\n")
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() != case["catalog_sha256"],
            "catalog hash did not detect damage",
        )
        reject(name, bad_pack=path)
    for name, position, value in [
        ("negative_seed", 3, "-1"),
        ("seed_suffix", 3, "7x"),
        ("budget_suffix", 4, "1x"),
        ("nan_budget", 4, "nan"),
        ("infinite_budget", 4, "inf"),
        ("zero_budget", 4, "0"),
    ]:
        reject(name, override=(position, value))
    report = {
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rejected": len(records),
        "controls": records,
        "independent_forbidden_family_rejected": True,
    }
    (HERE / "damaged-controls.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"rejected": len(records)}))


if __name__ == "__main__":
    main()
