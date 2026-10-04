# Document:    Structural Assessment of the Two Three-Hole States
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      c962a9cb01f69f87bce4a1b3d4a3ba1a19ea00d78c13b0efcc8b4728407ff36a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount known states and their one-block augmentations; do not run a search."""

import hashlib
import itertools as it
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/three-hole-escape-assessment-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    RAW.mkdir(exist_ok=True)
    core_path = HERE.parent / "web-source-evidence/fixed-core-certificate.json"
    core = {tuple(block) for block in json.loads(core_path.read_text())["core_blocks"]}
    prior_path = HERE.parent / "core-orbit/verification.json"
    prior = json.loads(prior_path.read_text())
    gate = next(c for c in prior["checks"] if c["removed_count"] == 4)
    assert gate["valid_certificate"] and gate["complete_obstruction"]
    assert gate["maximum_core_blocks_in_any_64_cover"] == 55
    certificate = prior_path.parent / gate["certificate"]
    assert sha(certificate) == gate["certificate_sha256"]
    paths = [
        HERE.parent / "heuristic-tabu-2026100301-deficit-3.txt",
        HERE.parent / "heavy-profile-neighborhood/improvement-h3.txt",
    ]
    reports, states = [], []
    for index, path in enumerate(paths):
        blocks = [tuple(map(int, row.split())) for row in path.read_text().splitlines()]
        assert len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks)
        states.append(set(blocks))
        counts = Counter(t for block in blocks for t in it.combinations(block, 3))
        holes = sorted(set(it.combinations(range(1, 17), 3)) - set(counts))
        assert len(holes) == 3
        checks = []
        for label, prefix in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", [sys.executable, "scripts/check_cover.py"]),
        ]:
            process = subprocess.run(
                prefix + [str(path), "--expected-blocks", "64"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            data = json.loads(process.stdout)
            assert process.returncode == 1 and not data["valid"]
            assert sorted(map(tuple, data["uncovered"])) == holes
            assert data["canonical_sha256"] == sha(path)
            output = RAW / f"state{index}-{label}.json"
            output.write_text(process.stdout)
            output.with_suffix(".stderr").write_text(process.stderr)
            checks.append(
                {"checker": label, "exit": process.returncode, "output_sha256": sha(output)}
            )
        degrees = Counter(point for block in blocks for point in block)
        pairs = Counter(pair for block in blocks for pair in it.combinations(block, 2))
        quad = set().union(*map(set, holes))
        assert len(quad) == 4 and len(set(blocks) & core) == 60
        private = {
            block: {triple for triple in it.combinations(block, 3) if counts[triple] == 1}
            for block in blocks
        }
        augmentations = []
        for extra in sorted(set(range(1, 17)) - quad):
            inserted = tuple(sorted(quad | {extra}))
            triples = set(it.combinations(inserted, 3))
            assert set(holes) <= triples and inserted not in set(blocks)
            losses = [len(private[block] - triples) for block in blocks]
            augmentations.append(
                {
                    "inserted_block": inserted,
                    "minimum_holes_after_one_old_block_deleted": min(losses),
                    "minimum_attained_by": losses.count(min(losses)),
                }
            )
        reports.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "holes": holes,
                "checks": checks,
                "point_degrees": [degrees[p] for p in range(1, 17)],
                "pair_histogram": dict(Counter(pairs.values())),
                "triple_histogram": dict(Counter(counts.values())),
                "core_overlap": len(set(blocks) & core),
                "hole_quad": sorted(quad),
                "private_triple_histogram": dict(Counter(map(len, private.values()))),
                "all_twelve_full_65_augmentations": augmentations,
            }
        )
    result = {
        "source_sha256": sha(Path(__file__)),
        "states": reports,
        "shared_blocks": len(states[0] & states[1]),
        "core_source_sha256": sha(core_path),
        "prior_gate_sha256": sha(prior_path),
        "prior_certificate_sha256": sha(certificate),
        "previously_checked_maximum_core_overlap_in_a_64_cover": 55,
        "scope": "Structural recount of known states and 12 direct augmentations per "
        "state. Uses existing checked core certificate; no new solver or pilot.",
    }
    (HERE / "assessment.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "states": len(reports),
                "shared_blocks": result["shared_blocks"],
                "core_overlap": [r["core_overlap"] for r in reports],
            }
        )
    )


if __name__ == "__main__":
    main()
