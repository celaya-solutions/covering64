# Document:    Independent Replay of Seven Affine Completion Contradictions
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      dcf1fb4411c56228fba8138a14446875d96a2ae42aba57e4e4d1bed9bf72ccbe
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check supplied deductions with independently rebuilt integer bitset rows."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "clebsch-affine-completion-finite-certificate"
CERTIFICATE = PRODUCER / "certificate.json"
CERTIFICATE_SHA = "935783a788c93d79046bf9599af2d95735e5ce087a43c876a6516acfbcfc7841"
PRODUCER_SHA = "df9d8f4abcf98da5ee14ba376bfbbd377bdbc987535d43fc210a60dceccb8f12"
MANIFEST = HERE.parent / "clebsch-affine-link-completion-pilot/manifest.json"
MANIFEST_SHA = "ea45a44104652ef27307c253849ce89e6d3937ff6e0683ac00167c24677b3d9c"
PRIOR_REVIEW = HERE.parent / "clebsch-affine-link-support-screen-independent/review.json"
PRIOR_REVIEW_SHA = "8c7fd636138ee781dc308ce04c1eee47da63345b0eb3805a611ae794a43ab6a3"
PROFILE = ROOT / (
    "experiments/2026-10-03/independent-geometry/independent-audit-seed-profiles.json"
)
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
PAIRS = [(0, 10), (40, 13), (4, 7), (18, 3), (16, 3), (16, 8), (60, 3)]
EXPECTED_PROBES = [5, 8, 4, 6, 7, 4, 10]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def canonical(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode("ascii")


def integer(value):
    return type(value) is int


def bits(ids):
    need(isinstance(ids, list), "ID list required")
    need(all(integer(index) and 0 <= index < 4368 for index in ids), "strict global variable IDs")
    need(ids == sorted(set(ids)), "sorted distinct IDs required")
    return sum(1 << index for index in ids)


def ids(mask):
    result = []
    while mask:
        low = mask & -mask
        result.append(low.bit_length() - 1)
        mask -= low
    return result


def validate_family(rows, size, cardinality):
    need(isinstance(rows, list) and len(rows) == cardinality, "family cardinality")
    need(all(isinstance(row, (list, tuple)) and len(row) == size for row in rows), "row size")
    need(all(integer(x) and 1 <= x <= 16 for row in rows for x in row), "strict labels")
    normalized = [tuple(sorted(row)) for row in rows]
    need(all(len(set(row)) == size for row in normalized), "distinct labels")
    need(len(set(normalized)) == cardinality, "distinct rows")
    return sorted(normalized)


def rebuild(case, pinned, audited_profiles):
    need(
        all(integer(case[key]) for key in ("case", "point", "profile_seed", "probes")),
        "strict case integers",
    )
    partial_path = ROOT / pinned["partial"]
    profile_path = ROOT / pinned["profile"]
    for key in ("case", "point", "profile_seed", "partial", "profile"):
        need(case[key] == pinned[key], f"case field {key}")
    need(
        digest(partial_path) == case["partial_sha256"] == pinned["partial_sha256"],
        "partial file pin",
    )
    need(digest(profile_path) == case["profile_sha256"], "profile file pin")
    raw = [list(map(int, line.split())) for line in partial_path.read_text().splitlines()]
    partial = validate_family(raw, 5, 20)
    need(partial_path.read_bytes() == canonical(partial), "canonical partial bytes")
    point = case["point"]
    need(all(point in block for block in partial), "every partial block contains fixed point")
    profile = validate_family(json.loads(profile_path.read_text()), 3, 80)
    need(
        profile == sorted(tuple(row) for row in audited_profiles[str(case["profile_seed"])]),
        "audited profile reconstruction",
    )
    demand = {triple: 1 + (triple in set(profile)) for triple in TRIPLES}
    used = Counter(triple for block in partial for triple in combinations(block, 3))
    residual = [demand[triple] - used[triple] for triple in TRIPLES]
    need(min(residual) >= 0 and sum(residual) == 440, "nonnegative exact residual demands")
    need(
        all(residual[index] == 0 for index, triple in enumerate(TRIPLES) if point in triple),
        "point rows satisfied",
    )
    domain = [index for index, block in enumerate(BLOCKS) if point not in block]
    need(len(domain) == 3003, "complete point-avoiding domain")
    masks = [0] * 560
    triple_rank = {triple: index for index, triple in enumerate(TRIPLES)}
    for index in domain:
        for triple in combinations(BLOCKS[index], 3):
            masks[triple_rank[triple]] |= 1 << index
    domain_mask = bits(domain)
    masks.append(domain_mask)
    residual.append(44)
    need(len(masks) == len(residual) == 561, "all residual rows plus exact44")
    return {
        "domain": domain_mask,
        "masks": masks,
        "demands": residual,
        "partial": partial,
        "profile": profile,
    }


def row_state(system, row, selected, removed):
    need(integer(row) and 0 <= row < 561, "row ID")
    mask = system["masks"][row]
    chosen = (mask & selected).bit_count()
    free = mask & ~(selected | removed)
    return chosen, free, system["demands"][row]


def contradiction(system, row, selected, removed):
    chosen, free, demand = row_state(system, row, selected, removed)
    need(chosen > demand or chosen + free.bit_count() < demand, "row is not contradictory")
    return {
        "row": row,
        "triple": list(TRIPLES[row]) if row < 560 else None,
        "selected_count": chosen,
        "free_count": free.bit_count(),
        "demand": demand,
    }


def trace(system, steps, selected, removed):
    need(isinstance(steps, list), "trace list")
    for step in steps:
        need(set(step) == {"row", "value", "variables"}, "trace schema")
        value = step["value"]
        need(integer(value) and value in (0, 1), "strict force value")
        chosen, free, demand = row_state(system, step["row"], selected, removed)
        force = bits(step["variables"])
        need(force != 0 and force == free, "trace must list every currently free row variable")
        need(
            not force & (selected | removed) and not force & ~system["domain"],
            "fresh domain variables",
        )
        if value == 0:
            need(chosen == demand, "zero-force requires saturated row")
            removed |= force
        else:
            need(chosen + free.bit_count() == demand, "one-force requires tight support")
            selected |= force
        need(not selected & removed, "consistent assignment")
    return selected, removed


def replay(case, system):
    selected, removed = trace(system, case["initial_trace"], 0, 0)
    failed = []
    force_steps = len(case["initial_trace"])
    deductions = case["deductions"]
    need(isinstance(deductions, list) and len(deductions) == case["probes"], "failed literal count")
    for number, deduction in enumerate(deductions):
        index = deduction["assume_selected"]
        need(integer(index) and 0 <= index < 4368, "assumption ID")
        bit = 1 << index
        need(bit & system["domain"] and not bit & (selected | removed), "assumption must be free")
        need(
            integer(deduction["forced_value"]) and deduction["forced_value"] == 0,
            "failed positive assumption forces zero",
        )
        branch_selected, branch_removed = trace(
            system, deduction["branch_trace"], selected | bit, removed
        )
        need(bits(deduction["branch_selected"]) == branch_selected, "exact selected branch state")
        evidence = contradiction(
            system, deduction["branch_contradiction_row"], branch_selected, branch_removed
        )
        failed.append({"assumed_block": index, "contradiction": evidence})
        removed |= bit
        selected, removed = trace(system, deduction["base_trace"], selected, removed)
        force_steps += len(deduction["branch_trace"]) + len(deduction["base_trace"])
        closed = deduction["base_contradiction_row"]
        if closed is not None:
            contradiction(system, closed, selected, removed)
            need(number == len(deductions) - 1, "base closure must end deductions")
            need(closed == case["final_contradiction_row"], "final row agrees with base closure")
        else:
            need(number != len(deductions) - 1, "last deduction must report closure")
    need(bits(case["final_selected"]) == selected, "final selected state")
    need(bits(case["final_removed"]) == removed, "final removed state")
    final = contradiction(system, case["final_contradiction_row"], selected, removed)
    return {
        "case": case["case"],
        "profile_seed": case["profile_seed"],
        "point": case["point"],
        "failed_positive_assumptions": len(deductions),
        "force_steps": force_steps,
        "failed_literal_evidence": failed,
        "final_contradiction": final,
        "selected_blocks": selected.bit_count(),
        "removed_blocks": removed.bit_count(),
        "passed": True,
    }


def controls(cases, systems):
    results = []

    def reject(name, index, mutation):
        damaged = copy.deepcopy(cases[index])
        mutation(damaged)
        try:
            replay(damaged, systems[index])
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            results.append({"name": name, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError(f"damaged certificate accepted: {name}")

    for index in range(7):
        reject(
            f"case{index + 1}-wrong-force-value",
            index,
            lambda c: c["initial_trace"][0].update(value=1),
        )
        reject(
            f"case{index + 1}-missing-first-force",
            index,
            lambda c: c["initial_trace"][0]["variables"].pop(),
        )
        empty = next(row for row, mask in enumerate(systems[index]["masks"][:560]) if mask == 0)
        reject(
            f"case{index + 1}-false-branch-contradiction",
            index,
            lambda c, row=empty: c["deductions"][0].update(branch_contradiction_row=row),
        )
        reject(f"case{index + 1}-damaged-final-state", index, lambda c: c["final_removed"].pop())
    reject("boolean-force-value", 0, lambda c: c["initial_trace"][0].update(value=False))
    reject("negative-row", 0, lambda c: c["initial_trace"][0].update(row=-1))
    reject("too-large-row", 0, lambda c: c["initial_trace"][0].update(row=561))
    reject(
        "duplicate-variable",
        0,
        lambda c: c["initial_trace"][0]["variables"].append(c["initial_trace"][0]["variables"][0]),
    )
    reject(
        "boolean-variable", 0, lambda c: c["initial_trace"][0]["variables"].__setitem__(0, False)
    )
    reject("negative-assumption", 0, lambda c: c["deductions"][0].update(assume_selected=-1))
    reject(
        "already-removed-assumption",
        0,
        lambda c: c["deductions"][0].update(assume_selected=c["initial_trace"][0]["variables"][0]),
    )
    reject("wrong-failed-literal-sign", 0, lambda c: c["deductions"][0].update(forced_value=1))
    reject("missing-branch-selected", 0, lambda c: c["deductions"][0]["branch_selected"].pop())
    reject("wrong-probe-count", 0, lambda c: c.update(probes=c["probes"] + 1))
    reject(
        "missing-base-closure", 0, lambda c: c["deductions"][-1].update(base_contradiction_row=None)
    )
    for name, family, size, count in [
        ("duplicate-partial", [systems[0]["partial"][0]] * 20, 5, 20),
        ("short-partial", systems[0]["partial"][:19], 5, 20),
        ("damaged-label", [[False, 2, 3, 4, 5]] + systems[0]["partial"][1:], 5, 20),
        ("duplicate-profile", [systems[0]["profile"][0]] * 80, 3, 80),
    ]:
        try:
            validate_family(family, size, count)
        except ValueError as exc:
            results.append({"name": name, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError(f"damaged input accepted: {name}")
    return results


def main():
    need(digest(CERTIFICATE) == CERTIFICATE_SHA, "frozen certificate")
    need(digest(PRODUCER / "build.py") == PRODUCER_SHA, "producer source pin")
    need(digest(MANIFEST) == MANIFEST_SHA, "completion manifest pin")
    certificate = json.loads(CERTIFICATE.read_text())
    need(
        certificate["all_seven_closed"] is True and certificate["solver_calls"] == 0,
        "finite seven-case claim",
    )
    need(
        certificate["does_not_exclude_all_links_in_any_class_or_profile"] is True, "scope boundary"
    )
    need(
        certificate["source_sha256"] == PRODUCER_SHA
        and certificate["manifest_sha256"] == MANIFEST_SHA,
        "certificate pins",
    )
    manifest = json.loads(MANIFEST.read_text())
    for path, expected in manifest["prepared_files"].items():
        if path.endswith(("-partial.txt", "-profile.json")):
            need(digest(ROOT / path) == expected, "manifest input pin")
    need(
        digest(PROFILE) == manifest["dependencies"][str(PROFILE.relative_to(ROOT))],
        "authoritative profile pin",
    )
    audited_profiles = json.loads(PROFILE.read_text())
    cases = certificate["cases"]
    need(len(cases) == 7, "seven certificate cases")
    need([(case["profile_seed"], case["point"]) for case in cases] == PAIRS, "seven exact branches")
    need([case["probes"] for case in cases] == EXPECTED_PROBES, "saved failed literal census")
    systems = [
        rebuild(case, pinned, audited_profiles) for case, pinned in zip(cases, manifest["cases"])
    ]
    results = [replay(case, system) for case, system in zip(cases, systems)]
    damaged = controls(cases, systems)
    need(digest(PRIOR_REVIEW) == PRIOR_REVIEW_SHA, "prior independent finite screen pin")
    prior = json.loads(PRIOR_REVIEW.read_text())
    need(
        prior["passed"] is True and prior["excluded_fixed_partials"] == 249,
        "prior checked exclusions",
    )
    need(prior["all_case_count"] == 256 and prior["surviving_fixed_partials"] == 7, "prior census")
    need(
        [(row["profile_seed"], row["point"]) for row in prior["summary_replay"]["survivors"]]
        == PAIRS,
        "the same seven surviving cases",
    )
    prior_cases_path = HERE.parent / "clebsch-affine-link-support-screen/cases.json"
    need(
        digest(prior_cases_path) == prior["producer_pins"]["cases.json"],
        "prior screened partial pins",
    )
    prior_cases = json.loads(prior_cases_path.read_text())
    by_pair = {(case["profile_seed"], case["point"]): case for case in prior_cases}
    need(len(by_pair) == len(prior_cases) == 256, "distinct prior cases")
    need(
        set(by_pair) == {(int(seed), point) for seed in audited_profiles for point in range(1, 17)},
        "all sixteen profile by sixteen point cases",
    )
    for case in cases:
        previous = by_pair[(case["profile_seed"], case["point"])]
        need(previous["outcome"] == "survives_finite_screen", "previous survivor")
        need(previous["partial_canonical_sha256"] == case["partial_sha256"], "same exact partial")
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    spec = importlib.util.spec_from_file_location(
        "standalone_partial_check", ROOT / "scripts/check_cover.py"
    )
    independent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(independent)
    dual = []
    for system in systems:
        package = verify_cover(system["partial"])
        standalone = independent.verify_cover(system["partial"], expected_blocks=20)
        need(package["blocks"] == standalone["blocks"] == 20, "dual cardinality")
        need(package["covered"] == standalone["covered_subsets"] == 185, "dual coverage")
        need(
            len(package["uncovered"]) == standalone["uncovered_count"] == 375, "dual partial holes"
        )
        need(package["canonical_sha256"] == standalone["canonical_sha256"], "dual hashes")
        dual.append(
            {
                "canonical_sha256": package["canonical_sha256"],
                "blocks": 20,
                "covered": 185,
                "holes": 375,
            }
        )
    audit = {
        "passed": True,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "checker_sha256": digest(__file__),
        "certificate_sha256": CERTIFICATE_SHA,
        "producer_sha256": PRODUCER_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "independent_engine": (
            "Standard-library integer bitsets; producer propagator neither imported nor called."
        ),
        "rows_per_case": 561,
        "domain_per_case": 3003,
        "cases": results,
        "total_failed_positive_assumptions": sum(
            row["failed_positive_assumptions"] for row in results
        ),
        "total_force_steps": sum(row["force_steps"] for row in results),
        "dual_partial_checks": dual,
        "damaged_controls": damaged,
        "optimizer_calls": 0,
        "search_calls": 0,
        "all_seven_independently_closed": True,
        "combined_with_prior_finite_screen": {
            "independent_review_sha256": PRIOR_REVIEW_SHA,
            "prior_checked_exclusions": 249,
            "new_checked_exclusions": 7,
            "same_partial_hashes_verified": True,
            "all_256_distinct_seed_point_cases_accounted_for": True,
            "combined_scope": (
                "The 256 specifically chosen affine links, one saved map per recipe and point. "
                "Other affine embeddings or local decompositions are not excluded."
            ),
        },
        "scope": "Only the seven pinned twenty-block partials and their exact excess profiles.",
        "global_lower_bound": False,
        "excludes_all_links_or_embeddings": False,
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                key: audit[key]
                for key in (
                    "passed",
                    "total_failed_positive_assumptions",
                    "total_force_steps",
                    "optimizer_calls",
                )
            },
            indent=2,
        )
    )
    print(json.dumps({"damaged_controls_rejected": len(damaged)}))


if __name__ == "__main__":
    main()
