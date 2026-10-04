# Document:    Fixed-g1 Continuation Diagnostic Additions
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      47c19e6a7cd3a96d1dffcfa4641b62ad5fc6d8c149896b4e3c67845105553a23
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Derive one conditional cut and excluded-link nogood without optimization."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    master = load(DAY / "g1-nearest-master/run.py", "continued_master")
    branch = master.branch
    sha = master.sha
    diagnostic = DAY / "g1-master-presolve-diagnostic/result.json"
    post_path = DAY / "g1-master-presolve-diagnostic-independent/postcheck.json"
    result = json.loads(diagnostic.read_text())
    post = json.loads(post_path.read_text())
    assert post["passed"] and post["result_sha256"] == sha(diagnostic)
    assert result["complete_diagnostic"] and result["fresh_completion_lps"] == 1
    accepted = next(item for item in result["cases"] if item["name"] == "presolve-off")
    rejected = next(item for item in result["cases"] if item["name"] == "normal-presolve")
    assert accepted["registry_accepted"] and accepted["lp"]["status"] == "OPTIMAL"
    assert accepted["lp"]["objective"] == 13.514017967610794
    assert not rejected["registry_accepted"]
    blocks, ordinary, heavy, _, rows, _ = branch.basis()
    heavy_global = [blocks.index(block) for block in heavy]
    lookup = {global_id: local for local, global_id in enumerate(heavy_global)}
    selected = [blocks[i] for i in accepted["heavy_global_ids"]]
    shifted = branch.generator.shifted_rows(rows, heavy, selected)
    assert branch.data_hash(selected) == accepted["heavy_sha256"]
    assert branch.data_hash(shifted) == accepted["shifted_rows_sha256"]
    dual_path = ROOT / accepted["dual_path"]
    assert sha(dual_path) == accepted["dual_sha256"]
    exact = load(branch.generator.LP_CORE, "continuation_exact")
    cut = master.helpers.derive_cut(
        exact,
        rows,
        shifted,
        json.loads(dual_path.read_text()),
        {lookup[i] for i in accepted["heavy_global_ids"]},
        len(ordinary),
        len(heavy),
    )
    assert cut is not None and cut["dual"]["proves_infeasible"]
    norm = max(abs(weight) for _, weight in cut["dual"]["weights"])
    assert norm <= cut["denominator"] == 1000000
    cut.update(
        id="g1-presolve-diagnostic-accepted",
        graph_index=1,
        family_sha256=result["family_sha256"],
        source_heavy_global_ids=accepted["heavy_global_ids"],
        source_heavy_sha256=accepted["heavy_sha256"],
        source_shifted_rows_sha256=accepted["shifted_rows_sha256"],
        numerical_dual_path=str(dual_path.relative_to(ROOT)),
        numerical_dual_sha256=sha(dual_path),
        maximum_signed_row_weight=norm,
        source_objective=accepted["lp"]["objective"],
    )
    registry = branch.registry_module.Registry()
    receipt = registry.classify([blocks[i] for i in rejected["heavy_global_ids"]])
    links = [link for link in receipt["links"] if link["excluded"]]
    assert len(links) == 1 and links[0]["representative"] == "cycle-028"
    assert links[0]["anchor_group_zero_based"] == 0
    group = links[0]["anchor_group_zero_based"]
    anchor = set(range(4 * group + 1, 4 * group + 4))
    ids = [i for i in rejected["heavy_global_ids"] if anchor <= set(blocks[i])]
    nogood = master.link_nogood(
        group, ids, blocks, lookup, registry, "g1_presolve_diagnostic_normal_presolve"
    )
    assert branch.data_hash(nogood["registry"]) == branch.data_hash(links[0])
    registry_path = (
        ROOT
        / "experiments/scratch/g1-master-presolve-diagnostic-20261004/normal-presolve/registry.json"
    )
    assert sha(registry_path) == rejected["registry_sha256"]
    assert branch.data_hash(json.loads(registry_path.read_text())) == branch.data_hash(receipt)
    paths = [
        Path(__file__),
        diagnostic,
        post_path,
        dual_path,
        registry_path,
        DAY / "g1-nearest-master/run.py",
        DAY / "g1-link-descent/run.py",
        DAY / "nearest-heavy-master/run.py",
        branch.generator.LP_CORE,
    ] + registry.input_paths()
    additions = {
        "graph_index": 1,
        "family_sha256": result["family_sha256"],
        "cut": cut,
        "nogood": nogood,
        "input_files": {str(path.relative_to(ROOT)): sha(path) for path in paths},
        "optimization_calls": 0,
        "scope": (
            "One fixed-g1 conditional cut and one fixed-g1 registry nogood; "
            "pending independent replay."
        ),
    }
    path = HERE / "diagnostic-additions.json"
    assert not path.exists()
    path.write_text(json.dumps(additions, indent=2) + "\n")
    print(
        json.dumps(
            {
                "additions_sha256": sha(path),
                "exact_gap": cut["dual"]["gap"],
                "nogood_ids": ids,
                "optimization_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
