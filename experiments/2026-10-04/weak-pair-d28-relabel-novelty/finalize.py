# Document:    D28 Audit Runtime Binding and Manifest
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      553dda457a9a5ff109a0cef83a5e0fe13817c8bd068de423696afd97ce6e2015
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Bind completed profile and independent runtime receipts without any search."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNTIME = HERE.parent / "weak-pair-two-swap-scan-v2-runtime-independent/postcheck.json"
RUNTIME_SHA = "c2922a53aae7a51154b2006f457d88df886ab115fa6b88993920d04c62eb8d41"
AUDIT_SHA = "ad20c60f68ef9fb9b25dd4ab25b984124d9fb89103589610ed86d145d486f198"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    assert not (HERE / "manifest.json").exists()
    assert sha(RUNTIME) == RUNTIME_SHA and sha(HERE / "audit.json") == AUDIT_SHA
    runtime = json.loads(RUNTIME.read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    assert runtime["passed"] and runtime["complete_exact_distance_two_shell"]
    assert runtime["producer_result_sha256"] == audit["producer_result_sha256"]
    assert runtime["final"] == audit["producer_final"]
    assert len(runtime["best_ties"]) == len(audit["saved_ties"]) == 6
    assert {row["sha256"] for row in runtime["best_ties"]} == {
        row["sha256"] for row in audit["saved_ties"]
    }
    for row in runtime["best_ties"]:
        assert sha(ROOT / row["path"]) == row["sha256"]
    for relative, digest in audit["input_files"].items():
        assert sha(ROOT / relative) == digest
    binding = {
        "passed": True,
        "optimizer_calls": 0,
        "enumeration_calls": 0,
        "source_sha256": sha(Path(__file__)),
        "audit_sha256": AUDIT_SHA,
        "runtime_postcheck_path": str(RUNTIME.relative_to(ROOT)),
        "runtime_postcheck_sha256": RUNTIME_SHA,
        "producer_result_sha256": audit["producer_result_sha256"],
        "same_terminal_accounting": True,
        "same_six_distinct_tie_hashes": True,
        "scope": "Crossbinding only; runtime's exact-distance-two scope and replay limitations "
        "remain unchanged. No new search or global claim.",
    }
    dump(HERE / "runtime-crosscheck.json", binding)
    manifest = {
        "document": "D28 Two-Swap Tie Relabel and Novelty Audit Manifest",
        "version": "v1.0.0",
        "date": "2026-10-04",
        "passed": True,
        "optimizer_calls": 0,
        "enumeration_calls": 0,
        "audit_sha256": AUDIT_SHA,
        "runtime_postcheck_path": str(RUNTIME.relative_to(ROOT)),
        "runtime_postcheck_sha256": RUNTIME_SHA,
        "representative_path": audit["representative_path"],
        "representative_sha256": audit["representative_sha256"],
        "scope": audit["scope"],
        "files": {
            str(path.relative_to(ROOT)): sha(path)
            for path in sorted(HERE.iterdir())
            if path.is_file()
        },
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "passed": True,
                "files": len(manifest["files"]),
                "manifest_sha256": sha(HERE / "manifest.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
