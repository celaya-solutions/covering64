# Document:    Heavy-Cut Separation Across Template Relabelings
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CUT = HERE.parent / "lookahead-parametric-cut/cut.json"
ANCHORS = [set(range(s, s + 3)) for s in (1, 5, 9, 13)]


def validate_map(mapping):
    assert sorted(mapping) == list(range(1, 17))
    for anchor in ANCHORS:
        image = {mapping[x - 1] for x in anchor}
        assert image in ANCHORS
        assert mapping[max(anchor)] == max(image) + 1


def maps():
    for groups in it.permutations(range(4)):
        for inner in it.product(list(it.permutations(range(3))), repeat=4):
            mapping = []
            for g in range(4):
                mapping.extend(4 * groups[g] + j + 1 for j in inner[g])
                mapping.append(4 * groups[g] + 4)
            yield tuple(mapping)


def inspect_witness(content, coefficients):
    blocks = [tuple(map(int, line.split())) for line in content.decode().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64
    assert all(len(b) == 5 and tuple(sorted(set(b))) == b
               and min(b) >= 1 and max(b) <= 16 for b in blocks)
    assert Counter(p for b in blocks for p in b) == {p: 20 for p in range(1, 17)}
    heavy = [b for b in blocks if b in coefficients]
    assert len(heavy) == 28
    assert all(b in coefficients or all(len(set(b) & a) <= 1 for a in ANCHORS)
               for b in blocks)
    for anchor in ANCHORS:
        local = [b for b in heavy if anchor <= set(b)]
        assert len(local) == 7
        assert Counter(p for b in local for p in set(b) - anchor) == {
            p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor}
    return heavy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("witness", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), "preserve existing evidence"
    cut_bytes = CUT.read_bytes()
    witness_bytes = args.witness.read_bytes()
    cut = json.loads(cut_bytes)
    receipt = json.loads((HERE.parent / "lookahead-cut-independent/audit.json").read_text())
    assert receipt["passed"] and receipt["sha256"]["cut"] == hashlib.sha256(
        cut_bytes).hexdigest()
    coefficients = dict(zip(map(tuple, cut["heavy_blocks"]), cut["coefficients"], strict=True))
    assert len(coefficients) == 276
    heavy = inspect_witness(witness_bytes, coefficients)
    mapping_set = set(maps())
    assert len(mapping_set) == 31104
    lowest, highest, best_map = None, None, None
    violated = 0
    # These are all bijections preserving the four anchor/hub groups. They
    # preserve the ordinary universe, template incidence conditions, regular
    # degrees, and the set of all six hub graphs. Pullback therefore preserves
    # validity of the already checked conditional inequality.
    for mapping in sorted(mapping_set):
        validate_map(mapping)
        lhs = sum(coefficients[tuple(sorted(mapping[p - 1] for p in b))] for b in heavy)
        if lowest is None or lhs < lowest:
            lowest, best_map = lhs, mapping
        highest = lhs if highest is None else max(highest, lhs)
        violated += lhs < cut["rhs"]
    pulled = [coefficients[tuple(sorted(best_map[p - 1] for p in b))]
              for b in coefficients]
    assert sum(c for b, c in zip(coefficients, pulled) if b in heavy) == lowest
    # Group generators provide direct finite domain checks, in addition to
    # every map's structural check above.
    generators = []
    for g in range(4):
        for offset in (0, 1):
            mapping = list(range(1, 17))
            a = 4 * g + offset
            mapping[a], mapping[a + 1] = mapping[a + 1], mapping[a]
            generators.append(mapping)
    for g in range(3):
        mapping = list(range(1, 17))
        mapping[4*g:4*g+4], mapping[4*g+4:4*g+8] = (
            mapping[4*g+4:4*g+8], mapping[4*g:4*g+4])
        generators.append(mapping)
    ordinary = {b for b in it.combinations(range(1, 17), 5)
                if all(len(set(b) & a) <= 1 for a in ANCHORS)}
    for mapping in generators:
        validate_map(mapping)
        assert {tuple(sorted(mapping[p - 1] for p in b)) for b in coefficients} == (
            set(coefficients))
        assert {tuple(sorted(mapping[p - 1] for p in b)) for b in ordinary} == ordinary
    broken = [list(range(1, 17)) for _ in range(3)]
    broken[0][0] = 2
    broken[1][0], broken[1][4] = broken[1][4], broken[1][0]
    broken[2][3], broken[2][7] = broken[2][7], broken[2][3]
    for mapping in broken:
        try:
            validate_map(mapping)
        except AssertionError:
            continue
        raise AssertionError("bad family map accepted")
    result = {"passed": True, "witness": str(args.witness),
              "witness_sha256": hashlib.sha256(witness_bytes).hexdigest(),
              "cut_sha256": hashlib.sha256(cut_bytes).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "maps": len(mapping_set), "domain_checked_generators": len(generators),
              "bad_maps_rejected": len(broken), "minimum_lhs": lowest,
              "maximum_lhs": highest, "rhs": cut["rhs"], "violated_maps": violated,
              "worst_violation": max(0, cut["rhs"] - lowest),
              "worst_map_images_of_1_to_16": best_map,
              "pulled_back_coefficients_in_base_order": pulled,
              "rules_out_fixed_heavy_completion": lowest < cut["rhs"],
              "scope": "Fixed heavy tuple within regular four-sevenfold family only; "
                       "no whole first-link exclusion or unrestricted conclusion."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k != "pulled_back_coefficients_in_base_order"}))


if __name__ == "__main__":
    main()
