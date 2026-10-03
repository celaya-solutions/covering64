# Document:    Certified automorphism subgroup of the fixed 60-block core
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Find generators with graph isomorphism; verify every point permutation exactly."""

import argparse
import hashlib
import json
import signal
import time
from pathlib import Path

import networkx as nx
import sympy
from networkx.algorithms.isomorphism import GraphMatcher, categorical_node_match
from sympy.combinatorics import Permutation, PermutationGroup

HERE = Path(__file__).resolve().parent


def expired(_signum, _frame):
    raise TimeoutError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=45)
    parser.add_argument("--limit", type=int, default=200000)
    args = parser.parse_args()
    certificate = json.loads((HERE / "fixed-core-certificate.json").read_text())
    core = {tuple(b) for b in certificate["core_blocks"]}
    graph = nx.Graph()
    for point in range(1, 17):
        graph.add_node(("p", point), kind="point")
    for i, block in enumerate(sorted(core)):
        graph.add_node(("b", i), kind="block")
        graph.add_edges_from((("b", i), ("p", point)) for point in block)
    matcher = GraphMatcher(graph, graph, node_match=categorical_node_match("kind", None))
    generators = []
    group = PermutationGroup(Permutation(list(range(16))))
    count = 0
    complete = False
    started = time.monotonic()
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(args.seconds)
    try:
        for mapping in matcher.isomorphisms_iter():
            values = [mapping[("p", point)][1] for point in range(1, 17)]
            if sorted(values) != list(range(1, 17)):
                raise ValueError("Not a point permutation")
            if {tuple(sorted(values[p - 1] for p in b)) for b in core} != core:
                raise ValueError("Permutation does not preserve core")
            count += 1
            perm = Permutation([v - 1 for v in values])
            if not group.contains(perm):
                generators.append(values)
                group = PermutationGroup(*(Permutation([v - 1 for v in g])
                                            for g in generators))
                print(json.dumps({"generators": len(generators), "subgroup_order": group.order(),
                                  "automorphisms_seen": count}), flush=True)
            if count >= args.limit:
                break
        else:
            complete = True
    except TimeoutError:
        pass
    finally:
        signal.alarm(0)
    # Verify only saved generators again; this assertion does not depend on a graph library.
    for values in generators:
        if {tuple(sorted(values[p - 1] for p in b)) for b in core} != core:
            raise ValueError("Saved generator failed independent set check")
    result = {
        "scope": "Certified subgroup preserving this fixed core; no global covering claim",
        "core_sha256": certificate["core_sha256"], "point_labels": "1-based",
        "generators_images_of_1_to_16": generators, "subgroup_order": int(group.order()),
        "automorphisms_seen": count, "graph_enumeration_exhausted": complete,
        "seconds_budget": args.seconds, "enumeration_limit": args.limit,
        "elapsed_seconds": time.monotonic() - started,
        "networkx_version": nx.__version__, "sympy_version": sympy.__version__,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (HERE / "core-automorphisms.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
