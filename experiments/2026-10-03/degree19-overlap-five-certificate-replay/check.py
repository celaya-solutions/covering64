# Document:    Independent Overlap-Five Pilot Certificate Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      38f285f73220f28bf440d343b8e7bcee9f34abe8ba121653c4a4ed65fc6ba44d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay an integer row-combination contradiction over a unit variable box."""

import argparse
import copy
import gzip
import hashlib
import json
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(matrix, certificate):
    width = matrix["width"]
    require(type(width) is int and width == 4368, "variable width")
    rows = matrix["rows"]
    for ids, coefs, lower, upper in rows:
        require(len(ids) == len(coefs) and ids == sorted(set(ids)), "row shape")
        require(all(type(i) is int and 0 <= i < width for i in ids), "variable IDs")
        require(all(type(c) is int and c != 0 for c in coefs), "integer coefficients")
        require(all(v is None or type(v) is int for v in (lower, upper)), "row bounds")
        require(lower is None or upper is None or lower <= upper, "ordered row bounds")
    denominator = certificate["denominator"]
    require(type(denominator) is int and denominator > 0, "denominator")
    weights = certificate["weights"]
    ids = [i for i, weight in weights]
    require(ids == sorted(set(ids)), "unique sorted row weights")
    vector = [0] * width
    rhs = 0
    for i, weight in weights:
        require(type(i) is int and 0 <= i < len(rows), "weight row ID")
        require(type(weight) is int and weight != 0, "integer nonzero weight")
        indices, coefficients, lower, upper = rows[i]
        bound = lower if weight > 0 else upper
        require(bound is not None, "weight has a finite implied lower bound")
        rhs += weight * bound
        for j, coefficient in zip(indices, coefficients, strict=True):
            vector[j] += weight * coefficient
    box_maximum = sum(max(0, coefficient) for coefficient in vector)
    gap = Fraction(rhs - box_maximum, denominator)
    require(certificate["checked_columns"] == width, "reported columns")
    require(certificate["rhs_numerator"] == rhs, "reported combined bound")
    require(certificate["box_max_numerator"] == box_maximum, "reported box maximum")
    require(certificate["gap"] == [gap.numerator, gap.denominator], "reported reduced gap")
    require(certificate["proves_infeasible"] is True and gap > 0, "positive exact gap")
    return dict(
        checked_columns=width,
        checked_rows=len(rows),
        nonzero_row_weights=len(weights),
        rhs_numerator=rhs,
        box_max_numerator=box_maximum,
        exact_gap=[gap.numerator, gap.denominator],
        combined_vector_sha256=hashlib.sha256(
            json.dumps(vector, separators=(",", ":")).encode()
        ).hexdigest(),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    matrix_path = args.pilot / "lp-rows.json.gz"
    certificate_path = args.pilot / "certificate.json"
    matrix = json.loads(gzip.decompress(matrix_path.read_bytes()))
    certificate = json.loads(certificate_path.read_text())
    checked = replay(matrix, certificate)
    damaged = []
    for name, mutation in (
        ("changed reported gap", lambda c: c.__setitem__("gap", [1, 1])),
        ("duplicate row weight", lambda c: c["weights"].append(c["weights"][0])),
        ("invalid row ID", lambda c: c["weights"][0].__setitem__(0, len(matrix["rows"]))),
        ("changed weighted bound", lambda c: c.__setitem__("rhs_numerator", 0)),
        ("changed box maximum", lambda c: c.__setitem__("box_max_numerator", 0)),
        ("changed denominator", lambda c: c.__setitem__("denominator", 0)),
    ):
        broken = copy.deepcopy(certificate)
        mutation(broken)
        try:
            replay(matrix, broken)
        except ValueError:
            damaged.append(dict(control=name, rejected=True))
        else:
            raise ValueError(f"accepted damaged control: {name}")
    broken_matrix = copy.deepcopy(matrix)
    index = certificate["weights"][0][0]
    broken_matrix["rows"][index][1][0] += 1
    try:
        replay(broken_matrix, certificate)
    except ValueError:
        damaged.append(dict(control="changed matrix coefficient", rejected=True))
    else:
        raise ValueError("accepted damaged matrix coefficient")
    report = dict(
        valid=True,
        pilot=args.pilot.name,
        checker_sha256=digest(Path(__file__)),
        matrix_sha256=digest(matrix_path),
        certificate_sha256=digest(certificate_path),
        variable_domains="All 4368 variables lie in [0,1].",
        replay=checked,
        damaged_controls=damaged,
        scope="Exact contradiction for the supplied independently audited overlap-five pilot "
        "matrix only. This replay does not prove the exhaustiveness of pilot selection "
        "or independently reconstruct its branch reduction.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
