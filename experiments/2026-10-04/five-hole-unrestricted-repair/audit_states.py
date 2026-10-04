# Document:    Unrestricted Five-Hole Repair State Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3a978f5620bf52ffacac90962d8096ee7b949e34109f4118f95e9686c1ee79a2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recover accepted states, independently recount, and run both cover checkers."""

import json
import subprocess
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/five-hole-unrestricted-repair-2026104061"
SEED = ROOT / "experiments/2026-10-04/lp-guided-best-lp/seed.txt"
OLD = ROOT / "experiments/scratch/heuristic-tabu-2026100301-deficit-3.txt"
CORE = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
BLOCKS = list(combinations(range(1, 17), 5))
TRIPLES = list(combinations(range(1, 17), 3))


def read(path):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) and all(b in BLOCKS for b in blocks)
    return sorted(blocks)


def profile(blocks):
    counts = Counter(t for b in blocks for t in combinations(b, 3))
    degrees = Counter(p for b in blocks for p in b)
    return {
        "blocks": len(blocks),
        "missing": [list(t) for t in TRIPLES if counts[t] == 0],
        "point_degrees": [degrees[p] for p in range(1, 17)],
        "degree_histogram": sorted(Counter(degrees.values()).items()),
        "triple_histogram": sorted(Counter(counts[t] for t in TRIPLES).items()),
        "heavy_triples_at_least_six": [[list(t), counts[t]] for t in TRIPLES if counts[t] >= 6],
    }


def save_and_verify(name, ids):
    blocks = sorted(BLOCKS[i] for i in ids)
    assert len(blocks) == len(set(blocks)) == 64
    path = HERE / f"{name}.txt"
    path.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
    direct = profile(blocks)
    outputs = {}
    for label, command in [
        ("package", [str(ROOT / ".venv/bin/covering64"), "verify"]),
        ("standalone", [sys.executable, str(ROOT / "scripts/check_cover.py")]),
    ]:
        proc = subprocess.run(
            command + [str(path), "--expected-blocks", "64"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        result = json.loads(proc.stdout)
        (HERE / f"{name}-{label}.json").write_text(json.dumps(result, indent=2) + "\n")
        assert proc.returncode == (1 if direct["missing"] else 0)
        assert result["valid"] == (not direct["missing"])
        assert result["blocks"] == 64
        assert result["uncovered"] == direct["missing"]
        outputs[label] = {
            "exit": proc.returncode,
            "sha256": sha256(proc.stdout.encode()).hexdigest(),
        }
    return {
        "name": name,
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "profile": direct,
        "verifiers": outputs,
    }


def main():
    initial = [BLOCKS.index(b) for b in read(SEED)]
    current = initial.copy()
    states = [save_and_verify("initial", initial)]
    traces, improvements = 0, 0
    for line in (RAW / "repair-traces.jsonl").read_text().splitlines():
        record = json.loads(line)
        assert record["start_ids"] == current
        traces += 1
        if record["kind"] == "improvement":
            assert record["deficit"] < len(profile([BLOCKS[i] for i in current])["missing"])
            current = record["end_ids"]
            improvements += 1
            states.append(save_and_verify(f"accepted-{improvements:03}", current))
        else:
            assert record["kind"] == "explored"
    states.append(save_and_verify("best", current))
    states.append(save_and_verify("terminal", current))
    best = read(HERE / "best.txt")
    assert best == read(RAW / "repair-best.txt")
    result = json.loads((HERE / "result.json").read_text())
    trace_audit = json.loads((HERE / "trace-audit.json").read_text())
    assert traces == result["final"]["trees"] == trace_audit["traces"]
    assert trace_audit["passed"]
    assert len(profile(best)["missing"]) == result["final"]["best_deficit"]
    old, core = read(OLD), read(CORE)
    structure = json.loads((HERE / "core-structure.json").read_text())
    mapping = structure["mapping_images_of_1_to_16"]
    assert sorted(mapping) == list(range(1, 17))
    mapped_core = {tuple(sorted(mapping[p - 1] for p in b)) for b in core}
    assert len(mapped_core) == 60 and mapped_core <= set(best)
    comparison = {
        "old_seed_path": str(OLD.relative_to(ROOT)),
        "old_seed_sha256": sha256(OLD.read_bytes()).hexdigest(),
        "old_profile": profile(old),
        "core_path": str(CORE.relative_to(ROOT)),
        "core_sha256": sha256(CORE.read_bytes()).hexdigest(),
        "new_original_label_core_overlap": len(set(best) & set(core)),
        "old_original_label_core_overlap": len(set(old) & set(core)),
        "new_old_labeled_overlap": len(set(best) & set(old)),
        "contains_relabelled_core": True,
        "directly_checked_core_mapping": mapping,
        "different_degree_histogram": profile(best)["degree_histogram"]
        != profile(old)["degree_histogram"],
        "different_triple_histogram": profile(best)["triple_histogram"]
        != profile(old)["triple_histogram"],
    }
    audit = {
        "passed": True,
        "traces": traces,
        "accepted_improvements": improvements,
        "states": states,
        "comparison": comparison,
        "terminal_is_latest_accepted_best": True,
        "checker_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "One bounded unrestricted repair; all states remain near-covers.",
    }
    (HERE / "state-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "states": len(states),
                "comparison": comparison,
                "new_profile": profile(best),
            }
        )
    )


if __name__ == "__main__":
    main()
