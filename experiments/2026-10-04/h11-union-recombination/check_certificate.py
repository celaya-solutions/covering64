# Document:    Independent H11 Union Support Certificate Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7724d6f0acbafa932e4acd8f8229a40c46525ebf9e4497a5ec12ce3e52e35149
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recompute all carrier sets without importing the certificate producer."""

import copy
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from covering64.core import verify_cover

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EXPECTED_SOURCE_HASHES = {
    "f621e945358cc9e51c53995ee9a4a6161a0124778984fa410a87227984a28a7a",
    "439d5153ba2f2063c8dedb20ce71f9381dfecdca087e4fa9f9f0dd3808f4d22f",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(certificate):
    all_blocks = list(itertools.combinations(range(1, 17), 5))
    block_ids = {block: index for index, block in enumerate(all_blocks)}
    require(len(certificate["sources"]) == 2, "wrong source count")
    require(
        {s["sha256"] for s in certificate["sources"]} == EXPECTED_SOURCE_HASHES,
        "wrong source hashes",
    )
    selected_sets = []
    for source in certificate["sources"]:
        path = ROOT / source["path"]
        require(sha(path) == source["sha256"], "source bytes changed")
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        require(len(blocks) == 64 and blocks == sorted(set(blocks)), "bad source cardinality")
        require(all(block in block_ids for block in blocks), "malformed source block")
        ids = [block_ids[block] for block in blocks]
        require(ids == source["ids"], "source IDs differ")
        selected_sets.append(set(ids))
    require(not selected_sets[0].intersection(selected_sets[1]), "sources unexpectedly overlap")
    union = sorted(selected_sets[0] | selected_sets[1])
    require(len(union) == 128 and certificate["union_ids"] == union, "wrong union")
    union_path = ROOT / certificate["union_path"]
    require(sha(union_path) == certificate["union_sha256"], "union witness changed")
    expected_text = "".join(" ".join(map(str, all_blocks[i])) + "\n" for i in union)
    require(union_path.read_text() == expected_text, "union witness differs")
    direct = {}
    for triple in itertools.combinations(range(1, 17), 3):
        direct[triple] = tuple(i for i in union if all(x in all_blocks[i] for x in triple))
        require(direct[triple], "union does not cover every triple")
    incidence_path = ROOT / certificate["incidence_path"]
    require(sha(incidence_path) == certificate["incidence_sha256"], "incidence bytes changed")
    incidence = json.loads(incidence_path.read_text())
    require(incidence["candidate_ids"] == union, "incidence union differs")
    expected_rows = [{"triple": list(t), "carrier_ids": list(ids)} for t, ids in direct.items()]
    require(incidence["triple_supports"] == expected_rows, "incidence recount differs")
    expected_histogram = {str(k): v for k, v in sorted(Counter(map(len, direct.values())).items())}
    require(certificate["support_histogram"] == expected_histogram, "support histogram differs")
    forced = sorted({ids[0] for ids in direct.values() if len(ids) == 1})
    require(certificate["forced_ids"] == forced and len(forced) == 19, "forced set differs")
    require(len(certificate["forced_rows"]) == len(forced), "missing singleton proof")
    used = set()
    rows = certificate["forced_rows"] + certificate["matched_pair_rows"]
    for index, row in enumerate(rows):
        triple, ids = row["triple"], row["carrier_ids"]
        require(all(type(value) is int for value in triple + ids), "noninteger certificate")
        require(tuple(triple) in direct, "invalid triple")
        require(tuple(ids) == direct[tuple(triple)], "wrong carrier support")
        required_size = 1 if index < len(forced) else 2
        require(len(ids) == required_size, "wrong support size")
        require(not used.intersection(ids), "support sets are not disjoint")
        used.update(ids)
    require(
        {r["carrier_ids"][0] for r in certificate["forced_rows"]} == set(forced),
        "singleton rows do not prove all forced variables",
    )
    require(
        len(certificate["matched_pair_rows"]) == certificate["matched_pair_count"] == 54,
        "wrong matching count",
    )
    bound = len(rows)
    require(type(certificate["selected_lower_bound"]) is int, "noninteger lower bound")
    require(certificate["selected_lower_bound"] == bound == 73, "unsupported lower bound")
    require(len(used) == 127, "wrong total disjoint carrier count")
    pair_rows = [
        ids for ids in direct.values() if len(ids) == 2 and not set(forced).intersection(ids)
    ]
    require(certificate["remaining_pair_rows"] == len(pair_rows) == 291, "wrong pair-row count")
    require(
        certificate["distinct_remaining_pair_supports"] == len(set(pair_rows)) == 244,
        "wrong pair-support count",
    )
    require(
        certificate["uncovered_after_forced"]
        == sum(not set(forced).intersection(ids) for ids in direct.values())
        == 387,
        "wrong forced residual",
    )
    return {"union_ids": union, "bound": bound, "disjoint_support_blocks": len(used)}


def main():
    path = HERE / "certificate.json"
    certificate = json.loads(path.read_text())
    checked = validate(certificate)
    spec = importlib.util.spec_from_file_location(
        "standalone_cover", ROOT / "scripts/check_cover.py"
    )
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    verifier_receipts = []
    for source in [*certificate["sources"], {"path": certificate["union_path"]}]:
        witness = ROOT / source["path"]
        blocks = standalone.parse_witness(witness.read_text())
        package = verify_cover(blocks)
        separate = standalone.verify_cover(blocks, expected_blocks=len(blocks))
        require(package["valid"] == separate["valid"], "dual cover labels differ")
        require(
            package["uncovered"] == [tuple(t) for t in separate["uncovered"]], "dual holes differ"
        )
        verifier_receipts.append(
            {
                "path": source["path"],
                "sha256": sha(witness),
                "blocks": len(blocks),
                "holes": separate["uncovered_count"],
                "valid": package["valid"],
                "dual_verifiers_agree": True,
            }
        )
    require([r["holes"] for r in verifier_receipts] == [11, 11, 0], "unexpected family holes")
    rejected = []
    for kind in (
        "duplicate_pair",
        "wrong_carrier",
        "removed_forced",
        "inflated_bound",
        "Boolean_carrier",
        "wrong_union",
        "wrong_source_hash",
    ):
        damaged = copy.deepcopy(certificate)
        if kind == "duplicate_pair":
            damaged["matched_pair_rows"][1] = copy.deepcopy(damaged["matched_pair_rows"][0])
        elif kind == "wrong_carrier":
            damaged["matched_pair_rows"][0]["carrier_ids"][0] += 1
        elif kind == "removed_forced":
            damaged["forced_rows"].pop()
        elif kind == "inflated_bound":
            damaged["selected_lower_bound"] += 1
        elif kind == "Boolean_carrier":
            damaged["matched_pair_rows"][0]["carrier_ids"][0] = True
        elif kind == "wrong_union":
            damaged["union_ids"].pop()
        else:
            damaged["sources"][0]["sha256"] = "0" * 64
        try:
            validate(damaged)
        except ValueError:
            rejected.append(kind)
        else:
            raise ValueError(f"damaged certificate accepted: {kind}")
    receipt = {
        "passed": True,
        "certificate_sha256": sha(path),
        "checker_sha256": sha(Path(__file__)),
        "scope": "At least 73 blocks required within this exact 128-block union; no global bound.",
        "forced_blocks": 19,
        "disjoint_pairs": 54,
        "lower_bound": checked["bound"],
        "disjoint_support_blocks": checked["disjoint_support_blocks"],
        "dual_verifier_receipts": verifier_receipts,
        "damaged_certificates_rejected": rejected,
        "package_verifier_sha256": sha(ROOT / "src/covering64/core.py"),
        "standalone_verifier_sha256": sha(ROOT / "scripts/check_cover.py"),
        "optimizer_launches": 0,
    }
    (HERE / "verification.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "lower_bound": checked["bound"],
                "verification_sha256": sha(HERE / "verification.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
