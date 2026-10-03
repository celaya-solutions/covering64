# Document:    Independent Four Sevenfold Reduction and Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      28493451e975a350069eb3c829afe891dc223fb92efa7adb2c5a02cda54c1b67
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import copy
import hashlib
import importlib.util
import itertools
import json
import pathlib
import sys

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = pathlib.Path(__file__).resolve().parent
SCRATCH = pathlib.Path("experiments/scratch/four-seven-independent-models")
SOURCE = pathlib.Path("scripts/four_seven_search.py")
ANCHORS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
HUBS = (4, 8, 12, 16)
MIN, MAX = -(2**63), 2**63 - 1


def require(value, message):
    if not value:
        raise ValueError(message)


def key(terms, domain):
    return tuple(sorted(terms.items())), tuple(domain)


def actual_rows(proto):
    names = [v.name for v in proto.variables]
    result = []
    for row in proto.constraints:
        require(
            row.WhichOneof("constraint") == "linear" and not row.enforcement_literal,
            "full model is not unconditional linear",
        )
        terms = collections.Counter()
        for variable, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True):
            terms[names[variable]] += coefficient
        result.append(key(dict(terms), row.linear.domain))
    return collections.Counter(result)


def independent_targets(case):
    edges = {(0, 1), (1, 2), (2, 3), (0, 3)} if case == "cycle" else {(0, 1), (2, 3)}
    targets = {}
    for pair in itertools.combinations(range(1, 17), 2):
        value = 5
        for group, hub in zip(ANCHORS, HUBS, strict=True):
            if set(pair) <= set(group):
                value = 7
            elif hub in pair and any(a in pair for a in group):
                value = 6
        if pair[0] in HUBS and pair[1] in HUBS:
            edge = tuple(HUBS.index(p) for p in pair)
            if edge in edges:
                value += 1 if case == "cycle" else 2
        targets[pair] = value
    return targets


def combinatorics(blocks):
    allowed = [b for b in blocks if all(sum(p in group for p in b) != 2 for group in ANCHORS)]
    heavy = [b for b in allowed if any(set(group) <= set(b) for group in ANCHORS)]
    require((len(allowed), len(heavy)) == (1476, 276), "allowed block counts")
    other_by_anchor_count = collections.Counter(
        sum(p not in HUBS for p in b) for b in allowed if b not in set(heavy)
    )
    require(
        other_by_anchor_count == {1: 12, 2: 216, 3: 648, 4: 324}, "nonheavy block count identity"
    )
    edges = list(itertools.combinations(range(4), 2))
    canonical = {"cycle": (1, 0, 1, 1, 0, 1), "matching": (2, 0, 0, 0, 0, 2)}
    maps = []
    for weights in itertools.product(range(3), repeat=6):
        if not all(
            sum(w for e, w in zip(edges, weights, strict=True) if p in e) == 2 for p in range(4)
        ):
            continue
        case = "cycle" if max(weights) == 1 else "matching"
        witnesses = []
        for permutation in itertools.permutations(range(4)):
            image = {
                tuple(sorted(permutation[p] for p in e)): w
                for e, w in zip(edges, weights, strict=True)
            }
            if tuple(image[e] for e in edges) == canonical[case]:
                witnesses.append(permutation)
        require(witnesses, "unmapped hub excess graph")
        maps.append(
            dict(weights=weights, case=case, to_canonical=witnesses[0], mappings=len(witnesses))
        )
    require(
        len(maps) == 6
        and collections.Counter(m["case"] for m in maps) == {"cycle": 3, "matching": 3},
        "hub graph classification",
    )
    # Exhaustive classification of every triple establishes the multiplicity argument's premise.
    triple_types = {}
    for case in ("cycle", "matching"):
        targets = independent_targets(case)
        types = collections.Counter()
        for triple in itertools.combinations(range(1, 17), 3):
            if triple in ANCHORS:
                types["heavy"] += 1
            elif any(
                hub in triple and len(set(triple) & set(group)) == 2
                for group, hub in zip(ANCHORS, HUBS, strict=True)
            ):
                types["two_anchors_own_hub"] += 1
            else:
                require(
                    any(targets[pair] == 5 for pair in itertools.combinations(triple, 2)),
                    "nonheavy triple without a pair of multiplicity five",
                )
                types["contains_five_pair"] += 1
        require(
            types == {"heavy": 4, "two_anchors_own_hub": 12, "contains_five_pair": 544},
            "triple classification",
        )
        triple_types[case] = dict(types)
    return dict(
        all_block_variables=4368,
        allowed_blocks=1476,
        forbidden_blocks=2892,
        heavy_block_variables=276,
        nonheavy_block_variables=1200,
        nonheavy_by_anchor_count=dict(other_by_anchor_count),
        hub_graph_maps=maps,
        triple_classification=triple_types,
    ), allowed


def audit_case(module, case, blocks, triples, allowed):
    universe, model, xs, holes = module.build_model(case, max_missing=0)
    proto = cp_model_pb2.CpModelProto()
    raw = str(model.proto)
    text_format.Parse(raw, proto)
    (SCRATCH / f"{case}.pbtxt").write_text(raw)
    require(
        list(universe.blocks) == blocks and list(universe.triples) == triples,
        "lexicographic universe",
    )
    require(
        len(xs) == 4368 and not holes and len(proto.variables) == 4368, "full model variable count"
    )
    require(
        [(v.name, list(v.domain)) for v in proto.variables]
        == [(f"block_{i}", [0, 1]) for i in range(4368)],
        "variable names or domains",
    )
    require(
        not proto.HasField("objective")
        and not proto.HasField("floating_point_objective")
        and not proto.assumptions
        and not proto.solution_hint.vars,
        "unexpected objective, assumptions, or hint",
    )
    targets = independent_targets(case)
    require(
        sum(targets.values()) == 640
        and all(
            sum(value for pair, value in targets.items() if point in pair) == 80
            for point in range(1, 17)
        ),
        "pair target budgets",
    )
    allowed_set = set(allowed)
    indices = [i for i, b in enumerate(blocks) if b in allowed_set]
    expected = [
        key({f"block_{i}": 1}, [0, 0]) for i, b in enumerate(blocks) if b not in allowed_set
    ]
    expected.append(key({f"block_{i}": 1 for i in range(4368)}, [64, 64]))
    for point in range(1, 17):
        expected.append(key({f"block_{i}": 1 for i in indices if point in blocks[i]}, [20, 20]))
    for pair, target in targets.items():
        expected.append(
            key({f"block_{i}": 1 for i in indices if set(pair) <= set(blocks[i])}, [target, target])
        )
    for group in ANCHORS:
        expected.append(
            key({f"block_{i}": 1 for i in indices if set(group) <= set(blocks[i])}, [7, 7])
        )
    for triple in triples:
        expected.append(
            key({f"block_{i}": 1 for i in indices if set(triple) <= set(blocks[i])}, [1, MAX])
        )
    require(len(proto.constraints) == len(expected) == 3593, "full model row count")
    expected = collections.Counter(expected)
    require(actual_rows(proto) == expected, "full model row reconstruction")
    controls = []
    for label, position in [
        ("allow forbidden block", 0),
        ("wrong pair count", 2909),
        ("wrong heavy count", 3029),
        ("uncovered triple allowed", 3033),
    ]:
        damaged = copy.deepcopy(proto)
        if label == "allow forbidden block":
            damaged.constraints[position].linear.domain[-1] += 1
        else:
            damaged.constraints[position].linear.domain[0] -= 1
        require(actual_rows(damaged) != expected, "damaged row accepted")
        controls.append(dict(control=label, rejected=True))
    damaged = copy.deepcopy(proto)
    del damaged.constraints[-1]
    require(actual_rows(damaged) != expected, "missing coverage row accepted")
    controls.append(dict(control="missing coverage row", rejected=True))
    return dict(
        variables=4368,
        constraints=3593,
        pair_histogram=dict(collections.Counter(targets.values())),
        model_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        every_row_independently_reconstructed=True,
        damaged_controls=controls,
    )


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    snapshot = SCRATCH / "four_seven_search.py"
    snapshot.write_bytes(SOURCE.read_bytes())
    sys.path.insert(0, str(pathlib.Path("scripts").resolve()))
    spec = importlib.util.spec_from_file_location("frozen_four_seven_model", snapshot)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    certificate, allowed = combinatorics(blocks)
    cases = {
        case: audit_case(module, case, blocks, triples, allowed) for case in ("cycle", "matching")
    }
    witness = (
        ROOT.parent / "reduced-family-heuristic/strong-penalty-2026100365/search-diverse-13-h13.txt"
    )
    rows = [tuple(map(int, line.split())) for line in witness.read_text().splitlines()]
    controls = []
    for label, broken in [
        ("empty", []),
        ("wrong branch partial", rows),
        ("duplicate", [*rows[:-1], rows[0]]),
        ("repeated label", [(1, 1, 2, 3, 4), *rows[1:]]),
        ("outside label", [(0, 1, 2, 3, 4), *rows[1:]]),
    ]:
        for case in ("cycle", "matching"):
            try:
                module.check_candidate(broken, case)
            except ValueError:
                controls.append(dict(case=case, control=label, rejected=True))
            else:
                raise ValueError("candidate checker accepted invalid branch control")
    result = dict(
        complete=True,
        combinatorial_certificate=certificate,
        model_cases=cases,
        candidate_negative_controls=controls,
        candidate_checker_positive_path="No branch witness is known; no positive path claimed.",
        source_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        source_body_sha256=hashlib.sha256(
            b"".join(snapshot.read_bytes().splitlines(keepends=True)[9:])
        ).hexdigest(),
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        scope=(
            "Complete reduction and exact encoding audit for regular full64 covers "
            "with four sevenfold triples only."
        ),
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
