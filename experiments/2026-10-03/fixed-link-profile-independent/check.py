# Document:    Independent Fixed-Link Native Search Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Independent snapshot recount, operation replay and fresh sanitized controls."""

import hashlib
import itertools as it
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "fixed-link-profile"
RAW = ROOT / "experiments/scratch/fixed-link-profile-v1.0.0"
OWN = ROOT / "experiments/scratch/fixed-link-profile-independent"
FROZEN = "e3c13c3d7bac16cc9318663539f0d5c3cdcfb7c5a64740e898c17bd529f0722c"
TRIPLES = set(it.combinations(range(1, 17), 3))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    rows = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    require(len(rows) == 64 and len(set(rows)) == 64, "wrong or duplicate block count")
    require(rows == sorted(rows), "noncanonical block order")
    require(all(len(b) == 5 and tuple(sorted(set(b))) == b for b in rows), "bad block")
    require(all(1 <= p <= 16 for b in rows for p in b), "point outside universe")
    return rows


def recount(path, case):
    rows = read(path)
    fixed = [
        tuple(map(int, s.split())) for s in (ROOT / case["link_path"]).read_text().splitlines()
    ]
    require([b for b in rows if case["anchor"] in b] == fixed, "changed fixed link")
    degree = Counter(p for b in rows for p in b)
    target = {
        p: 19 if p == case["anchor"] else 21 if p == case["high_point"] else 20
        for p in range(1, 17)
    }
    require(degree == target, "changed point profile")
    counts = Counter(t for b in rows for t in it.combinations(b, 3))
    missing = TRIPLES - counts.keys()
    require(all(case["anchor"] not in t for t in missing), "anchor triple uncovered")
    if "-h" in path.stem and path.stem.rsplit("-h", 1)[1].isdigit():
        require(len(missing) == int(path.stem.rsplit("-h", 1)[1]), "wrong hole filename")
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "holes": len(missing)}


def replay(path):
    operations = []
    for e in map(json.loads, path.read_text().splitlines()):
        if e["event"] != "operation":
            continue
        before, after = set(read(Path(e["before"]))), set(read(Path(e["after"])))
        removed, added = list(map(tuple, e["removed"])), list(map(tuple, e["added"]))
        require(len(set(removed)) == len(removed) == len(set(added)) == len(added), "duplicates")
        require(2 <= len(removed) <= 6, "wrong move size")
        require(set(removed) <= before, "removed absent block")
        require(not set(added) & (before - set(removed)), "result collision")
        require(before - set(removed) | set(added) == after, "descriptor mismatch")
        require(
            Counter(p for b in removed for p in b) == Counter(p for b in added for p in b),
            "unbalanced move",
        )
        require(all(1 not in b for b in removed + added), "fixed-link move")
        require(before != after, "no-op accepted")
        if e["mode"] in [0, 1]:
            require(len(removed) == 2, "wrong two-block move size")
            a, b = map(set, removed)
            c, d = map(set, added)
            require(a & b == c & d and a | b == c | d, "repartition mismatch")
        if e["role"] == "forced_apply":
            rollback = Path(e["before"].replace("-before.txt", "-rollback.txt"))
            require(set(read(rollback)) == before, "rollback differs")
        operations.append({"mode": e["mode"], "role": e["role"]})
    return operations


def main():
    OWN.mkdir(exist_ok=True)
    source = ROOT / "scripts/fixed_link_profile_heuristic.cpp"
    require(sha(source) == FROZEN == sha(RAW / source.name), "source hash changed")
    metadata = json.loads((INPUT / "environment.json").read_text())
    for name, digest in metadata["binaries"].items():
        require(sha(RAW / name) == digest, "binary hash changed")
    cases = json.loads((INPUT / "seeds.json").read_text())["cases"]
    snapshots, operations, runs = [], [], []
    for c in cases:
        for key in ["seed", "link"]:
            require(sha(ROOT / c[key + "_path"]) == c[key + "_sha256"], "input hash changed")
        for p in sorted(RAW.glob(c["name"] + "-*.txt")):
            snapshots.append(recount(p, c))
        log = RAW / (c["name"] + "-smoke.log")
        operations.extend(replay(log))
        events = list(map(json.loads, log.read_text().splitlines()))
        require(events[0]["seed"] == c["seed"] and events[0]["seconds"] == 2, "wrong smoke")
        require(events[-1]["event"] == "finished", "unfinished smoke")
        best = recount(RAW / (c["name"] + "-smoke-best.txt"), c)
        require(events[-1]["best_holes"] == best["holes"], "reported best mismatch")
        require(not (RAW / (c["name"] + "-smoke.err")).read_bytes(), "sanitizer output")
    command = [
        "clang++",
        "-std=c++17",
        "-O1",
        "-g",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-fsanitize=address,undefined",
        "-fno-omit-frame-pointer",
        str(source),
        "-o",
        str(OWN / "search-sanitize"),
    ]
    built = subprocess.run(command, capture_output=True, text=True, check=True)
    require(not built.stdout and not built.stderr, "compiler diagnostics")
    for c in cases:
        prefix = OWN / c["name"]
        argv = [
            str(OWN / "search-sanitize"),
            str(ROOT / c["seed_path"]),
            "1",
            str(c["high_point"]),
            str(c["seed"]),
            "0.05",
            str(prefix),
        ]
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)
        require(proc.returncode in [0, 1] and not proc.stderr, "fresh sanitized run failed")
        log = prefix.with_suffix(".log")
        log.write_text(proc.stdout)
        events = list(map(json.loads, proc.stdout.splitlines()))
        require(events[-1]["event"] == "finished", "fresh run incomplete")
        own_ops = replay(log)
        require(
            {x["mode"] for x in own_ops if x["role"] == "forced_apply"} == {0, 1, 2},
            "missing mode controls",
        )
        states = [recount(p, c) for p in sorted(OWN.glob(c["name"] + "-*.txt"))]
        runs.append(
            {
                "command": argv,
                "exit": proc.returncode,
                "states": states,
                "operations": own_ops,
                "last_event": events[-1],
            }
        )
    base = (ROOT / cases[0]["seed_path"]).read_text().splitlines()
    invalid = {
        "duplicate": base[:-1] + [base[0]],
        "short": base[:-1],
        "out_of_range": ["1 2 3 4 17"] + base[1:],
        "repeat_point": ["1 2 3 4 4"] + base[1:],
        "garbage": base + ["garbage"],
    }
    negatives = []
    for name, rows in invalid.items():
        path = OWN / ("invalid-" + name + ".txt")
        path.write_text("\n".join(rows) + "\n")
        argv = [
            str(OWN / "search-sanitize"),
            str(path),
            "1",
            "2",
            "7",
            "0.01",
            str(OWN / ("invalid-" + name)),
        ]
        p = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=False)
        require(p.returncode == 2 and p.stderr and not p.stdout, "malformed input accepted")
        negatives.append({"name": name, "exit": p.returncode, "error": p.stderr.strip()})
    result = {
        "passed": True,
        "source_sha256": FROZEN,
        "checker_sha256": sha(Path(__file__)),
        "saved_state_count": len(snapshots),
        "saved_operation_count": len(operations),
        "saved_states": snapshots,
        "fresh_build_command": command,
        "fresh_binary_sha256": sha(OWN / "search-sanitize"),
        "fresh_runs": runs,
        "malformed_controls": negatives,
        "scope": "Clears four 300-second single-thread heuristic pilots, at most two concurrent. "
        "No reachability proof, exclusion, lower bound or cover claim.",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({k: result[k] for k in ["passed", "saved_state_count", "saved_operation_count"]})
    )


if __name__ == "__main__":
    main()
