# Document:    Audited Heavy Tuple Inventory for the Cut Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7a043b796a392c6a90023c67ba02df1259e55d97983abd3a0cfc6bedd1114d22
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read only the45 audited states; group exact canonical heavy tuples. No solving."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/four-seven-template-cut-pilot-v1.0.0"
AUDIT = ROOT / "experiments/2026-10-03/four-seven-template-cut-pilot/audit.json"
MANIFEST = AUDIT.parent / "manifest.json"
ANCHORS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
BEST_HASH = "b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(blocks):
    return "".join(" ".join(map(str, block)) + "\n" for block in sorted(blocks))


def parse(path):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks)
    assert all(
        len(block) == 5 and tuple(sorted(set(block))) == block and set(block) <= set(range(1, 17))
        for block in blocks
    )
    assert canonical(blocks) == path.read_text()
    return blocks


def heavy_tuple(blocks):
    result = tuple(
        block for block in blocks if any(set(anchor) <= set(block) for anchor in ANCHORS)
    )
    assert len(result) == len(set(result)) == 28 and result == tuple(sorted(result))
    assert [sum(set(anchor) <= set(block) for block in result) for anchor in ANCHORS] == [7] * 4
    return result


def main():
    output = HERE / "tuple-inventory.json"
    assert not output.exists(), "preserve completed inventory"
    audit = json.loads(AUDIT.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert audit["passed"] and audit["states"] == 45 and len(audit["snapshots"]) == 45
    assert (
        audit["both_cover_checkers_on_every_saved_state"]
        and audit["complete_lookahead_sets_checked"]
    )
    assert audit["manifest_sha256"] == sha(MANIFEST)
    expected_paths = {Path(path).resolve() for path in audit["snapshots"]}
    actual_paths = set(RAW.glob("*.txt"))
    assert expected_paths == actual_paths and len(actual_paths) == 45
    cut_path = RAW / "inputs/cut.json"
    seed_path = RAW / "inputs/seed.txt"
    assert sha(cut_path) == manifest["cut_sha256"] and sha(seed_path) == manifest["seed_sha256"]
    cut = json.loads(cut_path.read_text())
    assert cut["seed_sha256"] == sha(seed_path)
    coefficients = {
        tuple(block): value
        for block, value in zip(cut["heavy_blocks"], cut["coefficients"], strict=True)
    }
    second_cut_path = HERE / "cut.json"
    assert (
        sha(second_cut_path) == "24c9a407e4abf90fe712ba297e549d32e748e000370d841984b107d0723a88a8"
    )
    second_cut = json.loads(second_cut_path.read_text())
    second_coefficients = {
        tuple(block): value
        for block, value in zip(second_cut["heavy_blocks"], second_cut["coefficients"], strict=True)
    }
    assert second_cut["rhs"] == 104444 and second_cut["seed_sha256"] == BEST_HASH
    seed = parse(seed_path)
    seed_heavy = heavy_tuple(seed)
    assert (
        560 - len({triple for block in seed for triple in itertools.combinations(block, 3)}) == 10
    )
    best_paths = [
        path for path, entry in audit["snapshots"].items() if entry["sha256"] == BEST_HASH
    ]
    assert best_paths and audit["raw_best"]["sha256"] == audit["score_best"]["sha256"] == BEST_HASH
    best_heavy = heavy_tuple(parse(Path(best_paths[0])))
    groups = {}
    checked = {
        str(path.relative_to(ROOT)): sha(path)
        for path in (AUDIT, MANIFEST, cut_path, seed_path, second_cut_path)
    }
    fields = (
        "holes",
        "score",
        "base_score",
        "cut_lhs",
        "cut_violation",
        "cut_penalty",
        "unsupported_count",
        "admissible_count",
        "heavy_excess",
    )
    for path in sorted(actual_paths):
        audited = audit["snapshots"][str(path)]
        assert sha(path) == audited["sha256"]
        checked[str(path.relative_to(ROOT))] = sha(path)
        sidecar_path = Path(str(path) + ".lookahead.json")
        assert sha(sidecar_path) == audited["sidecar_sha256"]
        checked[str(sidecar_path.relative_to(ROOT))] = sha(sidecar_path)
        sidecar = json.loads(sidecar_path.read_text())
        assert all(sidecar[field] == audited[field] for field in fields)
        blocks = parse(path)
        heavy = heavy_tuple(blocks)
        holes = 560 - len(
            {triple for block in blocks for triple in itertools.combinations(block, 3)}
        )
        assert holes == audited["holes"]
        lhs = sum(coefficients[block] for block in heavy)
        assert lhs == audited["cut_lhs"] and max(0, cut["rhs"] - lhs) == audited["cut_violation"]
        assert (
            audited["score"]
            == audited["base_score"] + 100 * audited["unsupported_count"] + audited["cut_penalty"]
        )
        groups.setdefault(heavy, []).append(
            {
                "file": path.name,
                "sha256": audited["sha256"],
                "sidecar_sha256": audited["sidecar_sha256"],
                **{field: audited[field] for field in fields},
            }
        )
    records = []
    for heavy, members in groups.items():
        second_lhs = sum(second_coefficients[block] for block in heavy)
        invariant_fields = (
            "cut_lhs",
            "cut_violation",
            "cut_penalty",
            "unsupported_count",
            "admissible_count",
            "heavy_excess",
        )
        assert all(len({member[field] for member in members}) == 1 for field in invariant_fields)
        row = {
            "heavy_sha256": hashlib.sha256(canonical(heavy).encode()).hexdigest(),
            "heavy_blocks": [list(block) for block in heavy],
            "members": members,
            "saved_state_count": len(members),
            "distinct_full_family_count": len({member["sha256"] for member in members}),
            "min_holes": min(member["holes"] for member in members),
            "max_holes": max(member["holes"] for member in members),
            "min_full_score": min(member["score"] for member in members),
            "max_full_score": max(member["score"] for member in members),
            **{field: members[0][field] for field in invariant_fields},
            "equals_original_ten_hole_seed_heavy": heavy == seed_heavy,
            "equals_final_best_heavy": heavy == best_heavy,
            "second_cut_lhs": second_lhs,
            "second_cut_violation": max(0, second_cut["rhs"] - second_lhs),
        }
        reasons = []
        if row["cut_violation"] > 0:
            reasons.append("violates the existing labeled necessary cut")
        if row["second_cut_violation"] > 0:
            reasons.append("violates the new second labeled necessary cut")
        if row["unsupported_count"] > 0:
            reasons.append("has unsupported triples under this heavy tuple")
        if row["heavy_excess"] > 0:
            reasons.append("exceeds audited heavy pair-overlap budgets")
        row["lp_batch_candidate"] = not reasons
        row["lp_priority_note"] = (
            "Final best tuple: primary second-cut target; avoid duplicating its LP."
            if row["equals_final_best_heavy"] and not reasons
            else "Already fails finite necessary conditions: " + "; ".join(reasons) + "."
            if reasons
            else "Remaining tuple passes the recorded finite screens; a later LP could separate it."
        )
        records.append(row)
    records.sort(
        key=lambda row: (
            not row["lp_batch_candidate"],
            row["min_holes"],
            row["min_full_score"],
            row["heavy_sha256"],
        )
    )
    for rank, row in enumerate(records, 1):
        row["inventory_rank"] = rank
    candidates = [row for row in records if row["lp_batch_candidate"]]
    extra = [row for row in candidates if not row["equals_final_best_heavy"]]
    body = {
        "source_sha256": sha(Path(__file__)),
        "audited_saved_states": 45,
        "distinct_full_families": len({entry["sha256"] for entry in audit["snapshots"].values()}),
        "distinct_heavy_tuples": len(records),
        "anchors": ANCHORS,
        "audit_path": str(AUDIT.relative_to(ROOT)),
        "audit_sha256": sha(AUDIT),
        "verified_input_sha256": checked,
        "metrics_origin": "Audit-bound sidecars; holes and both cut lhs values "
        "independently recounted here.",
        "original_seed_sha256": sha(seed_path),
        "final_best_sha256": BEST_HASH,
        "old_cut_sha256": sha(cut_path),
        "old_cut_rhs": cut["rhs"],
        "second_cut_sha256": sha(second_cut_path),
        "second_cut_rhs": second_cut["rhs"],
        "tuples_violating_old_cut": sum(row["cut_violation"] > 0 for row in records),
        "tuples_violating_second_cut": sum(row["second_cut_violation"] > 0 for row in records),
        "tuples_violating_either_cut": sum(
            row["cut_violation"] > 0 or row["second_cut_violation"] > 0 for row in records
        ),
        "tuple_multiplicity_histogram": dict(
            sorted(Counter(row["saved_state_count"] for row in records).items())
        ),
        "tuples_passing_recorded_finite_screens": len(candidates),
        "additional_lp_candidates_beyond_final_best": len(extra),
        "suggested_additional_lp_priority": [row["heavy_sha256"] for row in extra],
        "tuples": records,
        "solver_calls": 0,
        "lp_calls": 0,
        "native_runs": 0,
        "scope": "Exact inventory of45 audited saved states only. Deduplication is labeled "
        "equality, not isomorphism. Finite-screen status and any future LP concern this labeled "
        "regular-template setting only; no unrestricted bound.",
    }
    body = json.loads(json.dumps(body))
    canonical_body = json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n"
    header = {
        "Document": "Audited Heavy Tuple Inventory for the Cut Pilot",
        "Version": "v1.0.0",
        "Author": "Celaya Solutions",
        "Contact": "hello@celayasolutions.com",
        "Date": "2026-10-04",
        "SHA256": hashlib.sha256(canonical_body.encode()).hexdigest(),
        "Chain": "n/a",
        "Tx": "[not anchored]",
        "License": "All Rights Reserved / Celaya Solutions",
    }
    output.write_text(json.dumps({"document_header": header, **body}, indent=2) + "\n")
    assert all(sha(ROOT / relative) == expected for relative, expected in checked.items())
    print(
        json.dumps(
            {
                key: body[key]
                for key in (
                    "audited_saved_states",
                    "distinct_full_families",
                    "distinct_heavy_tuples",
                    "tuples_passing_recorded_finite_screens",
                    "additional_lp_candidates_beyond_final_best",
                )
            }
        )
    )
    for row in records:
        print(
            json.dumps(
                {key: value for key, value in row.items() if key not in ("heavy_blocks", "members")}
            )
        )


if __name__ == "__main__":
    main()
