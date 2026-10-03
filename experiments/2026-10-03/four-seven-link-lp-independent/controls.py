# Document:    Independent LP Certificate Controls
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b8a904f3bf974213a3040d86510c7f67c12ae4ffa9e5128ebd3d5639cdb8d193
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Toy algebraic controls only; none of these fixtures is a covering candidate."""

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

from check import check_certificate

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
SOURCE = ROOT / "scripts/four_seven_link_lp.py"
spec = importlib.util.spec_from_file_location("subject", SOURCE)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


def rejected(call):
    try:
        call()
    except (ValueError, TypeError, KeyError, IndexError):
        return True
    raise AssertionError("damaged control was accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("controls.json"))
    args = parser.parse_args()
    toy_cases = [
        ("feasible_box", [((0,), (1,), 0, 1)], 1, False),
        ("fractional_feasible_integer_impossible", [((0,), (2,), 1, 1)], 1, False),
        ("conflicting_rows", [((0,), (1,), 1, None), ((0,), (1,), None, 0)], 1, True),
        ("upper_box_violation", [((0,), (2,), 3, None)], 1, True),
        ("lower_box_violation", [((0,), (2,), None, -1)], 1, True),
    ]
    toys, positive = [], None
    for name, rows, width, infeasible in toy_cases:
        normal = subject.solve_lp(rows, width, 2)
        phase = subject.solve_lp(rows, width, 2, phase_one=True)
        assert normal["status"] == (2 if infeasible else 0), (name, normal)
        assert phase["status"] == 0, (name, phase)
        certificate = subject.exact_certificate(rows, width, phase["weights"])
        checked = check_certificate(rows, width, certificate)
        assert checked["proves_infeasible"] == infeasible
        assert (phase["objective"] > 0) == infeasible
        toys.append({"name": name, "lp": normal, "phase": phase,
                     "certificate": certificate, "independent": checked})
        if name == "conflicting_rows":
            positive = rows, width, certificate
    damages = {}
    feasible = [((0,), (1,), 0, 1)]
    for denominator in [-1, 0, True, 1.5]:
        damages[f"denominator_{denominator!r}"] = rejected(
            lambda d=denominator: subject.exact_certificate(feasible, 1, [1.0], d))
    for label, row in {
        "length": ((0,), (), 0, 1), "duplicate": ((0, 0), (1, 1), 0, 1),
        "negative_index": ((-1,), (1,), 0, 1), "large_index": ((1,), (1,), 0, 1),
        "boolean_index": ((True,), (1,), 0, 1), "float_coefficient": ((0,), (1.5,), 0, 1),
        "boolean_coefficient": ((0,), (True,), 0, 1), "bad_interval": ((0,), (1,), 2, 1),
        "float_bound": ((0,), (1,), 0.5, 1), "boolean_bound": ((0,), (1,), False, 1),
    }.items():
        damages[label] = rejected(lambda row=row: subject.exact_certificate([row], 1, [1.0]))
    for label, weights in {"missing_weight": [], "nan": [float("nan")],
                           "infinity": [float("inf")]}.items():
        damages[label] = rejected(lambda w=weights: subject.exact_certificate(feasible, 1, w))
    damages["weight_toward_infinity"] = rejected(
        lambda: subject.exact_certificate([((0,), (1,), 1, None)], 1, [-1.0]))
    partial_rows = [((0,), (1,), None, 0), ((0,), (1,), 1, 1)]
    partial = subject.solve_lp(partial_rows, 1, 2, phase_one=True, soft_rows=[1])
    assert partial["status"] == 0 and partial["objective"] == 1
    partial_certificate = subject.exact_certificate(partial_rows, 1, partial["weights"])
    assert check_certificate(partial_rows, 1, partial_certificate)["proves_infeasible"]
    for indices in [[-1], [2], [True], [0.5], [1, 1]]:
        damages[f"soft_rows_{indices!r}"] = rejected(lambda indices=indices: subject.solve_lp(
            partial_rows, 1, 2, phase_one=True, soft_rows=indices))
    damages["soft_rows_without_phase_one"] = rejected(
        lambda: subject.solve_lp(partial_rows, 1, 2, soft_rows=[1]))
    rows, width, certificate = positive
    for name, mutate in {
        "rhs": lambda c: c.update(rhs_numerator=c["rhs_numerator"] + 1),
        "box": lambda c: c.update(box_max_numerator=c["box_max_numerator"] + 1),
        "gap": lambda c: c.update(gap=[99, 1]),
        "claim": lambda c: c.update(proves_infeasible=False),
        "width": lambda c: c.update(checked_columns=2),
        "denominator": lambda c: c.update(denominator=-1),
        "boolean_width": lambda c: c.update(checked_columns=True),
        "float_rhs": lambda c: c.update(rhs_numerator=float(c["rhs_numerator"])),
        "boolean_gap": lambda c: c.update(gap=[True, True]),
        "duplicate_weight": lambda c: c["weights"].append(c["weights"][0]),
        "wrong_weight": lambda c: c["weights"][0].__setitem__(1, 1),
    }.items():
        damaged = copy.deepcopy(certificate)
        mutate(damaged)
        damages[f"certificate_{name}"] = rejected(
            lambda c=damaged: check_certificate(rows, width, c))
    rng = random.Random(2026100368)
    for _ in range(100):
        point = [Fraction(rng.randrange(3), 2) for _ in range(3)]
        rows = []
        for _ in range(6):
            values = tuple(rng.randint(-3, 3) for _ in range(3))
            exact = sum(c * x for c, x in zip(values, point, strict=True))
            rows.append(((0, 1, 2), values, math.floor(exact) - rng.randrange(3),
                         math.ceil(exact) + rng.randrange(3)))
        certificate = subject.exact_certificate(rows, 3, [rng.randint(-10, 10) for _ in rows], 1)
        assert not check_certificate(rows, 3, certificate)["proves_infeasible"]
    result = {"scope": __doc__, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "controls_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(
                  Path(__file__).with_name("check.py").read_bytes()).hexdigest(),
              "toys": toys, "damaged_controls": damages,
              "partial_soft_phase": {"lp": partial, "certificate": partial_certificate},
              "known_feasible_rational_models": 100, "random_seed": 2026100368}
    output = args.output
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"toys": len(toys), "damaged_controls": len(damages),
                      "known_feasible_rational_models": 100}))


if __name__ == "__main__":
    main()
