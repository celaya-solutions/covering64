# Document:    Fixed-g1 Continuation Proof Archive
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      72a30477d5312e269ff7addcadee587151593d5eab88b056eff2b3c185fb416d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Preserve exact cut and nogood bytes in a small deterministic gzip bundle."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/g1-nearest-master-continuation-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    result = json.loads((HERE / "result.json").read_text())
    paths = [
        ROOT / record["learned_cut_path"]
        for record in result["records"]
        if "learned_cut_path" in record
    ]
    assert len(paths) == result["new_conditional_cuts"]
    paths.append(RAW / "final-registry-nogoods.json")
    bundle = {
        "graph_index": 1,
        "family_sha256": result["family_sha256"],
        "result_sha256": sha(HERE / "result.json"),
        "files": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "text": path.read_text()}
            for path in paths
        ],
        "scope": "Fixed-g1 conditional cuts and registry nogoods; no broad or global claim.",
    }
    path = HERE / "learned-proofs.json.gz"
    assert not path.exists()
    path.write_bytes(gzip.compress((json.dumps(bundle, indent=2) + "\n").encode(), mtime=0))
    restored = json.loads(gzip.decompress(path.read_bytes()))
    for item in restored["files"]:
        assert hashlib.sha256(item["text"].encode()).hexdigest() == item["sha256"]
        assert (ROOT / item["path"]).read_text() == item["text"]
    receipt = {
        "source_sha256": sha(__file__),
        "result_sha256": sha(HERE / "result.json"),
        "archive_sha256": sha(path),
        "archive_bytes": path.stat().st_size,
        "graph_index": 1,
        "new_conditional_cuts": result["new_conditional_cuts"],
        "new_registry_nogoods": result["new_registry_nogoods"],
        "restored_files_exactly": len(paths),
        "optimizer_calls": 0,
        "restore_instruction": (
            "gzip-decode learned-proofs.json.gz, parse JSON, and write each files[].text "
            "as UTF-8 to its files[].path after validating files[].sha256."
        ),
    }
    (HERE / "archive.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
