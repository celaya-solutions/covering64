# Document:    Audited Local Family Pair and Triple Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Add redundant cuts only after checking their assumptions in a saved model.

Each local point has degree4, hence12 local pair incidences. Its missing-pair
degree is at most1: all nongraph pairs are covered and at most one P3 spoke is
missing. Thus each point has at most one repeated-pair incidence. A local pair
of multiplicity3, or two quadruples sharing a triple, contradicts this count.
The argument is invariant under point relabeling and does not require global
point-essentiality or full coverage of outside triples.
"""

import argparse
import copy
import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

from covering64.core import verify_cover, write_blocks

BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
PAIRS = tuple(itertools.combinations(range(4, 17), 2))
TRIPLES = tuple(itertools.combinations(range(4, 17), 3))
G = {(4, 5), (4, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)}
COMMON = {(1, 2, 3, *pair) for pair in G}
MINIMUM = -(2**63)
MAXIMUM = 2**63 - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def family_audit(family):
    blocks = [tuple(b) for b in family]
    require(len(blocks) == len(set(blocks)) == 13, "13 distinct quadruples required")
    require(
        all(
            len(b) == 4
            and tuple(sorted(set(b))) == b
            and all(type(p) is int and 1 <= p <= 13 for p in b)
            for b in blocks
        ),
        "malformed local quadruple",
    )
    degrees = Counter(p for b in blocks for p in b)
    require(degrees == Counter({p: 4 for p in range(1, 14)}), "local degree is not4")
    pairs = Counter(p for b in blocks for p in itertools.combinations(b, 2))
    triples = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    missing = set(itertools.combinations(range(1, 14), 2)) - set(pairs)
    missing_degrees = Counter(p for pair in missing for p in pair)
    for p in range(1, 14):
        excess = sum(max(0, pairs[tuple(sorted((p, q)))] - 1) for q in range(1, 14) if p != q)
        require(excess == missing_degrees[p] <= 1, "missing or excess degree exceeds1")
    require(max(pairs.values()) <= 2, "pair cut violated")
    require(max(triples.values()) <= 1, "triple cut violated")
    return {
        "missing_pairs": len(missing),
        "maximum_pair_count": max(pairs.values()),
        "maximum_triple_count": max(triples.values()),
    }


def audit_classification(path):
    data = json.loads(path.read_text())
    require(
        data["complete"] is True and all(p["complete"] for p in data["patterns"]),
        "classification replay is incomplete",
    )
    rows = [family_audit(family) for pattern in data["patterns"] for family in pattern["families"]]
    require(len(rows) == 88, "expected88 independently enumerated families")
    return {
        "families": len(rows),
        "by_missing_pair_count": dict(Counter(r["missing_pairs"] for r in rows)),
        "maximum_pair_count": max(r["maximum_pair_count"] for r in rows),
        "maximum_triple_count": max(r["maximum_triple_count"] for r in rows),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "relabeling_argument": "Point permutations preserve every incidence and multiplicity; "
        "the same two cut bounds hold for every relabeling.",
    }


def key(terms, lo, hi, enforced=()):
    return tuple(sorted(terms)), (lo, hi), tuple(sorted(enforced))


def row_keys(model):
    return Counter(
        key(zip(row.linear.vars, row.linear.coeffs), *row.linear.domain, row.enforcement_literal)
        for row in model.constraints
        if row.HasField("linear") and len(row.linear.domain) == 2
    )


def local_terms(anchor, subset):
    subset = set(subset)
    return [
        (i, 1) for i, b in enumerate(BLOCKS) if set(b) & {1, 2, 3} == {anchor} and subset <= set(b)
    ]


def check_model_assumptions(model):
    require(len(model.variables) >= len(BLOCKS), "too few block variables")
    require(
        [(v.name, list(v.domain)) for v in model.variables[:4368]]
        == [(f"block_{i}", [0, 1]) for i in range(4368)],
        "block variables are not lexicographic",
    )
    rows = row_keys(model)
    names = {v.name: i for i, v in enumerate(model.variables)}

    def has(terms, lo, hi, enforced=()):
        require(
            rows[key(terms, lo, hi, enforced)] > 0, "required local-family assumption is absent"
        )

    for i, b in enumerate(BLOCKS):
        if b in COMMON:
            has([(i, 1)], 1, 1)
        elif len(set(b) & {1, 2, 3}) >= 2:
            has([(i, 1)], 0, 0)
    for anchor in (2, 3):
        for p in range(4, 17):
            target = 6 if p == 4 else 5
            has([(i, 1) for i, b in enumerate(BLOCKS) if anchor in b and p in b], target, target)
        for pair in PAIRS:
            if pair not in G:
                has(local_terms(anchor, pair), 1, MAXIMUM)
        spoke_flags = []
        for pair in ((4, 5), (4, 6)):
            name = f"local_hole_{anchor}_{pair}"
            require(name in names, "missing local spoke flag")
            variable = names[name]
            require(list(model.variables[variable].domain) == [0, 1], "spoke flag is not Boolean")
            has(local_terms(anchor, pair), 0, 0, (variable,))
            has(local_terms(anchor, pair), 1, MAXIMUM, (-variable - 1,))
            spoke_flags.append((variable, 1))
        has(spoke_flags, MINIMUM, 1)
    return {
        "scope": "Local families at anchors2 and3 in the normalized sevenfold-triple model",
        "local_degrees_derived": 4,
        "maximum_missing_pair_degree_derived": 1,
    }


def expected_cuts():
    cuts = []
    for anchor in (2, 3):
        cuts.extend((local_terms(anchor, pair), 2) for pair in PAIRS)
        cuts.extend((local_terms(anchor, triple), 1) for triple in TRIPLES)
    return cuts


def add_cuts(model):
    assumptions = check_model_assumptions(model)
    before = copy.deepcopy(model)
    rows = row_keys(model)
    added = []
    for terms, upper in expected_cuts():
        signature = key(terms, MINIMUM, upper)
        if rows[signature]:
            continue
        row = model.constraints.add()
        row.linear.vars.extend(i for i, _ in terms)
        row.linear.coeffs.extend(n for _, n in terms)
        row.linear.domain.extend((MINIMUM, upper))
        rows[signature] += 1
        added.append(signature)
    before_rows = row_keys(before)
    after_rows = row_keys(model)
    require(after_rows - before_rows == Counter(added), "unexpected added rows")
    before.ClearField("constraints")
    control = copy.deepcopy(model)
    control.ClearField("constraints")
    require(
        before.SerializeToString() == control.SerializeToString(), "nonconstraint model changed"
    )
    return {
        "assumptions": assumptions,
        "cuts_added": len(added),
        "pair_cut_count": 156,
        "triple_cut_count": 572,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument(
        "--classification",
        type=Path,
        default=Path("experiments/2026-10-03/local-family-root-audit/replay.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--seed", type=int, default=2026102400)
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to overwrite output")
    require(
        args.seconds is None or math.isfinite(args.seconds) and args.seconds > 0,
        "invalid time budget",
    )
    classification = audit_classification(args.classification)
    original = args.model.read_bytes()
    model = cp_model_pb2.CpModelProto()
    text_format.Parse(original.decode(), model)
    applied = add_cuts(model)
    args.output.mkdir(parents=True)
    output_model = args.output / "model.pbtxt"
    output_model.write_text(text_format.MessageToString(model))
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    metadata = {
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "input_model": str(args.model),
        "input_model_sha256": hashlib.sha256(original).hexdigest(),
        "model_sha256": hashlib.sha256(output_model.read_bytes()).hexdigest(),
        "classification_audit": classification,
        "cut_application": applied,
        "solver_version": ortools.__version__,
        "python_version": platform.python_version(),
        "seed": args.seed,
        "seconds_budget": args.seconds,
        "workers": 2,
        "command": sys.argv,
        "scope": "Only the supplied normalized fixed-family model; "
        "these cuts are redundant and no solver negative is an independent proof.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        json.dumps({"classification_families": classification["families"], **applied}), flush=True
    )
    if args.seconds is None:
        return
    cp = cp_model.CpModel()
    require(cp.proto.parse_text_format(output_model.read_text()), "failed to load cut model")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    with (args.output / "solver.log").open("w") as stream:
        solver.log_callback = lambda line: (stream.write(line + "\n"), stream.flush())
        status = solver.Solve(cp)
    result = {
        "status": solver.StatusName(status),
        "seconds": solver.WallTime(),
        "response_stats": solver.ResponseStats(),
        "cover_found": False,
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        candidate = [
            b for i, b in enumerate(BLOCKS) if solver.Value(cp.get_bool_var_from_proto_index(i))
        ]
        path = args.output / "candidate.txt"
        write_blocks(path, candidate)
        package = verify_cover(candidate)
        run = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
            capture_output=True,
            text=True,
        )
        standalone = json.loads(run.stdout)
        require(
            package["canonical_sha256"] == standalone["canonical_sha256"]
            and len(package["uncovered"]) == standalone["uncovered_count"],
            "candidate verifiers disagree",
        )
        result.update(
            package=package,
            standalone=standalone,
            cover_found=standalone["valid"],
            holes=standalone["uncovered_count"],
        )
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "seconds", "cover_found")}), flush=True)


if __name__ == "__main__":
    main()
