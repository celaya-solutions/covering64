#!/usr/bin/env python3
# Document:    Complete Degree Split Cover Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Two complete branches for covers with at most64 blocks; timeout is inconclusive.

Every pair lies in at least ceil(14/3)=5 blocks. Summing over pairs incident
with a point gives4*r >=15*5, hence point degree r>=19. At most64 blocks give
total point degree<=320. Thus either all degrees are20 (and there are64 blocks)
or some point has degree19. Relabel that point1. Its19 four-block link has
15 vertex degrees at least5 summing76: one degree6, fourteen degree5. The
excess multigraph of pair coverage over one has degrees4 and fourteen1, hence
is exactly K1,4 plus five disjoint edges, with no parallel edges. Relabel its
center2, leaves3..6, and matching (7,8),(9,10),(11,12),(13,14),(15,16).
These are the only normalizations imposed; no particular link is fixed.

Optional further normalization fixes one block in the regular branch. In the
degree19 branch, the six center-link blocks have eight star-leaf incidences,
so one has at most one star leaf. Under permutations preserving the canonical
excess graph, its matching vertices have four orbit types. Require one of the
four representative blocks; this preserves existence within the branch.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, normalize_blocks, read_blocks, verify_cover, write_blocks


def excess_pairs():
    return {(2, x) for x in range(3, 7)} | {(x, x + 1) for x in range(7, 17, 2)}


def representative_blocks():
    return [(1, 2, 7, 8, 9), (1, 2, 7, 9, 11), (1, 2, 3, 7, 8), (1, 2, 3, 7, 9)]


def canonicalize_degree19_hint(blocks):
    """Relabel a complete degree19 point link, allowing holes away from that point."""
    blocks = normalize_blocks(blocks, 16, 5)
    replication = Counter(x for block in blocks for x in block)
    for point in range(1, 17):
        if replication[point] != 19:
            continue
        link = [tuple(x for x in block if x != point) for block in blocks if point in block]
        counts = Counter(pair for block in link for pair in combinations(block, 2))
        others = [x for x in range(1, 17) if x != point]
        if any(counts[pair] < 1 for pair in combinations(others, 2)):
            continue
        degrees = Counter(x for block in link for x in block)
        if sorted(degrees.values()) != [5] * 14 + [6]:
            raise RuntimeError("degree19 link violated the counting derivation")
        center = next(x for x in others if degrees[x] == 6)
        edges = [pair for pair, count in counts.items() if count == 2]
        if any(count not in (1, 2) for count in counts.values()):
            raise RuntimeError("degree19 link has an impossible parallel excess edge")
        leaves = sorted({x for pair in edges if center in pair for x in pair} - {center})
        matching = sorted(pair for pair in edges if center not in pair)
        if len(leaves) != 4 or len(matching) != 5:
            raise RuntimeError("degree19 link has an invalid excess graph")
        mapping = {point: 1, center: 2}
        mapping.update(zip(leaves, range(3, 7)))
        for pair, first in zip(matching, range(7, 17, 2)):
            mapping.update(zip(pair, (first, first + 1)))
        if set(mapping) != set(range(1, 17)) or set(mapping.values()) != set(range(1, 17)):
            raise RuntimeError("canonicalization did not produce a label permutation")
        transformed = sorted(tuple(sorted(mapping[x] for x in block)) for block in blocks)
        return transformed, mapping
    raise ValueError("hint has no complete degree19 point link")


def normalize_split_hint(blocks, branch):
    """Apply the optional, existence-preserving normalization to a soft hint."""
    if branch == "regular20":
        blocks = normalize_blocks(blocks, 16, 5)
        if not blocks:
            raise ValueError("cannot normalize an empty hint")
        first = min(blocks)
        order = list(first) + [x for x in range(1, 17) if x not in first]
        mapping = dict(zip(order, range(1, 17)))
    elif branch == "degree19":
        blocks, original = canonicalize_degree19_hint(blocks)
        chosen = next(block for block in blocks if 1 in block and 2 in block
                      and len(set(block).intersection(range(3, 7))) <= 1)
        stars = sorted(set(chosen).intersection(range(3, 7)))
        star_order = stars + [x for x in range(3, 7) if x not in stars]
        mapping = {1: 1, 2: 2, **dict(zip(star_order, range(3, 7)))}
        pairs = [(x, x + 1) for x in range(7, 17, 2)]
        selected = set(chosen).intersection(range(7, 17))
        pair_order = sorted(pairs, key=lambda pair: (-len(selected.intersection(pair)), pair))
        for old, first in zip(pair_order, range(7, 17, 2)):
            ordered = sorted(old, key=lambda x: (x not in selected, x))
            mapping.update(zip(ordered, (first, first + 1)))
        if {tuple(sorted((mapping[a], mapping[b]))) for a, b in excess_pairs()} != excess_pairs():
            raise RuntimeError("hint normalization changed the canonical excess pattern")
        if tuple(sorted(mapping[x] for x in chosen)) not in representative_blocks():
            raise RuntimeError("hint normalization missed its representative block")
        transformed = sorted(tuple(sorted(mapping[x] for x in block)) for block in blocks)
        return transformed, {old: mapping[mid] for old, mid in original.items()}
    else:
        raise ValueError("invalid degree branch")
    return sorted(tuple(sorted(mapping[x] for x in block)) for block in blocks), mapping


def build_split_model(branch, target=64, normalize=False):
    """All4368 variables remain lexicographic; target>64 is useful only for controls."""
    if branch not in ("regular20", "degree19"):
        raise ValueError("branch must be regular20 or degree19")
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    universe = Universe.build()
    model = cp_model.CpModel()
    variables = [model.NewBoolVar(f"block_{i}") for i in range(len(universe.blocks))]
    excess = excess_pairs()
    for triple, containing in zip(universe.triples, universe.containing):
        terms = [variables[i] for i in containing]
        if branch == "degree19" and triple[0] == 1:
            model.Add(sum(terms) == (2 if triple[1:] in excess else 1))
        else:
            model.AddBoolOr(terms)
    model.Add(sum(variables) <= target)
    if branch == "regular20":
        model.Add(sum(variables) == 64)
    if normalize:
        if branch == "regular20":
            model.Add(variables[0] == 1)
        else:
            model.AddBoolOr([variables[universe.blocks.index(block)]
                             for block in representative_blocks()])
    for point in range(1, 17):
        terms = [variables[i] for i, block in enumerate(universe.blocks) if point in block]
        if branch == "regular20":
            model.Add(sum(terms) == 20)
        elif point == 1:
            model.Add(sum(terms) == 19)
        else:
            model.Add(sum(terms) >= 19)
    for a, b in combinations(range(1, 17), 2):
        model.Add(sum(variables[i] for i, block in enumerate(universe.blocks)
                      if a in block and b in block) >= 5)
    return universe, model, variables


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("branch", choices=["regular20", "degree19"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=900)
    parser.add_argument("--seed", type=int, default=2026100719)
    parser.add_argument("--hint", type=Path)
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--core-proof", type=Path)
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    universe, model, variables = build_split_model(args.branch, normalize=args.normalize)
    mapping = None
    if args.hint:
        hint = read_blocks(args.hint)
        if args.normalize:
            hint, mapping = normalize_split_hint(hint, args.branch)
        elif args.branch == "degree19":
            hint, mapping = canonicalize_degree19_hint(hint)
        selected = set(hint)
        for block, variable in zip(universe.blocks, variables):
            model.AddHint(variable, int(block in selected))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    core_cut = None
    if args.core_proof:
        helper = Path(__file__).with_name("checked_core_cut.py")
        spec = importlib.util.spec_from_file_location("split_checked_core", helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        core_cut = module.checked_core_cuts(universe, args.core_proof, mapping)
        for cut in core_cut["cuts"]:
            model.Add(sum(variables[i] for i in cut["block_ids"]) <= cut["limit"])
        (args.output / "core_cut_source_snapshot.py").write_bytes(helper.read_bytes())
        (args.output / "core_checker_snapshot.py").write_bytes(
            Path(core_cut["checker_path"]).read_bytes())
        (args.output / "core_proof_check.json").write_text(json.dumps(core_cut, indent=2) + "\n")
    model_path = args.output / "model.pbtxt"
    model.ExportToFile(str(model_path))
    metadata = {
        "branch": args.branch, "seconds": args.seconds, "seed": args.seed, "workers": 2,
        "normalize": args.normalize,
        "core_cut": core_cut,
        "solver": "OR-Tools CP-SAT", "version": ortools.__version__,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "hint_sha256": hashlib.sha256(args.hint.read_bytes()).hexdigest() if args.hint else None,
        "hint_permutation": mapping,
        "repair_hint": bool(args.hint), "hint_conflict_limit": 10000 if args.hint else None,
        "scope": "one of two complete <=64 degree branches; no independently checked UNSAT proof",
        "completeness_derivation": __doc__,
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = args.seed
    if args.hint:
        solver.parameters.repair_hint = True
        solver.parameters.hint_conflict_limit = 10000
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda text: (log.write(text + "\n"), log.flush())
        status = solver.Solve(model)
    result = {"status": solver.StatusName(status), "solver_seconds": solver.WallTime(),
              "scope": metadata["scope"], "witness": None, "response_stats": solver.ResponseStats()}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        witness = [block for block, variable in zip(universe.blocks, variables)
                   if solver.Value(variable)]
        checked = verify_cover(witness)
        if not checked["valid"] or len(witness) > 64:
            raise RuntimeError("degree-split witness failed package verification")
        path = args.output / "cover.txt"
        write_blocks(path, witness)
        independent = subprocess.run([sys.executable, "scripts/check_cover.py", str(path)],
                                     capture_output=True, text=True, check=True)
        result.update(witness=witness, verification=checked,
                      standalone_verification=json.loads(independent.stdout))
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
