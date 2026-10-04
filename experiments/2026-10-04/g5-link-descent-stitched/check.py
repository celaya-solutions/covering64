# Document:    Matching Descent Stitched States
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      cfb19dbbe8c1b43343bdee0102c88bb093198c56a5890afb9641a666fcd1c6de
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Attach the original 36 ordinary blocks and recount; never optimize."""

import json
import subprocess
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    result_path = ROOT / "experiments/2026-10-04/g5-link-descent/result.json"
    seed_path = (
        ROOT / "experiments/2026-10-03/four-seven-template-native-soft/matching-raw-best.txt"
    )
    manifest_path = ROOT / "experiments/2026-10-04/matching-g5-lp/soft-raw-17/manifest.json"
    result = json.loads(result_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    seed = {tuple(map(int, row.split())) for row in seed_path.read_text().splitlines()}
    assert len(seed) == 64 and digest(seed_path) == manifest["seed_sha256"]
    heavy = {tuple(b) for b in manifest["heavy_blocks"]}
    assert len(heavy) == 28 and heavy <= seed
    ordinary = seed - heavy
    assert len(ordinary) == 36
    blocks = list(combinations(range(1, 17), 5))
    triples = list(combinations(range(1, 17), 3))
    records = []
    for round_record in result["rounds"]:
        selected = round_record["selected"]
        updated = {blocks[i] for i in selected["heavy_global_ids"]}
        assert len(updated) == 28 and not updated & ordinary
        candidate = sorted(updated | ordinary)
        path = HERE / f"round-{round_record['round']}.txt"
        path.write_text("".join(" ".join(map(str, b)) + "\n" for b in candidate))
        counts = Counter(t for b in candidate for t in combinations(b, 3))
        missing = [t for t in triples if not counts[t]]
        degrees = Counter(p for b in candidate for p in b)
        receipts = {}
        for label, command in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
        ]:
            proc = subprocess.run(
                command + [str(path), "--expected-blocks", "64"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            report = json.loads(proc.stdout)
            assert proc.returncode == 1 and not proc.stderr
            assert report["blocks"] == 64 and not report["valid"]
            assert report["canonical_sha256"] == digest(path)
            assert report["uncovered"] == [list(t) for t in missing]
            receipt = HERE / f"round-{round_record['round']}-{label}.json"
            receipt.write_text(proc.stdout)
            receipts[label] = {"path": str(receipt.relative_to(ROOT)), "sha256": digest(receipt)}
        record = {
            "round": round_record["round"],
            "path": str(path.relative_to(ROOT)),
            "sha256": digest(path),
            "blocks": 64,
            "holes": len(missing),
            "lp_objective": selected["objective"],
            "uncovered": missing,
            "degree_histogram": sorted(Counter(degrees.values()).items()),
            "triple_histogram": sorted(Counter(counts[t] for t in triples).items()),
            "heavy_global_ids": selected["heavy_global_ids"],
            "verifiers": receipts,
        }
        records.append(record)
        print(round_record["round"], selected["objective"], len(missing), digest(path))
    audit = {
        "optimization_calls": 0,
        "checker_sha256": digest(Path(__file__)),
        "inputs": {
            str(p.relative_to(ROOT)): digest(p) for p in [result_path, seed_path, manifest_path]
        },
        "ordinary_blocks": sorted(ordinary),
        "records": records,
        "scope": "Explicit partial states; elastic score is not the number of holes.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
