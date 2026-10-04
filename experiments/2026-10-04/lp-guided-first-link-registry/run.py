# Document:    LP-Guided Heavy Tuple First-Link Registry Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1913b2339ec2b4a6c27217f8dae53f9e0676cc7a38f92d9d331e3db4df9c4656
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay the frozen complete first-link classifier; no optimization calls."""

import contextlib
import importlib.util
import io
import json
from hashlib import sha256
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FROZEN = ROOT / "experiments/2026-10-03/cut-pilot-heavy-completion/check_first_links.py"
BASELINE = ROOT / "experiments/2026-10-04/lp-guided-best-lp/manifest.json"
NEAREST = ROOT / "experiments/2026-10-04/nearest-heavy-master/result.json"
MASTER_SOURCE = ROOT / "experiments/2026-10-04/lazy-heavy-master/run.py"
MASTER_FILE = ROOT / "experiments/scratch/nearest-heavy-master-20261004/master.pbtxt"
MASTER_MANIFEST = ROOT / "experiments/2026-10-04/nearest-heavy-master/manifest.json"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert sha256(FROZEN.read_bytes()).hexdigest() == (
        "d2cd38584203570f6392d2c117471de25ddaa1108f6a56a2fda5a5d4da3f37b5"
    )
    assert sha256(NEAREST.read_bytes()).hexdigest() == (
        "1dfc1ac5b1d2d9d2dceff0eb4f37dbf43a2f1588c1b4fa3e444586226b51a11d"
    )
    checker = load(FROZEN, "frozen_first_link_classifier")
    blocks = list(combinations(range(1, 17), 5))
    baseline = json.loads(BASELINE.read_text())["heavy_blocks"]
    record = json.loads(NEAREST.read_text())["records"][38]
    assert record["step"] == 38
    nearest = [blocks[i] for i in record["heavy_global_ids"]]
    summaries = []
    for name, heavy in [("best-5p575883", baseline), ("nearest-step-038", nearest)]:
        folder = HERE / name
        folder.mkdir(exist_ok=True)
        (folder / "seed.txt").write_text(
            "".join(" ".join(map(str, b)) + "\n" for b in sorted(heavy))
        )
        checker.HERE = folder
        with contextlib.redirect_stdout(io.StringIO()):
            checker.main()
        result = json.loads((folder / "first-link-screen.json").read_text())
        summaries.append(
            {
                "name": name,
                "heavy_seed_sha256": result["seed_sha256"],
                "surviving_graph_indices_zero_based": result["surviving_graph_indices_zero_based"],
                "maps_sha256": sha256((folder / "first-link-screen.json").read_bytes()).hexdigest(),
                "cases": [
                    {
                        "graph": c["graph_index_zero_based"],
                        "kind": c["case"],
                        "hub_excesses": c["hub_excesses_in_lex_pair_order"],
                        "representatives": [x["representative"] for x in c["links"]],
                        "excluded": [x["representative"] for x in c["links"] if x["excluded"]],
                    }
                    for c in result["cases"]
                ],
            }
        )
    assert summaries[0]["surviving_graph_indices_zero_based"] == []
    assert summaries[1]["surviving_graph_indices_zero_based"] == [1]

    # The saved master starts with exactly the documented 605 necessary rows.
    master_manifest = json.loads(MASTER_MANIFEST.read_text())
    assert sha256(MASTER_FILE.read_bytes()).hexdigest() == master_manifest["master_sha256"]
    assert (
        sha256(MASTER_SOURCE.read_bytes()).hexdigest()
        == master_manifest["input_files"][str(MASTER_SOURCE.relative_to(ROOT))]
    )
    original = load(MASTER_SOURCE, "frozen_original_master")
    anchors = [set(range(a, a + 3)) for a in (1, 5, 9, 13)]
    heavy = [
        b
        for b in blocks
        if any(a <= set(b) for a in anchors) and all(len(a & set(b)) in (0, 1, 3) for a in anchors)
    ]
    model, _ = original.build_master(heavy, [blocks.index(b) for b in heavy], [])
    rebuilt = text_format.Parse(str(model.proto), cp_model_pb2.CpModelProto())
    saved = text_format.Parse(MASTER_FILE.read_text(), cp_model_pb2.CpModelProto())
    assert len(rebuilt.variables) == len(saved.variables) == 276
    assert len(rebuilt.constraints) == 605
    assert list(rebuilt.variables) == list(saved.variables)
    assert list(rebuilt.constraints) == list(saved.constraints[:605])
    assert len(saved.constraints) == master_manifest["cut_count"] + 605 == 843
    assert not any(
        "registry" in key or "relabelings" in key for key in master_manifest["input_files"]
    )
    result = {
        "passed": True,
        "checked_exclusions": 109,
        "tuples": summaries,
        "master_base_rows": 605,
        "master_certificate_cut_rows": 238,
        "master_explicit_registry_constraints": 0,
        "optimization_calls": 0,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": {
            str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
            for p in [FROZEN, BASELINE, NEAREST, MASTER_SOURCE, MASTER_FILE, MASTER_MANIFEST]
        },
        "scope": "First-link registry exclusions are conditional on the hub graph. "
        "A tuple is excluded by this registry only when all six graphs are removed. "
        "A remaining graph is not evidence of a completion.",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "survivors": {
                    s["name"]: s["surviving_graph_indices_zero_based"] for s in summaries
                },
                "explicit_registry_constraints": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
