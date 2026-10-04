"""SQS(8) extension recipes with proved redundant pair, point and triple rows."""

import argparse
import importlib.util
import itertools
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/eight-eight-strengthened-20261004"
COMMON_PATH = HERE.parent / "two-point-star-repair-v2/run.py"
SPEC = importlib.util.spec_from_file_location("checked_vector_helpers", COMMON_PATH)
COMMON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMMON)
BLOCKS, RANK, TRIPLES = COMMON.BLOCKS, COMMON.RANK, COMMON.TRIPLES
sha, dump = COMMON.sha, COMMON.dump


def cores(kind, offset):
    omitted = {1, 2, 3} if kind == "A" else {1, 2, 4}
    planes = []
    for direction in sorted(set(range(1, 8)) - omitted):
        for parity in (0, 1):
            planes.append(tuple(x + offset + 1 for x in range(8)
                                if (x & direction).bit_count() % 2 == parity))
    triples = Counter(t for b in planes for t in itertools.combinations(b, 3))
    assert len(planes) == 8 and set(triples.values()) == {1}
    assert set(Counter(v for b in planes for v in b).values()) == {4}
    leftover = [t for t in itertools.combinations(range(offset + 1, offset + 9), 3)
                if t not in triples]
    assert len(leftover) == 24
    return sorted(planes + leftover)


def strengthen(model, variables, groups, kinds):
    for offset, kind in zip((0, 8), kinds):
        points = set(range(offset + 1, offset + 9))
        other = set(range(1, 17)) - points
        quads = [b for b in cores(kind, offset) if len(b) == 4]
        qcounts = Counter(p for b in quads for p in itertools.combinations(b, 2))
        pair_groups = [g for g in groups if len(g["base"]) == 3
                       and set(g["base"]) <= other]
        singleton_groups = [g for g in groups if len(g["base"]) == 4
                            and set(g["base"]) <= other]
        pair_carriers = {}
        for pair in itertools.combinations(sorted(points), 2):
            ids = [i for g in pair_groups for i in g["ids"]
                   if set(pair) <= set(BLOCKS[i])]
            assert len(ids) == 24
            pair_carriers[pair] = ids
            expression = sum(variables[i] for i in ids)
            if kind == "A":
                assert qcounts[pair] in (0, 2)
                model.add(expression == int(qcounts[pair] == 2))
            else:
                model.add(expression >= max(qcounts[pair] - 1, 0))
            if kind == "A" and qcounts[pair] == 2:
                for outside in sorted(other):
                    triple = set(pair) | {outside}
                    model.add(sum(variables[i] for i, b in enumerate(BLOCKS)
                                  if triple <= set(b)) <= 2)
        for point in sorted(points):
            pair_ids = [i for g in pair_groups for i in g["ids"] if point in BLOCKS[i]]
            single_ids = [i for g in singleton_groups for i in g["ids"]
                          if point in BLOCKS[i]]
            assert len(pair_ids) == 168 and len(single_ids) == 8
            p = sum(variables[i] for i in pair_ids)
            single = sum(variables[i] for i in single_ids)
            model.add(p + 2 * single >= 7)
            if kind == "A":
                model.add(single == 1)
                model.add(sum(variables[i] for i, b in enumerate(BLOCKS) if point in b) == 20)


def build(kinds):
    groups = []
    for offset, kind in zip((0, 8), kinds):
        opposite = range(9, 17) if offset == 0 else range(1, 9)
        for base in cores(kind, offset):
            ids = [RANK[tuple(sorted(base + extension))]
                   for extension in itertools.combinations(opposite, 5 - len(base))]
            groups.append({"base": list(base), "ids": sorted(ids)})
    allowed = {i for g in groups for i in g["ids"]}
    assert len(groups) == 64 and len(allowed) == 1472
    assert sum(len(g["ids"]) for g in groups) == len(allowed)
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"b_{i}") if i in allowed
                 else model.new_int_var(0, 0, f"b_{i}") for i in range(len(BLOCKS))]
    model.add(sum(variables) == 64)
    for group in groups:
        model.add(sum(variables[i] for i in group["ids"]) == 1)
    for triple in TRIPLES:
        model.add(sum(variables[i] for i, block in enumerate(BLOCKS)
                      if set(triple) <= set(block)) >= 1)
    strengthen(model, variables, groups, kinds)
    assert not model.validate()
    return model, groups


def prepare():
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    RAW.mkdir(parents=True)
    entries = []
    for number, kinds in enumerate(("AA", "AB", "BB"), 1):
        model, groups = build(kinds)
        path = RAW / f"model-{number}.pbtxt"
        path.write_text(str(model.proto))
        dump(RAW / f"groups-{number}.json", groups)
        entries.append({"number": number, "kinds": kinds,
                        "model": str(path.relative_to(ROOT)), "model_sha256": sha(path),
                        "groups": str((RAW / f"groups-{number}.json").relative_to(ROOT)),
                        "groups_sha256": sha(RAW / f"groups-{number}.json"),
                        "variables": len(model.proto.variables),
                        "rows": len(model.proto.constraints), "seed": 2026105500 + number})
    dump(HERE / "manifest.json", {
        "source_sha256": sha(__file__), "common_sha256": sha(COMMON_PATH),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "ortools_version": ortools.__version__, "entries": entries,
        "proof_files": {str(path.relative_to(ROOT)): sha(path) for path in
                        sorted((HERE.parent / "eight-eight-redundant-cut-plan").iterdir())
                        if path.is_file()},
        "seconds": 120, "workers": 4, "watchdog": 145, "grace": 5,
        "search_launches_during_preparation": 0,
        "scope": "Three specified restricted recipes with proved redundant pair/point/triple rows: "
        "one extension of each of eight "
        "affine quadruples and24 complementary triples on each8-point half. No claim "
        "every64-cover has this form. UNKNOWN and CP INFEASIBLE are not proof certificates.",
    })


def child(number):
    manifest = json.loads((HERE / "manifest.json").read_text())
    entry = manifest["entries"][number - 1]
    model = COMMON.read_model(ROOT / entry["model"])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = manifest["seconds"]
    solver.parameters.num_search_workers = manifest["workers"]
    solver.parameters.random_seed = entry["seed"]
    solver.parameters.log_search_progress = True
    output = RAW / f"run-{number}"
    (output / "parameters.pbtxt").write_text(str(solver.parameters))
    collector = COMMON.Collector(model, output)
    status = solver.solve(model, collector)
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        dump(output / "final-vector.json", {"values": list(solver.response_proto.solution)})
    (output / "response.pbtxt").write_text(str(solver.response_proto))
    dump(output / "outcome.json", {"status": solver.status_name(status),
                                  "wall_seconds": solver.wall_time,
                                  "callbacks": collector.count})


def execute(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["decision"] == "GO" and gate["passed"] is True
    assert gate["manifest_sha256"] == sha(manifest_path)
    assert manifest["source_sha256"] == sha(__file__)
    assert manifest["common_sha256"] == sha(COMMON_PATH)
    for path, digest in manifest["proof_files"].items():
        assert sha(ROOT / path) == digest
    assert not (HERE / "result.json").exists() and not any(RAW.glob("run-*"))
    for entry in manifest["entries"]:
        assert sha(ROOT / entry["model"]) == entry["model_sha256"]
        assert sha(ROOT / entry["groups"]) == entry["groups_sha256"]
    runs = []
    for entry in manifest["entries"]:
        number = entry["number"]
        output = RAW / f"run-{number}"
        output.mkdir()
        command = [sys.executable, str(Path(__file__).resolve()), "--child", str(number)]
        started = time.monotonic()
        timed_out = False
        with (output / "stdout.log").open("w") as out, (output / "stderr.log").open("w") as err:
            process = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err)
            try:
                process.wait(timeout=manifest["watchdog"])
            except subprocess.TimeoutExpired:
                timed_out = True
                process.terminate()
                try:
                    process.wait(timeout=manifest["grace"])
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        model = COMMON.read_model(ROOT / entry["model"])
        vectors = sorted(output.glob("callback-*.json"))
        if (output / "final-vector.json").exists():
            vectors.append(output / "final-vector.json")
        saved = []
        for path in vectors:
            values = json.loads(path.read_text())["values"]
            COMMON.check_vector(model, values)
            ids = [i for i, value in enumerate(values) if value]
            witness = output / (path.stem + ".txt")
            witness.write_text(COMMON.family(ids))
            verifiers = COMMON.dual(witness)
            assert verifiers[0]["valid"]
            saved.append({"vector": str(path.relative_to(ROOT)),
                          "witness": str(witness.relative_to(ROOT)),
                          "sha256": sha(witness), "verifiers": verifiers})
            (HERE / "cover.txt").write_text(witness.read_text())
        outcome_path = output / "outcome.json"
        outcome = json.loads(outcome_path.read_text()) if outcome_path.exists() else None
        row = {"number": number, "kinds": entry["kinds"], "command": command,
               "elapsed_seconds": time.monotonic() - started, "returncode": process.returncode,
               "watchdog_fired": timed_out, "outcome": outcome, "saved": saved,
               "cover_found": bool(saved)}
        dump(HERE / f"run-{number}-result.json", row)
        runs.append(row)
        if saved or timed_out or process.returncode != 0 or outcome is None:
            break
    dump(HERE / "result.json", {
        "manifest_sha256": sha(manifest_path), "gate_sha256": sha(gate_path),
        "runs": runs, "cover_found": any(r["cover_found"] for r in runs), "relaunch": False,
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.rglob("*"))
                      if p.is_file()}, "scope": manifest["scope"],
    })
    print(json.dumps({"runs": len(runs), "cover_found": any(r["cover_found"] for r in runs),
                      "result_sha256": sha(HERE / "result.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--child", type=int, choices=(1, 2, 3))
    group.add_argument("--execute", type=Path, metavar="GATE")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.child:
        child(args.child)
    else:
        execute(args.execute)
