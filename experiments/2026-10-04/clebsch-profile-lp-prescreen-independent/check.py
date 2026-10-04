# Document:    Clebsch Profile LP Independent Vector Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      8960e50375f3ce3efb363e7b51a6bd1cfa8c9692a1de8a86b3a6b22efcde182f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay saved fractional vectors with Python counts; never invoke a solver."""

import ast
import hashlib
import importlib.util
import itertools
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "clebsch-profile-lp-prescreen"
RESULT_SHA = "4c4894584ed399a4949c8fa00e41079dde5d36aa99af0ca2aa659b692bd0cf64"
SOURCE_SHA = "ef1aedc938cf4db27da05b0042497ec80c2be2f372d61ce228646c1f472ef0ad"
CERTIFICATE_SHA = "800d05d6d504d82260fd50e93cb854d9d47f2e2f52de017f634d80a0e7cd9f67"
GENERATOR_SHA = "a31ed5c0a4a503007c6c744ccea9c583747280e18830607b41c763f062cbe2bb"
REFERENCE_SHA = "e18a4552bc805e162ccfae341fd85d2ae79749ff81e9f1063f9c1c0016539d12"
SEEDS = [0, 1, 9, 40, 19, 8, 4, 18, 16, 12, 3, 10, 11, 26, 60, 25]
POINTS = tuple(range(1, 17))
BLOCKS = tuple(itertools.combinations(POINTS, 5))
TRIPLES = tuple(itertools.combinations(POINTS, 3))
PAIRS = tuple(itertools.combinations(POINTS, 2))
TOLERANCE = 1e-8


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(values, profile):
    assert len(values) == 4368
    assert all(type(x) in (float, int) and math.isfinite(x) for x in values)
    assert len(profile) == len(set(profile)) == 80
    assert all(t in TRIPLES for t in profile)
    pair_extra = Counter(p for t in profile for p in itertools.combinations(t, 2))
    point_extra = Counter(p for t in profile for p in t)
    pair_targets = {p: (14 + pair_extra[p]) / 3 for p in PAIRS}
    point_targets = {p: (105 + point_extra[p]) / 6 for p in POINTS}
    assert Counter(pair_targets.values()) == {5.0: 80, 6.0: 40}
    assert set(point_targets.values()) == {20.0}
    triple_terms = {t: [] for t in TRIPLES}
    pair_terms = {p: [] for p in PAIRS}
    point_terms = {p: [] for p in POINTS}
    for block, value in zip(BLOCKS, values, strict=True):
        for triple in itertools.combinations(block, 3):
            triple_terms[triple].append(value)
        for pair in itertools.combinations(block, 2):
            pair_terms[pair].append(value)
        for point in block:
            point_terms[point].append(value)
    assert all(len(terms) == 78 for terms in triple_terms.values())
    assert all(len(terms) == 364 for terms in pair_terms.values())
    assert all(len(terms) == 1365 for terms in point_terms.values())
    triple_residual = max(
        abs(math.fsum(terms) - 1 - int(t in profile)) for t, terms in triple_terms.items()
    )
    pair_residual = max(abs(math.fsum(terms) - pair_targets[p]) for p, terms in pair_terms.items())
    point_residual = max(
        abs(math.fsum(terms) - point_targets[p]) for p, terms in point_terms.items()
    )
    bounds = max(max(-x, x - 1, 0) for x in values)
    total = math.fsum(values)
    fractional = sum(abs(x - round(x)) > 1e-7 for x in values)
    assert max(triple_residual, pair_residual, point_residual, bounds, abs(total - 64)) <= TOLERANCE
    return {
        "max_triple_demand_residual": triple_residual,
        "max_pair_demand_residual": pair_residual,
        "max_point_demand_residual": point_residual,
        "max_bound_violation": bounds,
        "sum_values": total,
        "sum_residual": abs(total - 64),
        "fractional_columns": fractional,
        "integral_columns_at_1e_minus7": 4368 - fractional,
        "positive_columns_at_1e_minus8": sum(x > 1e-8 for x in values),
        "near_one_columns_at_1e_minus7": sum(abs(x - 1) <= 1e-7 for x in values),
        "exact_zero_columns": sum(x == 0 for x in values),
        "pair_demand_histogram": {"5": 80, "6": 40},
        "point_demand": 20,
        "is_integral_cover_witness": fractional == 0,
    }


def main():
    result_path = PRODUCER / "output/result.json"
    assert sha(result_path) == RESULT_SHA and sha(PRODUCER / "run.py") == SOURCE_SHA
    generator_path = ROOT / "scripts/independent_clebsch_profiles.py"
    reference_path = ROOT / "scripts/check_independent_clebsch.py"
    certificate_path = (
        ROOT / "experiments/2026-10-03/independent-geometry/profile-orbits/certificate.json"
    )
    assert sha(generator_path) == GENERATOR_SHA and sha(reference_path) == REFERENCE_SHA
    assert sha(certificate_path) == CERTIFICATE_SHA
    result = json.loads(result_path.read_text())
    certificate = json.loads(certificate_path.read_text())
    assert result["source_sha256"] == SOURCE_SHA
    assert result["profile_source_sha256"] == GENERATOR_SHA
    assert result["orbit_certificate_sha256"] == CERTIFICATE_SHA
    assert result["profile_seeds"] == SEEDS and len(result["rows"]) == 16
    tree = ast.parse((PRODUCER / "run.py").read_text())
    source_seeds = next(
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "SEEDS" for t in n.targets)
    )
    assert source_seeds == SEEDS == [row["seed"] for row in certificate["body"]["orbits"]]
    assert [row["profile_seed"] for row in result["rows"]] == SEEDS
    assert certificate["body"]["generator_file_sha256"] == GENERATOR_SHA
    spec = importlib.util.spec_from_file_location("independent_recipe_certificate", reference_path)
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    seed_profiles = {str(row["profile_seed"]): row["profile"] for row in result["rows"]}
    orbit_audit = reference.audit_profile_certificate(certificate, seed_profiles)
    assert orbit_audit["valid"] and orbit_audit["seed_maps_checked"]
    assert orbit_audit["solver_invoked"] is False
    checked = []
    all_values = []
    for record in result["rows"]:
        seed = record["profile_seed"]
        vector_path = PRODUCER / f"output/profile-{seed}-vector.json"
        assert sha(vector_path) == record["vector_sha256"]
        values = json.loads(vector_path.read_text())
        profile = tuple(tuple(t) for t in record["profile"])
        assert profile == tuple(sorted(profile))
        metrics = replay(values, profile)
        assert record["status"] == "OPTIMAL" and record["columns"] == 4368 and record["rows"] == 560
        assert record["fractional_columns"] == metrics["fractional_columns"] == 560
        assert record["positive_columns"] == metrics["positive_columns_at_1e_minus8"] == 560
        assert metrics["near_one_columns_at_1e_minus7"] == 0
        assert abs(record["sum_values"] - metrics["sum_values"]) < 1e-9
        assert abs(record["max_row_residual"] - metrics["max_triple_demand_residual"]) < 1e-9
        assert abs(record["max_bound_violation"] - metrics["max_bound_violation"]) < 1e-9
        checked.append(
            {
                "seed": seed,
                "path": str(vector_path.relative_to(ROOT)),
                "sha256": sha(vector_path),
                "producer_status": record["status"],
                **metrics,
            }
        )
        all_values.append(values)
    assert len({row["seed"] for row in checked}) == 16
    values = all_values[0]
    profile = tuple(tuple(t) for t in result["rows"][0]["profile"])
    damaged_cases = [
        ("short_vector", values[:4367]),
        ("long_vector", [*values, 0]),
        ("zero_vector", [0.0] * 4368),
    ]
    for name, value in [
        ("boolean", True),
        ("nonfinite", float("nan")),
        ("negative_bound", -0.1),
        ("upper_bound", 1.1),
    ]:
        damaged = list(values)
        damaged[0] = value
        damaged_cases.append((name, damaged))
    damaged = list(values)
    positive = next(i for i, x in enumerate(values) if x > 1e-8)
    damaged[positive] += 0.001
    damaged_cases.append(("perturbed_positive_coefficient", damaged))
    rejected = []
    for name, damaged in damaged_cases:
        try:
            replay(damaged, profile)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError(f"accepted damaged vector: {name}")
    receipt = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "producer_result_sha256": RESULT_SHA,
        "producer_source_sha256": SOURCE_SHA,
        "generator_sha256": GENERATOR_SHA,
        "reference_checker_sha256": REFERENCE_SHA,
        "orbit_certificate_sha256": CERTIFICATE_SHA,
        "orbit_certificate_replay": orbit_audit,
        "profile_seeds": SEEDS,
        "lexicographic_blocks": 4368,
        "triple_rows_per_vector": 560,
        "pair_rows_per_vector": 120,
        "point_rows_per_vector": 16,
        "numerical_feasibility_tolerance": TOLERANCE,
        "vectors": checked,
        "maximum_triple_residual": max(row["max_triple_demand_residual"] for row in checked),
        "maximum_pair_residual": max(row["max_pair_demand_residual"] for row in checked),
        "maximum_point_residual": max(row["max_point_demand_residual"] for row in checked),
        "maximum_sum_residual": max(row["sum_residual"] for row in checked),
        "maximum_bound_violation": max(row["max_bound_violation"] for row in checked),
        "integral_cover_witnesses": sum(row["is_integral_cover_witness"] for row in checked),
        "damaged_vectors_rejected": rejected,
        "optimizer_launches": 0,
        "scope": (
            "Numerical feasibility of sixteen fractional recipe relaxations only. "
            "No binary cover, rational proof, or unrestricted existence result. "
            "Integral-column counts include zero coefficients."
        ),
    }
    path = HERE / "review.json"
    assert not path.exists(), "preserve replay receipt"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    assert path.stat().st_size < 1_000_000
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(path),
                "max_triple_residual": receipt["maximum_triple_residual"],
                "integral_cover_witnesses": receipt["integral_cover_witnesses"],
            }
        )
    )


if __name__ == "__main__":
    main()
