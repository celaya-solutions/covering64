# Document:    Independent Heavy-Triple Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e405df3e0f0cdfa874e22bf3f018a62273d382e6c0e613c7c3f4bdcff155e494
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite truth tables and exact model rows; no full-cover infeasibility claim."""

import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import heavy_triple_search as subject  # noqa: E402


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(triples, counts):
    heavy = [t for t, n in zip(triples, counts) if n >= 6]
    return (max(counts) <= 7
            and len(set(itertools.chain.from_iterable(heavy))) == 3 * len(heavy)
            and sum(4 if n == 7 else 3 for n in counts if n >= 6) <= 16)


def gadget(triples, counts, flags=None, clear=None):
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"incidence_{i}") for i in range(9 * len(triples))]
    containing = [list(range(9 * i, 9 * i + 9)) for i in range(len(triples))]
    subject.add_heavy_count_cuts(SimpleNamespace(triples=triples, containing=containing),
                                 model, selected)
    if clear is not None:
        model.proto.constraints[clear].clear_linear()
    for ids, count in zip(containing, counts):
        model.add(sum(selected[i] for i in ids) == count)
    if flags is not None:
        by_name = {v.name: i for i, v in enumerate(model.proto.variables)}
        for name, value in flags.items():
            model.add(model.get_bool_var_from_proto_index(by_name[name]) == value)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 1
    status = solver.solve(model)
    require(status in (cp_model.OPTIMAL, cp_model.INFEASIBLE), "inconclusive gadget check")
    return status == cp_model.OPTIMAL


def truth_tables():
    rows = []
    for count, high, seven in itertools.product(range(10), range(2), range(2)):
        expected = count <= 7 and high == (count >= 6) and seven == (count == 7)
        actual = gadget([(1, 2, 3)], [count], {"heavy6_0": high, "heavy7_0": seven})
        require(actual == expected, f"flag truth table mismatch: {count, high, seven}")
        rows.append([count, high, seven, actual])
    overlap_cases = 0
    for triples in [[(1, 2, 3), (1, 4, 5)], [(1, 2, 3), (1, 2, 4)]]:
        for counts in itertools.product(range(8), repeat=2):
            require(gadget(triples, counts) == oracle(triples, counts),
                    f"overlap mismatch: {triples, counts}")
            overlap_cases += 1
    disjoint = [tuple(range(3 * i + 1, 3 * i + 4)) for i in range(5)]
    disjoint_cases = 0
    for counts in itertools.product([5, 6, 7], repeat=5):
        require(gadget(disjoint, counts) == oracle(disjoint, counts),
                f"weighted count mismatch: {counts}")
        disjoint_cases += 1
    damages = {
        "missing_high_false_direction": gadget([(1, 2, 3)], [6],
            {"heavy6_0": 0, "heavy7_0": 0}, clear=2),
        "missing_seven_true_direction": gadget([(1, 2, 3)], [6],
            {"heavy6_0": 1, "heavy7_0": 1}, clear=3),
        "missing_vertex_disjointness": gadget([(1, 2, 3), (1, 4, 5)], [6, 6], clear=10),
        "missing_weighted_bound": gadget(disjoint, [7, 7, 7, 6, 6], clear=41),
    }
    require(all(damages.values()), "a damage control was not exposed")
    return {"threshold_truth_table": rows, "overlap_cases": overlap_cases,
            "disjoint_weight_cases": disjoint_cases, "damage_controls_exposed": damages}


def linear(row, variables, target):
    require(not row.enforcement_literal, "unexpected reification")
    require(list(row.linear.vars) == variables, "wrong variable IDs")
    require(list(row.linear.coeffs) == [1] * len(variables), "wrong coefficients")
    require(list(row.linear.domain) == [target, target], "wrong exact target")


def model_rows():
    expected_blocks = list(itertools.combinations(range(1, 17), 5))
    fixed = [(1, 2, 3, 4, 5), (1, 2, 3, 4, 6), (1, 2, 3, 7, 8),
             (1, 2, 3, 9, 10), (1, 2, 3, 11, 12), (1, 2, 3, 13, 14), (1, 2, 3, 15, 16)]
    require(subject.FIXED == fixed, "wrong normalized fixed family")
    base_u, base, _, _, _ = subject.build_model(0)
    universe, model, selected, _, _ = subject.build_heavy_model(0)
    require(list(universe.blocks) == expected_blocks == list(base_u.blocks),
            "lex universe mismatch")
    require([x.index for x in selected] == list(range(4368)), "block variable order mismatch")
    boundary = len(base.proto.constraints)
    require(all(str(a) == str(b) for a, b in
                zip(base.proto.constraints, model.proto.constraints)), "base model changed")
    extra = list(model.proto.constraints)[boundary:]
    cursor = 0
    fixed_ids = [expected_blocks.index(b) for b in fixed]
    for index in fixed_ids:
        linear(extra[cursor], [index], 1)
        cursor += 1
    targets = []
    for p in (1, 2, 3):
        for q in range(p + 1, 17):
            target = 7 if q in (2, 3) else 6 if q == 4 else 5
            ids = [i for i, b in enumerate(expected_blocks) if p in b and q in b]
            linear(extra[cursor], ids, target)
            targets.append([p, q, target])
            cursor += 1
    excluded = [i for i, b in enumerate(expected_blocks)
                if len({1, 2, 3}.intersection(b)) >= 2 and b not in fixed]
    for index in excluded:
        linear(extra[cursor], [index], 0)
        cursor += 1
    require(cursor == len(extra) == 978, "unexpected extra normalized restriction")
    _, with_cuts, _, _, _ = subject.build_heavy_model(0, count_cuts=True)
    require(len(with_cuts.proto.constraints) - len(model.proto.constraints) == 2817,
            "wrong count-cut row count")
    require(len(with_cuts.proto.variables) - len(model.proto.variables) == 1120,
            "wrong threshold variable count")
    return {"fixed_ids": fixed_ids, "fixed_blocks": fixed, "pair_targets": targets,
            "excluded_block_count": len(excluded), "normalized_extra_rows": cursor,
            "count_cut_extra_rows": 2817, "count_cut_extra_variables": 1120,
            "base_scope": "Point-essential regular20 branch; degree19 branch remains separate"}


def archived_models():
    results = []
    for name in ["full", "partial", "counts"]:
        folder = ROOT / f"experiments/scratch/heavy-triple-{name}-20261003"
        metadata = json.loads((folder / "metadata.json").read_text())
        require(sha(folder / "model.pbtxt") == metadata["model_sha256"],
                "stored model hash mismatch")
        for filename, expected in metadata["sources"].items():
            require(sha(folder / filename) == expected, "stored source hash mismatch")
        with tempfile.TemporaryDirectory(prefix="heavy-model-rebuild-") as temporary:
            output = Path(temporary) / "rebuilt.pbtxt"
            command = [sys.executable, "-c", """
import inspect,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import heavy_triple_search as m
meta=json.loads(Path(sys.argv[1], 'metadata.json').read_text())
args={'max_missing':meta['max_missing']}
if 'count_cuts' in inspect.signature(m.build_heavy_model).parameters:
    args['count_cuts']=meta.get('count_cuts',False)
m.build_heavy_model(**args)[1].export_to_file(sys.argv[2])
""", str(folder), str(output)]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
            require(sha(output) == metadata["model_sha256"], "archived model replay hash mismatch")
        results.append({"campaign": name, "source_hashes": metadata["sources"],
                        "model_sha256": metadata["model_sha256"], "byte_identical_rebuild": True,
                        "max_missing": metadata["max_missing"],
                        "count_cuts": metadata.get("count_cuts", False)})
    return results


def main():
    body = {"scope": "Finite gadget truth tables, model rows, and byte-identical model replays; "
                    "no global impossibility proof",
            "source_sha256": sha(ROOT / "scripts/heavy_triple_search.py"),
            "base_source_sha256": sha(ROOT / "scripts/essential_regular_search.py"),
            "proof_sha256": sha(ROOT / "experiments/2026-10-03/regular-heavy-triples/README.md"),
            "audit_source_sha256": sha(Path(__file__)),
            "truth_tables": truth_tables(), "normalized_model": model_rows(),
            "archived_models": archived_models(), "status": "PASS"}
    header = {"Document": "Independent Heavy-Triple Model Audit", "Version": "v1.0.0",
              "Author": "Celaya Solutions", "Contact": "hello@celayasolutions.com",
              "Date": "2026-10-03", "SHA256": hashlib.sha256(json.dumps(body, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest(), "Chain": "n/a",
              "Tx": "[not anchored]", "License": "All Rights Reserved / Celaya Solutions"}
    Path(__file__).with_name("result.json").write_text(
        json.dumps({"document_header": header, "body": body}, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "truth_table_rows": 40, "overlap_cases": 128,
                      "disjoint_weight_cases": 243, "damage_controls": 4,
                      "archived_models_replayed": 3}))


if __name__ == "__main__":
    main()
