# Document:    Two-Partition Profile-Avoiding Heterogeneous Pool Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a22b5f3c930452e4176e8b20ba66e018e055dbbfbbee3c1bcf434c19d055d3ce
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare or run two mixed block pools with declared core and profile restrictions."""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations, product
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/heterogeneous-profile-pool-20261004"
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
    core = [
        tuple(map(int, line.split()))
        for line in (ROOT / inventory["core_path"]).read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(core) == len(set(core)) == 60
    result = []
    for source in inventory["entries"][:2]:
        images = source["known_checked_core_map_images"]
        assert sorted(images) == list(range(1, 17))
        ids = sorted(RANK[tuple(sorted(images[p - 1] for p in block))] for block in core)
        assert len(set(ids)) == 60
        result.append(ids)
    return result


def partitions():
    source = ROOT / "experiments/2026-10-04/heterogeneous-five-heavy-screen/audit.json"
    rows = json.loads(source.read_text())["partitions"]
    assert len(rows) == 2
    for row in rows:
        assert len(row) == 5 and len({p for t in row for p in t}) == 15
        assert all(tuple(t) in TRIPLES for t in row)
    return rows


def threshold_truth_table():
    local = []
    for count in range(79):
        admitted = []
        for six, seven in product((0, 1), repeat=2):
            if (count >= 6 if six else count <= 5) and (count >= 7 if seven else count <= 6):
                admitted.append([six, seven])
        assert admitted == [[int(count >= 6), int(count >= 7)]]
        local.append({"count": count, "unique_indicators": admitted[0]})
    table = []
    damaged = {"bound_25": 0, "bound_27": 0, "six_coefficient_4": 0, "unconditional_seven_cap": 0}
    for counts in product((5, 6, 7), repeat=5):
        six = [int(c >= 6) for c in counts]
        seven = [int(c >= 7) for c in counts]
        forbidden = all(six) and sum(seven) >= 2
        score = 5 * sum(six) + sum(seven)
        assert (score <= 26) == (not forbidden)
        table.append(
            {
                "category_representatives": counts,
                "six": six,
                "seven": seven,
                "weighted_sum": score,
                "forbidden": forbidden,
            }
        )
        for name, admitted in {
            "bound_25": score <= 25,
            "bound_27": score <= 27,
            "six_coefficient_4": 4 * sum(six) + sum(seven) <= 26,
            "unconditional_seven_cap": sum(seven) <= 1,
        }.items():
            damaged[name] += admitted != (not forbidden)
    assert len(table) == 243 and sum(row["forbidden"] for row in table) == 26
    assert all(damaged.values())
    return {
        "optimizer_calls": 0,
        "category_meanings": ["count<6", "count=6", "count>=7"],
        "local_counts": local,
        "per_partition_cases": 243,
        "forbidden_cases": 26,
        "allowed_cases": 217,
        "table": table,
        "damaged_rule_mismatches": damaged,
    }


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
    indicators = []
    for partition_index, partition in enumerate(partitions()):
        sixes, sevens = [], []
        for position, triple in enumerate(partition):
            triple_id = TRIPLES.index(tuple(triple))
            count = sum(variables[i] for i in SUPPORT[triple_id])
            six = model.new_bool_var(f"partition_{partition_index}_triple_{position}_at_least_6")
            seven = model.new_bool_var(f"partition_{partition_index}_triple_{position}_at_least_7")
            model.add(count >= 6).only_enforce_if(six)
            model.add(count <= 5).only_enforce_if(six.Not())
            model.add(count >= 7).only_enforce_if(seven)
            model.add(count <= 6).only_enforce_if(seven.Not())
            sixes.append(six)
            sevens.append(seven)
            indicators.extend([(six, triple_id, 6), (seven, triple_id, 7)])
        model.add(5 * sum(sixes) + sum(sevens) <= 26)
    model.minimize(sum(holes))
    chosen = set(hint)
    for i, variable in enumerate(variables):
        model.add_hint(variable, int(i in chosen))
    missing = set(profile(hint)["holes"])
    for i, hole in enumerate(holes):
        model.add_hint(hole, int(i in missing))
    for indicator, triple_id, threshold in indicators:
        model.add_hint(indicator, int(len(chosen.intersection(SUPPORT[triple_id])) >= threshold))
    return model, variables, holes


def prepare(seed_list):
    assert not (HERE / "manifest.json").exists()
    seed_list = seed_list.resolve()
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
    hint_source = next(row for row in sources if Path(row["path"]).stem == "g5-raw-17")
    hint = hint_source["ids"]
    assert len(profile(hint)["holes"]) == 17
    assert all(len(set(hint) & set(core)) <= 59 for core in cores)
    partition_rows = partitions()
    hint_profiles = [
        [len(set(hint).intersection(SUPPORT[TRIPLES.index(tuple(t))])) for t in row]
        for row in partition_rows
    ]
    assert all(not (min(row) >= 6 and sum(n >= 7 for n in row) >= 2) for row in hint_profiles)
    truth_table = threshold_truth_table()
    dump(HERE / "threshold-truth-table.json", truth_table)
    additions = random.Random(SEED).sample(sorted(set(range(len(BLOCKS))) - elite), 60)
    pools = {"elite": sorted(elite), "expanded": sorted(elite | set(additions))}
    cases = []
    for name, pool in pools.items():
        model, _, _ = build_model(pool, hint)
        path = RAW / f"{name}-model.pbtxt"
        path.write_text(str(model.proto))
        support_sizes = [len(set(pool).intersection(s)) for s in SUPPORT]
        cases.append(
            {
                "name": name,
                "pool": pool,
                "model_path": str(path.relative_to(ROOT)),
                "model_sha256": sha(path),
                "support_histogram": sorted(Counter(support_sizes).items()),
            }
        )
    proof_dir = ROOT / "experiments/2026-10-03/five-heavy-triples"
    proof_paths = [proof_dir / name for name in ("README.md", "check.py", "result.json")]
    proof = json.loads((proof_dir / "result.json").read_text())
    assert proof["complete"] and proof["assignments_checked"] == 27040
    assert proof["feasible_two_sevenfold_assignments"] == 0
    assert proof["source_sha256"] == sha(proof_dir / "check.py")
    input_paths = (
        [
            ROOT / "experiments/2026-10-04/heterogeneous-core-pool/run.py",
            ROOT / "experiments/2026-10-04/heterogeneous-core-pool/manifest.json",
            ROOT / "experiments/2026-10-04/heterogeneous-core-pool-independent/gate.json",
            ROOT / "experiments/2026-10-04/heterogeneous-core-pool-independent/postcheck.json",
            ROOT / "experiments/2026-10-04/heterogeneous-seed-inventory/inventory.json",
            ROOT / "experiments/2026-10-04/heterogeneous-five-heavy-screen/audit.json",
            ROOT / "experiments/2026-10-03/partial-core-holes/core.txt",
            HERE / "threshold-truth-table.json",
            seed_list,
        ]
        + proof_paths
        + [ROOT / row["path"] for row in sources]
    )
    manifest = {
        "source_sha256": sha(__file__),
        "ortools_version": ortools.__version__,
        "python_version": sys.version,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "core_rows": cores,
        "partitions": partition_rows,
        "partition_triple_ids": [[TRIPLES.index(tuple(t)) for t in row] for row in partition_rows],
        "partition_names": ["original_saved_core", "mapped_saved_core"],
        "threshold_indicators": [
            {
                "variable_id": 4928 + 10 * p + 2 * i + (level - 6),
                "partition": p,
                "position": i,
                "triple": t,
                "threshold": level,
            }
            for p, row in enumerate(partition_rows)
            for i, t in enumerate(row)
            for level in (6, 7)
        ],
        "profile_rule": {"six_coefficient": 5, "seven_coefficient": 1, "upper_bound": 26},
        "proof_files": {str(path.relative_to(ROOT)): sha(path) for path in proof_paths},
        "input_files": {str(path.relative_to(ROOT)): sha(path) for path in input_paths},
        "threshold_truth_table_sha256": sha(HERE / "threshold-truth-table.json"),
        "hint_source_path": hint_source["path"],
        "hint_partition_counts": hint_profiles,
        "optimization_calls": 0,
        "seed": SEED,
        "sources": sources,
        "hint": hint,
        "random_additions": additions,
        "cases": cases,
        "budget": {"seconds_per_case": 60, "workers": 4, "cases": 2},
        "scope": "Two finite block pools; all 4368 global block IDs retained. No degree, "
        "hub, heavy-pattern, symmetry, or graph-specific constraints. "
        "Two declared 60-block core-avoidance rows are added "
        "as construction restrictions. Two named five-heavy partitions are also excluded "
        "using the proved conditional obstruction, applied to partial states as "
        "a construction restriction; no all-relabelings claim.",
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "pool_sizes": {k: len(v) for k, v in pools.items()},
                "manifest_sha256": sha(HERE / "manifest.json"),
            }
        )
    )


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
        self.records.append(
            {
                "objective": value,
                "ids": ids,
                "profile": recounted,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
            }
        )
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
    assert partitions() == manifest["partitions"]
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    assert not (RAW / "start.json").exists()
    for source in manifest["sources"]:
        assert sha(ROOT / source["path"]) == source["sha256"]
        assert read_seed(ROOT / source["path"]) == source["ids"]
    dump(
        RAW / "start.json",
        {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "manifest_sha256": sha(HERE / "manifest.json"),
            "gate_sha256": sha(gate_path),
        },
    )
    records = []
    for offset, case in enumerate(manifest["cases"]):
        directory = HERE / case["name"]
        directory.mkdir()
        model, variables, holes = build_model(case["pool"], manifest["hint"])
        assert hashlib.sha256(str(model.proto).encode()).hexdigest() == case["model_sha256"]
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60
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
        records.append(
            {
                "name": case["name"],
                "status": solver.status_name(status),
                "seconds": elapsed,
                "objective_bound": solver.best_objective_bound,
                "best_holes": callback.best if callback.records else None,
                "improvements": callback.records,
            }
        )
        dump(
            HERE / "result.json",
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "gate_sha256": sha(gate_path),
                "cases": records,
            },
        )
        if callback.best == 0:
            break
    print(
        json.dumps(
            [{k: r[k] for k in ("name", "status", "seconds", "best_holes")} for r in records]
        )
    )


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
