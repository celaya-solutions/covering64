# Document:    Eligible Candidate Degree Nineteen Link Inventory
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount eligible partials and seek a degree19 point touching no hole."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROFILE_PATH = HERE.parent / "heavy-profile-neighborhood/run.py"
SPEC = importlib.util.spec_from_file_location("profile_inventory", PROFILE_PATH)
PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROFILE)


def main():
    paths = list((ROOT / "experiments/2026-10-03/heavy-profile-search").rglob("*.txt"))
    for directory in ("heavy-profile-neighborhood-h6-20261003",
                      "heavy-profile-neighborhood-cuts-h6-20261003"):
        paths.extend((ROOT / "experiments/scratch" / directory).glob("attempt-*/candidate.txt"))
    records, seen = [], set()
    for path in sorted(paths):
        try:
            blocks = read_blocks(path)
        except ValueError:
            continue
        if len(blocks) != 64:
            continue
        package = verify_cover(blocks)
        digest = package["canonical_sha256"]
        if digest in seen:
            continue
        seen.add(digest)
        profile = PROFILE.profile(blocks)
        if profile["forbidden_five_disjoint"] is not None:
            continue
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_cover.py"), str(path),
             "--expected-blocks", "64"], capture_output=True, text=True,
        )
        if proc.returncode not in (0, 1):
            raise ValueError(f"standalone checker failed: {path}")
        standalone = json.loads(proc.stdout)
        if (standalone["canonical_sha256"] != digest
                or standalone["uncovered_count"] != len(package["uncovered"])):
            raise ValueError("cover checker reports disagree")
        counts = Counter(point for block in blocks for point in block)
        nineteen = [{"point": p, "incident_holes": [t for t in package["uncovered"] if p in t]}
                    for p, count in sorted(counts.items()) if count == 19]
        records.append({
            "path": str(path.relative_to(ROOT)), "canonical_sha256": digest,
            "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "holes": len(package["uncovered"]), "degree19": nineteen,
            "complete_link_points": [r["point"] for r in nineteen if not r["incident_holes"]],
            "profile": profile, "package": package, "standalone": standalone,
        })
    result = {
        "scope": "Saved eligible64-block states in heavy-profile-search and two repair pilots",
        "unique_candidates_examined": len(seen), "eligible_candidates": records,
        "eligible_count": len(records),
        "complete_link_count": sum(len(r["complete_link_points"]) for r in records),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "profile_checker_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
    }
    (HERE / "inventory.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ["unique_candidates_examined", "eligible_count", "complete_link_count"]}))


if __name__ == "__main__":
    main()
