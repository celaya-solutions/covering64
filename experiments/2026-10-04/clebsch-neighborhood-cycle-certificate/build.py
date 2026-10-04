# Document:    Finite Clebsch Neighborhood Cycle Exclusion Certificate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c4b5d02bca697d029e0c75dd2ee5547c070e5787e281b98982aa2b0bf1dc284a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay nine failed literals and provide every cycle-transitivity map; no solver."""

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GEOMETRY = HERE.parent / "clebsch-neighborhood-cycle-pilot/geometry.json"
FAILED_LITERALS = [4, 5, 20, 12, 13, 18, 19, 6, 14]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def propagate(rows, selected, removed):
    selected, removed = set(selected), set(removed)
    trace = []
    while True:
        changed = False
        for i, row in enumerate(rows):
            support = set(row["support"])
            count = len(support & selected)
            unknown = support - selected - removed
            lo, hi = row["lower"], row["upper"]
            if count > hi or count + len(unknown) < lo:
                return selected, removed, trace, i
            if count == hi and unknown:
                removed.update(unknown)
                trace.append({"row": i, "value": 0, "variables": sorted(unknown)})
                changed = True
            elif count + len(unknown) == lo and unknown:
                selected.update(unknown)
                trace.append({"row": i, "value": 1, "variables": sorted(unknown)})
                changed = True
        if not changed:
            return selected, removed, trace, None


def main():
    target = HERE / "certificate.json"
    assert not target.exists()
    geometry = json.loads(GEOMETRY.read_text())
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    cycle_ids = geometry["free_cycle_ids"]
    cycles = [blocks[i] for i in cycle_ids]
    rows = [
        {"triple": list(t), "support": [i for i, c in enumerate(cycles) if set(t) <= set(c)],
         "lower": 1, "upper": 1 if kind == 1 else 2}
        for t, kind in zip(triples, geometry["triple_kinds"], strict=True) if kind
    ]
    rows.append({"triple": None, "support": list(range(192)), "lower": 48, "upper": 48})
    yes, no, initial_trace, bad = propagate(rows, {0}, set())
    assert bad is None
    deductions = []
    for variable in FAILED_LITERALS:
        assert variable not in yes | no
        branch_yes, branch_no, branch_trace, branch_bad = propagate(rows, yes | {variable}, no)
        assert branch_bad is not None
        no.add(variable)
        yes, no, base_trace, bad = propagate(rows, yes, no)
        deductions.append({
            "assume_selected": variable,
            "branch_trace": branch_trace,
            "branch_selected": sorted(branch_yes), "branch_removed": sorted(branch_no),
            "branch_contradiction_row": branch_bad,
            "forced_value": 0, "base_trace": base_trace,
            "base_contradiction_row": bad,
        })
    assert bad is not None
    words = [x for x in range(32) if x.bit_count() % 2 == 0]
    label = {word: i + 1 for i, word in enumerate(words)}
    cycle_index = {cycle: i for i, cycle in enumerate(cycles)}
    maps = {}
    for permutation in itertools.permutations(range(5)):
        permuted = [sum(((word >> i) & 1) << permutation[i] for i in range(5)) for word in words]
        for shift in words:
            mapping = [label[word ^ shift] for word in permuted]
            image = tuple(sorted(mapping[v - 1] for v in cycles[0]))
            index = cycle_index[image]
            if index not in maps:
                maps[index] = {"target_cycle": index, "point_permutation": mapping,
                               "coordinate_permutation": list(permutation), "xor_word": shift}
    assert set(maps) == set(range(192))
    certificate = {
        "scope": "No64cover in the Clebsch pair-profile recipe with all16neighbor pentads fixed.",
        "not_unrestricted": True, "solver_calls": 0,
        "source_sha256": sha(Path(__file__)), "geometry_sha256": sha(GEOMETRY),
        "global_cycle_ids": cycle_ids, "cycle_blocks": cycles, "rows": rows,
        "reference_cycle": 0, "initial_selected": [0], "initial_trace": initial_trace,
        "deductions": deductions, "final_selected": sorted(yes), "final_removed": sorted(no),
        "final_contradiction_row": bad,
        "automorphisms": [maps[i] for i in range(192)],
        "completion_argument": (
            "Any recipe solution selects48cycles, hence onecycle. The verified automorphisms "
            "are transitive on all192cycles and preserve every row. A solution therefore "
            "maps to one selecting referencecycle0, contradicted by the nine checked "
            "failed-literal deductions. This does not exclude other Clebsch-profile covers."
        ),
    }
    target.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"certificate_sha256": sha(target), "deductions": len(deductions),
                      "automorphisms": len(maps), "contradiction_row": bad}))


if __name__ == "__main__":
    main()
