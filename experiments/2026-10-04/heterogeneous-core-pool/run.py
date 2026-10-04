# Document:    Core-Avoiding Heterogeneous Block Pool Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a52c50efa675635a13f178d89303c7f18b2fedd4efa426d6497062909eadc2ae
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recombine checked partial covers without retaining their family constraints."""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/heterogeneous-core-pool-20261004"
BLOCKS = list(combinations(range(1, 17), 5))
TRIPLES = list(combinations(range(1, 17), 3))
RANK = {block: index for index, block in enumerate(BLOCKS)}
SUPPORT = [[i for i, b in enumerate(BLOCKS) if set(t) <= set(b)] for t in TRIPLES]
SEED = 2026104091


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_seed(path):
    blocks = []
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        block = tuple(sorted(map(int, line.split())))
        if len(block) != 5 or len(set(block)) != 5 or not set(block) <= set(range(1, 17)):
            raise ValueError("malformed block")
        blocks.append(block)
    if len(blocks) != 64 or len(set(blocks)) != 64:
        raise ValueError("exactly 64 distinct blocks required")
    return sorted(RANK[b] for b in blocks)


def profile(ids):
    selected = set(ids)
    counts = [len(selected.intersection(support)) for support in SUPPORT]
    blocks = [BLOCKS[i] for i in ids]
    degrees = [sum(p in b for b in blocks) for p in range(1, 17)]
    pairs = [sum(set(p) <= set(b) for b in blocks) for p in combinations(range(1, 17), 2)]
    return {
        "holes": [i for i, n in enumerate(counts) if n == 0],
        "degree_histogram": sorted(Counter(degrees).items()),
        "pair_histogram": sorted(Counter(pairs).items()),
        "triple_histogram": sorted(Counter(counts).items()),
    }


def core_rows():
    path = ROOT / "experiments/2026-10-04/heterogeneous-seed-inventory/inventory.json"
    inventory = json.loads(path.read_text())
    core = [tuple(map(int, line.split()))
            for line in (ROOT / inventory["core_path"]).read_text().splitlines()
            if line.strip() and not line.startswith("#")]
    assert len(core) == len(set(core)) == 60
    result = []
    for source in inventory["entries"][:2]:
        images = source["known_checked_core_map_images"]
        assert sorted(images) == list(range(1, 17))
        ids = sorted(RANK[tuple(sorted(images[p - 1] for p in block))] for block in core)
        assert len(set(ids)) == 60
        result.append(ids)
    return result


def build_model(pool, hint):
    allowed = set(pool)
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{i}") for i in range(len(BLOCKS))]
    holes = [model.new_bool_var(f"hole_{i}") for i in range(len(TRIPLES))]
    model.add(sum(variables) == 64)
    model.add(sum(variables[i] for i in range(len(BLOCKS)) if i not in allowed) == 0)
    for hole, carriers in zip(holes, SUPPORT, strict=True):
        coverage = sum(variables[i] for i in carriers)
        model.add(coverage >= 1).only_enforce_if(hole.Not())
        model.add(coverage == 0).only_enforce_if(hole)
    for core in core_rows():
        model.add(sum(variables[i] for i in core) <= 59)
    model.minimize(sum(holes))
    chosen = set(hint)
    for i, variable in enumerate(variables):
        model.add_hint(variable, int(i in chosen))
    missing = set(profile(hint)["holes"])
    for i, hole in enumerate(holes):
        model.add_hint(hole, int(i in missing))
    return model, variables, holes


def prepare(seed_list):
    assert not (HERE / "manifest.json").exists()
    RAW.mkdir(parents=True, exist_ok=True)
    sources = []
    elite = set()
    for relative in json.loads(seed_list.read_text()):
        path = ROOT / relative
        ids = read_seed(path)
        sources.append({"path": relative, "sha256": sha(path), "ids": ids, **profile(ids)})
        elite.update(ids)
    assert len(sources) >= 6 and len({tuple(s["ids"]) for s in sources}) == len(sources)
    cores = core_rows()
    eligible = [row for row in sources
                if all(len(set(row["ids"]) & set(core)) <= 59 for core in cores)]
    hint = min(eligible, key=lambda row: len(row["holes"]))["ids"]
    additions = random.Random(SEED).sample(sorted(set(range(len(BLOCKS))) - elite), 60)
    pools = {"elite": sorted(elite), "expanded": sorted(elite | set(additions))}
    cases = []
    for name, pool in pools.items():
        model, _, _ = build_model(pool, hint)
        path = RAW / f"{name}-model.pbtxt"
        path.write_text(str(model.proto))
        support_sizes = [len(set(pool).intersection(s)) for s in SUPPORT]
        cases.append({
            "name": name, "pool": pool, "model_path": str(path.relative_to(ROOT)),
            "model_sha256": sha(path), "support_histogram": sorted(Counter(support_sizes).items()),
        })
    manifest = {
        "source_sha256": sha(__file__), "ortools_version": ortools.__version__,
        "python_version": sys.version,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "core_rows": cores, "seed": SEED, "sources": sources,
        "hint": hint, "random_additions": additions,
        "cases": cases, "budget": {"seconds_per_case": 30, "workers": 4, "cases": 2},
        "scope": "Two finite block pools; all 4368 global block IDs retained. No degree, "
                 "hub, heavy-pattern, symmetry, or graph-specific constraints. "
                 "Two declared 60-block core-avoidance rows are added "
                 "as construction restrictions.",
    }
    dump(HERE / "manifest.json", manifest)
    print(json.dumps({"pool_sizes": {k: len(v) for k, v in pools.items()},
                      "manifest_sha256": sha(HERE / "manifest.json")}))


class SaveBest(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables, holes, directory):
        super().__init__()
        self.variables = variables
        self.holes = holes
        self.directory = directory
        self.best = 561
        self.records = []

    def on_solution_callback(self):
        value = int(round(self.objective_value))
        if value >= self.best:
            return
        ids = [i for i, variable in enumerate(self.variables) if self.value(variable)]
        recounted = profile(ids)
        assert len(ids) == len(set(ids)) == 64
        assert len(recounted["holes"]) == value
        assert [i for i, h in enumerate(self.holes) if self.value(h)] == recounted["holes"]
        path = self.directory / f"best-{len(self.records):02d}-h{value}.txt"
        path.write_text("".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in ids))
        self.records.append({"objective": value, "ids": ids, "profile": recounted,
                             "path": str(path.relative_to(ROOT)), "sha256": sha(path)})
        self.best = value
        if value == 0:
            self.stop_search()


def run(gate_path):
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert manifest["source_sha256"] == sha(__file__)
    assert manifest["ortools_version"] == ortools.__version__
    assert core_rows() == manifest["core_rows"]
    assert not (RAW / "start.json").exists()
    for source in manifest["sources"]:
        assert sha(ROOT / source["path"]) == source["sha256"]
        assert read_seed(ROOT / source["path"]) == source["ids"]
    dump(RAW / "start.json", {"started_utc": datetime.now(timezone.utc).isoformat(),
                               "manifest_sha256": sha(HERE / "manifest.json"),
                               "gate_sha256": sha(gate_path)})
    records = []
    for offset, case in enumerate(manifest["cases"]):
        directory = HERE / case["name"]
        directory.mkdir()
        model, variables, holes = build_model(case["pool"], manifest["hint"])
        assert hashlib.sha256(str(model.proto).encode()).hexdigest() == case["model_sha256"]
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30
        solver.parameters.num_search_workers = 4
        solver.parameters.random_seed = SEED + offset
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = False
        logs = []
        solver.log_callback = logs.append
        callback = SaveBest(variables, holes, directory)
        before = time.monotonic()
        status = solver.solve(model, callback)
        elapsed = time.monotonic() - before
        (RAW / f"{case['name']}-solver.log").write_text("".join(logs))
        (RAW / f"{case['name']}-response.pbtxt").write_text(str(solver.response_proto))
        (RAW / f"{case['name']}-parameters.pbtxt").write_text(str(solver.parameters))
        records.append({"name": case["name"], "status": solver.status_name(status),
                        "seconds": elapsed, "objective_bound": solver.best_objective_bound,
                        "best_holes": callback.best if callback.records else None,
                        "improvements": callback.records})
        dump(HERE / "result.json", {"manifest_sha256": sha(HERE / "manifest.json"),
                                    "gate_sha256": sha(gate_path), "cases": records})
        if callback.best == 0:
            break
    print(json.dumps([{k: r[k] for k in ("name", "status", "seconds", "best_holes")}
                      for r in records]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", type=Path, metavar="SEED_LIST_JSON")
    group.add_argument("--run", type=Path, metavar="GATE_JSON")
    arguments = parser.parse_args()
    if arguments.prepare:
        prepare(arguments.prepare)
    else:
        run(arguments.run)
