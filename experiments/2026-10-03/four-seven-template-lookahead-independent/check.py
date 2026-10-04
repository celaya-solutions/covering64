# Document:    Independent Native Anchor-Lookahead Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b6498e8b5c5e298d45a68c55b1ced66521e2b422dbce472ee718cbe01e2889ee
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import gzip
import importlib.util
import itertools as it
import json
import subprocess
from collections import Counter
from pathlib import Path

from oracle import analyze, budgets, heavy_blocks, require
from prepare_oracles import HERE, RAW, ROOT, SOFT, sha

PRIOR = HERE.parent / "four-seven-template-native-soft-independent"
SPEC = importlib.util.spec_from_file_location("prior_gate", PRIOR / "check.py")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
BASE = OLD.BASE
SOURCE = ROOT / "scripts/four_seven_template_lookahead_heuristic.cpp"
SOURCE_SHA = "e9584eb88bb4bb744b7a2d83af26d1f3f3cf23c5efeeb42a1d94438582c4da35"
CACHED = {}


def expected(blocks, case):
    fixed = tuple(heavy_blocks(blocks))
    if fixed not in CACHED:
        oracle = analyze(fixed)
        counts = Counter(t for b in fixed for t in it.combinations(b, 3))
        excess = Counter()
        for triple, count in counts.items():
            for pair in it.combinations(triple, 2):
                excess[pair] += max(0, count - 1)
        oracle["heavy_excess"] = sum(max(0, excess[p] - cap) for p, cap in budgets().items())
        CACHED[fixed] = oracle
    value = copy.deepcopy(CACHED[fixed])
    base = OLD.score(blocks, case)
    value.update(
        base_score=base["score"],
        holes=base["holes"],
        score=base["score"] + 100 * value["unsupported_count"],
    )
    return value


def compare(native, value):
    require(native["event"] == "lookahead" and native["weight"] == 100, "lookahead identity")
    for key in ["holes", "base_score", "score", "unsupported_count", "heavy_excess"]:
        require(native[key] == value[key], "wrong " + key)
    require(native["admissible_count"] == value["allowed_ordinary"], "wrong admissible count")
    require(
        native["unsupported_triples"] == [list(t) for t in value["unsupported"]],
        "unsupported set differs",
    )
    require(
        native["admissible_blocks"] == [list(b) for b in value["admissible_blocks"]],
        "admissible set differs",
    )


def execute(command, prefix, allowed=(0,)):
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    prefix.with_suffix(".log").write_text(run.stdout)
    prefix.with_suffix(".err").write_text(run.stderr)
    require(run.returncode in allowed and not run.stderr, "native/sanitizer failure")
    return run


def check_run(prefix, case, maps):
    reports, details = [], {}
    for path in sorted(prefix.parent.glob(prefix.name + "-*.txt")):
        legality = BASE.recount(path, maps)
        value = expected(BASE.read(path), case)
        detail_path = Path(str(path) + ".lookahead.json")
        native = json.loads(detail_path.read_text())
        compare(native, value)
        require(
            native["template_ids_1based"] == legality["template_ids_1based"], "template ID drift"
        )
        details[str(path)] = native
        reports.append(
            {
                **legality,
                "score": value["score"],
                "base_score": value["base_score"],
                "unsupported": value["unsupported_count"],
                "admissible": value["allowed_ordinary"],
                "detail_sha256": sha(detail_path),
            }
        )
    moves = BASE.operations(prefix.with_suffix(".log"), maps)
    events = list(map(json.loads, prefix.with_suffix(".log").read_text().splitlines()))
    require(not prefix.with_suffix(".err").read_bytes(), "sanitizer diagnostics")
    for event in events:
        if event["event"] != "operation":
            continue
        before, after = details[event["before"]], details[event["after"]]
        for role, value in [("before", before), ("after", after)]:
            require(event["holes_" + role] == value["holes"], "operation holes")
            require(event["score_" + role] == value["score"], "operation score")
        if event["mode"] != 3:
            for field in [
                "unsupported_triples",
                "admissible_blocks",
                "heavy_excess",
                "template_ids_1based",
                "cache_hits",
                "cache_misses",
                "cache_clears",
            ]:
                require(before[field] == after[field], "ordinary move changed heavy cache")
        if event["role"] == "forced_apply":
            rollback = details[event["before"].replace("-before.txt", "-rollback.txt")]
            for field in [
                "unsupported_triples",
                "admissible_blocks",
                "heavy_excess",
                "score",
                "template_ids_1based",
            ]:
                require(rollback[field] == before[field], "rollback lookahead drift")
    require(
        {e["mode"] for e in moves if e["role"] == "forced_apply"} == {0, 1, 2, 3}, "move inventory"
    )
    first, final = events[0], events[-1]
    require(final["event"] == "finished", "fresh smoke incomplete")
    initial = details[str(prefix) + "-initial.txt"]
    require(first["initial_unsupported"] == initial["unsupported_count"], "initial unsupported")
    require(first["initial_score"] == initial["score"], "initial score")
    raw, scored = details[str(prefix) + "-raw-best.txt"], details[str(prefix) + "-score-best.txt"]
    require(
        sha(Path(str(prefix) + "-best.txt")) == sha(Path(str(prefix) + "-raw-best.txt")),
        "best alias",
    )
    require(
        (final["best_holes"], final["best_raw_score"]) == (raw["holes"], raw["score"]),
        "raw best log",
    )
    require(
        (final["best_score_holes"], final["best_score"]) == (scored["holes"], scored["score"]),
        "score best log",
    )
    eligible = [r for r in reports if "-control" not in r["path"]]
    require(
        min((r["holes"], r["score"]) for r in eligible) == (raw["holes"], raw["score"]),
        "raw minimum",
    )
    require(
        min((r["score"], r["holes"]) for r in eligible) == (scored["score"], scored["holes"]),
        "score minimum",
    )
    return {"states": reports, "operations": moves, "final": final}


def main():
    require(sha(SOURCE) == SOURCE_SHA, "frozen native source changed")
    prior = json.loads((PRIOR / "audit.json").read_text())
    require(
        prior["passed"] and prior["checker_sha256"] == sha(PRIOR / "check.py"), "prior gate changed"
    )
    fixture_path = HERE / "oracle-fixtures.json"
    fixtures = json.loads(fixture_path.read_text())
    require(fixtures["oracle_sha256"] == sha(HERE / "oracle.py"), "oracle changed")
    require(fixtures["generator_sha256"] == sha(HERE / "prepare_oracles.py"), "generator changed")
    encoding = json.loads((BASE.ENCODING / "independent-audit.json").read_text())
    require(
        encoding["passed"]
        and prior["catalog_audit_sha256"] == sha(BASE.ENCODING / "independent-audit.json"),
        "catalog gate changed",
    )
    binary = RAW / "search-sanitize"
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
        str(SOURCE),
        "-o",
        str(binary),
    ]
    built = subprocess.run(command, capture_output=True, text=True, check=True)
    require(not built.stdout and not built.stderr, "compiler diagnostics")
    reports, damaged = [], []
    for fixture in fixtures["fresh_tuples"]:
        path = ROOT / fixture["state"]
        require(sha(path) == fixture["state_sha256"], "fixture changed")
        require(sha(ROOT / fixture["catalog"]) == fixture["catalog_sha256"], "catalog pack changed")
        archived = json.loads(gzip.decompress((ROOT / fixture["expected"]).read_bytes()))
        require(
            sha(ROOT / fixture["expected"]) == fixture["expected_sha256"], "oracle bytes changed"
        )
        value = expected(BASE.read(path), fixture["case"])
        require(archived["unsupported_count"] == value["unsupported_count"], "oracle count drift")
        argv = [
            str(binary),
            str(ROOT / fixture["catalog"]),
            str(path),
            "2026104202",
            "1",
            str(path.with_suffix("")),
            "--lookahead-only",
        ]
        run = execute(argv, path.with_suffix(".native"))
        native = json.loads(run.stdout)
        compare(native, value)
        require(
            native["template_ids_1based"] == fixture["template_ids_1based"], "fixture template IDs"
        )
        require(
            native["cache_hits"] >= 2 and native["cache_misses"] == 1, "same-process cache reuse"
        )
        reports.append(
            {
                "case": fixture["case"],
                "trial": fixture["trial"],
                "unsupported": value["unsupported_count"],
                "admissible": value["allowed_ordinary"],
                "heavy_excess": value["heavy_excess"],
                "command": argv,
                "log_sha256": sha(path.with_suffix(".log")),
            }
        )
        if len(damaged) < 8:
            for field in [
                "score",
                "base_score",
                "unsupported_count",
                "admissible_count",
                "heavy_excess",
                "weight",
                "holes",
            ]:
                bad = copy.deepcopy(native)
                bad[field] += 1
                try:
                    compare(bad, value)
                except ValueError:
                    damaged.append({"field": field, "rejected": True})
                else:
                    raise ValueError("damaged output accepted")
    require(len(reports) == 32, "fresh tuple inventory")
    require(any(r["heavy_excess"] > 0 for r in reports), "missing heavy-excess control")
    require(
        any(r["heavy_excess"] == r["unsupported"] == 0 for r in reports),
        "missing zero-obstruction control",
    )
    cases = json.loads((SOFT / "seeds.json").read_text())["cases"]
    smokes, cache_controls = [], []
    for case in cases:
        name = case["name"]
        maps = BASE.catalogs(case, next(c for c in encoding["cases"] if c["case"] == name))
        seed = SOFT / (name + "-raw-best.txt")
        prefix = RAW / (name + "-fresh")
        argv = [
            str(binary),
            str(ROOT / case["catalog_path"]),
            str(seed),
            "2026104203",
            "0.25",
            str(prefix),
        ]
        execute(argv, prefix, (0, 1))
        smokes.append({"case": name, "command": argv, **check_run(prefix, name, maps)})
        cache_prefix = RAW / (name + "-cache")
        argv[-1] = str(cache_prefix)
        result = execute(argv + ["--cache-control"], cache_prefix)
        cache = json.loads(result.stdout)
        require(
            cache["passed"] and cache["test_limit"] == 2 and cache["production_limit"] == 100000,
            "cache capacity control",
        )
        require(
            cache["production_eviction_branch_count"] == 1 and cache["hits"] >= 2,
            "cache clear/refill control",
        )
        cache_controls.append({"case": name, **cache})
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "oracle_sha256": sha(HERE / "oracle.py"),
        "source_sha256": SOURCE_SHA,
        "prior_gate_sha256": sha(PRIOR / "audit.json"),
        "fixture_manifest_sha256": sha(fixture_path),
        "build_command": command,
        "binary_sha256": sha(binary),
        "fresh_tuples": reports,
        "fresh_smokes": smokes,
        "cache_controls": cache_controls,
        "damaged_outputs": damaged,
        "zero_hole_acceptance": "Executed native assertion with projected holes0 and "
        "positive score delta1000000; source bypass reviewed.",
        "scope": "Construction gate for exact anchor-pair lookahead, "
        "full scores, cache and rollback only.",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "fresh_tuples": 32,
                "smoke_states": sum(len(s["states"]) for s in smokes),
                "operations": sum(len(s["operations"]) for s in smokes),
                "cache_clear_controls": 2,
                "damaged_outputs": len(damaged),
            }
        )
    )


if __name__ == "__main__":
    main()
