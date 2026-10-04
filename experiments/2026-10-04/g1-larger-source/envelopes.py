# Document:    Fixed-g1 Saved-Dual Planes and Finite Envelopes
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      df69253271b3e6bfe8e30bd276617b121aede0ad525cfabbfe9e4bb797dafe19
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Derive conditional exact planes and screen finite states without solving."""

import gzip
import importlib.util
import json
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DAY = ROOT / "experiments/2026-10-04"
SCALE = 1000000


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


run = load(DAY / "g1-link-descent/run.py", "envelope_g1")
nearest = load(DAY / "nearest-heavy-master/run.py", "envelope_nearest")
margin = load(DAY / "margin-heavy-master/run.py", "envelope_margin")
sha = run.sha
started = time.monotonic()
assert not (HERE / "g1-cuts.json").exists()
blocks, ordinary, heavy, _, rows, changes = run.basis()
heavy_global = [blocks.index(b) for b in heavy]
lookup = {g: i for i, g in enumerate(heavy_global)}
source_path = DAY / "g1-link-descent/result.json"
source = json.loads(source_path.read_text())
manifest = json.loads((DAY / "g1-link-descent/manifest.json").read_text())
post = json.loads((DAY / "g1-link-descent-independent/postcheck.json").read_text())
assert post["passed"]
exact = run.load(run.generator.LP_CORE, "envelope_exact")
conditional = []
inputs = {
    str(p.relative_to(ROOT)): sha(p)
    for p in [
        Path(__file__),
        HERE / "count.py",
        HERE / "counts.json",
        DAY / "g1-link-descent/run.py",
        DAY / "g1-link-descent/registry.py",
        DAY / "g1-link-descent/manifest.json",
        source_path,
        DAY / "g1-link-descent-independent/postcheck.json",
        DAY / "nearest-heavy-master/run.py",
        run.generator.LP_CORE,
        DAY / "margin-heavy-master/run.py",
    ]
}
for record in source["records"]:
    if record["cached"]:
        continue
    assert record["status"] == "OPTIMAL" and record["family_sha256"] == manifest["family_sha256"]
    numeric_path = ROOT / record["dual_path"]
    assert sha(numeric_path) == record["dual_sha256"]
    numeric = json.loads(numeric_path.read_text())
    chosen = [blocks[i] for i in record["heavy_global_ids"]]
    shifted = run.generator.shifted_rows(rows, heavy, chosen)
    assert run.data_hash(shifted) == record["shifted_rows_sha256"]
    positions = {lookup[i] for i in record["heavy_global_ids"]}
    cut = nearest.derive_cut(exact, rows, shifted, numeric, positions, len(ordinary), len(heavy))
    assert cut is not None
    norm = max(abs(weight) for _, weight in cut["dual"]["weights"])
    assert norm <= cut["denominator"] == SCALE
    cut.update(
        id=f"g1-round{record['round']}-rank{record['rank']:03d}",
        graph_index=1,
        family_sha256=manifest["family_sha256"],
        source_heavy_global_ids=record["heavy_global_ids"],
        source_heavy_sha256=record["heavy_sha256"],
        source_shifted_rows_sha256=record["shifted_rows_sha256"],
        numerical_dual_path=record["dual_path"],
        numerical_dual_sha256=record["dual_sha256"],
        maximum_signed_row_weight=norm,
        source_objective=record["objective"],
    )
    conditional.append(cut)
    inputs[record["dual_path"]] = record["dual_sha256"]
assert len(conditional) == 243
bundle = {
    "graph_index": 1,
    "hub_excesses": [0, 1, 1, 1, 1, 0],
    "six_row_changes": changes,
    "family_sha256": manifest["family_sha256"],
    "ordinary_global_ids": [blocks.index(b) for b in ordinary],
    "heavy_global_ids": heavy_global,
    "cuts": conditional,
    "count": 243,
    "source_sha256": sha(__file__),
    "descent_result_sha256": sha(source_path),
    "scope": (
        "These 243 planes require fixed graph g1; "
        "never append them to the broad cut inventory."
    ),
    "optimization_calls": 0,
}
save("g1-cuts.json", bundle)
save("g1-unconditional-rows.json", rows)
print("derived243", sha(HERE / "g1-cuts.json"), flush=True)

base, broad, paths = margin.load_cuts()
prior = json.loads((DAY / "margin-heavy-master/result.json").read_text())
prior_post = json.loads((DAY / "margin-heavy-master-independent/postcheck.json").read_text())
assert prior_post["passed"] and len(prior["records"]) == 20
paths += [
    DAY / "margin-heavy-master/result.json",
    DAY / "margin-heavy-master-independent/postcheck.json",
]
for record in prior["records"]:
    path = (
        ROOT
        / "experiments/scratch/margin-heavy-master-20261004"
        / f"step-{record['step']:03d}/learned-cut.json"
    )
    assert sha(path) == record["learned_cut_sha256"]
    broad.append(json.loads(path.read_text()))
    paths.append(path)
assert len(broad) == 353 and base["heavy_global_ids"] == heavy_global
for cut in broad:
    if "dual" in cut:
        dual = cut["dual"]
    elif "dual_path" in cut:
        path = ROOT / cut["dual_path"]
        assert sha(path) == cut["dual_sha256"]
        paths.append(path)
        dual = json.loads(path.read_text())
    elif "maximum_signed_row_weight" in cut:
        assert cut["maximum_signed_row_weight"] <= cut["denominator"]
        continue
    else:
        raise AssertionError(cut.keys())
    assert max(abs(weight) for _, weight in dual["weights"]) <= cut["denominator"]
inputs.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
save(
    "broad-cuts-reference.json",
    {"cuts": broad, "count": 353, "scope": "Existing broad planes copied as planning inputs only."},
)


def matrix(cuts):
    coefficients = []
    rhs = []
    for cut in cuts:
        assert SCALE % cut["denominator"] == 0
        factor = SCALE // cut["denominator"]
        row = [factor * x for x in cut["coefficients"]]
        bound = factor * cut["rhs"]
        assert abs(bound) + sum(abs(x) for x in row) < 2**60
        coefficients.append(row)
        rhs.append(bound)
    return np.array(coefficients, dtype=np.int64), np.array(rhs, dtype=np.int64)


c_matrix, c_rhs = matrix(conditional)
b_matrix, b_rhs = matrix(broad)
upper_path = DAY / "g1-descent-best-independent/audit.json"
upper_audit = json.loads(upper_path.read_text())
assert upper_audit["passed"] and upper_audit["graph_index"] == 1
upper = Fraction(*upper_audit["certified_elastic_upper_bound"])
inputs[str(upper_path.relative_to(ROOT))] = sha(upper_path)
threshold = (upper.numerator * SCALE + upper.denominator - 1) // upper.denominator
cache = json.loads(
    (ROOT / "experiments/scratch/g1-link-descent-20261004/final-cache.json").read_text()
)
cached = {tuple(record["heavy_global_ids"]) for record in cache.values()}
summary = {}
for name in ["proper-three", "paired-two", "whole-link", "alternatives"]:
    path = HERE / (name + ".json.gz")
    states = json.loads(gzip.decompress(path.read_bytes()))
    inputs[str(path.relative_to(ROOT))] = sha(path)
    scores = []
    for offset in range(0, len(states), 256):
        group = states[offset : offset + 256]
        local = np.array([[lookup[x] for x in state] for state in group], dtype=np.int64)
        cb = np.maximum(0, (c_rhs[:, None] - c_matrix[:, local].sum(axis=2)).max(axis=0))
        bb = np.maximum(0, (b_rhs[:, None] - b_matrix[:, local].sum(axis=2)).max(axis=0))
        scores.extend((int(c), int(b), int(max(c, b))) for c, b in zip(cb, bb, strict=True))
    (HERE / (name + "-envelopes.json.gz")).write_bytes(
        gzip.compress(json.dumps(scores).encode(), mtime=0)
    )
    unexcluded = [state for state, score in zip(states, scores, strict=True) if score[2] == 0]
    improving = [state for state, score in zip(states, scores, strict=True) if score[2] < threshold]
    (HERE / (name + "-unexcluded.json.gz")).write_bytes(
        gzip.compress(json.dumps(unexcluded).encode(), mtime=0)
    )
    (HERE / (name + "-possibly-improving.json.gz")).write_bytes(
        gzip.compress(json.dumps(improving).encode(), mtime=0)
    )
    best_indices = sorted(
        range(len(scores)), key=lambda i: (scores[i][2], scores[i][0], states[i])
    )[:20]
    summary[name] = {
        "registry_safe_states": len(states),
        "g1_positive": sum(s[0] > 0 for s in scores),
        "g1_unexcluded": sum(s[0] == 0 for s in scores),
        "broad_positive": sum(s[1] > 0 for s in scores),
        "combined_positive": sum(s[2] > 0 for s in scores),
        "combined_unexcluded": len(unexcluded),
        "combined_unexcluded_uncached": sum(tuple(state) not in cached for state in unexcluded),
        "combined_bound_reaches_incumbent_upper": sum(s[2] >= threshold for s in scores),
        "combined_possibly_improving": len(improving),
        "combined_possibly_improving_uncached": sum(
            tuple(state) not in cached for state in improving
        ),
        "g1_minimum_lower_bound": [min(s[0] for s in scores), SCALE],
        "combined_minimum_lower_bound": [min(s[2] for s in scores), SCALE],
        "best_twenty": [
            {
                "heavy_global_ids": states[i],
                "g1_bound_numerator": scores[i][0],
                "broad_bound_numerator": scores[i][1],
                "combined_bound_numerator": scores[i][2],
                "cached": tuple(states[i]) in cached,
            }
            for i in best_indices
        ],
        "states_sha256": sha(path),
        "scores_sha256": sha(HERE / (name + "-envelopes.json.gz")),
    }
    print(
        name, json.dumps({k: v for k, v in summary[name].items() if k != "best_twenty"}), flush=True
    )
report = {
    "source_sha256": sha(__file__),
    "bundle_sha256": sha(HERE / "g1-cuts.json"),
    "broad_reference_sha256": sha(HERE / "broad-cuts-reference.json"),
    "graph_index": 1,
    "fixed_g1_planes": 243,
    "broad_planes": 353,
    "denominator": SCALE,
    "incumbent_certified_upper": [upper.numerator, upper.denominator],
    "integer_threshold": threshold,
    "neighborhoods": summary,
    "optimization_calls": 0,
    "seconds": time.monotonic() - started,
    "scope": (
        "Finite lower envelopes only. Positive values exclude exact fractional completion "
        "in the fixed branch; a zero is inconclusive. No optimum claim."
    ),
}
save("envelope-results.json", report)
save("inputs.json", inputs)
print("complete", report["seconds"], flush=True)
