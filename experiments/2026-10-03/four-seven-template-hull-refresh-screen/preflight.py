# Document:    Refreshed Matching LP Independent No-Solve Preflight
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      7e9bf7a4361d8d2d1c9419e1c24fe71a1386eb49e417700f2cd53edc60cc8818
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check every new-matrix coefficient, unit box, slack and fixed/reset state."""

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(proto, matrix, kind, phase, fixed, reference=None):
    width = matrix["width"]
    slack_count = (560 if kind == "whole" else 14) if phase else 0
    require(len(proto.variable) == width + slack_count, "variable count")
    require(len(proto.constraint) == 4550 + (7 if kind == "fixed" else 0), "row count")
    require(not proto.maximize and proto.objective_offset == 0, "objective direction/offset")
    for index, variable in enumerate(proto.variable[:width]):
        require(variable.lower_bound == 0 and variable.upper_bound == 1, "unit-box domain")
        require(
            variable.objective_coefficient == 0 and not variable.is_integer,
            "original objective/type",
        )
        require(variable.name == f"x{index}", "original variable order")
    for variable in proto.variable[width:]:
        require(variable.lower_bound == 0 and variable.upper_bound == math.inf, "slack bounds")
        require(
            variable.objective_coefficient == 1 and not variable.is_integer, "slack objective/type"
        )
    canonical = []
    for index, (row, expected) in enumerate(
        zip(proto.constraint[:4550], matrix["rows"], strict=True)
    ):
        base_terms = [
            (i, c) for i, c in zip(row.var_index, row.coefficient, strict=True) if i < width
        ]
        require(
            all(float(c).is_integer() for _, c in base_terms), "integral unchanged coefficients"
        )
        actual = [
            [i for i, _ in base_terms],
            [int(c) for _, c in base_terms],
            None if row.lower_bound == -math.inf else int(row.lower_bound),
            None if row.upper_bound == math.inf else int(row.upper_bound),
        ]
        require(
            row.lower_bound == (-math.inf if expected[2] is None else expected[2])
            and row.upper_bound == (math.inf if expected[3] is None else expected[3]),
            "exact matrix bounds",
        )
        require(actual == expected and row.name == f"row_{index}", "exact matrix row")
        canonical.append(actual)
        extra = [(i, c) for i, c in zip(row.var_index, row.coefficient, strict=True) if i >= width]
        expected_extra = []
        if phase and kind == "whole" and index >= 4270:
            expected_extra = [(width + 2 * (index - 4270), 1), (width + 2 * (index - 4270) + 1, -1)]
        require(extra == expected_extra, "whole-hull phase-one support/signs")
    encoded = json.dumps(canonical, separators=(",", ":")).encode()
    require(
        encoded == json.dumps(matrix["rows"], separators=(",", ":")).encode(),
        "byte-identical canonical refreshed matrix",
    )
    if kind == "fixed":
        for offset, row in enumerate(proto.constraint[4550:]):
            terms = [] if fixed is None else [(fixed[offset], 1)]
            if phase:
                terms += [(width + 2 * offset, 1), (width + 2 * offset + 1, -1)]
            require(
                sorted(zip(row.var_index, row.coefficient, strict=True)) == sorted(terms),
                "seven fixed rows and their exclusive slacks",
            )
            require(
                row.lower_bound == row.upper_bound == (0 if fixed is None else 1), "fixed bounds"
            )
            require(row.name == f"fixed_block_{offset}", "fixed names")
    core = copy.deepcopy(proto)
    del core.variable[width:]
    del core.constraint[4550:]
    for row in core.constraint:
        kept = [(i, c) for i, c in zip(row.var_index, row.coefficient, strict=True) if i < width]
        del row.var_index[:]
        del row.coefficient[:]
        row.var_index.extend(i for i, _ in kept)
        row.coefficient.extend(c for _, c in kept)
    serialized = core.SerializeToString(deterministic=True)
    require(reference is None or serialized == reference, "byte-identical original protobuf core")
    return serialized, hashlib.sha256(encoded).hexdigest()


def damaged_controls(proto, matrix, kind, phase, reference):
    width = matrix["width"]
    mutations = [
        ("matrix coefficient", lambda p: p.constraint[0].coefficient.__setitem__(0, 2)),
        ("matrix bound", lambda p: setattr(p.constraint[0], "upper_bound", 1)),
        ("original domain", lambda p: setattr(p.variable[0], "upper_bound", 0)),
        ("original objective", lambda p: setattr(p.variable[0], "objective_coefficient", 1)),
        ("original type", lambda p: setattr(p.variable[0], "is_integer", True)),
        ("objective direction", lambda p: setattr(p, "maximize", True)),
        ("extra row", lambda p: p.constraint.add()),
        ("extra variable", lambda p: p.variable.add()),
    ]
    if kind == "fixed":
        mutations.append(
            (
                "stale fixed row",
                lambda p: (
                    p.constraint[4550].var_index.append(0),
                    p.constraint[4550].coefficient.append(1),
                ),
            )
        )
    if phase:
        first_soft = 4270 if kind == "whole" else 4550
        mutations += [
            ("slack bound", lambda p: setattr(p.variable[width], "upper_bound", 1)),
            ("slack objective", lambda p: setattr(p.variable[width], "objective_coefficient", 0)),
            ("slack sign", lambda p: p.constraint[first_soft].coefficient.__setitem__(-1, 1)),
        ]
    controls = []
    for label, mutation in mutations:
        broken = copy.deepcopy(proto)
        mutation(broken)
        try:
            inspect(broken, matrix, kind, phase, None, reference)
        except ValueError:
            controls.append(dict(control=label, rejected=True))
        else:
            raise ValueError(f"damaged control accepted: {label}")
    return controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "new preflight output required")
    spec = importlib.util.spec_from_file_location("refreshed_matching_screen", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    matrix, selection, inputs, _ = runner.prepare()
    args.output.mkdir(parents=True)
    for name in ("run.py", "preflight.py"):
        (args.output / name).write_bytes((HERE / name).read_bytes())
    (args.output / "selection.json").write_text(json.dumps(selection, indent=2) + "\n")
    records, reference = [], None
    for kind in ("whole", "fixed"):
        for phase in (False, True):
            model = (
                runner.WholeHull(matrix, phase)
                if kind == "whole"
                else runner.PREVIOUS.ReusableHull(matrix, phase)
            )

            def no_solve(*args):
                raise ValueError("preflight forbids Solve")

            model.solver.Solve = no_solve
            proto = model.export()
            core, rows_hash = inspect(proto, matrix, kind, phase, None, reference)
            if reference is None:
                reference = core
            controls = damaged_controls(proto, matrix, kind, phase, reference)
            transitions = []
            if kind == "fixed":
                for selected in selection:
                    fixed = selected["fixed_ids"]
                    model.fix(fixed)
                    inspect(model.export(), matrix, kind, phase, fixed, reference)
                    try:
                        model.fix(fixed)
                    except ValueError:
                        pass
                    else:
                        raise ValueError("unreset transition accepted")
                    model.reset()
                    inspect(model.export(), matrix, kind, phase, None, reference)
                    transitions.append(selected["id"])
                for invalid in ([0] * 7, [-1, 1, 2, 3, 4, 5, 6], list(range(6))):
                    try:
                        model.fix(invalid)
                    except ValueError:
                        controls.append(dict(control="invalid fixed IDs", rejected=True))
                    else:
                        raise ValueError("invalid fixed IDs accepted")
            stage = "phase-one" if phase else "feasibility"
            path = args.output / f"{kind}-{stage}.pb.gz"
            path.write_bytes(gzip.compress(proto.SerializeToString(deterministic=True), mtime=0))
            records.append(
                dict(
                    kind=kind,
                    phase_one=phase,
                    rows=len(proto.constraint),
                    columns=len(proto.variable),
                    canonical_rows_sha256=rows_hash,
                    core_protobuf_sha256=hashlib.sha256(core).hexdigest(),
                    prefix_sha256=model.prefix_sha256,
                    exported_proto_sha256=digest(path),
                    transitions=transitions,
                    damaged_controls=controls,
                )
            )
    report = dict(
        valid=True,
        solver_calls=0,
        runner_sha256=digest(HERE / "run.py"),
        checker_sha256=digest(Path(__file__)),
        input_hashes=inputs,
        selected_representatives=50,
        transitions=sum(len(r["transitions"]) for r in records),
        damaged_controls=sum(len(r["damaged_controls"]) for r in records),
        models=records,
        scope="Four layouts preserve exact refreshed matrix coefficients, unit boxes and "
        "objective fields. Whole phase I softens only 280 template rows; fixed-link "
        "phase I softens only seven fixes. All 50 transitions checked twice. No Solve.",
    )
    (args.output / "preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "models"}))


if __name__ == "__main__":
    main()
