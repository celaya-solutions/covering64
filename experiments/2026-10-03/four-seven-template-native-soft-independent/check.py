# Document:    Independent Soft-Score Native Search Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      50df742eb9ca57994f18c44d907a10f8ffb0497ece576f631d4df0c1ed6c4222
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reuse the independent legality check, separately recompute scores and deltas."""

import importlib.util
import itertools as it
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "four-seven-template-native-soft"
RAW = ROOT / "experiments/scratch/four-seven-template-native-v1.1.0"
OWN = ROOT / "experiments/scratch/four-seven-template-native-soft-independent"
PRIOR = HERE.parent / "four-seven-template-native-independent"
SPEC = importlib.util.spec_from_file_location("prior_gate", PRIOR / "check.py")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
require, sha = BASE.require, BASE.sha
SOURCE_SHA = "f20f5140aad14cb46f24cc49feb1d46decb90d18635ac413755b9fdebc0b51ed"


def targets(case):
    result = dict.fromkeys(it.combinations(range(1, 17), 2), 5)
    for anchor in BASE.ANCHORS:
        for pair in it.combinations(sorted(anchor), 2):
            result[pair] = 7
        hub = max(anchor) + 1
        for point in anchor:
            result[tuple(sorted((point, hub)))] = 6
    hub_pairs = [(4, 8), (12, 16)] if case == "matching" else [(4, 8), (8, 12), (12, 16), (4, 16)]
    for pair in hub_pairs:
        result[pair] = 7 if case == "matching" else 6
    require(len(result) == 120 and sum(result.values()) == 640, "wrong target universe")
    return result


def score(blocks, case):
    triples = Counter(t for block in blocks for t in it.combinations(block, 3))
    pairs = Counter(p for block in blocks for p in it.combinations(block, 2))
    holes = len(BASE.TRIPLES - triples.keys())
    l1 = sum(abs(pairs[pair] - target) for pair, target in targets(case).items())
    heavy = {tuple(sorted(anchor)) for anchor in BASE.ANCHORS}
    excess = sum(max(0, count - 2) for triple, count in triples.items() if triple not in heavy)
    return {
        "holes": holes,
        "pair_l1": l1,
        "nonheavy_excess": excess,
        "score": 5 * holes + l1 + 5 * excess,
    }


def check_operation(event, case):
    before = BASE.read(Path(event["before"]))
    after = BASE.read(Path(event["after"]))
    bscore, ascore = score(before, case), score(after, case)
    for role, value in [("before", bscore), ("after", ascore)]:
        require(event[f"holes_{role}"] == value["holes"], "incorrect logged holes")
        require(event[f"score_{role}"] == value["score"], "incorrect logged score")
    triples = Counter(t for block in before for t in it.combinations(block, 3))
    pairs = Counter(p for block in before for p in it.combinations(block, 2))
    old_triples, old_pairs = triples.copy(), pairs.copy()
    for field, sign in [("removed", -1), ("added", 1)]:
        for block in event[field]:
            for triple in it.combinations(block, 3):
                triples[triple] += sign
            for pair in it.combinations(block, 2):
                pairs[pair] += sign
    require(
        triples == Counter(t for block in after for t in it.combinations(block, 3)),
        "triple delta drift",
    )
    require(
        pairs == Counter(p for block in after for p in it.combinations(block, 2)),
        "pair delta drift",
    )
    heavy = {tuple(sorted(anchor)) for anchor in BASE.ANCHORS}
    delta_holes = sum((triples[t] == 0) - (old_triples[t] == 0) for t in BASE.TRIPLES)
    delta_excess = sum(
        max(0, triples[t] - 2) - max(0, old_triples[t] - 2) for t in BASE.TRIPLES - heavy
    )
    delta_pairs = sum(
        abs(pairs[p] - target) - abs(old_pairs[p] - target) for p, target in targets(case).items()
    )
    require(delta_holes == ascore["holes"] - bscore["holes"], "hole delta differs")
    require(
        5 * delta_holes + delta_pairs + 5 * delta_excess == ascore["score"] - bscore["score"],
        "score delta differs",
    )
    return {"mode": event["mode"], "role": event["role"], "before": bscore, "after": ascore}


def audit_run(prefix, case, maps):
    states = [
        {**BASE.recount(path, maps), **score(BASE.read(path), case)}
        for path in sorted(prefix.parent.glob(prefix.name + "-*.txt"))
    ]
    events = list(map(json.loads, prefix.with_suffix(".log").read_text().splitlines()))
    moves = BASE.operations(prefix.with_suffix(".log"), maps)
    scored_moves = [check_operation(e, case) for e in events if e["event"] == "operation"]
    require(len(moves) == len(scored_moves), "operation inventory")
    require(not prefix.with_suffix(".err").read_bytes(), "sanitizer diagnostics")
    first, last = events[0], events[-1]
    initial = score(BASE.read(Path(str(prefix) + "-initial.txt")), case)
    require(
        (
            first["initial_holes"],
            first["initial_pair_l1"],
            first["initial_nonheavy_excess"],
            first["initial_score"],
        )
        == tuple(initial[k] for k in ["holes", "pair_l1", "nonheavy_excess", "score"]),
        "start fields differ",
    )
    raw = score(BASE.read(Path(str(prefix) + "-raw-best.txt")), case)
    best = score(BASE.read(Path(str(prefix) + "-score-best.txt")), case)
    require(
        sha(Path(str(prefix) + "-best.txt")) == sha(Path(str(prefix) + "-raw-best.txt")),
        "raw best alias drift",
    )
    require(
        (last["best_holes"], last["best_raw_score"]) == (raw["holes"], raw["score"]),
        "raw minima fields differ",
    )
    require(
        (last["best_score_holes"], last["best_score"]) == (best["holes"], best["score"]),
        "score minima fields differ",
    )
    eligible = [s for s in states if "-control" not in s["path"]]
    require(
        min((s["holes"], s["score"]) for s in eligible) == (raw["holes"], raw["score"]),
        "raw saved minimum differs",
    )
    require(
        min((s["score"], s["holes"]) for s in eligible) == (best["score"], best["holes"]),
        "score saved minimum differs",
    )
    controls = []
    for event in events:
        if event["event"] != "operation":
            continue
        for field in ["holes_before", "holes_after", "score_before", "score_after"]:
            damaged = {**event, field: event[field] + 1}
            try:
                check_operation(damaged, case)
            except ValueError:
                controls.append({"field": field, "rejected": True})
            else:
                raise ValueError("damaged score accepted")
    return {"states": states, "operations": scored_moves, "damaged_fields": controls, "final": last}


def main():
    OWN.mkdir(exist_ok=True)
    source = ROOT / "scripts/four_seven_template_soft_heuristic.cpp"
    require(sha(source) == SOURCE_SHA, "source changed")
    prior = json.loads((PRIOR / "audit.json").read_text())
    require(
        prior["passed"] and prior["checker_sha256"] == sha(PRIOR / "check.py"),
        "prior checker changed",
    )
    encoding = json.loads((BASE.ENCODING / "independent-audit.json").read_text())
    require(
        encoding["passed"]
        and prior["encoding_audit_sha256"] == sha(BASE.ENCODING / "independent-audit.json"),
        "catalog audit changed",
    )
    build = [
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
    built = subprocess.run(build, capture_output=True, text=True, check=True)
    require(not built.stdout and not built.stderr, "build diagnostics")
    cases = json.loads((INPUT / "seeds.json").read_text())["cases"]
    reports = []
    for case in cases:
        name = case["name"]
        maps = BASE.catalogs(case, next(c for c in encoding["cases"] if c["case"] == name))
        seed = ROOT / case["seed_path"]
        require(
            sha(seed) == case["seed_sha256"] == sha(ROOT / case["parent_best_path"]),
            "seed provenance changed",
        )
        initial = {**BASE.recount(seed, maps), **score(BASE.read(seed), name)}
        expected = (21, 30, 4, 155) if name == "matching" else (19, 24, 3, 134)
        require(
            tuple(initial[k] for k in ["holes", "pair_l1", "nonheavy_excess", "score"]) == expected,
            "seed score",
        )
        saved = audit_run(RAW / "smokes" / name, name, maps)
        prefix = OWN / name
        command = [
            str(OWN / "search-sanitize"),
            str(ROOT / case["catalog_path"]),
            str(seed),
            str(case["seed"] + 100),
            "0.5",
            str(prefix),
        ]
        p = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
        prefix.with_suffix(".log").write_text(p.stdout)
        prefix.with_suffix(".err").write_text(p.stderr)
        require(p.returncode in [0, 1] and not p.stderr, "fresh native failure")
        fresh = audit_run(prefix, name, maps)
        require({e["mode"] for e in fresh["operations"]} == {0, 1, 2, 3}, "missing move mode")
        reports.append(
            {
                "case": name,
                "seed": initial,
                "saved": saved,
                "fresh": fresh,
                "command": command,
                "exit": p.returncode,
            }
        )
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "source_sha256": SOURCE_SHA,
        "prior_gate_sha256": sha(PRIOR / "audit.json"),
        "catalog_audit_sha256": sha(BASE.ENCODING / "independent-audit.json"),
        "build_command": build,
        "binary_sha256": sha(OWN / "search-sanitize"),
        "cases": reports,
        "scope": "Independent score/delta/rollback and legality gate only; "
        "no completeness or exact exclusion.",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "saved_states": sum(len(c["saved"]["states"]) for c in reports),
                "fresh_states": sum(len(c["fresh"]["states"]) for c in reports),
                "operations": sum(
                    len(c[k]["operations"]) for c in reports for k in ["saved", "fresh"]
                ),
                "damaged_fields": sum(
                    len(c[k]["damaged_fields"]) for c in reports for k in ["saved", "fresh"]
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
