# Document:    Independent Group Symmetry Pair Parity Certificate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      8c2bc3d1456761d1b4f4ecce094aac8b8c1f3df442baf69cd9d77a597535001f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: i for i, block in enumerate(BLOCKS)}
GROUPS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compose(outer, inner):
    return tuple(outer[inner[p] - 1] for p in range(16))


def block_image(block, permutation):
    return tuple(sorted(permutation[p - 1] for p in block))


def parity_certificate(permutation, pair, required):
    identity = tuple(range(1, 17))
    require(tuple(sorted(permutation)) == identity, "not a point permutation")
    require(compose(permutation, permutation) == identity, "not an involution")
    require(all(permutation[p - 1] != p for p in range(1, 17)), "involution has fixed points")
    require(
        block_image(pair, permutation) == pair and permutation[pair[0] - 1] == pair[1],
        "pair is not transposed",
    )
    require(required % 2 == 1, "pair target is not odd")
    require(
        all(block_image(block, permutation) != block for block in BLOCKS), "a five-subset is fixed"
    )
    pair_blocks = [block for block in BLOCKS if set(pair) <= set(block)]
    orbits = set()
    for block in pair_blocks:
        image = block_image(block, permutation)
        require(
            set(pair) <= set(image) and block_image(image, permutation) == block,
            "pair-containing blocks are not partitioned into two-cycles",
        )
        orbits.add(tuple(sorted((RANK[block], RANK[image]))))
    require(
        len(pair_blocks) == 364 and len(orbits) == 182 and all(a != b for a, b in orbits),
        "pair block orbit count",
    )
    return dict(
        involution=permutation,
        transposed_pair=pair,
        required_pair_multiplicity=required,
        all_4368_five_subsets_checked=True,
        fixed_five_subsets=0,
        pair_containing_blocks=364,
        two_block_orbits=sorted(orbits),
        reduced_coefficients=[2] * 182,
        coefficient_gcd=2,
        right_hand_side_mod_gcd=1,
        conclusion="No invariant integer block family can have this odd pair count.",
    )


def case_certificate(case):
    identity = tuple(range(1, 17))
    if case == "cycle":
        generator = tuple(4 * (((p // 4) + 1) % 4) + p % 4 + 1 for p in range(16))
        action = [identity, generator, compose(generator, generator)]
        action.append(compose(generator, action[2]))
        involution, pair = action[2], (1, 9)
        generators = [generator]
    else:
        first = tuple(4 * ((p // 4) ^ 1) + p % 4 + 1 for p in range(16))
        second = tuple(4 * ((p // 4) ^ 2) + p % 4 + 1 for p in range(16))
        action = [identity, first, second, compose(first, second)]
        involution, pair = first, (1, 5)
        generators = [first, second]
    require(
        len(set(action)) == 4 and all(compose(a, b) in action for a in action for b in action),
        "wrong order-four action",
    )
    targets = dict.fromkeys(itertools.combinations(range(1, 17), 2), 5)
    for group, hub in zip(GROUPS, (4, 8, 12, 16), strict=True):
        for q in itertools.combinations(group, 2):
            targets[q] = 7
        for anchor in group:
            targets[tuple(sorted((anchor, hub)))] = 6
    hub_edges = [(4, 8), (8, 12), (12, 16), (4, 16)] if case == "cycle" else [(4, 8), (12, 16)]
    for edge in hub_edges:
        targets[edge] += 1 if case == "cycle" else 2
    require(
        all(targets[block_image(q, p)] == value for q, value in targets.items() for p in action),
        "pair targets not invariant",
    )
    require(
        any(pair[0] in group for group in GROUPS)
        and any(pair[1] in group for group in GROUPS)
        and not any(set(pair) <= set(group) for group in GROUPS),
        "pair is not cross-anchor",
    )
    allowed = {b for b in BLOCKS if all(len(set(b) & set(g)) != 2 for g in GROUPS)}
    all_orbits = {tuple(sorted(RANK[block_image(b, p)] for p in action)) for b in BLOCKS}
    allowed_orbits = {tuple(sorted(RANK[block_image(b, p)] for p in action)) for b in allowed}
    require(all(len(set(orbit)) == 4 for orbit in all_orbits), "nonfree block orbit")
    require(len(all_orbits) == 1092 and len(allowed_orbits) == 369, "group orbit counts")
    require(
        all(block_image(b, p) in allowed for b in allowed for p in action),
        "allowed set not preserved",
    )
    result = parity_certificate(involution, pair, 5)
    result.update(
        case=case,
        generators=generators,
        whole_action=action,
        full_block_orbits=1092,
        allowed_block_orbits=369,
        all_pair_targets_preserved=True,
        scope="Only the explicit simultaneous group action is excluded.",
    )
    return result


def main():
    cases = {case: case_certificate(case) for case in ("cycle", "matching")}
    cycle = cases["cycle"]
    controls = []
    for label, permutation, pair, required in [
        ("identity has fixed points", tuple(range(1, 17)), (1, 9), 5),
        ("order four is not an involution", tuple(cycle["generators"][0]), (1, 9), 5),
        ("pair is not transposed", tuple(cycle["involution"]), (1, 2), 5),
        ("even target has no parity contradiction", tuple(cycle["involution"]), (1, 9), 6),
    ]:
        try:
            parity_certificate(permutation, pair, required)
        except ValueError:
            controls.append(dict(control=label, rejected=True))
        else:
            raise ValueError("invalid parity certificate accepted")
    result = dict(
        complete=True,
        cases=cases,
        damaged_controls=controls,
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        scope=(
            "Elementary parity proof for two restricted group-invariant branches only; "
            "no solver used."
        ),
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                complete=True,
                excluded_restricted_actions=list(cases),
                parity_equation="2 times an integer equals 5",
                controls=len(controls),
            )
        )
    )


if __name__ == "__main__":
    main()
