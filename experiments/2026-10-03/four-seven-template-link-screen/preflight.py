# Document:    Fixed-Row and Reset Preflight for the Template Hull Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b95b2b697093eb4f231edc80119e9ba8ca60e5ca670884a39c6b272c7ca60a3d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import json
import math
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent
OUT = run.REPO / "experiments/scratch/four-seven-template-link-preflight-20261003"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_export(proto, payload, phase, fixed_ids=None, full=True):
    width = payload["width"]
    require(len(proto.variable) == width + (14 if phase else 0), "variable count")
    require(len(proto.constraint) == 4557 and not proto.general_constraint, "constraint shape")
    require(not proto.maximize and proto.objective_offset == 0, "objective sense or constant")
    if full:
        for index, variable in enumerate(proto.variable[:width]):
            require(
                variable.name == f"x{index}"
                and variable.lower_bound == 0
                and variable.upper_bound == 1
                and not variable.is_integer
                and variable.objective_coefficient == 0,
                "original variable changed",
            )
        for index, (saved, actual) in enumerate(
            zip(payload["rows"], proto.constraint[:4550], strict=True)
        ):
            ids, coefficients, lower, upper = saved
            require(
                sorted(zip(actual.var_index, actual.coefficient, strict=True))
                == sorted(zip(ids, coefficients, strict=True)),
                "original coefficients changed",
            )
            require(
                actual.lower_bound == (lower if lower is not None else -math.inf)
                and actual.upper_bound == (upper if upper is not None else math.inf),
                "original row domain changed",
            )
            require(actual.name == f"row_{index}", "original row name changed")
    if phase:
        for i, variable in enumerate(proto.variable[width:]):
            side = "lower" if i % 2 == 0 else "upper"
            require(
                variable.name == f"fixed_slack_{side}_{i // 2}"
                and variable.lower_bound == 0
                and variable.upper_bound == math.inf
                and not variable.is_integer
                and variable.objective_coefficient == 1,
                "phase slack or objective changed",
            )
    for i, row in enumerate(proto.constraint[4550:]):
        terms = [] if fixed_ids is None else [(fixed_ids[i], 1)]
        if phase:
            terms.extend(((width + 2 * i, 1), (width + 2 * i + 1, -1)))
        require(
            sorted(zip(row.var_index, row.coefficient, strict=True)) == sorted(terms),
            "fixed support mismatch",
        )
        expected = 0 if fixed_ids is None else 1
        require(row.lower_bound == row.upper_bound == expected, "fixed equality mismatch")


def main():
    require(not OUT.exists(), "preflight output must be new")
    helpers, utility_path = run.utilities()
    _, prepared, input_hashes = run.load_inputs(
        run.REPO / "experiments/scratch/four-seven-template-hull-20261003",
        run.ARTIFACTS / "four-seven-blossom-screen/remaining-representatives.json",
        run.ARTIFACTS / "four-seven-template-hull/independent-audit.json",
    )
    OUT.mkdir(parents=True)
    for source in (HERE / "run.py", Path(__file__), utility_path):
        (OUT / source.name).write_bytes(source.read_bytes())
    results = []
    for name, case in prepared.items():
        payload = case["payload"]
        helpers.validate_rows(payload["rows"], payload["width"])
        for phase in (False, True):
            model = run.ReusableHull(payload, phase_one=phase)
            check_export(model.export(), payload, phase)
            prefix = f"{name}-{'phase-one' if phase else 'feasibility'}"
            (OUT / f"{prefix}-base.pb.gz").write_bytes(gzip.compress(model.prefix_bytes, mtime=0))
            states = []
            for representative in case["representatives"]:
                ids = representative["fixed_ids"]
                active = model.fix(ids)
                check_export(model.export(), payload, phase, ids, full=False)
                reset = model.reset()
                check_export(model.export(), payload, phase, full=False)
                states.append(
                    dict(
                        id=representative["id"],
                        fixed_ids=ids,
                        fixed_audit=active,
                        reset_audit=reset,
                    )
                )
            check_export(model.export(), payload, phase)
            controls = []
            ids = case["representatives"][0]["fixed_ids"]

            def rejects(label, action, restore, active_ids=None):
                action()
                try:
                    model.audit(active_ids)
                except ValueError:
                    controls.append(dict(control=label, rejected=True))
                else:
                    raise ValueError("damaged state accepted: " + label)
                finally:
                    restore()
                model.audit(None)

            model.fix(ids)
            rejects(
                "stale fixed coefficient",
                lambda: model.fixed_rows[0].SetCoefficient(model.variables[4367], 1),
                model.reset,
                ids,
            )
            model.fix(ids)
            rejects(
                "wrong fixed equality",
                lambda: model.fixed_rows[0].SetBounds(0, 1),
                model.reset,
                ids,
            )
            rejects(
                "original box changed",
                lambda: model.variables[0].SetBounds(-1, 1),
                lambda: model.variables[0].SetBounds(0, 1),
            )
            rejects(
                "original objective changed",
                lambda: model.solver.Objective().SetCoefficient(model.variables[0], 1),
                lambda: model.solver.Objective().SetCoefficient(model.variables[0], 0),
            )
            row = model.constraints[0]
            original_bounds = (row.lb(), row.ub())
            rejects(
                "original row changed",
                lambda: row.SetBounds(0, 1),
                lambda: row.SetBounds(*original_bounds),
            )
            if phase:
                slack = model.slacks[0][0]
                rejects(
                    "slack objective changed",
                    lambda: model.solver.Objective().SetCoefficient(slack, 0),
                    lambda: model.solver.Objective().SetCoefficient(slack, 1),
                )
                rejects(
                    "slack bound changed",
                    lambda: slack.SetBounds(-1, math.inf),
                    lambda: slack.SetBounds(0, math.inf),
                )
                rejects(
                    "slack row sign changed",
                    lambda: model.fixed_rows[0].SetCoefficient(slack, -1),
                    model.reset,
                )
            for wrong in ([ids[0]] * 7, [4368, *ids[1:]], ids[:6]):
                try:
                    model.fix(wrong)
                except ValueError:
                    controls.append(dict(control="invalid block ID list", rejected=True))
                else:
                    raise ValueError("invalid IDs accepted")
                model.audit(None)
            model.fix(ids)
            try:
                model.fix(ids)
            except ValueError:
                controls.append(dict(control="unreset transition", rejected=True))
            else:
                raise ValueError("unreset transition accepted")
            model.reset()
            check_export(model.export(), payload, phase)
            record = dict(
                case=name,
                phase_one=phase,
                original_width=payload["width"],
                solver_width=payload["width"] + (14 if phase else 0),
                original_rows=4550,
                total_rows=4557,
                prefix_sha256=model.prefix_sha256,
                transitions=len(states),
                fixed_row_states=states,
                damaged_controls=controls,
            )
            results.append(record)
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in record.items()
                        if k not in ("fixed_row_states", "damaged_controls")
                    }
                ),
                flush=True,
            )
    contradiction = helpers.integer_certificate(
        [[[0], [1], 1, 1], [[0], [1], 0, 0]], 1, [1.0, -1.0], 1_000_000
    )
    require(
        contradiction["proves_infeasible"]
        and contradiction["gap"] == [1, 1]
        and contradiction["checked_columns"] == 1,
        "certificate control",
    )
    output = dict(
        valid=True,
        runner_sha256=run.digest(HERE / "run.py"),
        checker_sha256=run.digest(Path(__file__)),
        utility_sha256=run.UTILITIES_SHA256,
        manifest_sha256=run.MANIFEST_SHA256,
        input_hashes=input_hashes,
        models=results,
        total_fixed_transitions=sum(r["transitions"] for r in results),
        total_damaged_controls=sum(len(r["damaged_controls"]) for r in results),
        solver_calls=0,
        scope="All 156 selected first links exercised on feasibility and phase-one models; "
        "exactly seven fixed equalities, objective/slack reset, and original-prefix preservation. "
        "No solve.",
    )
    (OUT / "preflight.json").write_text(json.dumps(output, indent=2) + "\n")
    (HERE / "preflight.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
