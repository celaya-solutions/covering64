#!/usr/bin/env python3
# Document:    Pooled Regular Link Construction Search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Choose three regular13-quad families and18 outside5-blocks together.

Integer family multiplicity permits the same family on different anchors.
All families cover the pairs outside G=P3+5K2; fixed123+G closes anchor triples.
This is only a finite template pool, never an unrestricted negative theorem.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
from itertools import combinations, permutations, product
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks

spec = importlib.util.spec_from_file_location(
    "three_links", Path(__file__).with_name("three_link_search.py"))
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


def spoke_pool(template):
    """Use source holes01 and34, representatives of the two audited edge orbits."""
    if links.check_template(template) != {(0, 1), *links.EDGES[2:]}:
        raise ValueError("unsupported missing-pair graph")
    families = set()
    missing_edges = ((0, 1), *links.EDGES[2:])
    for central, leaf, orientation, pairs, flips in product(
            (0, 1), (1, 2), (0, 1), permutations(range(5)), product((0, 1), repeat=5)):
        mapping = [None] * 13
        source_a, source_b = missing_edges[central]
        mapping[source_a], mapping[source_b], mapping[2] = 0, leaf, 3 - leaf
        if orientation:
            mapping[source_a], mapping[source_b] = mapping[source_b], mapping[source_a]
        remaining_edges = [pair for i, pair in enumerate(missing_edges) if i != central]
        for (source_a, source_b), target, flip in zip(remaining_edges, pairs, flips):
            values = [3 + 2 * target, 4 + 2 * target]
            if flip:
                values.reverse()
            mapping[source_a], mapping[source_b] = values
        family = links.mapped(template, mapping)
        links.check_template(family)
        families.add(family)
    return sorted(families)


def assemble(families, counts, outside_blocks):
    chosen = [family for family, count in zip(families, counts) for _ in range(count)]
    if len(chosen) != 3:
        raise ValueError("exactly three families required")
    fixed = links.fixed_blocks(chosen, [list(range(13))] * 3)
    return sorted(list(fixed) + list(outside_blocks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spoke-template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", default=2026101600, type=int)
    parser.add_argument("--seconds", default=240, type=float)
    parser.add_argument("--pg-samples", default=256, type=int)
    parser.add_argument("--fix-source", action="store_true")
    parser.add_argument("--spoke-omissions", action="store_true")
    parser.add_argument("--minimize-uncovered", action="store_true")
    args = parser.parse_args()
    if args.output.exists() or args.seconds <= 0 or args.pg_samples < 0:
        parser.error("fresh output, positive time and nonnegative PG count required")
    source_template = tuple(sorted(tuple(x - 1 for x in b)
                                   for b in read_blocks(args.spoke_template, v=13, k=4)))
    families = spoke_pool(source_template)
    spoke_count = len(families)
    rng = random.Random(args.seed)
    plane = links.projective_plane()
    families.extend(links.mapped(plane, links.random_map("pg", 1, rng))
                    for _ in range(args.pg_samples))
    families = sorted(set(families))
    holes = [links.check_template(family) for family in families]
    triples = list(combinations(range(13), 3))
    pair_universe = list(combinations(range(13), 2))
    triple_rank = {t: i for i, t in enumerate(triples)}
    family_triples = [{triple_rank[t] for b in family for t in combinations(b, 3)}
                      for family in families]
    family_pairs = [{p: sum(set(p) <= set(b) for b in family) for p in pair_universe}
                    for family in families]
    universe = Universe.build()
    candidates = [i for i, b in enumerate(universe.blocks) if min(b) >= 4]
    outside = [tuple(x - 4 for x in universe.blocks[i]) for i in candidates]
    outside_triples = [{triple_rank[t] for t in combinations(b, 3)} for b in outside]
    model = cp_model.CpModel()
    fixed_family = families.index(source_template) if args.fix_source else None
    remaining_count = 2 if args.fix_source else 3
    choices = [model.NewIntVar(0, remaining_count, f"family_{i}")
               for i in range(len(families))]
    variables = [model.NewBoolVar(f"block_{i}") for i in candidates]
    model.Add(sum(choices) == remaining_count)
    model.Add(sum(variables) == 18)
    uncovered = []
    for tid in range(len(triples)):
        coverage = (sum(choices[i] for i, ts in enumerate(family_triples) if tid in ts)
                    + sum(variables[i] for i, ts in enumerate(outside_triples) if tid in ts)
                    + int(fixed_family is not None and tid in family_triples[fixed_family]))
        if args.minimize_uncovered:
            hole = model.NewBoolVar(f"uncovered_{tid}")
            model.Add(coverage == 0).OnlyEnforceIf(hole)
            model.Add(coverage >= 1).OnlyEnforceIf(hole.Not())
            uncovered.append(hole)
        else:
            model.Add(coverage >= 1)
    if uncovered:
        model.Minimize(sum(uncovered))
    for point in range(13):
        model.Add(sum(variables[i] for i, b in enumerate(outside) if point in b)
                  == (6 if point == 0 else 7))
    for pair in pair_universe:
        model.Add(sum(choices[i] * counts[pair] for i, counts in enumerate(family_pairs)
                      if counts[pair])
                  + sum(variables[i] for i, b in enumerate(outside) if set(pair) <= set(b))
                  + int(pair in links.EDGES)
                  + (family_pairs[fixed_family][pair] if fixed_family is not None else 0) >= 5)
    if args.spoke_omissions:
        for pair in links.EDGES[:2]:
            model.Add(sum(choices[i] for i, missing in enumerate(holes) if pair in missing)
                      + int(fixed_family is not None and pair in holes[fixed_family]) >= 1)
    args.output.mkdir(parents=True)
    source = Path(__file__).read_bytes()
    helper = Path(links.__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    (args.output / "helper.py").write_bytes(helper)
    pool = {"families": families, "source_template": source_template,
            "spoke_family_count": spoke_count, "total_family_count": len(families)}
    pool_raw = gzip.compress((json.dumps(pool, separators=(",", ":")) + "\n").encode(), mtime=0)
    (args.output / "pool.json.gz").write_bytes(pool_raw)
    model.ExportToFile(str(args.output / "model.pbtxt"))
    metadata = {"source_sha256": hashlib.sha256(source).hexdigest(),
                "helper_sha256": hashlib.sha256(helper).hexdigest(),
                "pool_sha256": hashlib.sha256(pool_raw).hexdigest(),
                "model_sha256": hashlib.sha256(
                    (args.output / "model.pbtxt").read_bytes()).hexdigest(),
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                          text=True).strip(),
                "ortools_version": ortools.__version__, "seed": args.seed,
                "seconds_budget": args.seconds, "workers": 2, "pg_samples": args.pg_samples,
                "spoke_family_count": spoke_count, "total_family_count": len(families),
                "outside_variable_count": len(candidates), "fix_source": args.fix_source,
                "fixed_family_index": fixed_family, "remaining_family_count": remaining_count,
                "spoke_omissions": args.spoke_omissions,
                "spoke_omissions_meaning": "Each spoke omitted by at least one chosen family",
                "minimize_uncovered": args.minimize_uncovered,
                "scope": "Only this finite three-link family pool and18 outside blocks"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata), flush=True)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = args.seed % 2_147_483_647
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    with (args.output / "solver.log").open("w") as stream:
        solver.log_callback = lambda line: (stream.write(line + "\n"), stream.flush())
        status = solver.Solve(model)
    result = {"status": solver.StatusName(status), "solver_seconds": solver.WallTime(),
              "response_stats": solver.ResponseStats(), "witness": None}
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        counts = [solver.Value(variable) for variable in choices]
        if fixed_family is not None:
            counts[fixed_family] += 1
        witness = assemble(families, counts, [universe.blocks[bid]
                                             for bid, variable in zip(candidates, variables)
                                             if solver.Value(variable)])
        package = verify_cover(witness)
        holes = len(package["uncovered"])
        if len(witness) != 64 or (not args.minimize_uncovered and holes):
            raise RuntimeError("package verifier rejected pooled candidate")
        if uncovered and holes != sum(solver.Value(variable) for variable in uncovered):
            raise RuntimeError("objective and independently counted holes disagree")
        write_blocks(args.output / "candidate.txt", witness)
        run = subprocess.run([sys.executable, "scripts/check_cover.py",
                              str(args.output / "candidate.txt"), "--expected-blocks", "64"],
                             check=False, capture_output=True, text=True)
        standalone = json.loads(run.stdout)
        if (standalone["uncovered_count"] != holes
                or standalone["valid"] != package["valid"]
                or standalone["canonical_sha256"] != package["canonical_sha256"]):
            raise RuntimeError("standalone verifier rejected pooled candidate")
        result.update(witness=witness if not holes else None, candidate=witness,
                      holes=holes, package=package, standalone=standalone,
                      selected_family_multiplicities=[[i, n] for i, n in enumerate(counts) if n])
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "solver_seconds")}), flush=True)


if __name__ == "__main__":
    main()
