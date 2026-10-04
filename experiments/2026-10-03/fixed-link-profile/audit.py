# Document:    Fixed Link Profile Snapshot and Operation Audit
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      279488c0a03102d76c61b5d5b24c6fc7bd270b76e39540c9ec1ba2bfcfed95ed
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independently recount every saved state and invoke both covering checkers."""

import argparse
import hashlib
import itertools as it
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW_RESULTS = ROOT / "experiments/scratch/fixed-link-profile-v1.0.0/verifier-output"
TRIPLES = set(it.combinations(range(1, 17), 3))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blocks(path):
    result = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    require(
        all(
            len(b) == len(set(b)) == 5 and min(b) >= 1 and max(b) <= 16 and b == tuple(sorted(b))
            for b in result
        ),
        "malformed block",
    )
    require(
        result == sorted(result) and len(result) == len(set(result)) == 64, "malformed inventory"
    )
    return result


def inspect(path, case):
    candidate = blocks(path)
    fixed = [
        tuple(map(int, line.split()))
        for line in (ROOT / case["link_path"]).read_text().splitlines()
    ]
    require([b for b in candidate if case["anchor"] in b] == fixed, "fixed link changed")
    degrees = Counter(p for b in candidate for p in b)
    require(
        degrees
        == {
            p: 19 if p == case["anchor"] else 21 if p == case["high_point"] else 20
            for p in range(1, 17)
        },
        "degree profile changed",
    )
    counts = Counter(t for b in candidate for t in it.combinations(b, 3))
    missing = sorted(TRIPLES - set(counts))
    require(all(case["anchor"] not in t for t in missing), "anchor triple uncovered")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    RAW_RESULTS.mkdir(exist_ok=True)
    checks = []
    for prefix in [
        ["uv", "run", "covering64", "verify"],
        [sys.executable, "scripts/check_cover.py"],
    ]:
        command = prefix + [str(path.resolve()), "--expected-blocks", "64"]
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        checker = "package" if prefix[0] == "uv" else "standalone"
        raw_path = RAW_RESULTS / f"{digest}.{checker}.json"
        raw_path.write_text(process.stdout)
        raw_path.with_suffix(".stderr").write_text(process.stderr)
        data = json.loads(process.stdout)
        require(process.returncode == int(bool(missing)), "checker exit disagrees")
        require(data["blocks"] == 64 and data["valid"] == (not missing), "checker status disagrees")
        require(
            sorted(map(tuple, data["uncovered"])) == missing, "checker uncovered triples disagree"
        )
        require(data["canonical_sha256"] == digest, "checker canonical hash disagrees")
        checks.append(
            {
                "command": command,
                "exit": process.returncode,
                "canonical_sha256": digest,
                "uncovered_count": len(missing),
                "valid": not missing,
                "raw_result_path": str(raw_path.relative_to(ROOT)),
                "raw_result_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            }
        )
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "holes": len(missing),
        "degrees": dict(sorted(degrees.items())),
        "checks": checks,
    }


def audit(folder):
    cases = json.loads((HERE / "seeds.json").read_text())["cases"]
    reports, operations = [], []
    for case in cases:
        name = case["name"]
        for path in sorted(folder.glob(f"{name}-*.txt")):
            reports.append(inspect(path, case))
        for path in sorted(folder.glob(f"{name}*.log")):
            for line in path.read_text().splitlines():
                event = json.loads(line)
                if event.get("event") != "operation":
                    continue
                before = set(blocks(Path(event["before"])))
                after = set(blocks(Path(event["after"])))
                removed = set(map(tuple, event["removed"]))
                added = set(map(tuple, event["added"]))
                require(removed <= before and not added & (before - removed), "operation collision")
                require((before - removed) | added == after, "operation differs from saved states")
                require(
                    Counter(p for b in removed for p in b) == Counter(p for b in added for p in b),
                    "operation changed degrees",
                )
                require(
                    all(case["anchor"] not in b for b in removed | added),
                    "operation changes anchor",
                )
                require(2 <= len(removed) <= 6 and len(removed) == len(added), "bad operation size")
                if event["role"] == "forced_apply":
                    rollback = Path(event["before"].replace("-before.txt", "-rollback.txt"))
                    require(
                        blocks(rollback) == sorted(before), "rollback did not restore exact blocks"
                    )
                operations.append(event)
    require(bool(reports), "no snapshots found")
    return {
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "snapshots": reports,
        "operations": operations,
        "snapshot_count": len(reports),
        "operation_count": len(operations),
        "covers": sum(r["holes"] == 0 for r in reports),
        "scope": "Independent exact recount and both covering verifiers for every saved state.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.folder.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["snapshot_count", "operation_count", "covers"]}))
