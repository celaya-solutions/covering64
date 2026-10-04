# Document:    Finite Two-Edge Link Switch Generator and LP Mapping
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      00b5fdd7eff30d2ab374dae7d9e0328b54444104670613627a596a517d3e9775
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Generate and map candidates without creating a solver or optimizing."""

import hashlib
import importlib.util
import itertools as it
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/2026-10-03/lookahead-cut-independent/check.py"
MANIFEST = ROOT / "experiments/2026-10-03/lookahead-heavy-strengthened/manifest.json"
SEED = (
    ROOT / "experiments/2026-10-03/four-seven-template-native-lookahead/performance-cycle-best.txt"
)
LP_CORE = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/lp_core.py"
BUNDLE = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
CUT_GATE = ROOT / "experiments/2026-10-04/cut-bundle-independent/audit.json"
BASELINE_RESULT = ROOT / "experiments/2026-10-03/lookahead-heavy-strengthened/lp-result.json"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def data_hash(data):
    return hashlib.sha256(json.dumps(data, separators=(",", ":")).encode()).hexdigest()


def candidates(fixed, heavy):
    fixed, heavy = set(fixed), set(heavy)
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    found = {}
    counters = Counter()
    for anchor in anchors:
        local = {block for block in fixed if anchor <= set(block)}
        edges = sorted(tuple(sorted(set(block) - anchor)) for block in local)
        assert len(edges) == 7
        for first, second in it.combinations(edges, 2):
            a, b = first
            c, d = second
            for new_edges in (((a, c), (b, d)), ((a, d), (b, c))):
                counters["proposals"] += 1
                if len({a, b, c, d}) != 4:
                    counters["adjacent_edges"] += 1
                    continue
                outgoing = {tuple(sorted(anchor | set(edge))) for edge in (first, second)}
                incoming = {tuple(sorted(anchor | set(edge))) for edge in new_edges}
                next_fixed = (fixed - outgoing) | incoming
                if len(next_fixed) != 28 or len(incoming - fixed) != 2:
                    counters["duplicate_or_unchanged"] += 1
                    continue
                if not next_fixed <= heavy:
                    counters["outside_276_universe"] += 1
                    continue
                counts = Counter(
                    triple for block in next_fixed for triple in it.combinations(block, 3)
                )
                if any(
                    count > 2 and frozenset(triple) not in anchors
                    for triple, count in counts.items()
                ):
                    counters["nonanchor_heavy_multiplicity_excess"] += 1
                    continue
                assert Counter(p for block in fixed for p in block) == Counter(
                    p for block in next_fixed for p in block
                )
                new_local = {block for block in next_fixed if anchor <= set(block)}
                assert Counter(p for block in local for p in set(block) - anchor) == Counter(
                    p for block in new_local for p in set(block) - anchor
                )
                key = tuple(sorted(next_fixed))
                if key in found:
                    counters["deduplicated"] += 1
                    continue
                found[key] = {
                    "anchor": sorted(anchor),
                    "removed": sorted(outgoing),
                    "added": sorted(incoming),
                }
                counters["accepted"] += 1
    return sorted(found.items()), dict(counters)


def shifted_rows(basis_rows, heavy, fixed):
    chosen = {i for i, block in enumerate(heavy) if block in set(fixed)}
    assert len(chosen) == 28
    result = []
    for ordinary_ids, heavy_ids, lower, upper in basis_rows:
        shift = len(chosen & set(heavy_ids))
        result.append(
            (
                ordinary_ids,
                [1] * len(ordinary_ids),
                lower - shift,
                upper if upper == INF else upper - shift,
            )
        )
    assert len(result) == 697
    return result


def ranked_neighbors(fixed, heavy, blocks, rows, cuts):
    generated, counts = candidates(fixed, heavy)
    records = []
    for candidate, move in generated:
        hids = [heavy.index(block) for block in candidate]
        numerators = [
            max(0, cut["rhs"] - sum(cut["coefficients"][i] for i in hids)) for cut in cuts
        ]
        records.append(
            {
                **move,
                "heavy_global_ids": [blocks.index(block) for block in candidate],
                "heavy_local_ids": hids,
                "heavy_sha256": data_hash(candidate),
                "shifted_rows_sha256": data_hash(shifted_rows(rows, heavy, candidate)),
                "cut_violation_numerators": numerators,
                "maximum_cut_lower_bound": [max(numerators), 1000],
            }
        )
    records.sort(
        key=lambda record: (record["maximum_cut_lower_bound"][0], record["heavy_global_ids"])
    )
    for rank, record in enumerate(records):
        record["rank"] = rank
    return records, counts


def main():
    assert not (HERE / "proposal.json").exists()
    manifest = json.loads(MANIFEST.read_text())
    assert sha(SEED) == "8bfb962deaeeede2032d9efac1783f7eaabde38aada16c8f5fecdd2f19f84ef3"
    model = ROOT / manifest["model"]
    assert sha(model) == manifest["model_sha256"]
    spec = importlib.util.spec_from_file_location("checked_switch_basis", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.MODEL, module.WITNESS = model, SEED
    blocks, ordinary, heavy, fixed, rows = module.rebuild()
    assert len(blocks) == 4368 and len(ordinary) == 1200 and len(heavy) == 276
    bundle = json.loads(BUNDLE.read_text())
    gate = json.loads(CUT_GATE.read_text())
    assert gate["passed"] and gate["cuts"] == 14 and gate["bundle_sha256"] == sha(BUNDLE)
    assert bundle["heavy_global_ids"] == [blocks.index(block) for block in heavy]
    cuts = bundle["cuts"]
    assert len(cuts) == 14
    for cut in cuts:
        dual = json.loads((ROOT / cut["dual_path"]).read_text())
        assert sha(ROOT / cut["dual_path"]) == cut["dual_sha256"]
        assert cut["denominator"] == dual["denominator"] == 1000
        assert max(abs(weight) for _, weight in dual["weights"]) <= 1000
    records, counts = ranked_neighbors(fixed, heavy, blocks, rows, cuts)
    baseline = json.loads(BASELINE_RESULT.read_text())
    objective = next(attempt["objective"] for attempt in baseline["attempts"] if attempt["elastic"])
    assert objective == 10.627554709636422
    proposal = {
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "input_files": {
            str(path.relative_to(ROOT)): sha(path)
            for path in (SOURCE, MANIFEST, SEED, model, LP_CORE, BUNDLE, CUT_GATE, BASELINE_RESULT)
        },
        "basis_rows": len(rows),
        "ordinary_variables": len(ordinary),
        "heavy_universe": len(heavy),
        "ordinary_global_ids": [blocks.index(block) for block in ordinary],
        "initial_heavy_global_ids": [blocks.index(block) for block in fixed],
        "initial_shifted_rows_sha256": data_hash(shifted_rows(rows, heavy, fixed)),
        "baseline_elastic_objective": objective,
        "cut_ids": [cut["id"] for cut in cuts],
        "ranking_rule": (
            "Maximum positive exact cut violation / 1000, then lexicographic global heavy IDs."
        ),
        "enumeration_counts": counts,
        "accepted_by_anchor": dict(Counter(str(row["anchor"]) for row in records)),
        "candidates": records,
        "selected_first_round_ranks": list(range(min(20, len(records)))),
        "optimization_calls": 0,
        "proposed_budget": {"rounds_max": 3, "lp_evaluations_max": 60, "solver_seconds_max": 30},
        "scope": (
            "Only degree-preserving two-edge switches in one of four fixed-anchor links. "
            "Finite candidate enumeration and affine LP row mapping; no LP or optimizer has run."
        ),
    }
    (HERE / "proposal.json").write_text(json.dumps(proposal, indent=2) + "\n")
    print(
        json.dumps(
            {
                "counts": counts,
                "by_anchor": proposal["accepted_by_anchor"],
                "proposal_sha256": sha(HERE / "proposal.json"),
                "optimization_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
