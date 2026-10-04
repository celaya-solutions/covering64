# Document:    Whole-Template-Hull First-Link Saved Result Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5d98a5da2d55b1de0f84c1d4c72a7398ef697935b40fb804b87c11ba676e22a0
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check saved run evidence and numerical primals without loading the runner."""

import argparse
import copy
import gzip
import hashlib
import itertools
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

RUNNER_HASH = "c8841227df38eec07b28f9776e812e1df4c8c4175e80c0feead9fb15f8289b9e"
SELECTION_HASH = "27c0e77561c37b86dd60b85427256b30f6ce9433a87edd39c41ed73dc69e601d"
MATRIX_HASHES = {
    "cycle": "27061fc3af3e1933b05b8c71c5fabef5229129d0ab57c73cf1cb9c9b282cf88d",
    "matching": "7bfcfd3b82f52016c9c594778d19443b2ed803c1f6e121461230bda28cbfb0ee",
}
EPSILON = Fraction(1, 10_000_000)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def check_states(result, prefix_hash, fixed_ids):
    fixed_rows = [
        dict(row_index=4550 + j, coefficients=[[i, 1.0]], lower=1, upper=1)
        for j, i in enumerate(fixed_ids)
    ]
    active = dict(
        prefix_sha256=prefix_hash,
        active_fixed_ids=fixed_ids,
        phase_one=False,
        fixed_rows=fixed_rows,
    )
    reset = dict(
        prefix_sha256=prefix_hash,
        active_fixed_ids=None,
        phase_one=False,
        fixed_rows=[dict(row_index=4550 + j, coefficients=[], lower=0, upper=0) for j in range(7)],
    )
    require(result["fixed_state_audit"] == active, "active state record")
    require(result["feasibility_lp"]["model_audit"] == active, "solve state record")
    require(result["reset_audit"] == reset, "reset state record")


def check_primal(primal, model, fixed_ids):
    width = model["width"]
    require(primal["width"] == width, "primal width")
    require(primal["zero_default"] is True, "sparse zero default")
    require(primal["fixed_ids"] == fixed_ids, "primal fixed IDs")
    pairs = primal["values"]
    ids = [pair[0] for pair in pairs]
    require(all(type(i) is int and 0 <= i < width for i in ids), "sparse index domain")
    require(ids == sorted(set(ids)), "sparse indices must be unique and sorted")
    values = [pair[1] for pair in pairs]
    require(
        all(type(v) in (int, float) and math.isfinite(v) and v != 0 for v in values),
        "nonzero finite sparse values",
    )
    fractions = [Fraction(v) for v in values]
    scale = max([1, *(v.denominator for v in fractions)])
    require(all(scale % v.denominator == 0 for v in fractions), "binary denominator")
    scaled = {
        i: v.numerator * (scale // v.denominator) for i, v in zip(ids, fractions, strict=True)
    }
    domain = max([0, *(-v for v in scaled.values()), *(v - scale for v in scaled.values())])
    fixed_rows = [[[i], [1], 1, 1] for i in fixed_ids]
    row_residual = 0
    for indices, coefficients, lower, upper in itertools.chain(model["rows"], fixed_rows):
        total = sum(scaled.get(i, 0) * c for i, c in zip(indices, coefficients, strict=True))
        if lower is not None:
            row_residual = max(row_residual, lower * scale - total)
        if upper is not None:
            row_residual = max(row_residual, total - upper * scale)
    exact_domain = Fraction(domain, scale)
    exact_residual = Fraction(row_residual, scale)
    require(exact_domain <= EPSILON and exact_residual <= EPSILON, "numerical feasibility")
    blocks = [scaled.get(i, 0) for i in range(4368)]
    epsilon_scaled = EPSILON * scale
    fractional = sum(epsilon_scaled < v < scale - epsilon_scaled for v in blocks)
    mass = sum(min(max(v, 0), max(scale - v, 0)) for v in blocks)
    integrality = max(min(abs(v), abs(scale - v)) for v in blocks)
    return dict(
        exact_binary_domain_residual=[exact_domain.numerator, exact_domain.denominator],
        exact_binary_row_residual=[exact_residual.numerator, exact_residual.denominator],
        numerical_row_residual=float(exact_residual),
        fractional_block_count=fractional,
        fractional_block_mass=float(Fraction(mass, scale)),
        positive_template_weights=sum(v > epsilon_scaled for i, v in scaled.items() if i >= 4768),
        selected_at_half=sum(2 * v >= scale for v in blocks),
        near_integral=integrality <= epsilon_scaled,
    )


def damaged_controls(primal, model, fixed_ids, result, prefix_hash):
    controls = []
    for label, change in (
        ("duplicate sparse entry", lambda p: p["values"].append(p["values"][0])),
        ("invalid sparse index", lambda p: p["values"][0].__setitem__(0, model["width"])),
        ("nonfinite value", lambda p: p["values"][0].__setitem__(1, float("nan"))),
        ("wrong vector width", lambda p: p.__setitem__("width", model["width"] - 1)),
        (
            "damaged fixed block",
            lambda p: p.__setitem__(
                "values", [[i, 0.5 if i == fixed_ids[0] else v] for i, v in p["values"]]
            ),
        ),
    ):
        broken = copy.deepcopy(primal)
        change(broken)
        try:
            check_primal(broken, model, fixed_ids)
        except ValueError:
            controls.append(dict(control=label, rejected=True))
        else:
            raise ValueError(f"damaged control accepted: {label}")
    broken = copy.deepcopy(result)
    broken["reset_audit"]["fixed_rows"][0]["coefficients"] = [[fixed_ids[0], 1]]
    try:
        check_states(broken, prefix_hash, fixed_ids)
    except ValueError:
        controls.append(dict(control="stale reset coefficient", rejected=True))
    else:
        raise ValueError("damaged state accepted")
    return controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    run = args.run
    require(digest(run / "run.py") == RUNNER_HASH, "runner hash")
    require(digest(run / "representatives.json") == SELECTION_HASH, "selection hash")
    selected = load(run / "representatives.json")
    metadata = load(run / "metadata.json")
    results_path = run / "results.json.gz"
    results_bytes = results_path.read_bytes()
    results = json.loads(gzip.decompress(results_bytes))
    expected = [(case["case"], r) for case in selected["cases"] for r in case["representatives"]]
    require(len(expected) == 156 and len(results) <= 156, "selection count")
    require(args.partial or len(results) == 156, "incomplete run")
    require(
        [r["id"] for r in results] == [r["id"] for _, r in expected[: len(results)]],
        "result identities and order",
    )
    block_ids = {b: i for i, b in enumerate(itertools.combinations(range(1, 17), 5))}
    models, prefixes, records, controls = {}, {}, [], []
    for result, (case, representative) in zip(results, expected, strict=False):
        directory = run / case
        matrix_path = directory / "extended-rows.json.gz"
        if case not in models:
            require(digest(matrix_path) == MATRIX_HASHES[case], "frozen matrix hash")
            models[case] = load(matrix_path)
            prefixes[case] = hashlib.sha256(
                gzip.decompress((directory / "feasibility-base.pb.gz").read_bytes())
            ).hexdigest()
            require(
                prefixes[case] == metadata["cases"][case]["feasibility_base_sha256"],
                "base protobuf prefix hash",
            )
        model = models[case]
        fixed = sorted(
            block_ids[tuple(sorted((1, 2, 3, *edge)))] for edge in representative["edges"]
        )
        require(len(fixed) == len(set(fixed)) == 7, "seven distinct fixed blocks")
        require(result["case"] == case and result["fixed_ids"] == fixed, "fixed blocks")
        require(
            result["checked_rows"] == 4557 and result["checked_columns"] == model["width"],
            "reported dimensions",
        )
        check_states(result, prefixes[case], fixed)
        target = directory / result["id"]
        require(load(target / "result.json") == result, "individual result matches archive")
        fixed_record = load(target / "fixed-rows.json")
        require(
            fixed_record
            == dict(
                id=result["id"],
                case=case,
                width=model["width"],
                base_matrix_sha256=MATRIX_HASHES[case],
                rows=[[[i], [1], 1, 1] for i in fixed],
            ),
            "saved fixed matrix rows",
        )
        require(
            digest(target / "feasibility-solver.log") == result["feasibility_lp"]["log_sha256"],
            "solver log hash",
        )
        feasibility_budget = result["feasibility_lp"]["allocated_seconds"]
        phase_budget = result.get("phase_one_lp", {}).get("allocated_seconds", 0)
        require(0 < feasibility_budget <= 15, "feasibility solver budget")
        if "phase_one_lp" in result:
            remaining = max(0, 15 - result["feasibility_lp"]["solve_seconds"])
            require(0 < phase_budget <= remaining + 0.000001, "remaining phase-one budget")
        require(result["independently_excluded"] is False, "premature exclusion flag")
        record = dict(
            id=result["id"],
            case=case,
            status=result["feasibility_lp"]["status_name"],
            feasibility_budget_seconds=feasibility_budget,
            phase_one_budget_seconds=phase_budget,
            solve_seconds=result["solve_seconds_total"],
            certificate_pending_replay=result["certificate_pending_replay"],
        )
        if "sparse_primal_sha256" in result:
            path = target / "sparse-primal.json.gz"
            require(digest(path) == result["sparse_primal_sha256"], "primal hash")
            primal = load(path)
            require(primal["base_matrix_sha256"] == MATRIX_HASHES[case], "primal matrix link")
            numerical = check_primal(primal, model, fixed)
            for name in ("fractional_block_count", "positive_template_weights"):
                require(numerical[name] == result["primal_metrics"][name], f"reported {name}")
            require(
                abs(
                    numerical["fractional_block_mass"]
                    - result["primal_metrics"]["fractional_block_mass"]
                )
                < 1e-10,
                "reported fractional mass",
            )
            require(
                abs(
                    numerical["numerical_row_residual"]
                    - result["primal_metrics"]["max_row_violation"]
                )
                < 1e-10,
                "reported floating residual",
            )
            require(
                numerical["selected_at_half"] == result["integral_blocks"]["selected_block_count"],
                "reported selected count",
            )
            require(
                numerical["near_integral"] == result["integral_blocks"]["near_integral"],
                "reported integrality",
            )
            record["primal_audit"] = numerical
            record["primal_sha256"] = digest(path)
            if not controls:
                controls = damaged_controls(primal, model, fixed, result, prefixes[case])
        records.append(record)
    report = dict(
        valid=True,
        complete=len(results) == 156,
        checked_representatives=len(results),
        checker_sha256=digest(Path(__file__)),
        runner_sha256=RUNNER_HASH,
        results_sha256=hashlib.sha256(results_bytes).hexdigest(),
        selected_sha256=SELECTION_HASH,
        matrix_hashes=MATRIX_HASHES,
        status_counts=dict(Counter(r["status"] for r in records)),
        damaged_controls=controls,
        records=records,
        scope="Readback evidence and exact arithmetic on stored binary floats. Numerical residuals "
        "within tolerance are not exact feasible witnesses. This checker does not replay "
        "infeasibility certificates or claim exclusions.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}))


if __name__ == "__main__":
    main()
