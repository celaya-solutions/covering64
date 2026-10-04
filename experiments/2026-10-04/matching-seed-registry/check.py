# Document:    Saved Native Matching Seed Registry Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6c8fe207956eff5ccdc0f562fe82105d09fe57466b6b8bb447d186dbe239f817
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read-only classification and recount of the saved matching native records."""

import importlib.util
import json
import subprocess
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT / "experiments/2026-10-03"
HELPER = HERE.parent / "lp-guided-first-link-registry-independent/check.py"
SCORER = OLD / "four-seven-template-native-soft/audit.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    checker = load(HELPER, "matching_registry_classifier")
    scorer = load(SCORER, "frozen_matching_score_auditor")
    registry, representatives, lookup, graphs = checker.load_catalog()
    assert graphs[5] == (2, 0, 0, 0, 0, 2)
    pairs = list(combinations(range(1, 17), 2))
    hub_pairs = list(combinations([4, 8, 12, 16], 2))
    results = []
    for label, path in [
        ("native-21", OLD / "four-seven-template-native/matching-best.txt"),
        ("soft-raw-17", OLD / "four-seven-template-native-soft/matching-raw-best.txt"),
        ("soft-score-19", OLD / "four-seven-template-native-soft/matching-score-best.txt"),
    ]:
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert len(blocks) == len(set(blocks)) == 64
        assert all(
            len(b) == 5 and b == tuple(sorted(set(b))) and set(b) <= set(range(1, 17))
            for b in blocks
        )
        degrees = Counter(p for b in blocks for p in b)
        assert set(degrees) == set(range(1, 17)) and set(degrees.values()) == {20}
        scores = scorer.score_components(blocks, "matching")
        targets = dict(zip(pairs, scores["pair_targets_lexicographic"], strict=True))
        assert [targets[pair] for pair in hub_pairs] == [7, 5, 5, 5, 5, 7]
        pair_counts = Counter(pair for b in blocks for pair in combinations(b, 2))
        triple_counts = Counter(t for b in blocks for t in combinations(b, 3))
        holes = [t for t in combinations(range(1, 17), 3) if triple_counts[t] == 0]
        assert len(holes) == scores["holes"]
        assert sum(abs(pair_counts[p] - targets[p]) for p in pairs) == scores["pair_target_l1"]
        links = []
        for group, anchor in enumerate(checker.ANCHORS):
            link = [b for b in blocks if anchor <= set(b)]
            assert len(link) == 7
            matches = checker.classify(link, group, graphs[5], representatives, lookup)
            identifier, mapping = matches[0]
            links.append(
                {
                    "anchor_group": group,
                    "representative": identifier,
                    "registry_excluded": identifier in registry["proof_sources"],
                    "physical_to_representative": mapping,
                    "both_transports_agree": True,
                    "heavy_blocks": link,
                    "proof_sources": registry["proof_sources"].get(identifier, []),
                }
            )
        for name, command in [
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
            assert proc.returncode == 1 and not result["valid"] and result["blocks"] == 64
            assert result["uncovered"] == list(map(list, holes))
            (HERE / f"{label}-{name}.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(
            {
                "label": label,
                "seed_path": str(path.relative_to(ROOT)),
                "seed_sha256": sha256(path.read_bytes()).hexdigest(),
                "holes": len(holes),
                "scores": scores,
                "intended_hub_graph": 5,
                "intended_hub_pair_targets": [7, 5, 5, 5, 5, 7],
                "actual_hub_pair_counts": [pair_counts[p] for p in hub_pairs],
                "links": links,
                "registry_open_in_graph_5": not any(row["registry_excluded"] for row in links),
            }
        )
    lookahead_seed = OLD / "four-seven-template-native-lookahead/matching-seed.txt"
    assert sha256(lookahead_seed.read_bytes()).hexdigest() == results[1]["seed_sha256"]
    output = {
        "passed": True,
        "optimization_calls": 0,
        "cases": results,
        "best_raw_registry_open_matching_seed": results[1]["seed_path"],
        "best_score_registry_open_matching_seed": results[2]["seed_path"],
        "lookahead_seed_is_same_as_raw_best": True,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "helper_sha256": sha256(HELPER.read_bytes()).hexdigest(),
        "scorer_sha256": sha256(SCORER.read_bytes()).hexdigest(),
        "registry_sha256": sha256(checker.REGISTRY.read_bytes()).hexdigest(),
        "scope": "Registry openness under intended matching graph 5 only. "
        "These partial states do not satisfy all exact pair targets or coverage.",
    }
    (HERE / "audit.json").write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "cases": [
                    {
                        "label": r["label"],
                        "holes": r["holes"],
                        "classes": [x["representative"] for x in r["links"]],
                        "open": r["registry_open_in_graph_5"],
                    }
                    for r in results
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
