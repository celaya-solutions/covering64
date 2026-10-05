# Document:    Independent Check of Circulant LP-Certified Trees
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1cfeff26570dd6adec774662c1f2f56301d06ea0ea92c96a39a0bd95029dfa6f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay saved exhaustion trees with plain integers; no producer or solver import.

For one excess profile, every triple t needs exactly mu_t blocks and the cover
has 64 blocks. A node fixes some blocks to one and others to zero. Its open
blocks are the unfixed blocks meeting no row whose demand is already met.

* Root: nothing fixed.
* Branch node: its row still needs blocks, and its listed candidates are
  exactly the open blocks through that row, in increasing block order. Child i
  fixes candidate i to one and all earlier candidates to zero. Any solution of
  the node selects a first candidate, so the children cover every solution.
* Support leaf: the named row needs more blocks than it has open blocks, or
  more blocks remain than there are open blocks.
* Farkas leaf: with residual demands b over the open rows and remaining count
  r, the integer vector Y satisfies
      sum_t b_t Y_t + r Y_sum - sum_open max(0, Y_sum + sum_{t in B} Y_t) > 0,
  which is impossible for any 0/1 completion.

Every saved node must be reached exactly once from the root.
"""

import gzip
import json
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CATALOG = HERE.parent / "circulant-chosen-link-catalog/profiles.json"
CATALOG_SHA = "24ccef8eb95cd04e683a575d60fcba854728615ee2ca6495f2bc6028fc56cf0f"
TRIPLE_LIST = list(combinations(range(1, 17), 3))
INDEX = {t: i for i, t in enumerate(TRIPLE_LIST)}
SUM = len(TRIPLE_LIST)
BLOCK_ROWS = [[INDEX[t] for t in combinations(b, 3)] for b in combinations(range(1, 17), 5)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def demands(profile_id):
    require(sha256(CATALOG.read_bytes()).hexdigest() == CATALOG_SHA, "profile catalog pin")
    profile = json.loads(CATALOG.read_text())[profile_id]
    require(profile["profile_id"] == profile_id, "profile identity")
    doubled = {tuple(t) for t in profile["excess_triples"]}
    require(len(doubled) == 80, "eighty doubled triples")
    return [2 if t in doubled else 1 for t in TRIPLE_LIST]


def state(mu, ones, zeros):
    require(len(set(ones)) == len(ones) and not set(ones) & set(zeros), "distinct fixings")
    need = list(mu)
    for j in ones:
        for t in BLOCK_ROWS[j]:
            need[t] -= 1
    require(min(need) >= 0, "no row is overfilled")
    fixed = set(ones) | set(zeros)
    open_blocks = [
        j
        for j in range(len(BLOCK_ROWS))
        if j not in fixed and all(need[t] > 0 for t in BLOCK_ROWS[j])
    ]
    return need, 64 - len(ones), open_blocks


def check_tree(mu, records, start=((), ())):
    nodes = {}
    for record in records:
        key = (tuple(record["ones"]), tuple(record["zeros"]))
        require(key not in nodes, "each node saved once")
        nodes[key] = record
    pending, seen, tally = [start], set(), Counter()
    while pending:
        key = pending.pop()
        require(key in nodes and key not in seen, "every required node is saved once")
        seen.add(key)
        record = nodes[key]
        need, remaining, open_blocks = state(mu, *key)
        require(remaining >= 0, "at most 64 blocks")
        if record.get("leaf") == "support":
            row = record["row"]
            if row == SUM:
                require(remaining > len(open_blocks), "too few open blocks for the count")
            else:
                through = sum(1 for j in open_blocks if row in BLOCK_ROWS[j])
                require(need[row] > through, "row support deficit")
            tally["support"] += 1
        elif record.get("leaf") == "farkas":
            y = {}
            for row, value in record["y"]:
                require(type(row) is int and type(value) is int and 0 <= row <= SUM, "entry")
                y[row] = value
            value = remaining * y.get(SUM, 0)
            value += sum(need[t] * v for t, v in y.items() if t < SUM)
            for j in open_blocks:
                s = y.get(SUM, 0) + sum(y.get(t, 0) for t in BLOCK_ROWS[j])
                if s > 0:
                    value -= s
            require(value > 0 and value == record["margin"], "positive exact Farkas margin")
            tally["farkas"] += 1
        elif "branch_row" in record:
            row = record["branch_row"]
            require(type(row) is int and 0 <= row < SUM and need[row] > 0, "open branch row")
            through = [j for j in open_blocks if row in BLOCK_ROWS[j]]
            require(record["candidates"] == through, "complete ordered candidate list")
            for i, j in enumerate(through):
                pending.append((key[0] + (j,), key[1] + tuple(through[:i])))
            tally["branch"] += 1
        else:
            raise ValueError("unexpected node kind; a cover candidate needs separate checks")
    if start == ((), ()):
        require(seen == set(nodes), "no unreachable saved node")
    return tally


def pilot(directory, children):
    """Check the first root subtrees of an incomplete depth-first run."""
    result = json.loads((directory / "result.json").read_text())
    tree = directory / "tree.jsonl.gz"
    require(sha256(tree.read_bytes()).hexdigest() == result["tree_sha256"], "tree pin")
    with gzip.open(tree, "rt") as handle:
        records = [json.loads(line) for line in handle]
    mu = demands(result["profile_id"])
    root = records[0]
    require(root["ones"] == [] and root["zeros"] == [] and "branch_row" in root, "root first")
    need, _, open_blocks = state(mu, (), ())
    row = root["branch_row"]
    require(need[row] > 0, "open root row")
    through = [j for j in open_blocks if row in BLOCK_ROWS[j]]
    require(root["candidates"] == through, "complete root candidates")
    tallies = []
    for i in range(children):
        start = ((through[i],), tuple(through[:i]))
        tallies.append(dict(check_tree(mu, records, start)))
    first = ((through[0],), ())
    inside = [i for i, r in enumerate(records) if r["ones"][:1] == [through[0]]]
    leaf = next(i for i in inside if records[i].get("leaf") == "farkas")
    branch = next(i for i in inside if "branch_row" in records[i])
    controls = []
    for label, index, mutate in (
        ("farkas multiplier changed", leaf, lambda r: r["y"][0].__setitem__(1, r["y"][0][1] + 1)),
        ("candidate dropped", branch, lambda r: r["candidates"].pop()),
        ("child record removed", leaf, None),
    ):
        damaged = [
            dict(r) if i != index else json.loads(json.dumps(r)) for i, r in enumerate(records)
        ]
        if mutate is None:
            damaged.pop(index)
        else:
            mutate(damaged[index])
        try:
            check_tree(mu, damaged, first)
        except ValueError:
            controls.append(label)
            continue
        raise AssertionError(f"damaged control accepted: {label}")
    return result, through, tallies, controls


def main():
    if sys.argv[1] == "pilot":
        directory, children = Path(sys.argv[2]), int(sys.argv[3])
        result, through, tallies, controls = pilot(directory, children)
        review = {
            "checker_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "checked_root_children": children,
            "damaged_controls_rejected": controls,
            "profile_id": result["profile_id"],
            "root_candidates": len(through),
            "scope": "Only the listed root subtrees of one profile; the run is incomplete.",
            "subtree_tallies": tallies,
            "tree_sha256": result["tree_sha256"],
        }
        (HERE / "review.json").write_text(json.dumps(review, indent=1, sort_keys=True) + "\n")
        print(json.dumps(review))
        return review
    reports = {}
    for result_path in sorted(Path(sys.argv[1]).glob("profile-*/result.json")):
        result = json.loads(result_path.read_text())
        require(result["status"] == "exhausted", f"{result_path.parent.name} complete")
        tree = result_path.parent / "tree.jsonl.gz"
        require(sha256(tree.read_bytes()).hexdigest() == result["tree_sha256"], "tree pin")
        with gzip.open(tree, "rt") as handle:
            records = [json.loads(line) for line in handle]
        tally = check_tree(demands(result["profile_id"]), records)
        require(sum(tally.values()) == result["census"]["nodes"], "node census")
        reports[result["profile_id"]] = dict(tally)
        print(result["profile_id"], dict(tally), flush=True)
    return reports


if __name__ == "__main__":
    main()
