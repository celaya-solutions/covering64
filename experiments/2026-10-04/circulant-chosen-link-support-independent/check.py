# Document:    Independent Chosen Link Support Screen Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a9518a325d829f32406bbc14a3096229ee25ffa1be2ba2eeffe6f1829b1a5328
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay 1,000 saved cases using candidate sets and direct integer supports."""

import ast
import copy
import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FULL = HERE.parent / "circulant-chosen-link-support-full"
BENCHMARK = HERE.parent / "circulant-chosen-link-support-screen"
CATALOG = HERE.parent / "circulant-chosen-link-catalog"
FULL_SHA = "26ea6b120238721c832f28421dfc4df3964cb1e3f101a3a930db02a118753567"
MANIFEST_SHA = "2c12c4372ef388026d7a6238b7789f72ad8dcaf74ba471035cb2dcdf86dc4439"
BENCHMARK_SHA = "5007aa2b9b38d980ecb4283aeb23c0873d770ee1e9036d3af0bab1045887428d"
CATALOG_AUDIT = HERE.parent / "circulant-chosen-link-independent/catalog-audit.json"
CATALOG_AUDIT_SHA = "e832913ef7d0ead42fdcb9c75538654e6dedfdb81091dd44519fa900cfbfe158"
WRAPPER = HERE.parent / "circulant-chosen-link-independent/launch_full.py"
WRAPPER_SHA = "c780d84eaa535fe2fc6966ee175d5dee862cd858504b55710c667b71dc51747b"
WRAPPER_BODY_SHA = "8eaf457651264c50fe4b1a01cb2f4fa63475c9ac6e1ee3b5428e17f0c3db774e"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(2, 17), 3))
RANK = {triple: index for index, triple in enumerate(TRIPLES)}
OUTSIDE = [i for i, block in enumerate(BLOCKS) if 1 not in block]
CANDIDATE_ROWS = {
    i: frozenset(RANK[t] for t in itertools.combinations(BLOCKS[i], 3)) for i in OUTSIDE
}


def require(test, message):
    if not test:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_case(ordinal, pairs, partials, profiles):
    partial_id, profile_id = pairs[ordinal]
    partial = partials[partial_id]
    require(partial["partial_id"] == partial_id, "partial ID")
    ids = partial["global_block_ids"]
    require(ids == sorted(set(ids)) and len(ids) == 20, "twenty fixed blocks")
    require(all(0 <= i < 1365 and BLOCKS[i][0] == 1 for i in ids), "fixed point-one blocks")
    fixed_counts = Counter(
        t for i in ids for t in itertools.combinations(BLOCKS[i], 3) if 1 not in t
    )
    require(len(fixed_counts) == 80 and set(fixed_counts.values()) == {1}, "outside fixed triples")
    excess = {tuple(t) for t in profiles[profile_id]["excess_triples"]}
    residual = [1 + int(t in excess) - fixed_counts[t] for t in TRIPLES]
    require(min(residual) >= 0 and sum(residual) == 440, "residual triple arithmetic")
    zero = {i for i, demand in enumerate(residual) if demand == 0}
    eligible = [i for i in OUTSIDE if CANDIDATE_ROWS[i].isdisjoint(zero)]
    supports = [[] for _ in TRIPLES]
    for global_id in eligible:
        for row in CANDIDATE_ROWS[global_id]:
            supports[row].append(global_id)
    # Build the documented byte format directly rather than using producer bitmasks.
    buffer = bytearray(376)
    for global_id in eligible:
        local = global_id - 1365
        buffer[local // 8] |= 1 << (local % 8)
    counters = {
        "zero_row_unions": len(zero),
        "support_row_popcounts": 0,
        "conflict_row_popcounts": 0,
        "cardinality_support_checks": 1,
    }
    result = {
        "pair_ordinal": ordinal,
        "partial_id": partial_id,
        "profile_id": profile_id,
        "initial_domain_count": 3003,
        "eligible_candidates": len(eligible),
        "eligible_mask_sha256": hashlib.sha256(buffer).hexdigest(),
        "operation_counts": counters,
    }
    if len(eligible) < 44:
        result.update(
            {
                "outcome": "insufficient_support",
                "row": 455,
                "demand": 44,
                "support_global_ids": eligible,
            }
        )
        return result
    forced_causes = {i: 455 for i in eligible} if len(eligible) == 44 else {}
    for row, demand in enumerate(residual):
        if demand == 0:
            continue
        counters["support_row_popcounts"] += 1
        if len(supports[row]) < demand:
            result.update(
                {
                    "outcome": "insufficient_support",
                    "row": row,
                    "triple": list(TRIPLES[row]),
                    "demand": demand,
                    "support_global_ids": supports[row],
                }
            )
            return result
        if len(supports[row]) == demand:
            for global_id in supports[row]:
                forced_causes.setdefault(global_id, row)
    forced = set(forced_causes)
    conflict = None
    conflict_ids = []
    if forced:
        for row, demand in enumerate(residual):
            counters["conflict_row_popcounts"] += 1
            selected = [i for i in supports[row] if i in forced]
            if len(selected) > demand:
                conflict, conflict_ids = row, selected
                break
        if conflict is None and len(forced) > 44:
            conflict, conflict_ids = 455, sorted(forced)
    if conflict is not None:
        evidence = []
        for global_id in conflict_ids:
            cause = forced_causes[global_id]
            cause_support = eligible if cause == 455 else supports[cause]
            demand = 44 if cause == 455 else residual[cause]
            require(
                global_id in cause_support and len(cause_support) == demand, "forcing justification"
            )
            evidence.append(
                {
                    "global_block_id": global_id,
                    "row": cause,
                    "demand": demand,
                    "support_global_ids": cause_support,
                }
            )
        result.update(
            {
                "outcome": "forced_conflict",
                "row": conflict,
                "demand": 44 if conflict == 455 else residual[conflict],
                "forced_global_ids": conflict_ids,
                "forcing_rows": evidence,
            }
        )
        if conflict != 455:
            result["triple"] = list(TRIPLES[conflict])
    else:
        result.update({"outcome": "survives_single_pass", "immediately_forced_blocks": len(forced)})
    return result


def source_checks():
    source = (FULL / "run.py").read_text()
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    run = functions["run"]
    for_nodes = [node for node in ast.walk(run) if isinstance(node, ast.For)]
    ordinal_loops = [
        node
        for node in for_nodes
        if isinstance(node.target, ast.Name) and node.target.id == "ordinal"
    ]
    require(len(ordinal_loops) == 1, "one ordinal loop")
    loop = ordinal_loops[0]
    require(ast.unparse(loop.iter) == "range(TOTAL)", "complete ordinal range")
    require(isinstance(loop.body[0], ast.If), "deadline checked before each case")
    require(
        ast.unparse(loop.body[0].test) == "time.monotonic() - started >= SECONDS - 0.5",
        "stop-new-cases rule",
    )
    require(
        len(loop.body[0].body) == 1 and isinstance(loop.body[0].body[0], ast.Break),
        "cap exits loop",
    )
    screen_calls = [
        node
        for node in ast.walk(run)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "screen"
    ]
    require(
        len(screen_calls) == 1
        and ast.unparse(screen_calls[0]) == "arithmetic.screen(data, ordinal)",
        "exactly one unchanged screen per ordinal",
    )
    require(
        not any(isinstance(node, ast.While) for node in ast.walk(run)), "no iterative outer loop"
    )
    require(
        "completed += 1" in source and '"next_pair_ordinal": completed' in source,
        "completed prefix cursor",
    )
    require("os.O_EXCL" in source and '"launch.json"' in source, "exclusive launch marker")
    require(
        "solver" not in [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)],
        "no solver entry",
    )
    return {
        "single_full_ordinal_loop": True,
        "single_screen_call_per_ordinal": True,
        "cooperative_stop_seconds": 44.5,
        "recorded_processing_budget_seconds": 45,
        "hard_45_second_process_cap": False,
        "cursor_half_open_prefix": True,
        "requires_external_watchdog_seconds": 50,
        "requires_external_termination_grace_seconds": 5,
    }


def main():
    require(sha(WRAPPER) == WRAPPER_SHA, "external wrapper pin")
    wrapper_body = "\n".join(WRAPPER.read_text().split("\n")[10:])
    require(
        hashlib.sha256(wrapper_body.encode()).hexdigest() == WRAPPER_BODY_SHA,
        "wrapper body unchanged from reviewed normal/terminate/kill control flow",
    )
    require(sha(FULL / "run.py") == FULL_SHA, "full source pin")
    require(sha(FULL / "manifest.json") == MANIFEST_SHA, "full manifest pin")
    require(sha(BENCHMARK / "run.py") == BENCHMARK_SHA, "benchmark arithmetic pin")
    require(sha(CATALOG_AUDIT) == CATALOG_AUDIT_SHA, "independent catalog audit pin")
    require(json.loads(CATALOG_AUDIT.read_text())["passed"] is True, "catalog prerequisite")
    manifest = json.loads((FULL / "manifest.json").read_text())
    for path, digest in manifest["dependencies"].items():
        require(sha(ROOT / path) == digest, "dependency " + path)
    same(
        {
            k: manifest[k]
            for k in (
                "case_count",
                "max_passes",
                "iteration",
                "remaining_domain_per_case",
                "triple_rows_per_case",
                "cardinality_demand",
                "wall_budget_seconds",
                "stop_starting_new_cases_at_seconds",
            )
        },
        {
            "case_count": 195296,
            "max_passes": 1,
            "iteration": False,
            "remaining_domain_per_case": 3003,
            "triple_rows_per_case": 455,
            "cardinality_demand": 44,
            "wall_budget_seconds": 45.0,
            "stop_starting_new_cases_at_seconds": 44.5,
        },
        "frozen workload and budget",
    )
    require(OUTSIDE == list(range(1365, 4368)) and len(TRIPLES) == 455, "full residual domain")
    require(
        all(sum(row in ranks for ranks in CANDIDATE_ROWS.values()) == 66 for row in range(455)),
        "all sixty-six triple carriers retained initially",
    )
    partials = json.loads((CATALOG / "partial-catalog.json").read_text())
    profiles = json.loads((CATALOG / "profiles.json").read_text())
    fibers = json.loads((CATALOG / "link-fibers.json").read_text())
    pairs = []
    for index, fiber in enumerate(fibers):
        require(fiber["excess_link_id"] == index, "fiber order")
        start, stop = fiber["partial_id_range_half_open"]
        require(fiber["profile_ids"] == sorted(set(fiber["profile_ids"])), "profile order")
        pairs.extend(
            (partial, profile) for partial in range(start, stop) for profile in fiber["profile_ids"]
        )
    require(len(pairs) == len(set(pairs)) == 195296, "complete distinct ordered pair domain")
    receipt = json.loads((BENCHMARK / "benchmark.json").read_text())
    sample = [(index * len(pairs)) // 1000 for index in range(1000)]
    same(receipt["completed_pair_ordinals"], sample, "complete fixed benchmark sample")
    require(
        sha(ROOT / receipt["proof_records"]) == receipt["proof_records_sha256"],
        "benchmark records pin",
    )
    with gzip.open(ROOT / receipt["proof_records"], "rt") as handle:
        records = [json.loads(line) for line in handle]
    require(len(records) == 1000, "benchmark record count")
    outcomes, operations = Counter(), Counter()
    examples = {}
    for ordinal, actual in zip(sample, records, strict=True):
        expected = reference_case(ordinal, pairs, partials, profiles)
        same(actual, expected, "independent benchmark case " + str(ordinal))
        outcomes[expected["outcome"]] += 1
        operations.update(expected["operation_counts"])
        examples.setdefault(expected["outcome"], expected)
    same(dict(outcomes), receipt["outcomes"], "outcome totals")
    same(dict(operations), receipt["operation_counts"], "operation totals")
    controls = {}
    for name, category, change in (
        ("wrong_ordinal", "insufficient_support", lambda r: r.__setitem__("pair_ordinal", -1)),
        ("wrong_profile", "insufficient_support", lambda r: r.__setitem__("profile_id", -1)),
        (
            "wrong_domain",
            "insufficient_support",
            lambda r: r.__setitem__("eligible_candidates", 3003),
        ),
        (
            "wrong_mask_hash",
            "insufficient_support",
            lambda r: r.__setitem__("eligible_mask_sha256", "0" * 64),
        ),
        ("wrong_demand", "insufficient_support", lambda r: r.__setitem__("demand", 3)),
        ("missing_support", "insufficient_support", lambda r: r["support_global_ids"].clear()),
        (
            "wrong_force_row",
            "forced_conflict",
            lambda r: r["forcing_rows"][0].__setitem__("row", 455),
        ),
        (
            "wrong_force_demand",
            "forced_conflict",
            lambda r: r["forcing_rows"][0].__setitem__("demand", 44),
        ),
        (
            "missing_force_support",
            "forced_conflict",
            lambda r: r["forcing_rows"][0]["support_global_ids"].pop(),
        ),
        ("missing_forced_block", "forced_conflict", lambda r: r["forced_global_ids"].pop()),
        (
            "wrong_survivor_count",
            "survives_single_pass",
            lambda r: r.__setitem__("immediately_forced_blocks", -1),
        ),
        (
            "invented_survival",
            "insufficient_support",
            lambda r: r.__setitem__("outcome", "survives_single_pass"),
        ),
    ):
        expected = examples[category]
        damaged = copy.deepcopy(expected)
        change(damaged)
        try:
            same(damaged, expected, "damaged certificate")
        except ValueError:
            controls[name] = "rejected"
        else:
            raise ValueError("damage accepted: " + name)
    gate = {
        "passed": True,
        "launch_permitted": True,
        "manifest_sha256": MANIFEST_SHA,
        "full_source_sha256": FULL_SHA,
        "benchmark_source_sha256": BENCHMARK_SHA,
        "catalog_audit_sha256": CATALOG_AUDIT_SHA,
        "external_wrapper": str(WRAPPER.relative_to(ROOT)),
        "external_wrapper_sha256": WRAPPER_SHA,
        "checker_sha256": sha(Path(__file__)),
        "dependencies_checked": len(manifest["dependencies"]),
        "complete_pair_domain": len(pairs),
        "benchmark_cases_replayed": len(records),
        "outcomes": dict(outcomes),
        "operation_counts": dict(operations),
        "damage_controls": controls,
        "source_review": source_checks(),
        "optimizer_calls": 0,
        "full_screen_launched": False,
        "launch_condition": (
            "Root must use an external50-second watchdog plus5-second termination grace "
            "and save true process time."
        ),
        "scope": "Only the full supplied chosen-link catalog; passing support is not feasibility.",
    }
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "outcomes": dict(outcomes),
                "damage_controls": len(controls),
            }
        )
    )


if __name__ == "__main__":
    main()
