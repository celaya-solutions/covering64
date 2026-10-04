# Document:    Fixed Link Profile Damaged Input Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      4ddacde2c751835a401c7c8dd1850e90b1498b98eec84a76541ae34d74a371c8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Require malformed seeds, profiles and command arguments to fail before saving."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/fixed-link-profile-v1.0.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    out = RAW / "damaged-controls"
    out.mkdir(exist_ok=True)
    case = json.loads((HERE / "seeds.json").read_text())["cases"][0]
    original = (ROOT / case["seed_path"]).read_text().splitlines()
    damage = {
        "missing_block": original[:-1],
        "duplicate_block": original[:-1] + original[:1],
        "repeated_label": ["1 1 3 4 5"] + original[1:],
        "outside_label": ["1 2 3 4 17"] + original[1:],
        "extra_token": [original[0] + " 6"] + original[1:],
        "noninteger": ["1 2 x 4 5"] + original[1:],
    }
    changed = list(original)
    for index, line in enumerate(changed):
        block = list(map(int, line.split()))
        if 1 not in block:
            replacement = sorted(block[1:] + [next(p for p in range(2, 17) if p not in block)])
            candidate = " ".join(map(str, replacement))
            if candidate not in changed:
                changed[index] = candidate
                break
    require(changed != original, "could not damage profile")
    damage["wrong_profile"] = sorted(changed, key=lambda line: tuple(map(int, line.split())))
    records = []
    for name, lines in damage.items():
        path = out / f"{name}.txt"
        path.write_text("\n".join(lines) + "\n")
        command = [str(RAW / "search"), str(path), "1", "2", "7", "0.01", str(out / name)]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        require(
            result.returncode == 2 and not (out / f"{name}-initial.txt").exists(),
            "native accepted damaged seed",
        )
        checks = []
        for prefix in [
            ["uv", "run", "covering64", "verify"],
            [sys.executable, "scripts/check_cover.py"],
        ]:
            check = subprocess.run(
                prefix + [str(path), "--expected-blocks", "64"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            require(check.returncode != 0, "cover checker accepted damaged seed as a cover")
            checks.append({"command": prefix, "exit": check.returncode})
        records.append(
            {
                "control": name,
                "native_exit": result.returncode,
                "native_error": result.stderr.strip(),
                "checks": checks,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    for name, position, value in [
        ("anchor_suffix", 2, "1x"),
        ("high_suffix", 3, "2x"),
        ("negative_seed", 4, "-7"),
        ("seed_suffix", 4, "7x"),
        ("budget_suffix", 5, "1x"),
        ("nan_budget", 5, "nan"),
        ("inf_budget", 5, "inf"),
        ("zero_budget", 5, "0"),
    ]:
        command = [
            str(RAW / "search"),
            str(ROOT / case["seed_path"]),
            "1",
            "2",
            "7",
            "0.01",
            str(out / name),
        ]
        command[position] = value
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        require(
            result.returncode == 2 and not (out / f"{name}-initial.txt").exists(),
            "native accepted damaged argument",
        )
        records.append(
            {
                "control": name,
                "native_exit": result.returncode,
                "native_error": result.stderr.strip(),
            }
        )
    report = {
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rejected": len(records),
        "controls": records,
        "scope": (
            "Cover checkers reject these partial/damaged inputs as covers; "
            "native also checks profile."
        ),
    }
    (HERE / "damaged-controls.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"rejected": len(records)}))


if __name__ == "__main__":
    main()
