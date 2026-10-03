# Document:    Independent Scored Candidate Structural Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      564e6f2e8d1e8ade16c1bdf81f54008c257fe8fe21d1ce8a0ab5d9a9d2fc28fe
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
import pathlib
import subprocess
import sys

from covering64.core import read_blocks, verify_cover

ROOT = pathlib.Path(__file__).resolve().parent
UTILITY = ROOT.parent / "regular-heavy-hub-bound/check.py"
spec = importlib.util.spec_from_file_location("frozen_hub_audit", UTILITY)
hub_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub_audit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    blocks = hub_audit.parse(args.candidate.read_text())
    hub_audit.require(blocks == sorted(read_blocks(args.candidate)), "parser disagreement")
    result = hub_audit.inspect(blocks)
    pairs = collections.Counter(p for b in blocks for p in itertools.combinations(b, 2))
    local = {t for b in blocks if min(b) <= 3 for t in itertools.combinations(b, 3) if min(t) >= 4}
    residual = [t for t in itertools.combinations(range(4, 17), 3) if t not in local]
    needs = {
        p: (sum(set(p) <= set(t) for t in residual) + 2) // 3
        for p in itertools.combinations(range(4, 17), 2)
    }
    rows = {point: sum(n for pair, n in needs.items() if point in pair) for point in range(4, 17)}
    overflow = sum(max(0, row - (24 if point == 4 else 28)) for point, row in rows.items())
    pair_deficits = [
        {"pair": pair, "multiplicity": pairs[pair]}
        for pair in itertools.combinations(range(1, 17), 2)
        if pairs[pair] < 5
    ]
    internal = []
    cross = []
    occupied_hubs = []
    for profile in result["profiles"]:
        for pair in itertools.combinations(profile["triple"], 2):
            if pairs[pair] < 7:
                internal.append(
                    dict(triple=profile["triple"], pair=pair, multiplicity=pairs[pair], required=7)
                )
        for hub in profile["hubs"]:
            for anchor in profile["triple"]:
                pair = tuple(sorted((hub, anchor)))
                if pairs[pair] < 6:
                    cross.append(
                        dict(
                            triple=profile["triple"],
                            hub=hub,
                            pair=pair,
                            multiplicity=pairs[pair],
                            required=6,
                        )
                    )
            for other in result["profiles"]:
                if hub in other["triple"]:
                    occupied_hubs.append(
                        dict(
                            triple=profile["triple"],
                            hub=hub,
                            occupying_heavy_triple=other["triple"],
                        )
                    )
    package = verify_cover(blocks)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(args.candidate), "--expected-blocks", "64"],
        text=True,
        capture_output=True,
        check=False,
    )
    standalone = json.loads(process.stdout)
    hub_audit.require(process.returncode == int(not package["valid"]), "standalone status")
    hub_audit.require(
        standalone["uncovered"]
        == [list(t) for t in result["uncovered"]]
        == [list(t) for t in package["uncovered"]],
        "three hole recounts disagree",
    )
    hub_audit.require(
        standalone["canonical_sha256"] == package["canonical_sha256"], "hash disagreement"
    )
    result.update(
        complete=True,
        candidate=str(args.candidate),
        candidate_sha256=hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        package=package,
        standalone=standalone,
        pair_multiplicities=[
            dict(pair=p, multiplicity=pairs[p]) for p in itertools.combinations(range(1, 17), 2)
        ],
        pairs_below_five=pair_deficits,
        heavy_internal_pair_deficits=internal,
        repeated_hub_cross_pair_deficits=cross,
        hubs_in_heavy_triples=occupied_hubs,
        local_family_pair_row_bounds=rows,
        local_family_pair_row_overflow=overflow,
        passes_full_cover_pair_lower_bounds=not pair_deficits and not internal and not cross,
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        utility_sha256=hashlib.sha256(UTILITY.read_bytes()).hexdigest(),
        verifier_source_hashes={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                pathlib.Path("src/covering64/core.py"),
                pathlib.Path("scripts/check_cover.py"),
            ]
        },
        scope=(
            "Raw partial-candidate diagnostics; passing listed filters is not a cover "
            "or a completeness claim."
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                candidate=str(args.candidate),
                holes=len(result["uncovered"]),
                refined_sum=result["refined_sum"],
                filters=result["filters"],
                pair_row_overflow=overflow,
                hubs_in_heavy=occupied_hubs,
                generic_pair_deficits=len(pair_deficits),
                heavy_internal_deficits=len(internal),
                hub_cross_deficits=len(cross),
            )
        )
    )


if __name__ == "__main__":
    main()
