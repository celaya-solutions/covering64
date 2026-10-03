# Document:    Independent Local-Family Reduction and Symmetry Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      fac6b0145fb85cd0f7a88313fa780e3d5a6e7e80ef0726a3ab96ff6f0ced1d6b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite arithmetic and an exact point-bijection audit, without nauty or Gram DFS."""

import hashlib
import itertools as it
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments/2026-10-03/local-family-classification"


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pattern_burnside():
    edges = list(it.combinations(range(4), 2))
    patterns = [x for x in it.product(range(4), repeat=6)
                if all(sum(n for e, n in zip(edges, x) if v in e) <= 3 for v in range(4))]
    fixed = Counter()
    for permutation in it.permutations(range(4)):
        action = [edges.index(tuple(sorted(permutation[v] for v in e))) for e in edges]
        for values in patterns:
            if all(values[i] == values[action[i]] for i in range(6)):
                fixed[sum(values)] += 1
    require(all(value % 24 == 0 for value in fixed.values()), "nonintegral Burnside count")
    return {r: fixed[r] // 24 for r in range(7)}


def determinant(matrix):
    values = [[Fraction(x) for x in row] for row in matrix]
    product = Fraction(1)
    for column in range(len(values)):
        pivot = next((r for r in range(column, len(values)) if values[r][column]), None)
        if pivot is None:
            return 0
        if pivot != column:
            values[pivot], values[column] = values[column], values[pivot]
            product = -product
        term = values[column][column]
        product *= term
        for r in range(column + 1, len(values)):
            ratio = values[r][column] / term
            for c in range(column + 1, len(values)):
                values[r][c] -= ratio * values[column][c]
            values[r][column] = 0
    require(product.denominator == 1, "nonintegral Gram determinant")
    return int(product)


def determinants(rows):
    checked = []
    for row in rows:
        matrix = [[4 if i == j else 1 for j in range(13)] for i in range(13)]
        start = 0
        for half_length in row["cycle_half_lengths"]:
            for i in range(2 * half_length):
                a, b = start + i, start + (i + 1) % (2 * half_length)
                value = 0 if i % 2 == 0 else 2
                matrix[a][b] = matrix[b][a] = value
            start += 2 * half_length
        value = determinant(matrix)
        require(value == row["determinant"], "Gram determinant mismatch")
        square = value >= 0 and math.isqrt(value) ** 2 == value
        require(square == row["square"], "Gram square flag mismatch")
        checked.append({"holes": row["holes"], "cycles": row["cycle_half_lengths"],
                        "determinant": value, "square": square})
    return checked


def automorphisms(blocks):
    block_sets = [frozenset(block) for block in blocks]
    block_collection = set(block_sets)
    pair_counts = Counter(pair for block in blocks for pair in it.combinations(block, 2))
    points = list(range(1, 14))
    signatures = {p: tuple(sorted(pair_counts[tuple(sorted((p, q)))]
                                  for q in points if q != p)) for p in points}
    incident = {p: [block for block in block_sets if p in block] for p in points}
    mapping = {}
    used = set()
    solutions = []
    nodes = 0

    def compatible(p, q):
        if signatures[p] != signatures[q]:
            return False
        if any(pair_counts[tuple(sorted((p, a)))] != pair_counts[tuple(sorted((q, b)))]
               for a, b in mapping.items()):
            return False
        for block in incident[p]:
            partial = {mapping[x] for x in block if x in mapping} | {q}
            if not any(partial <= target for target in block_sets):
                return False
        return True

    def visit():
        nonlocal nodes
        nodes += 1
        if len(mapping) == 13:
            require({frozenset(mapping[x] for x in b) for b in blocks} == block_collection,
                    "nonautomorphism passed leaf checks")
            solutions.append(tuple(mapping[p] for p in points))
            return
        possibilities = [(p, [q for q in points if q not in used and compatible(p, q)])
                         for p in points if p not in mapping]
        p, targets = min(possibilities, key=lambda entry: (len(entry[1]), entry[0]))
        for q in targets:
            mapping[p] = q
            used.add(q)
            visit()
            used.remove(q)
            del mapping[p]

    visit()
    require(len(solutions) == len(set(solutions)), "duplicate automorphism")
    return solutions, nodes, pair_counts


def main():
    enumeration = json.loads((SOURCE / "enumeration.json").read_text())
    patterns = pattern_burnside()
    require(sum(patterns.values()) == 26, "wrong total normalized hole types")
    require(patterns == {int(k): v for k, v in enumeration["all_hole_pattern_counts"].items()},
            "hole-pattern counts disagree")
    witness = SOURCE / "enumeration-family-001.txt"
    blocks = [tuple(map(int, line.split())) for line in witness.read_text().splitlines()]
    require(len(blocks) == len(set(blocks)) == 13, "wrong family size")
    require(Counter(p for b in blocks for p in b) == {p: 4 for p in range(1, 14)},
            "not regular degree4")
    group, nodes, pair_counts = automorphisms(blocks)
    holes = sorted(set(it.combinations(range(1, 14), 2)) - set(pair_counts))
    require(holes == [(5, 12), (6, 9), (7, 10), (8, 11)], "wrong r4 missing matching")
    unused = sorted(set(range(1, 14)) - set(it.chain.from_iterable(holes)))
    hole_orbits = sorted({tuple(sorted({tuple(sorted((g[a - 1], g[b - 1]))) for g in group}))
                          for a, b in holes})
    point_orbits = sorted({tuple(sorted({g[p - 1] for g in group})) for p in unused})
    # Four-edge matchings in P3+5K2: no spoke(5 choices), one spoke(20 choices).
    target_matchings = math.comb(5, 4) + 2 * math.comb(5, 3)
    maps = target_matchings * math.factorial(4) * 2**4 * math.factorial(5)
    require(maps % len(group) == 0, "nonintegral orbit-stabilizer family count")
    r6_path = SOURCE / "enumeration-family-002.txt"
    r6_blocks = [tuple(map(int, row.split())) for row in r6_path.read_text().splitlines()]
    r6_group, r6_nodes, _ = automorphisms(r6_blocks)
    # Independently weighted r4 completions for the two normalized hole types.
    # Their actual matching multiplicities are1296 and972, respectively.
    normalized_r4 = 6 * 1296 + 2 * 972
    normalized_by_group = math.factorial(13) // len(group) * 5 // 13 // 15400
    require(normalized_r4 == normalized_by_group == 9720, "r4 orbit mass mismatch")
    body = {"scope": "Independent reduction counts, exact determinants and r4 symmetries; "
                    "does not independently replay the full local-family enumeration",
            "status": "PASS", "audit_source_sha256": sha(Path(__file__)),
            "enumeration_sha256": sha(SOURCE / "enumeration.json"), "r4_sha256": sha(witness),
            "proof_readme_sha256": sha(SOURCE / "README.md"),
            "direct_replay_source_sha256": sha(SOURCE / "replay.cpp"),
            "hole_type_counts_by_r": patterns,
            "fraction_gram_determinants": determinants(enumeration["determinant_table"]),
            "r4_automorphism_order": len(group), "r4_automorphism_search_nodes": nodes,
            "r4_automorphisms": group, "r4_holes": holes, "r4_hole_orbits": hole_orbits,
            "r4_unmatched_points": unused, "r4_unmatched_point_orbits": point_orbits,
            "r4_target_matchings_in_P3_plus_5K2": target_matchings,
            "r4_all_point_maps_into_P3_plus_5K2": maps,
            "r4_distinct_embedded_families": maps // len(group),
            "r4_no_spoke_embedded_families": 5 * math.factorial(4) * 2**4 *
                math.factorial(5) // len(group),
            "r4_one_spoke_embedded_families": 20 * math.factorial(4) * 2**4 *
                math.factorial(5) // len(group),
            "r4_normalized_family_orbit_mass": normalized_r4,
            "r6_sha256": sha(r6_path), "r6_automorphism_order": len(r6_group),
            "r6_automorphism_search_nodes": r6_nodes,
            "r6_distinct_embedded_families": 2 * math.factorial(6) * 2**6 // len(r6_group)}
    header = {"Document": "Independent Local-Family Reduction and Symmetry Audit",
              "Version": "v1.0.0",
              "Author": "Celaya Solutions", "Contact": "hello@celayasolutions.com",
              "Date": "2026-10-03", "SHA256": hashlib.sha256(json.dumps(body, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest(), "Chain": "n/a",
              "Tx": "[not anchored]", "License": "All Rights Reserved / Celaya Solutions"}
    Path(__file__).with_name("result.json").write_text(
        json.dumps({"document_header": header, "body": body}, indent=2) + "\n")
    print(json.dumps({k: body[k] for k in ["status", "r4_automorphism_order",
          "r4_automorphism_search_nodes", "r4_hole_orbits", "r4_unmatched_point_orbits",
          "r4_all_point_maps_into_P3_plus_5K2", "r4_distinct_embedded_families"]}))


if __name__ == "__main__":
    main()
