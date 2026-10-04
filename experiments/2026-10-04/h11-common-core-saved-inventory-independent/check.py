# Document:    Independent Saved Partial Common-Core Inventory
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      5ff4d6a566bc6c3a62403f60754e42353880f53957d108553e9b9af4dc2ba431
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read saved families only; no solver, neighborhood, or native search calls."""

import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from covering64.core import verify_cover

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / "experiments/2026-10-04"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def exact_ids(text, oracle):
    rows = [tuple(map(int, line.split())) for line in text.splitlines() if line.strip()]
    require(len(rows) == 64, "wrong cardinality")
    require(rows == sorted(set(rows)), "duplicate or noncanonical family")
    require(all(row in oracle.RANK for row in rows), "malformed block")
    return tuple(oracle.RANK[row] for row in rows)


def main():
    oracle_path = BASE / "weak-pair-swap-scan-independent/oracle.py"
    require(
        digest(oracle_path) == "7fc14c0e2078894a03cc8945c94cb8f9987e79f4780d49558d311e83f0d0ba92",
        "oracle changed",
    )
    oracle = load("independent_oracle", oracle_path)
    standalone_path = ROOT / "scripts/check_cover.py"
    standalone = load("standalone_cover", standalone_path)
    manifest_path = BASE / "weak-pair-neutral-queue/manifest.json"
    require(
        digest(manifest_path) == "5a1082e2f28194ee4c90ee0d16bf0d5b22502164e082e757a35842547eae2a82",
        "old-core manifest changed",
    )
    old_cores = json.loads(manifest_path.read_text())["core_rows"]
    certificate_path = BASE / "h11-d25-common-core-cap/certificate.json"
    require(
        digest(certificate_path)
        == "1006dc7a15b515c075311da4ef8f074d92da60d10ed9fe3b12db23c77dc687ad",
        "common-core certificate changed",
    )
    certificate = json.loads(certificate_path.read_text())
    core_path = ROOT / certificate["core_path"]
    require(
        digest(core_path) == "c2190a6c9fdc0e0f5cc56c991b79c109925e1c3f7ea375ec353535c717415b72",
        "common core changed",
    )
    common = set(oracle.parse(core_path))
    require(sorted(common) == certificate["core_ids"] and len(common) == 62, "wrong core")
    require(certificate["passed"] and certificate["exact_64_overlap_cap"] == 56, "wrong cap")

    input_path = OUT / "inputs.json"
    if not input_path.exists():
        paths = sorted(
            p
            for date in ("2026-10-03", "2026-10-04")
            for p in (ROOT / "experiments" / date).rglob("*.txt")
            if OUT not in p.parents
        )
        dump(input_path, {str(p.relative_to(ROOT)): digest(p) for p in paths})
    inputs = json.loads(input_path.read_text())
    groups = {}
    classifications = Counter()
    for relative, expected_hash in inputs.items():
        path = ROOT / relative
        require(digest(path) == expected_hash, f"saved input changed: {relative}")
        text = path.read_text()
        try:
            ids = exact_ids(text, oracle)
        except ValueError:
            classifications["not_canonical_exact64"] += 1
            continue
        classifications["canonical_exact64_files"] += 1
        blocks = [oracle.SUBSETS[5][i] for i in ids]
        holes = 560 - len({t for b in blocks for t in itertools.combinations(b, 3)})
        if holes > 11:
            classifications["more_than_11_holes_files"] += 1
            continue
        classifications["at_most_11_holes_files"] += 1
        if ids not in groups:
            groups[ids] = {"holes": holes, "sources": []}
        groups[ids]["sources"].append({"path": relative, "sha256": expected_hash})

    families = []
    for ids, group in sorted(groups.items()):
        blocks = [oracle.SUBSETS[5][i] for i in ids]
        text = "".join(" ".join(map(str, b)) + "\n" for b in blocks)
        sha = hashlib.sha256(text.encode()).hexdigest()
        fresh = oracle.analyze(ids, old_cores)
        metrics = fresh["metrics"]
        metrics["cardinality"] = len(ids)
        metrics["common62_overlap"] = len(set(ids) & common)
        package = verify_cover(blocks)
        separate = standalone.verify_cover(standalone.parse_witness(text), expected_blocks=64)
        require(
            len(package["uncovered"])
            == separate["uncovered_count"]
            == metrics["holes"]
            == group["holes"],
            "triple counts disagree",
        )
        require(
            separate["cardinality_matches"] and separate["canonical_sha256"] == sha,
            "canonical verifier mismatch",
        )
        require(
            package["valid"] == separate["valid"] == (metrics["holes"] == 0),
            "cover labels disagree",
        )
        five_caps = max(metrics["core_overlaps"]) <= 55 and metrics["common62_overlap"] <= 56
        weak = metrics["minimum_pair_count"] >= 5 and metrics["D3"] == metrics["D4"] == 0
        witness_path = OUT / f"family-{sha[:16]}.txt"
        witness_path.write_text(text)
        families.append(
            {
                "sha256": sha,
                "path": str(witness_path.relative_to(ROOT)),
                "ids": list(ids),
                "metrics": metrics,
                "five_named_caps_pass": five_caps,
                "weak_pair_rules_pass": weak,
                "all_checks_pass": five_caps and weak,
                "package_valid": package["valid"],
                "standalone_valid": separate["valid"],
                "dual_verifiers_agree": True,
                "sources": group["sources"],
            }
        )

    require(families, "no saved low-hole families found")
    positive = (ROOT / families[0]["path"]).read_text()
    rows = positive.splitlines()
    controls = {
        "duplicate": "\n".join([rows[0], *rows[:-1]]) + "\n",
        "wrong_cardinality": "\n".join(rows[:-1]) + "\n",
        "zero_label": positive.replace("1 ", "0 ", 1),
        "float_label": positive.replace("1 ", "1.0 ", 1),
        "bool_label": positive.replace("1 ", "True ", 1),
        "unsorted_blocks": "\n".join(reversed(rows)) + "\n",
    }
    for name, damaged in controls.items():
        try:
            exact_ids(damaged, oracle)
        except ValueError:
            continue
        raise ValueError(f"damaged control accepted: {name}")

    families.sort(key=lambda f: (f["metrics"]["holes"], f["metrics"]["D2max"], f["ids"]))
    receipt = {
        "passed": True,
        "scope": (
            "Finite inventory of frozen saved canonical exact64 text families with H<=11; "
            "no new search, no global conclusion."
        ),
        "selection": (
            "All .txt paths below experiments/2026-10-03 and experiments/2026-10-04 at initial "
            "snapshot, excluding this output folder; only canonical exact64 witnesses retained."
        ),
        "inputs_path": str(input_path.relative_to(ROOT)),
        "inputs_sha256": digest(input_path),
        "source_sha256": digest(Path(__file__)),
        "oracle_sha256": digest(oracle_path),
        "package_verifier_sha256": digest(ROOT / "src/covering64/core.py"),
        "standalone_verifier_sha256": digest(standalone_path),
        "old_core_manifest_sha256": digest(manifest_path),
        "common_core_certificate_sha256": digest(certificate_path),
        "common_core_sha256": digest(core_path),
        "frozen_text_inputs": len(inputs),
        "classifications": dict(classifications),
        "distinct_low_hole_families": len(families),
        "holes_histogram": dict(sorted(Counter(f["metrics"]["holes"] for f in families).items())),
        "five_cap_pass_count": sum(f["five_named_caps_pass"] for f in families),
        "weak_pair_pass_count": sum(f["weak_pair_rules_pass"] for f in families),
        "all_checks_pass_count": sum(f["all_checks_pass"] for f in families),
        "cover_found": any(f["package_valid"] for f in families),
        "damaged_controls_rejected": sorted(controls),
        "optimizer_launches": 0,
        "native_requeries": 0,
        "families": families,
    }
    dump(OUT / "inventory.json", receipt)
    require((OUT / "inventory.json").stat().st_size < 1_000_000, "receipt too large")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in (
                    "passed",
                    "distinct_low_hole_families",
                    "holes_histogram",
                    "five_cap_pass_count",
                    "weak_pair_pass_count",
                    "all_checks_pass_count",
                    "cover_found",
                )
            }
            | {"inventory_sha256": digest(OUT / "inventory.json")}
        )
    )


if __name__ == "__main__":
    main()
