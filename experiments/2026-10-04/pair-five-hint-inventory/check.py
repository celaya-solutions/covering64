# Document:    Audited Pair-Five Hint Inventory
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      322297d698dfc4c32936002d5388e41a6563c2d97083b5ce98e53462974a6556
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount a declared set of saved states; never call an optimizer."""

import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NATIVE = ROOT / "experiments/2026-10-03/reduced-family-heuristic"
DAY = ROOT / "experiments/2026-10-04"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}
PAIRS = list(itertools.combinations(range(1, 17), 2))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
NATIVE_FOLDERS = (
    "clean-penalty-2026100367",
    "full-penalty-2026100366",
    "penalty-2026100363",
    "sanitizer-v1.2.1-2026100363",
    "sanitizer-v1.3-2026100366",
    "sanitizer-v1.3-final-2026100366",
    "strong-penalty-2026100365",
    "trades-2026100362",
)
POSTCHECKS = (
    "heterogeneous-core-pool-independent/postcheck.json",
    "heterogeneous-profile-postcheck/audit.json",
    "six-hole-strong-core-release-independent/postcheck.json",
    "three-core-profile-release-independent/postcheck.json",
    "global-five-heavy-dp-independent/postcheck.json",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def parse(text):
    blocks = [tuple(map(int, line.split())) for line in text.splitlines() if line.strip()]
    if len(blocks) != 64 or len(set(blocks)) != 64 or any(b not in RANK for b in blocks):
        raise ValueError("expected 64 distinct ascending five-element blocks on labels 1..16")
    return blocks


def candidate_bindings(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and value["path"].endswith(".txt"):
            checksum = value.get("sha256")
            if isinstance(checksum, str) and len(checksum) == 64:
                yield value["path"], checksum
        for child in value.values():
            yield from candidate_bindings(child)
    elif isinstance(value, list):
        for child in value:
            yield from candidate_bindings(child)


def partition_maximum(counts):
    positive = [
        (sum(1 << (point - 1) for point in triple), 5 + int(counts[triple] >= 7))
        for triple in TRIPLES
        if counts[triple] >= 6
    ]

    @lru_cache(maxsize=None)
    def visit(start, used):
        # At most five disjoint triples fit in sixteen points.
        best = 0
        for index in range(start, len(positive)):
            mask, weight = positive[index]
            if not mask & used:
                best = max(best, weight + visit(index + 1, used | mask))
        return best

    return visit(0, 0)


def profile(blocks, cores):
    ids = sorted(RANK[block] for block in blocks)
    pairs = Counter(pair for block in blocks for pair in itertools.combinations(block, 2))
    triples = Counter(triple for block in blocks for triple in itertools.combinations(block, 3))
    points = Counter(point for block in blocks for point in block)
    overlaps = [len(set(ids) & core) for core in cores]
    basic = min(pairs[pair] for pair in PAIRS) >= 5 and max(overlaps) <= 55
    maximum = partition_maximum(triples) if basic else None
    return {
        "ids": ids,
        "holes": sum(triples[triple] == 0 for triple in TRIPLES),
        "uncovered": [triple for triple in TRIPLES if triples[triple] == 0],
        "minimum_pair_count": min(pairs[pair] for pair in PAIRS),
        "pairs_below_five": sum(pairs[pair] < 5 for pair in PAIRS),
        "pair_histogram": dict(sorted(Counter(pairs[pair] for pair in PAIRS).items())),
        "minimum_point_degree": min(points.values()),
        "point_degrees": [points[point] for point in range(1, 17)],
        "core_overlaps": overlaps,
        "heavy_triples": [
            {"triple": triple, "count": triples[triple]}
            for triple in TRIPLES
            if triples[triple] >= 6
        ],
        "maximum_partition_weight": maximum,
        "eligible": basic and maximum <= 26,
    }


def main():
    assert not (HERE / "result.json").exists()
    manifest_path = DAY / "global-five-heavy-dp/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    cores = [set(core) for core in manifest["core_rows"]]
    assert len(cores) == 3 and all(len(core) == 60 for core in cores)
    audits = [NATIVE / name / "metric-audit.json" for name in NATIVE_FOLDERS]
    audits.extend(DAY / name for name in POSTCHECKS)
    candidates, audit_bindings = {}, {}
    for audit_path in audits:
        data = json.loads(audit_path.read_text())
        if audit_path.parent.parent == NATIVE:
            assert data["records"] and data["snapshots"] == len(data["records"])
        else:
            assert data["passed"]
        audit_bindings[relative(audit_path)] = sha(audit_path)
        for name, checksum in candidate_bindings(data):
            path = Path(name)
            if not path.is_absolute():
                path = ROOT / path
            assert path.is_relative_to(ROOT) and sha(path) == checksum
            key = relative(path)
            item = candidates.setdefault(key, {"path": key, "sha256": checksum, "audits": []})
            assert item["sha256"] == checksum
            if relative(audit_path) not in item["audits"]:
                item["audits"].append(relative(audit_path))
    cache, rows = {}, []
    for item in sorted(candidates.values(), key=lambda item: item["path"]):
        blocks = parse((ROOT / item["path"]).read_text())
        signature = tuple(sorted(blocks))
        if signature not in cache:
            cache[signature] = profile(blocks, cores)
        rows.append(item | cache[signature])
    eligible = sorted(
        (row for row in rows if row["eligible"]),
        key=lambda row: (row["holes"], row["core_overlaps"][0], row["path"]),
    )
    assert eligible
    best = eligible[0]
    verifiers = []
    for label, command in [
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", [sys.executable, "scripts/check_cover.py"]),
    ]:
        command += [str(ROOT / best["path"]), "--expected-blocks", "64"]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        report = json.loads(run.stdout)
        assert run.returncode == int(best["holes"] != 0) and not run.stderr
        assert report["blocks"] == 64 and report["valid"] == (best["holes"] == 0)
        assert report["canonical_sha256"] == best["sha256"]
        assert report["uncovered"] == [list(triple) for triple in best["uncovered"]]
        out = HERE / ("best-" + label + ".json")
        out.write_text(run.stdout)
        verifiers.append({"path": relative(out), "sha256": sha(out), "exit": run.returncode})
    blocks = parse((ROOT / best["path"]).read_text())
    controls = {
        "missing_block": blocks[:-1],
        "duplicate_block": blocks[:-1] + [blocks[0]],
        "repeated_label": [(1, 1, 2, 3, 4)] + blocks[1:],
        "outside_label": [(1, 2, 3, 4, 17)] + blocks[1:],
    }
    rejected = []
    for name, damaged in controls.items():
        try:
            parse("\n".join(" ".join(map(str, block)) for block in damaged))
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError(name)
    native_bindings = {}
    historical_bindings = []
    historical = ROOT / "experiments/scratch/reduced-family-heuristic-20261003"
    historical_files = [path for path in historical.iterdir() if path.is_file()]

    def bind_historical(name, checksum):
        direct = ROOT / name
        matches = [direct] if direct.is_file() and sha(direct) == checksum else []
        matches += [path for path in historical_files if sha(path) == checksum]
        assert matches, (name, checksum)
        resolved = matches[0]
        native_bindings[relative(resolved)] = checksum
        historical_bindings.append(
            {"declared_path": name, "sha256": checksum, "resolved_path": relative(resolved)}
        )

    for audit_name in best["audits"]:
        audit = json.loads((ROOT / audit_name).read_text())
        if "native_source_hashes" in audit:
            for name, checksum in audit["native_source_hashes"].items():
                bind_historical(name, checksum)
            bind_historical(relative(NATIVE / "audit_campaign_metrics.py"), audit["source_sha256"])
            metadata = ROOT / audit_name
            metadata = metadata.with_name("metadata.json")
            native_bindings[relative(metadata)] = sha(metadata)
            metadata_data = json.loads(metadata.read_text())
            for name, checksum in metadata_data["input_hashes"].items():
                input_path = NATIVE / "inputs" / name
                assert sha(input_path) == checksum
                native_bindings[relative(input_path)] = checksum
            binary = Path(metadata_data["command"][0])
            assert sha(binary) == metadata_data["binary_sha256"]
            native_bindings[relative(binary)] = sha(binary)
    sources = {
        relative(Path(__file__)): sha(Path(__file__)),
        relative(manifest_path): sha(manifest_path),
    }
    sources.update(native_bindings)
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "audit_files": audit_bindings,
        "source_files": sources,
        "historical_source_bindings": historical_bindings,
        "candidate_paths": len(rows),
        "distinct_states": len(cache),
        "eligible_paths": len(eligible),
        "eligible_distinct_states": len({row["sha256"] for row in eligible}),
        "selection_order": ["holes", "original_core_overlap", "path"],
        "best": best,
        "best_verifiers": verifiers,
        "malformed_controls_rejected": rejected,
        "records": rows,
        "scope": "Read-only inventory of eight named native metric-audit folders and five named "
        "recent independent postchecks. Best only within this declared inventory. No optimizer.",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "passed",
                    "optimizer_calls",
                    "candidate_paths",
                    "distinct_states",
                    "eligible_paths",
                    "eligible_distinct_states",
                ]
            }
            | {
                "best_path": best["path"],
                "best_holes": best["holes"],
                "best_sha256": best["sha256"],
                "core_overlaps": best["core_overlaps"],
                "minimum_pair_count": best["minimum_pair_count"],
                "maximum_partition_weight": best["maximum_partition_weight"],
            }
        )
    )


if __name__ == "__main__":
    main()
