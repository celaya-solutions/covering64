# Document:    Fresh Readback of the Point-Star Repair Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4a674a734df10bda14ea542847d8438f5005e4ed7198e0d3a3c613a0e498f3d7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/point-star-repair-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "postcheck.json").exists()
    gate = json.loads((HERE / "gate.json").read_text())
    summary = json.loads((HERE / "summary.json").read_text())
    metadata = json.loads((HERE / "metadata.json").read_text())
    assert summary["gate_sha256"] == sha(HERE / "gate.json")
    assert summary["metadata_sha256"] == gate["metadata_sha256"] == sha(HERE / "metadata.json")
    assert gate["source_sha256"] == sha(HERE / "check.py")
    for relative, expected in gate["verified_inputs"].items():
        assert sha(ROOT / relative) == expected
    universe = list(itertools.combinations(range(1, 17), 5))
    triples = set(itertools.combinations(range(1, 17), 3))
    seed = {
        tuple(map(int, line.split())) for line in (HERE / "initial.txt").read_text().splitlines()
    }
    ids = {block: i for i, block in enumerate(universe)}
    seed_ids = {ids[block] for block in seed}
    rows = []
    assert len(summary["runs"]) == 4
    for run, planned in zip(summary["runs"], metadata["runs"], strict=True):
        assert all(run[key] == value for key, value in planned.items())
        log = RAW / f"p{run['point']}-seed{run['seed']}.log"
        assert sha(log) == run["log_sha256"]
        model = next(model for model in metadata["models"] if model["point"] == run["point"])
        for saved in run["saved"]:
            path = HERE / saved["path"]
            assert sha(path) == saved["sha256"]
            blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
            assert len(blocks) == len(set(blocks)) == 64 and all(block in ids for block in blocks)
            chosen = {ids[block] for block in blocks}
            assert set(model["retained_ids"]) <= chosen
            counts = Counter(
                triple for block in blocks for triple in itertools.combinations(block, 3)
            )
            holes = sorted(triples - counts.keys())
            assert len(holes) == saved["holes"]
            assert sorted(seed_ids - chosen) == saved["deleted_from_initial"]
            assert sorted(chosen - seed_ids) == saved["added_to_initial"]
            old = len(chosen & set(model["removed_ids"]))
            assert old == saved["old_removed_blocks_reselected"]
            assert saved["objective"] == model["weight"] * len(holes) + old
            heavy = sorted((triple, count) for triple, count in counts.items() if count >= 6)
            disjoint = [
                group
                for group in itertools.combinations(heavy, 5)
                if len({p for triple, _ in group for p in triple}) == 15
            ]
            forbidden = [group for group in disjoint if sum(count >= 7 for _, count in group) >= 2]
            profile = saved["profile"]
            assert json.loads(json.dumps(heavy)) == profile["heavy_triples"]
            assert json.loads(json.dumps(disjoint)) == profile["five_disjoint_heavy_sets"]
            assert json.loads(json.dumps(forbidden)) == profile["forbidden_witnesses"]
            assert bool(forbidden) == profile["forbidden_five_heavy_profile"]
            audit = json.loads(path.with_suffix(".audit.json").read_text())
            for checker in ("package", "standalone"):
                assert audit[checker]["canonical_sha256"] == sha(path)
                assert audit[checker]["uncovered"] == [list(t) for t in holes]
                assert audit[checker]["valid"] == (not holes)
            rows.append(
                {
                    "point": run["point"],
                    "seed": run["seed"],
                    "path": saved["path"],
                    "sha256": sha(path),
                    "holes": len(holes),
                    "same_as_seed": set(blocks) == seed,
                    "deleted": len(seed_ids - chosen),
                    "added": len(chosen - seed_ids),
                    "forbidden_profile": bool(forbidden),
                    "status": run["status"],
                    "solver_seconds": run["solver_seconds"],
                    "objective_bound": run["objective_bound"],
                }
            )
    result = {
        "passed": True,
        "date": "2026-10-04",
        "source_sha256": sha(__file__),
        "summary_sha256": sha(HERE / "summary.json"),
        "gate_sha256": sha(HERE / "gate.json"),
        "states": rows,
        "unique_witnesses": len({row["sha256"] for row in rows}),
        "all_same_as_seed": all(row["same_as_seed"] for row in rows),
        "optimization_runs": 0,
        "scope": "Fresh saved-state recount only; no global conclusion.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
