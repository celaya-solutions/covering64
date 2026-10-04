# Document:    Independent Combined Template-and-Hub Model Preflight
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      528cbdff9108bf2c82976e208cb21bfdfd811ef9e321243c41f42b47b2d1fc60
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""No-solve structural and reset checks independent of the runner's audits."""

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import math
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREVIOUS_PREFLIGHT_SHA256 = "dc1dd91cc3b505229daabe266e7136479d6c05b1bebf823662da81ed3d1605e7"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(proto, original, width, m4, z, fixed, phase):
    require(len(proto.constraint) == 4559, "exactly two hub and seven fixed rows")
    require(len(proto.variable) == width + (14 if phase else 0), "variable count")
    for variable in proto.variable[:width]:
        require(variable.lower_bound == 0 and variable.upper_bound == 1, "original unit domains")
        require(variable.objective_coefficient == 0, "original zero objective")
    for variable in proto.variable[width:]:
        require(variable.lower_bound == 0 and variable.upper_bound == math.inf, "slack domain")
        require(variable.objective_coefficient == 1, "slack objective")
    core = copy.deepcopy(proto)
    del core.constraint[4550:]
    require(core.SerializeToString(deterministic=True) == original, "original prefix bytes")
    blocks = list(combinations(range(1, 17), 5))
    hubs = {4, 8, 12, 16}
    hub_counts = [sum(point in hubs for point in block) for block in blocks]
    expected_hub = [
        ([(i, 1) for i, n in enumerate(hub_counts) if n == 4], m4),
        ([(i, 1 if n == 3 else 4) for i, n in enumerate(hub_counts) if n >= 3], 4 + z),
    ]
    for index, (terms, value) in enumerate(expected_hub, 4550):
        row = proto.constraint[index]
        require(
            list(zip(row.var_index, row.coefficient, strict=True)) == terms,
            "hub coefficients and lexicographic variables",
        )
        require(row.lower_bound == row.upper_bound == value, "hub equality bounds")
        require(row.name == f"row_{index}", "hub row name")
    for offset, row in enumerate(proto.constraint[4552:]):
        terms = []
        if fixed is not None:
            terms.append((fixed[offset], 1))
        if phase:
            terms.extend(((width + offset * 2, 1), (width + offset * 2 + 1, -1)))
        require(
            sorted(zip(row.var_index, row.coefficient, strict=True)) == sorted(terms),
            "fixed-row exact coefficients",
        )
        require(
            row.lower_bound == row.upper_bound == (1 if fixed is not None else 0),
            "fixed-row equality bounds",
        )
        require(row.name == f"fixed_block_{offset}", "fixed-row name")
    return dict(
        original_prefix_sha256=hashlib.sha256(original).hexdigest(),
        hub_rows=2,
        fixed_rows=7,
        variables=len(proto.variable),
        rows=4559,
    )


def controls(proto, original, width, m4, z, phase):
    mutations = [
        ("changed original coefficient", lambda p: p.constraint[0].coefficient.__setitem__(0, 2)),
        ("changed original domain", lambda p: setattr(p.variable[0], "upper_bound", 0)),
        (
            "changed original objective",
            lambda p: setattr(p.variable[0], "objective_coefficient", 1),
        ),
        (
            "changed first hub coefficient",
            lambda p: p.constraint[4550].coefficient.__setitem__(0, 2),
        ),
        (
            "changed second hub coefficient",
            lambda p: p.constraint[4551].coefficient.__setitem__(0, 2),
        ),
        ("changed first hub bound", lambda p: setattr(p.constraint[4550], "upper_bound", m4 + 1)),
        ("changed second hub bound", lambda p: setattr(p.constraint[4551], "lower_bound", 5 + z)),
        ("missing hub row", lambda p: p.constraint.__delitem__(4550)),
        ("extra row", lambda p: p.constraint.add()),
        (
            "stale fixed coefficient",
            lambda p: (
                p.constraint[4552].var_index.append(0),
                p.constraint[4552].coefficient.append(1),
            ),
        ),
    ]
    if phase:
        mutations.extend(
            [
                ("changed slack domain", lambda p: setattr(p.variable[width], "upper_bound", 1)),
                (
                    "changed slack objective",
                    lambda p: setattr(p.variable[width], "objective_coefficient", 0),
                ),
                ("changed slack sign", lambda p: p.constraint[4552].coefficient.__setitem__(0, -1)),
            ]
        )
    results = []
    for name, mutation in mutations:
        broken = copy.deepcopy(proto)
        mutation(broken)
        try:
            inspect(broken, original, width, m4, z, None, phase)
        except ValueError:
            results.append(dict(control=name, rejected=True))
        else:
            raise ValueError(f"damaged model accepted: {name}")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "new preflight output required")
    old_path = REPO / "experiments/2026-10-03/four-seven-template-link-screen/preflight.json"
    require(digest(old_path) == PREVIOUS_PREFLIGHT_SHA256, "frozen earlier preflight")
    old = json.loads(old_path.read_text())
    spec = importlib.util.spec_from_file_location("combined_screen", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    plan, _, cases, inputs, selected = runner.prepare()
    args.output.mkdir(parents=True)
    for name in ("run.py", "preflight.py", "priority-plan.json"):
        (args.output / name).write_bytes((HERE / name).read_bytes())
    by_model = {}
    for record in selected:
        key = (record["case"], *record["hub_case"])
        by_model.setdefault(key, []).append(record)
    records = []
    for (case, m4, z), representatives in sorted(by_model.items()):
        for phase in (False, True):
            stage = "phase-one" if phase else "feasibility"
            baseline_path = (
                REPO
                / "experiments/scratch/four-seven-template-link-preflight-20261003"
                / f"{case}-{stage}-base.pb.gz"
            )
            baseline = gzip.decompress(baseline_path.read_bytes())
            old_model = next(
                m for m in old["models"] if m["case"] == case and m["phase_one"] == phase
            )
            require(
                hashlib.sha256(baseline).hexdigest() == old_model["prefix_sha256"],
                "frozen original protobuf hash",
            )
            model = runner.CombinedHull(cases[case]["payload"], m4, z, phase_one=phase)
            def no_solve(*args):
                raise ValueError("preflight forbids solving")

            model.solver.Solve = no_solve
            proto = model.export()
            checked = inspect(proto, baseline, model.width, m4, z, None, phase)
            damaged = controls(proto, baseline, model.width, m4, z, phase)
            transitions = []
            for representative in representatives:
                fixed = representative["fixed_ids"]
                model.fix(fixed)
                inspect(model.export(), baseline, model.width, m4, z, fixed, phase)
                try:
                    model.fix(fixed)
                except ValueError:
                    pass
                else:
                    raise ValueError("unreset transition accepted")
                model.reset()
                inspect(model.export(), baseline, model.width, m4, z, None, phase)
                transitions.append(representative["id"])
            proto_path = args.output / f"{case}-m4-{m4}-z-{z}-{stage}.pb.gz"
            proto_path.write_bytes(
                gzip.compress(proto.SerializeToString(deterministic=True), mtime=0)
            )
            records.append(
                dict(
                    case=case,
                    hub_case=[m4, z],
                    phase_one=phase,
                    original_prefix_audit=checked,
                    combined_prefix_sha256=model.prefix_sha256,
                    proto_sha256=digest(proto_path),
                    transitions=transitions,
                    damaged_controls=damaged,
                )
            )
    report = dict(
        valid=True,
        solver_calls=0,
        runner_sha256=digest(HERE / "run.py"),
        checker_sha256=digest(Path(__file__)),
        plan_sha256=digest(HERE / "priority-plan.json"),
        earlier_preflight_sha256=PREVIOUS_PREFLIGHT_SHA256,
        source_input_hashes=inputs,
        priority_representatives=len(plan["priority"]),
        models=records,
        transitions=sum(len(r["transitions"]) for r in records),
        damaged_controls=sum(len(r["damaged_controls"]) for r in records),
        scope="All eight feasibility/phase-one layouts retain byte-identical original "
        "hull prefixes and append exactly two hub equalities and seven fixed rows. "
        "No solver calls or infeasibility claims.",
    )
    (args.output / "preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "models"}))


if __name__ == "__main__":
    main()
