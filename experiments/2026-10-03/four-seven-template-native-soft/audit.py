# Document:    Soft-Score Complete Template Native State and Move Audit
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ffd4c92ec8abf19c1b4d31079cc982a440f406dc09ccc775223dffdcb382c110
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independently check frozen catalog bytes, every saved state and move traces."""

import argparse
import functools
import gzip
import hashlib
import itertools as it
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-native-v1.1.0"
ANCHORS = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
TRIPLES = set(it.combinations(range(1, 17), 3))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordinary(block):
    return all(len(set(block) & anchor) <= 1 for anchor in ANCHORS)


@functools.lru_cache(maxsize=2)
def catalog(name):
    case = next(
        c for c in json.loads((HERE / "seeds.json").read_text())["cases"] if c["name"] == name
    )
    source = ROOT / case["source_catalog_path"]
    pack = ROOT / case["catalog_path"]
    require(sha(source) == case["source_catalog_sha256"], "catalog source hash mismatch")
    require(sha(pack) == case["catalog_sha256"], "catalog pack hash mismatch")
    groups = json.loads(gzip.decompress(source.read_bytes()))
    indices = []
    with pack.open() as stream:
        require(
            stream.readline().split() == ["C64T1", name] + [str(case["templates_per_group"])] * 4,
            "pack header mismatch",
        )
        for group, data in enumerate(groups):
            mapping = {}
            require(len(data["templates"]) == case["templates_per_group"], "source count mismatch")
            for index, template in enumerate(data["templates"]):
                expected = [group + 1, index + 1, *(p for edge in template for p in edge)]
                require(
                    list(map(int, stream.readline().split())) == expected,
                    "pack differs from source",
                )
                key = tuple(sorted(tuple(edge) for edge in template))
                require(
                    key not in mapping and len(set(key)) == 7, "duplicate catalog template/edge"
                )
                degree = Counter(p for edge in key for p in edge)
                require(
                    degree
                    == {
                        p: 2 if p == 4 * group + 4 else 1
                        for p in range(1, 17)
                        if p not in ANCHORS[group]
                    },
                    "catalog incidence mismatch",
                )
                mapping[key] = index + 1
            indices.append(mapping)
        require(stream.read() == "", "extra pack data")
    return indices


def blocks(path):
    result = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    require(len(result) == len(set(result)) == 64 and result == sorted(result), "block inventory")
    require(
        all(
            len(b) == len(set(b)) == 5 and b == tuple(sorted(b)) and min(b) >= 1 and max(b) <= 16
            for b in result
        ),
        "malformed block",
    )
    return result


def score_components(candidate, name):
    pairs = Counter(p for block in candidate for p in it.combinations(block, 2))
    triples = Counter(t for block in candidate for t in it.combinations(block, 3))
    targets = {pair: 5 for pair in it.combinations(range(1, 17), 2)}
    for anchor in ANCHORS:
        for pair in it.combinations(sorted(anchor), 2):
            targets[pair] = 7
        for point in anchor:
            targets[(point, max(anchor) + 1)] = 6
    hub_edges = [(4, 8), (12, 16)] if name == "matching" else [(4, 8), (8, 12), (12, 16), (4, 16)]
    for edge in hub_edges:
        targets[edge] = 7 if name == "matching" else 6
    require(sum(targets.values()) == 640, "pair target total")
    heavy = {tuple(sorted(anchor)) for anchor in ANCHORS}
    nonheavy = [triples[triple] for triple in sorted(TRIPLES - heavy)]
    holes = len(TRIPLES - set(triples))
    pair_l1 = sum(abs(pairs[pair] - target) for pair, target in targets.items())
    excess = sum(max(0, count - 2) for count in nonheavy)
    return {
        "holes": holes,
        "pair_target_l1": pair_l1,
        "nonheavy_excess": excess,
        "score": 5 * holes + pair_l1 + 5 * excess,
        "nonheavy_max": max(nonheavy),
        "nonheavy_over_two": sum(count > 2 for count in nonheavy),
        "nonheavy_histogram": dict(sorted(Counter(nonheavy).items())),
        "pair_targets_lexicographic": list(targets.values()),
    }


def check_score_event(event, before, after, name):
    first = score_components(before, name)
    last = score_components(after, name)
    for field in ["holes", "score"]:
        require(event[f"{field}_before"] == first[field], f"wrong {field} before")
        require(event[f"{field}_after"] == last[field], f"wrong {field} after")
    return {
        "hole_delta": last["holes"] - first["holes"],
        "score_delta": last["score"] - first["score"],
    }


def analyze(candidate, case):
    mappings = catalog(case["name"])
    require(
        Counter(p for b in candidate for p in b) == {p: 20 for p in range(1, 17)}, "degree20 drift"
    )
    free = [b for b in candidate if ordinary(b)]
    require(len(free) == 36, "ordinary block count")
    require(
        Counter(p for b in free for p in b) == {p: 15 if p % 4 == 0 else 10 for p in range(1, 17)},
        "ordinary degree drift",
    )
    selected = []
    accounted = set(free)
    for group, anchor in enumerate(ANCHORS):
        heavy = [b for b in candidate if anchor <= set(b)]
        require(len(heavy) == 7, "heavy group count")
        edges = tuple(sorted(tuple(p for p in b if p not in anchor) for b in heavy))
        require(edges in mappings[group], "heavy template absent from frozen catalog")
        selected.append(mappings[group][edges])
        accounted.update(heavy)
    require(accounted == set(candidate), "unclassified block")
    triples = Counter(t for b in candidate for t in it.combinations(b, 3))
    missing = sorted(TRIPLES - set(triples))
    require(
        all(all(len(set(t) & anchor) <= 1 for anchor in ANCHORS) for t in missing),
        "anchor-pair triple uncovered",
    )
    pairs = Counter(p for b in candidate for p in it.combinations(b, 2))
    return {
        **score_components(candidate, case["name"]),
        "missing": missing,
        "template_ids_1based": selected,
        "pair_counts_lexicographic": [pairs[p] for p in it.combinations(range(1, 17), 2)],
        "pair_histogram": dict(
            sorted(Counter(pairs[p] for p in it.combinations(range(1, 17), 2)).items())
        ),
    }


def inspect(path, case):
    result = analyze(blocks(path), case)
    digest = sha(path)
    directory = RAW / "verifier-output"
    directory.mkdir(exist_ok=True)
    checks = []
    for label, prefix in [
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", [sys.executable, "scripts/check_cover.py"]),
    ]:
        command = prefix + [str(path.resolve()), "--expected-blocks", "64"]
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        raw = directory / f"{digest}.{label}.json"
        raw.write_text(process.stdout)
        raw.with_suffix(".stderr").write_text(process.stderr)
        data = json.loads(process.stdout)
        require(process.returncode == int(result["holes"] != 0), "checker exit mismatch")
        require(
            data["valid"] == (result["holes"] == 0) and data["blocks"] == 64,
            "checker status mismatch",
        )
        require(
            sorted(map(tuple, data["uncovered"])) == result["missing"],
            "missing-triple disagreement",
        )
        require(data["canonical_sha256"] == digest, "checker hash mismatch")
        checks.append(
            {
                "command": command,
                "exit": process.returncode,
                "output_path": str(raw.relative_to(ROOT)),
                "output_sha256": sha(raw),
            }
        )
    result.pop("missing")
    return {"path": str(path.relative_to(ROOT)), "sha256": digest, **result, "checks": checks}


def audit(folder):
    cases = json.loads((HERE / "seeds.json").read_text())["cases"]
    reports, operations = [], []
    for case in cases:
        name = case["name"]
        catalog(name)
        for path in sorted(folder.glob(f"{name}-*.txt")):
            if path.name.endswith("-catalog.txt"):
                continue
            reports.append(inspect(path, case))
        for path in sorted(folder.glob(f"{name}*.log")):
            events = [json.loads(line) for line in path.read_text().splitlines()]
            early_cover = any(e.get("reason") == "control_cover" for e in events)
            for event in events:
                if event.get("event") != "operation":
                    continue
                before = set(blocks(Path(event["before"])))
                after = set(blocks(Path(event["after"])))
                event["independent_delta"] = check_score_event(event, before, after, name)
                removed, added = set(map(tuple, event["removed"])), set(map(tuple, event["added"]))
                require(removed <= before and not added & (before - removed), "move collision")
                require((before - removed) | added == after, "move differs from snapshots")
                require(
                    Counter(p for b in removed for p in b) == Counter(p for b in added for p in b),
                    "move changes degree",
                )
                require(len(removed) == len(added), "move changes block count")
                if event["mode"] == 3:
                    group = event["template_group"] - 1
                    require(group in range(4) and len(removed) == 7, "invalid template move")
                    require(
                        removed == {b for b in before if ANCHORS[group] <= set(b)},
                        "partial template",
                    )
                    for state, field in [(before, "template_before"), (after, "template_after")]:
                        require(
                            analyze(sorted(state), case)["template_ids_1based"][group]
                            == event[field],
                            "template move identity mismatch",
                        )
                else:
                    require(
                        event["mode"] in range(3)
                        and 2 <= len(removed) <= 6
                        and all(ordinary(b) for b in removed | added),
                        "invalid ordinary move",
                    )
                if event["role"] == "forced_apply":
                    rollback = Path(event["before"].replace("-before.txt", "-rollback.txt"))
                    if rollback.exists():
                        require(blocks(rollback) == sorted(before), "rollback mismatch")
                        require(
                            score_components(blocks(rollback), name)
                            == score_components(before, name),
                            "score rollback mismatch",
                        )
                    else:
                        require(
                            early_cover and analyze(sorted(after), case)["holes"] == 0,
                            "missing rollback without verified early cover",
                        )
                operations.append(event)
    require(bool(reports), "no snapshots")
    return {
        "checker_sha256": sha(Path(__file__)),
        "snapshots": reports,
        "operations": operations,
        "snapshot_count": len(reports),
        "operation_count": len(operations),
        "covers": sum(r["holes"] == 0 for r in reports),
        "scope": (
            "Construction heuristic with soft pair and nonheavy overcoverage penalties; "
            "no exclusion claim."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.folder.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["snapshot_count", "operation_count", "covers"]}))
