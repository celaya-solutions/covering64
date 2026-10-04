# Document:    Refreshed Template Certificate Chain and Registry
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Bind independently replayed exact proofs to the checked encoding and archive them."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ENCODING = HERE.parent / "four-seven-template-hull-refresh"
RAW = ROOT / "experiments/scratch/four-seven-template-hull-refresh-screen-20261003"
MATRIX_SHA = "ee2072837ae28bcce599c60975995a5c88b3fc3eb635352abc089b3eb6d78bab"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + "\n")


def main():
    audit_path = ENCODING / "independent-audit.json"
    audit = load(audit_path)
    require(audit["passed"] is True, "encoding audit incomplete")
    require(sha(ENCODING / "check_independent.py") == audit["checker_sha256"], "audit changed")
    require(sha(ENCODING / "manifest.json") == audit["manifest_sha256"], "manifest changed")
    matching = next(c for c in audit["cases"] if c["case"] == "matching")
    require(
        matching["matrix_sha256"] == sha(RAW / "extended-rows.json.gz") == MATRIX_SHA,
        "matrix chain mismatch",
    )
    require(
        matching["columns"] == 55528 and matching["templates_per_group"] == 12690,
        "wrong refresh revision",
    )
    prior_path = (
        HERE.parent / "four-seven-template-hub-independent/combined-first-link-exclusions.json"
    )
    prior = load(prior_path)
    require(prior["passed"] is True and prior["excluded_count"] == 106, "wrong predecessor")
    require(
        sha(prior_path) == "dc1f0790d593238d00c8eff3ac58753d70a7fc9c6820d73d0bb835569ac9fd0e",
        "predecessor changed",
    )
    records, evidence = [], []
    sources = dict(prior["proof_sources"])
    remaining = set(prior["remaining_ids"])
    for identifier in ["matching-095", "matching-113"]:
        replay_path = HERE / (identifier + "-audit.json")
        replay = load(replay_path)
        require(replay["passed"] is replay["proves_infeasible"] is True, "unchecked proof")
        require(
            replay["representative"] == identifier and replay["matrix_sha256"] == MATRIX_SHA,
            "wrong proof scope",
        )
        require(replay["gap"][0] > 0 and replay["gap"][1] > 0, "nonpositive gap")
        require(sha(HERE / "check.py") == replay["checker_sha256"], "replay source changed")
        for name, field in [
            ("fixed-rows.json", "fixed_rows_sha256"),
            ("certificate-1000000.json", "certificate_sha256"),
        ]:
            require(sha(RAW / identifier / name) == replay[field], "raw proof changed")
        require(identifier in remaining and identifier not in sources, "not a new exclusion")
        records.append(
            {
                "id": identifier,
                "replay_sha256": sha(replay_path),
                "gap": replay["gap"],
                "certificate_sha256": replay["certificate_sha256"],
            }
        )
        evidence.append(
            {
                "id": identifier,
                "fixed_rows": load(RAW / identifier / "fixed-rows.json"),
                "certificate": load(RAW / identifier / "certificate-1000000.json"),
            }
        )
        sources[identifier] = [str(replay_path.relative_to(HERE.parent))]
        remaining.remove(identifier)
    chain = {
        "passed": True,
        "encoding_audit_sha256": sha(audit_path),
        "encoding_checker_sha256": audit["checker_sha256"],
        "encoding_manifest_sha256": audit["manifest_sha256"],
        "matching_matrix_sha256": MATRIX_SHA,
        "matching_catalog_sha256": matching["catalog_sha256"],
        "matching_group_catalogs_sha256": matching["group_catalogs_sha256"],
        "certificates": records,
        "scope": "Two checked restricted first-link exclusions only.",
    }
    save("encoding-chain-audit.json", chain)
    (HERE / "evidence.json.gz").write_bytes(
        gzip.compress(
            json.dumps({"chain": chain, "proofs": evidence}, separators=(",", ":")).encode(),
            mtime=0,
        )
    )
    require(len(sources) == 108 and len(remaining) == 150, "wrong combined inventory")
    save(
        "combined-first-link-exclusions.json",
        {
            "passed": True,
            "excluded_count": len(sources),
            "remaining_count": len(remaining),
            "proof_sources": dict(sorted(sources.items())),
            "remaining_ids": sorted(remaining),
            "prior_union_sha256": sha(prior_path),
            "new_encoding_chain_sha256": sha(HERE / "encoding-chain-audit.json"),
            "evidence_sha256": sha(HERE / "evidence.json.gz"),
            "scope": "Checked restricted first-link exclusion union. "
            "The regular four-sevenfold branch "
            "and unrestricted covering number remain unresolved.",
        },
    )
    print(
        json.dumps(
            {
                "excluded": len(sources),
                "open": len(remaining),
                "evidence_bytes": (HERE / "evidence.json.gz").stat().st_size,
                "registry_sha256": sha(HERE / "combined-first-link-exclusions.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
