# Document:    Independent Integer Double Triple Pattern Checker
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      25f3058fdaf6a411ba0cc4aab0703f0fa35654940414e8caf3891e52aadc9ca9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import collections
import hashlib
import itertools
import json
import pathlib
import subprocess
import sys

from covering64.core import verify_cover

GROUPS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
HUBS = (4, 8, 12, 16)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse(raw):
    rows = [tuple(map(int, line.split())) for line in raw.splitlines()]
    require(len(rows) == len(set(rows)) == 44, "requires44distinct triples")
    require(
        all(
            len(t) == 3
            and len(set(t)) == 3
            and tuple(sorted(t)) == t
            and min(t) >= 1
            and max(t) <= 16
            for t in rows
        ),
        "malformed triple",
    )
    return rows


def check(rows, case):
    require(
        all(all(len(set(t) & set(group)) <= 1 for group in GROUPS) for t in rows),
        "two anchors from one group",
    )
    demands = dict.fromkeys(itertools.combinations(range(1, 17), 2), 1)
    for group, hub in zip(GROUPS, HUBS, strict=True):
        for pair in itertools.combinations(group, 2):
            demands[pair] = 0
        for anchor in group:
            demands[tuple(sorted((anchor, hub)))] = 2
    edges = [(4, 8), (8, 12), (12, 16), (4, 16)] if case == "cycle" else [(4, 8), (12, 16)]
    for pair in edges:
        demands[pair] = 4 if case == "cycle" else 7
    counts = collections.Counter(pair for t in rows for pair in itertools.combinations(t, 2))
    require(all(counts[p] == required for p, required in demands.items()), "pair demand mismatch")
    degrees = collections.Counter(point for t in rows for point in t)
    require(all(degrees[p] == (12 if p in HUBS else 7) for p in range(1, 17)), "degree identity")
    classes = collections.Counter(sum(p not in HUBS for p in t) for t in rows)
    z = classes[0]
    require(
        z in (0, 1, 2)
        and [classes[i] for i in range(4)] == [z, 18 - 3 * z, 12 + 3 * z, 14 - z],
        "anchor-count identity",
    )
    return dict(
        pair_demands=[dict(pair=p, required=d, actual=counts[p]) for p, d in demands.items()],
        point_degrees=dict(sorted(degrees.items())),
        triples_by_anchor_count=dict(classes),
        all_hub_triples=z,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=("cycle", "matching"))
    parser.add_argument("witness", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    rows = parse(args.witness.read_text())
    report = check(rows, args.case)
    package = verify_cover(rows, v=16, k=3, t=2)
    process = subprocess.run(
        [
            sys.executable,
            "scripts/check_cover.py",
            str(args.witness),
            "--v",
            "16",
            "--k",
            "3",
            "--t",
            "2",
            "--expected-blocks",
            "44",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    standalone = json.loads(process.stdout)
    expected_missing = sorted(pair for group in GROUPS for pair in itertools.combinations(group, 2))
    require(
        process.returncode == 1 and not package["valid"] and not standalone["valid"],
        "expected internal-pair holes",
    )
    require(
        [list(p) for p in expected_missing]
        == standalone["uncovered"]
        == [list(p) for p in package["uncovered"]],
        "pair coverage report mismatch",
    )
    require(
        package["canonical_sha256"] == standalone["canonical_sha256"], "canonical hash mismatch"
    )
    controls = []
    for name, broken in [
        ("duplicate", [*rows[:-1], rows[0]]),
        ("repeated label", [(1, 1, 2), *rows[1:]]),
        ("outside label", [(0, 1, 2), *rows[1:]]),
    ]:
        try:
            parse("".join(" ".join(map(str, t)) + "\n" for t in broken))
        except ValueError:
            controls.append(dict(control=name, rejected=True))
        else:
            raise ValueError("malformed pattern accepted")
    try:
        check(rows, "matching" if args.case == "cycle" else "cycle")
    except ValueError:
        controls.append(dict(control="wrong hub case", rejected=True))
    else:
        raise ValueError("wrong-case pattern accepted")
    report.update(
        complete=True,
        valid_double_pattern=True,
        case=args.case,
        distinct_triples=44,
        package_pair_check=package,
        standalone_pair_check=standalone,
        witness_sha256=hashlib.sha256(args.witness.read_bytes()).hexdigest(),
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        damaged_controls=controls,
        scope="Integer solution of the necessary44-double-triple system; not a64-block cover.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                case=args.case,
                valid_double_pattern=True,
                triples=44,
                all_hub_triples=z if (z := report["all_hub_triples"]) else 0,
            )
        )
    )


if __name__ == "__main__":
    main()
