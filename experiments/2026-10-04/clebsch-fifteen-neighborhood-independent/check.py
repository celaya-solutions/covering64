# Document:    Independent Fifteen Neighborhood Forcing Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      67f82c0324e5ee2a160cfb9b291892212914a08dbd949754d00d035957bd0294
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild finite candidates and exact identities; replay the prior finite proof."""

import copy
import hashlib
import importlib.util
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "clebsch-fifteen-neighborhood-forcing"
FILES_SHA = "335bac9d154ded7028b1d54d3089811b72472c5cab76aca4f1b2ff4b7deaebd1"
SUMMARY_SHA = "2cb7a539e586c3c35c926bcc8ac1888ebf8e003fe8b1f783e42ba8bcab50ab8f"
PRIOR = HERE.parent / "clebsch-neighborhood-cycle-certificate-independent"
PRIOR_CHECK_SHA = "b1d2355fac870cb985d0e81c13a0a78c52bc59fc3a3ea08bd38142ecec4f9337"
CERT_SHA = "6802e49098940c70253dbf17e0a44bc05acb800185d85356dc5031faa6c545fc"
AUDIT_SHA = "de03e575af4237a99f5ad10083ac7f0651021c8349d3250162cef2972f752e84"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(test, message):
    if not test:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), message)


def reference():
    points = tuple(range(1, 17))
    vertices = tuple(itertools.product((0, 1), repeat=4))
    labels = {v: 1 + sum((b ^ (sum(v) % 2)) * 2**i for i, b in enumerate(v)) for v in vertices}
    edges = {
        tuple(sorted((labels[u], labels[v])))
        for u, v in itertools.combinations(vertices, 2)
        if sum(a != b for a, b in zip(u, v, strict=True)) in (1, 4)
    }
    neighbors = {p: tuple(q for q in points if tuple(sorted((p, q))) in edges) for p in points}
    require(len(edges) == 40 and all(len(n) == 5 for n in neighbors.values()), "graph sizes")
    fixed = [neighbors[p] for p in points if p != 1]
    covered = set().union(*(set(itertools.combinations(b, 3)) for b in fixed))
    missing = set(itertools.combinations(neighbors[1], 3))
    require(
        len(covered) == 150 and len(missing) == 10 and not covered & missing,
        "independent triple partition",
    )
    all_triples = list(itertools.combinations(points, 3))
    independent = {
        t for t in all_triples if not any(p in edges for p in itertools.combinations(t, 2))
    }
    require(covered | missing == independent, "all independent triples accounted")
    rows = []
    for index, block in enumerate(itertools.combinations(points, 5)):
        if any(t in covered for t in itertools.combinations(block, 3)):
            continue
        inside = [p for p in itertools.combinations(block, 2) if p in edges]
        degrees = sorted(sum(v in pair for pair in inside) for v in block)
        kinds = {
            (2, 2, 2, 2, 2): "C5",
            (1, 2, 2, 2, 3): "C4-leaf",
            (1, 1, 2, 2, 2): "P5",
            (1, 1, 1, 1, 4): "K1,4",
            (0, 0, 0, 0, 0): "missing-neighborhood",
        }
        require(tuple(degrees) in kinds, "unexpected degree type")
        kind = kinds[tuple(degrees)]
        if kind != "missing-neighborhood":
            reached = {block[0]}
            for _ in range(4):
                reached |= {v for pair in inside if set(pair) & reached for v in pair}
            require(reached == set(block), "type must be connected")
        else:
            require(block == neighbors[1], "only missing independent pentad allowed")
        rows.append(
            {
                "block": list(block),
                "class": kind,
                "contains_point_one": 1 in block,
                "degree_sequence": degrees,
                "edge_count": len(inside),
                "id": index,
                "independent_triples": sum(
                    t in independent for t in itertools.combinations(block, 3)
                ),
                "point_one_graph_degree": sum(1 in pair for pair in inside),
            }
        )
    require(len(rows) == 258, "candidate count")
    return points, edges, neighbors, fixed, covered, missing, rows


def check(data, ref):
    points, edges, neighbors, fixed, covered, missing, candidates = ref
    summary, identities, maps = data["summary"], data["identities"], data["translations"]
    same(data["candidates"], candidates, "complete candidate records")
    counts = dict(Counter(c["class"] for c in candidates))
    same(
        counts,
        {"C5": 192, "C4-leaf": 30, "P5": 30, "K1,4": 5, "missing-neighborhood": 1},
        "class counts",
    )
    rooted = defaultdict(Counter)
    for c in candidates:
        rooted[c["class"]][str(c["point_one_graph_degree"])] += 1
    same(summary["candidate_class_point_degrees"], dict(rooted), "rooted degree counts")
    same(summary["candidate_classes"], counts, "summary class counts")
    same(summary["fixed_neighborhoods"], [list(b) for b in fixed], "fixed neighborhoods")
    same(summary["missing_neighborhood"], list(neighbors[1]), "missing neighborhood")
    for key, value in {
        "all_pentads_examined": 4368,
        "candidate_count": 258,
        "fixed_independent_triples": 150,
        "remaining_independent_triples": 10,
        "transitivity_cases_checked": 16,
        "passed": True,
        "solver_calls": 0,
        "unrestricted_claim": False,
    }.items():
        same(summary[key], value, "summary " + key)
    columns = ["a", "b", "c", "d", "e", "x"]
    same(identities["columns"], columns, "identity columns")
    # Derive right-hand sides from the fixed blocks and the stated pair profile.
    rooted_pair_sum = sum(6 if tuple(sorted((1, p))) in edges else 5 for p in points if p != 1)
    require(rooted_pair_sum == 80 and rooted_pair_sum % 4 == 0, "point replication")
    expected = {
        "cardinality": {"coefficients": [1, 1, 1, 1, 1, 0], "rhs": 64 - len(fixed)},
        "graph_edges": {"coefficients": [5, 5, 4, 4, 0, 0], "rhs": len(edges) * 6},
        "independent_triples": {"coefficients": [0, 1, 1, 4, 10, 0], "rhs": len(missing)},
        "point_one_occurrences": {
            "coefficients": [0, 1, 0, 1, 0, 1],
            "rhs": rooted_pair_sum // 4 - sum(1 in b for b in fixed),
        },
        "graph_edges_at_point_one": {
            "coefficients": [0, 3, 0, 4, 0, 2],
            "rhs": len(neighbors[1]) * 6,
        },
    }
    require(
        not any(pair in edges for b in fixed for pair in itertools.combinations(b, 2)),
        "fixed blocks are independent",
    )
    same(identities["rows"], expected, "derived coefficient matrix and right-hand sides")
    types = {"C5": 0, "C4-leaf": 1, "P5": 2, "K1,4": 3, "missing-neighborhood": 4}
    for c in candidates:
        vector = [0] * 6
        vector[types[c["class"]]] = 1
        vector[5] = int(c["class"] == "C5" and c["contains_point_one"])
        measured = {
            "cardinality": 1,
            "graph_edges": c["edge_count"],
            "independent_triples": c["independent_triples"],
            "point_one_occurrences": int(c["contains_point_one"]),
            "graph_edges_at_point_one": c["point_one_graph_degree"],
        }
        for name, row in expected.items():
            require(
                sum(a * b for a, b in zip(row["coefficients"], vector, strict=True))
                == measured[name],
                "per-block identity contribution",
            )

    def subtract(left, factor, right):
        return {
            "coefficients": [
                a - factor * b
                for a, b in zip(left["coefficients"], right["coefficients"], strict=True)
            ],
            "rhs": left["rhs"] - factor * right["rhs"],
        }

    first = subtract(expected["graph_edges_at_point_one"], 2, expected["point_one_occurrences"])
    second = subtract(
        {
            "coefficients": [5 * x for x in expected["cardinality"]["coefficients"]],
            "rhs": 5 * expected["cardinality"]["rhs"],
        },
        1,
        expected["graph_edges"],
    )
    third = subtract(expected["independent_triples"], 1, second)
    same(first, {"coefficients": [0, 1, 0, 2, 0, 0], "rhs": 0}, "b+2d=0")
    same(second, {"coefficients": [0, 0, 1, 1, 5, 0], "rhs": 5}, "c+d+5e=5")
    same(third, {"coefficients": [0, 1, 0, 3, 5, 0], "rhs": 5}, "b+3d+5e=5")
    # Nonnegative b,d are zero by the first identity. The third then gives
    # e=1; second gives c=0; cardinality gives a=48; point count gives x=15.
    solution = [48, 0, 0, 0, 1, 15]
    for row in expected.values():
        require(
            sum(a * b for a, b in zip(row["coefficients"], solution, strict=True)) == row["rhs"],
            "derived unique solution",
        )
    same(identities["aggregate_solutions"], [solution], "saved unique aggregate solution")
    same(summary["aggregate_solution"], solution, "summary solution")
    same(summary["aggregate_solution_columns"], columns, "summary columns")
    require(len(maps) == 16, "sixteen normalization cases")
    words = [2 * x + sum((x // 2**i) % 2 for i in range(4)) % 2 for x in range(16)]
    for point, entry in zip(points, maps, strict=True):
        same(entry["missing_neighborhood_point"], point, "normalization source")
        mapping = entry["to_point_one"]
        same(
            mapping,
            [words.index(word ^ words[point - 1]) + 1 for word in words],
            "explicit XOR translation",
        )
        require(set(mapping) == set(points) and mapping[point - 1] == 1, "point normalization")
        image = lambda block: tuple(sorted(mapping[p - 1] for p in block))  # noqa: E731
        require({image(pair) for pair in edges} == edges, "translation graph preservation")
        require(image(neighbors[point]) == neighbors[1], "omitted neighborhood normalization")
        require(
            {image(neighbors[p]) for p in points if p != point} == set(fixed),
            "fifteen fixed neighborhood normalization",
        )
    dependency = summary["sixteen_neighborhood_exclusion_dependency"]
    same(dependency["certificate_sha256"], CERT_SHA, "prior certificate pin")
    same(dependency["independent_audit_sha256"], AUDIT_SHA, "prior audit pin")
    same(dependency["independent_audit_passed"], True, "prior audit passed")
    same(
        dependency["certificate"],
        "experiments/2026-10-04/clebsch-neighborhood-cycle-certificate/certificate.json",
        "prior certificate path",
    )
    same(
        dependency["independent_audit"],
        "experiments/2026-10-04/clebsch-neighborhood-cycle-certificate-independent/audit.json",
        "prior audit path",
    )
    return {
        "candidate_classes": counts,
        "rooted_degrees": dict(rooted),
        "solution": solution,
        "forcing_identities": [first, second, third],
        "normalization_cases": len(maps),
    }


def controls(data, ref):
    cases = {
        "omitted_candidate": lambda d: d["candidates"].pop(),
        "duplicate_candidate": lambda d: d["candidates"].append(d["candidates"][0]),
        "bad_label": lambda d: d["candidates"][0]["block"].__setitem__(0, 0),
        "bad_id": lambda d: d["candidates"][0].__setitem__("id", 0),
        "bad_class": lambda d: d["candidates"][0].__setitem__("class", "P5"),
        "bad_root_degree": lambda d: d["candidates"][0].__setitem__("point_one_graph_degree", 3),
        "bad_independent_count": lambda d: d["candidates"][0].__setitem__("independent_triples", 1),
        "bool_id": lambda d: d["candidates"][0].__setitem__("id", True),
        "bad_rooted_summary": lambda d: d["summary"]["candidate_class_point_degrees"][
            "C5"
        ].__setitem__("2", 61),
        "bad_identity_rhs": lambda d: d["identities"]["rows"]["cardinality"].__setitem__("rhs", 48),
        "bad_identity_coefficient": lambda d: d["identities"]["rows"]["graph_edges_at_point_one"][
            "coefficients"
        ].__setitem__(1, 2),
        "omitted_identity": lambda d: d["identities"]["rows"].pop("independent_triples"),
        "bad_solution": lambda d: d["identities"]["aggregate_solutions"][0].__setitem__(4, 0),
        "missing_translation": lambda d: d["translations"].pop(),
        "bad_translation": lambda d: d["translations"][1]["to_point_one"].__setitem__(0, 1),
        "bad_missing_point": lambda d: d["translations"][1].__setitem__(
            "missing_neighborhood_point", 1
        ),
        "bad_proof_pin": lambda d: d["summary"][
            "sixteen_neighborhood_exclusion_dependency"
        ].__setitem__("certificate_sha256", "0" * 64),
        "failed_prior_audit": lambda d: d["summary"][
            "sixteen_neighborhood_exclusion_dependency"
        ].__setitem__("independent_audit_passed", False),
        "unrestricted_claim": lambda d: d["summary"].__setitem__("unrestricted_claim", True),
    }
    results = {}
    for name, mutate in cases.items():
        damaged = copy.deepcopy(data)
        mutate(damaged)
        try:
            check(damaged, ref)
        except (ValueError, KeyError, TypeError, IndexError):
            results[name] = "rejected"
        else:
            raise ValueError("damaged data accepted: " + name)
    return results


def main():
    require(sha(PRODUCER / "files.json") == FILES_SHA, "file manifest pin")
    require(sha(PRODUCER / "summary.json") == SUMMARY_SHA, "summary pin")
    files = json.loads((PRODUCER / "files.json").read_text())
    for name, digest in files.items():
        require(sha(PRODUCER / name) == digest, "producer file hash: " + name)
    data = {
        key: json.loads((PRODUCER / (key + ".json")).read_text())
        for key in ("candidates", "identities", "translations", "summary")
    }
    ref = reference()
    result = check(data, ref)
    damaged = controls(data, ref)
    require(sha(PRIOR / "check.py") == PRIOR_CHECK_SHA, "prior checker pin")
    require(sha(PRIOR / "audit.json") == AUDIT_SHA, "prior audit file")
    certificate = HERE.parent / "clebsch-neighborhood-cycle-certificate/certificate.json"
    require(sha(certificate) == CERT_SHA, "prior certificate file")
    spec = importlib.util.spec_from_file_location("prior_finite_checker", PRIOR / "check.py")
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.check(json.loads(certificate.read_text()), prior.reference())
    audit = {
        "passed": True,
        "files_sha256": FILES_SHA,
        "summary_sha256": SUMMARY_SHA,
        "checker_sha256": sha(Path(__file__)),
        "producer_pins_checked": len(files),
        "result": result,
        "damage_controls": damaged,
        "sixteen_exclusion_fresh_replay": replay,
        "sixteen_certificate_sha256": CERT_SHA,
        "sixteen_checker_sha256": PRIOR_CHECK_SHA,
        "sixteen_audit_sha256": AUDIT_SHA,
        "optimizer_calls": 0,
        "cover_searches": 0,
        "conditional_conclusion": (
            "At most fourteen neighborhood pentads in any Clebsch-pair-profile cover."
        ),
        "independently_checked_conditional_proof": True,
        "global_lower_bound": False,
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "damage_controls": len(damaged),
                "result": result,
            }
        )
    )


if __name__ == "__main__":
    main()
