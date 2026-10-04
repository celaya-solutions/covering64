# Document:    Independent Best Graph One Descent Profile and Dual Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6d0b2653beec5e1c42cdaee7eb9d34680f9f90e6420269cef28e4eab5047f7f8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild the selected profile and exact certificate without optimization."""

import importlib.util
import json
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/g1-descent-best-independent-20261004"
RESULT = DAY / "g1-link-descent/result.json"
RUNNER = DAY / "g1-link-descent/run.py"
PROOF = DAY / "four-seven-pinned-regularity/check.py"
CATALOG = DAY / "lp-guided-first-link-registry-independent/check.py"
HELPER = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/lp_core.py"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    result = json.loads(RESULT.read_text())
    assert digest(RESULT) == "cb4f322921b64eab8eba21b13a870d97e067c8e84f15f4b95f07c618bdf88ea6"
    assert digest(RUNNER) == result["source_sha256"]
    best = result["trajectory"][-1]
    assert best["heavy_global_ids"] == result["best_heavy_global_ids"]
    assert best["objective"] == result["best_objective"]
    runner = load(RUNNER, "frozen_g1_descent_runner")
    blocks, ordinary, heavy, _, symbolic, _ = runner.basis()
    fixed = [blocks[i] for i in best["heavy_global_ids"]]
    shifted = runner.generator.shifted_rows(symbolic, heavy, fixed)
    assert runner.data_hash(shifted) == best["shifted_rows_sha256"]
    proof = load(PROOF, "independent_g1_profile")
    independent_ordinary, independent_rows, profile = proof.derive(
        [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)], [4, 8, 12, 16], fixed
    )
    assert ordinary == independent_ordinary
    pairs = list(combinations(range(1, 17), 2))
    graph = [0, 1, 1, 1, 1, 0]
    for pair, e in zip(combinations([4, 8, 12, 16], 2), graph, strict=True):
        row_index = 577 + pairs.index(pair)
        support, _, _ = independent_rows[row_index]
        target = 5 + e - sum(set(pair) <= set(b) for b in fixed)
        independent_rows[row_index] = (support, target, target)
    for (ids, coefficients, lo, hi), (support, lower, upper) in zip(
        shifted, independent_rows, strict=True
    ):
        assert [ordinary[i] for i in ids] == support and coefficients == [1] * len(ids)
        assert (lo, hi) == (lower, upper)
    proto = cp_model_pb2.CpModelProto()
    for block in ordinary:
        proto.variables.add(name=f"block_{blocks.index(block)}", domain=[0, 1])
    for ids, coefficients, lo, hi in shifted:
        row = proto.constraints.add().linear
        row.vars.extend(ids)
        row.coeffs.extend(coefficients)
        row.domain.extend([lo, hi])
    proof.check_model(proto, ordinary, independent_rows)
    RAW.mkdir(exist_ok=True)
    (RAW / "model.pbtxt").write_text(text_format.MessageToString(proto))
    save(RAW / "rows.json", shifted)
    values_path, dual_path = ROOT / best["vector_path"], ROOT / best["dual_path"]
    assert digest(values_path) == best["vector_sha256"]
    assert digest(dual_path) == best["dual_sha256"]
    values, dual = json.loads(values_path.read_text()), json.loads(dual_path.read_text())
    assert len(values) == 1200 and len(dual) == 697
    xs = [max(Fraction(0), min(Fraction(1), Fraction(value))) for value in values]
    residual = Fraction(0)
    for ids, coefficients, lo, hi in shifted:
        value = sum(
            (coefficient * xs[i] for i, coefficient in zip(ids, coefficients, strict=True)),
            Fraction(0),
        )
        residual += max(Fraction(lo) - value, 0)
        if hi != 2**63 - 1:
            residual += max(value - hi, 0)
    assert abs(float(residual) - best["objective"]) < 1e-8
    upper_units = (residual.numerator * 10**9 + residual.denominator - 1) // residual.denominator

    registry = load(CATALOG, "independent_g1_registry")
    exclusions, representatives, lookup, graphs = registry.load_catalog()
    assert list(graphs[1]) == graph
    maps = []
    for group, anchor in enumerate(registry.ANCHORS):
        link = [b for b in fixed if anchor <= set(b)]
        matches = registry.classify(link, group, graphs[1], representatives, lookup)
        identifier, mapping = matches[0]
        assert identifier not in exclusions["proof_sources"]
        maps.append(
            {"anchor_group": group, "class": identifier, "physical_to_representative": mapping}
        )
    heavy_text = "".join(" ".join(map(str, b)) + "\n" for b in sorted(fixed))
    manifest = {
        "graph_index": 1,
        "hub_excesses": graph,
        "heavy_blocks": fixed,
        "heavy_global_ids": best["heavy_global_ids"],
        "heavy_sha256": sha256(heavy_text.encode()).hexdigest(),
        "model_sha256": digest(RAW / "model.pbtxt"),
        "recorded_objective": best["objective"],
        "source_sha256": digest(__file__),
        "optimization_calls": 0,
        "input_sha256": {
            str(p.relative_to(ROOT)): digest(p)
            for p in [RESULT, RUNNER, PROOF, CATALOG, HELPER, values_path, dual_path]
        },
    }
    save(HERE / "manifest.json", manifest)
    helper = load(HELPER, "frozen_g1_exact_dual_arithmetic")
    certificate = helper.exact_dual(shifted, dual, 10**6)
    assert certificate["proves_infeasible"]
    certificate |= {
        "heavy_sha256": manifest["heavy_sha256"],
        "model_sha256": manifest["model_sha256"],
        "manifest_sha256": digest(HERE / "manifest.json"),
    }
    save(HERE / "dual.json", certificate)
    proof.INPUT = HERE / "manifest.json"
    exact = proof.check_dual(certificate, ordinary, independent_rows, manifest)
    rejected = []
    for field in [
        "denominator",
        "rhs_numerator",
        "box_max_numerator",
        "model_sha256",
        "heavy_sha256",
        "manifest_sha256",
        "gap",
        "weights",
    ]:
        bad = deepcopy(certificate)
        if field.endswith("sha256"):
            bad[field] = "0" * 64
        elif field == "gap":
            bad[field][0] += 1
        elif field == "weights":
            bad[field][0][1] += 1
        else:
            bad[field] += 1
        try:
            proof.check_dual(bad, ordinary, independent_rows, manifest)
        except ValueError:
            rejected.append(field)
        else:
            raise AssertionError("Damaged dual accepted")
    audit = {
        "passed": True,
        "graph_index": 1,
        "independently_rebuilt_rows": 697,
        "ordinary_columns": 1200,
        "profile": profile,
        "registry_maps": maps,
        "recorded_objective": best["objective"],
        "exact_dual": exact,
        "exact_clipped_primal_residual": [residual.numerator, residual.denominator],
        "certified_elastic_upper_bound": [upper_units, 10**9],
        "damaged_controls_rejected": rejected,
        "optimization_calls": 0,
        "dual_sha256": digest(HERE / "dual.json"),
        "checker_sha256": digest(__file__),
        "scope": "Selected fixed heavy tuple and graph 1 only. No all-graph cut, "
        "no exact fractional feasible point, and no covering witness.",
    }
    save(HERE / "audit.json", audit)
    print(
        json.dumps(
            {
                "passed": True,
                "exact_dual": exact,
                "upper_bound": [upper_units, 10**9],
                "classes": [row["class"] for row in maps],
            }
        )
    )


if __name__ == "__main__":
    main()
