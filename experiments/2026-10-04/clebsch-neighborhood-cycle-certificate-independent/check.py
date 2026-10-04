# Document:    Independent Finite Clebsch Cycle Certificate Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3a91883e87cc93e1bcb9622cf5f25066b19c40f72e919caa43905b767276ace7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay supplied logical deductions with standard library only; no search."""

import copy
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "clebsch-neighborhood-cycle-certificate"
CERT_SHA = "6802e49098940c70253dbf17e0a44bc05acb800185d85356dc5031faa6c545fc"
BUILD_SHA = "2119950b2ff8d0967b02589f309f77466d12b6d7be1d0ee0eb87b5ccdc5fc007"
GEOMETRY_SHA = "ee685b514552f4ef85b6d4b4d71619a72c25a8b178b0763bc7fde71e330f3886"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(test, message):
    if not test:
        raise ValueError(message)


def canonical_ids(items, bound, name):
    require(isinstance(items, list), name + " must be a list")
    require(all(type(i) is int and 0 <= i < bound for i in items), name + " invalid index")
    require(items == sorted(set(items)), name + " duplicate or noncanonical")


def reference():
    points = tuple(range(1, 17))
    vertices = tuple(itertools.product((0, 1), repeat=4))
    label = {v: 1 + sum((b ^ (sum(v) % 2)) * 2**i for i, b in enumerate(v)) for v in vertices}
    edges = {
        tuple(sorted((label[u], label[v])))
        for u, v in itertools.combinations(vertices, 2)
        if sum(a != b for a, b in zip(u, v, strict=True)) in (1, 4)
    }
    neighbors = {p: {q for q in points if tuple(sorted((p, q))) in edges} for p in points}
    require(len(edges) == 40, "edge count")
    require(all(len(v) == 5 for v in neighbors.values()), "degree")
    require(
        all(
            len(neighbors[p] & neighbors[q]) == (0 if (p, q) in edges else 2)
            for p, q in itertools.combinations(points, 2)
        ),
        "common neighbors",
    )
    blocks = list(itertools.combinations(points, 5))
    triples = list(itertools.combinations(points, 3))
    kinds = [sum(p in edges for p in itertools.combinations(t, 2)) for t in triples]
    require(Counter(kinds) == {0: 160, 1: 240, 2: 160}, "triple counts")
    fixed = {tuple(sorted(v)) for v in neighbors.values()}
    independent = [t for t, k in zip(triples, kinds, strict=True) if not k]
    cycles = [b for b in blocks if all(len(set(b) & neighbors[p]) == 2 for p in b)]
    require(len(cycles) == 192 and len(fixed) == 16, "pentad counts")
    require(
        [b for b in blocks if not any(set(t) <= set(b) for t in independent)] == cycles,
        "cycle domain completeness under independent triple exclusion",
    )
    require(
        all(
            sum(set(t) <= set(b) for b in fixed) == (1 if k == 0 else 0)
            for t, k in zip(triples, kinds, strict=True)
        ),
        "fixed triple coverage",
    )
    rows = [
        {
            "triple": list(t),
            "support": [i for i, b in enumerate(cycles) if set(t) <= set(b)],
            "lower": 1,
            "upper": 1 if k == 1 else 2,
        }
        for t, k in zip(triples, kinds, strict=True)
        if k
    ]
    rows.append({"triple": None, "support": list(range(192)), "lower": 48, "upper": 48})
    return edges, fixed, cycles, rows, [blocks.index(b) for b in cycles]


def row_state(row, values):
    known_one = sum(values.get(i) == 1 for i in row["support"])
    unknown = [i for i in row["support"] if i not in values]
    return known_one, unknown


def violated(row, values):
    ones, unknown = row_state(row, values)
    return ones > row["upper"] or ones + len(unknown) < row["lower"]


def replay(trace, values, rows):
    require(isinstance(trace, list), "trace is not a list")
    values = dict(values)
    for step in trace:
        require(set(step) == {"row", "value", "variables"}, "trace fields")
        rid, value, ids = step["row"], step["value"], step["variables"]
        require(type(rid) is int and 0 <= rid < len(rows), "trace row index")
        require(type(value) is int and value in (0, 1), "trace Boolean")
        canonical_ids(ids, 192, "trace variables")
        ones, unknown = row_state(rows[rid], values)
        require(
            ids == unknown and bool(ids), "trace variables must be all unassigned row variables"
        )
        require(not violated(rows[rid], values), "cannot force from already contradicted row")
        require(
            ones == rows[rid]["upper"] if value == 0 else ones + len(unknown) == rows[rid]["lower"],
            "unjustified forced value",
        )
        values.update(dict.fromkeys(ids, value))
    return values


def contradiction(rid, values, rows):
    require(type(rid) is int and 0 <= rid < len(rows), "contradiction row index")
    require(violated(rows[rid], values), "claimed row is not contradicted")


def endpoints(values, selected, removed):
    canonical_ids(selected, 192, "selected")
    canonical_ids(removed, 192, "removed")
    require(selected == sorted(i for i, v in values.items() if v == 1), "selected endpoint")
    require(removed == sorted(i for i, v in values.items() if v == 0), "removed endpoint")


def check(certificate, ref):
    edges, fixed, cycles, rows, ids = ref
    require(certificate["not_unrestricted"] is True, "scope")
    require(certificate["solver_calls"] == 0, "producer solver count")
    require(certificate["source_sha256"] == BUILD_SHA, "producer source pin")
    require(certificate["geometry_sha256"] == GEOMETRY_SHA, "geometry pin")
    require(certificate["global_cycle_ids"] == ids, "lexicographic global cycle IDs")
    require(certificate["cycle_blocks"] == [list(b) for b in cycles], "cycle blocks")
    require(certificate["rows"] == rows, "complete reduced matrix")
    require(
        certificate["reference_cycle"] == 0 and certificate["initial_selected"] == [0],
        "reference assumption",
    )
    values = replay(certificate["initial_trace"], {0: 1}, rows)
    require(not any(violated(row, values) for row in rows), "initial state contradiction")
    deductions = certificate["deductions"]
    require(isinstance(deductions, list) and len(deductions) == 9, "nine deductions required")
    step_count = len(certificate["initial_trace"])
    for index, deduction in enumerate(deductions):
        variable = deduction["assume_selected"]
        require(
            type(variable) is int and 0 <= variable < 192 and variable not in values,
            "failed literal must be unassigned",
        )
        require(
            type(deduction["forced_value"]) is int and deduction["forced_value"] == 0,
            "failed positive literal forces zero",
        )
        branch = dict(values)
        branch[variable] = 1
        branch = replay(deduction["branch_trace"], branch, rows)
        contradiction(deduction["branch_contradiction_row"], branch, rows)
        endpoints(branch, deduction["branch_selected"], deduction["branch_removed"])
        values[variable] = 0
        values = replay(deduction["base_trace"], values, rows)
        if index + 1 < len(deductions):
            require(deduction["base_contradiction_row"] is None, "premature base contradiction")
            require(not any(violated(row, values) for row in rows), "unrecorded base contradiction")
        else:
            contradiction(deduction["base_contradiction_row"], values, rows)
            require(
                deduction["base_contradiction_row"] == certificate["final_contradiction_row"],
                "final contradiction identity",
            )
        step_count += len(deduction["branch_trace"]) + len(deduction["base_trace"])
    endpoints(values, certificate["final_selected"], certificate["final_removed"])
    contradiction(certificate["final_contradiction_row"], values, rows)
    # Check every explicit point map directly; trust no claimed symmetry group.
    maps = certificate["automorphisms"]
    require(isinstance(maps, list) and len(maps) == 192, "automorphism count")
    require([m["target_cycle"] for m in maps] == list(range(192)), "all cycle targets")
    words = [2 * x + sum((x // 2**i) % 2 for i in range(4)) % 2 for x in range(16)]
    expected_row_set = {(tuple(r["triple"]), r["lower"], r["upper"]) for r in rows[:-1]}
    cycle_set = set(cycles)
    for mapping in maps:
        permutation = mapping["point_permutation"]
        require(
            isinstance(permutation, list)
            and len(permutation) == 16
            and all(type(p) is int for p in permutation)
            and set(permutation) == set(range(1, 17)),
            "point bijection",
        )
        image = lambda items: tuple(sorted(permutation[p - 1] for p in items))  # noqa: E731
        require({image(e) for e in edges} == edges, "edge preservation")
        require({image(b) for b in fixed} == fixed, "fixed neighborhood preservation")
        require({image(b) for b in cycles} == cycle_set, "cycle domain preservation")
        require(
            {(image(r["triple"]), r["lower"], r["upper"]) for r in rows[:-1]} == expected_row_set,
            "triple row preservation",
        )
        require(image(cycles[0]) == cycles[mapping["target_cycle"]], "reference cycle target")
        coordinate = mapping["coordinate_permutation"]
        require(
            isinstance(coordinate, list)
            and len(coordinate) == 5
            and all(type(p) is int for p in coordinate)
            and set(coordinate) == set(range(5)),
            "coordinate bijection",
        )
        shift = mapping["xor_word"]
        require(type(shift) is int and shift in words, "even translation word")
        transported = [
            sum(((word // 2**i) % 2) * 2 ** coordinate[i] for i in range(5)) ^ shift
            for word in words
        ]
        require(
            [words.index(word) + 1 for word in transported] == permutation,
            "coordinate description differs from explicit map",
        )
    final_row = rows[certificate["final_contradiction_row"]]
    return {
        "propagation_steps": step_count,
        "failed_literals": [d["assume_selected"] for d in deductions],
        "final_row": final_row,
        "final_support_values": [values[i] for i in final_row["support"]],
        "final_selected": sum(v == 1 for v in values.values()),
        "final_removed": sum(v == 0 for v in values.values()),
        "automorphisms": len(maps),
    }


def damage_controls(certificate, ref):
    cases = {
        "wrong_row_lower": lambda c: c["rows"][0].__setitem__("lower", 0),
        "wrong_row_upper": lambda c: c["rows"][0].__setitem__("upper", 2),
        "missing_support": lambda c: c["rows"][0]["support"].pop(),
        "missing_row": lambda c: c["rows"].pop(),
        "bad_cardinality": lambda c: c["rows"][400].__setitem__("upper", 49),
        "missing_cycle": lambda c: c["cycle_blocks"].pop(),
        "changed_global_id": lambda c: c["global_cycle_ids"].__setitem__(0, 0),
        "missing_reference": lambda c: c.__setitem__("initial_selected", []),
        "bad_force_value": lambda c: c["initial_trace"][0].__setitem__("value", 1),
        "missing_force_variable": lambda c: c["initial_trace"][0]["variables"].pop(),
        "duplicate_force_variable": lambda c: c["initial_trace"][0]["variables"].append(1),
        "bool_force": lambda c: c["initial_trace"][0].__setitem__("value", False),
        "unjustified_force_row": lambda c: c["initial_trace"][0].__setitem__("row", 400),
        "wrong_failed_literal": lambda c: c["deductions"][0].__setitem__("assume_selected", 0),
        "inverted_failed_literal": lambda c: c["deductions"][0].__setitem__("forced_value", 1),
        "missing_branch_trace": lambda c: c["deductions"][2]["branch_trace"].clear(),
        "wrong_branch_conflict": lambda c: c["deductions"][0].__setitem__(
            "branch_contradiction_row", 400
        ),
        "bad_branch_endpoint": lambda c: c["deductions"][0]["branch_removed"].pop(),
        "missing_deduction": lambda c: c["deductions"].pop(),
        "bad_final_conflict": lambda c: c.__setitem__("final_contradiction_row", 400),
        "bad_final_endpoint": lambda c: c["final_selected"].pop(),
        "missing_automorphism": lambda c: c["automorphisms"].pop(),
        "duplicate_target": lambda c: c["automorphisms"][1].__setitem__("target_cycle", 0),
        "bad_point_map": lambda c: c["automorphisms"][0]["point_permutation"].__setitem__(0, 2),
        "bad_coordinate_map": lambda c: c["automorphisms"][0]["coordinate_permutation"].__setitem__(
            0, 1
        ),
        "odd_translation": lambda c: c["automorphisms"][0].__setitem__("xor_word", 1),
        "false_scope": lambda c: c.__setitem__("not_unrestricted", False),
    }
    results = {}
    for name, mutate in cases.items():
        damaged = copy.deepcopy(certificate)
        mutate(damaged)
        try:
            check(damaged, ref)
        except (ValueError, KeyError, IndexError, TypeError):
            results[name] = "rejected"
        else:
            raise ValueError("damaged certificate accepted: " + name)
    return results


def main():
    path = PRODUCER / "certificate.json"
    require(sha(path) == CERT_SHA, "certificate pin")
    require(sha(PRODUCER / "build.py") == BUILD_SHA, "build pin")
    certificate = json.loads(path.read_text())
    ref = reference()
    result = check(certificate, ref)
    controls = damage_controls(certificate, ref)
    audit = {
        "passed": True,
        "certificate_sha256": CERT_SHA,
        "producer_source_sha256": BUILD_SHA,
        "checker_sha256": sha(Path(__file__)),
        "rows": 401,
        "cycles": 192,
        "result": result,
        "damage_controls": controls,
        "optimizer_calls": 0,
        "cover_searches": 0,
        "independently_checked_conditional_proof": True,
        "scope": (
            "No cover with both the Clebsch pair profile and all sixteen fixed neighbor pentads."
        ),
        "excludes_all_clebsch_profile_covers": False,
        "global_lower_bound": False,
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "damage_controls": len(controls),
                "result": result,
            }
        )
    )


if __name__ == "__main__":
    main()
