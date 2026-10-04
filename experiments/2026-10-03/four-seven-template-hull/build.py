# Document:    Full Surviving Heavy-Link Hull Sparse LP Prototype
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      42810d396774d55506d8878308192317e5c9c6bac47433eb8887374df65b1106
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import collections
import gzip
import hashlib
import itertools
import json
import subprocess
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ORBIT_DIR = HERE.parent / "four-seven-link-orbits"
SCREEN = REPO / "experiments/scratch/four-seven-link-lp-full"
ANCHORS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def write_gzip(path, value):
    path.write_bytes(
        gzip.compress((json.dumps(value, separators=(",", ":")) + "\n").encode(), mtime=0)
    )


def graph(case):
    return {
        frozenset(e)
        for e in (((0, 1), (1, 2), (2, 3), (0, 3)) if case == "cycle" else ((0, 1), (2, 3)))
    }


def automorphisms(case):
    edges = graph(case)
    result = [
        p
        for p in itertools.permutations(range(4))
        if {frozenset((p[a], p[b])) for a, b in map(tuple, edges)} == edges
    ]
    require(len(result) == 8, "hub graph order")
    return result


def point_permutation(groups):
    return tuple(4 * groups[g] + offset + 1 for g in range(4) for offset in range(4))


def transform(edges, points):
    return tuple(sorted(tuple(sorted(points[p - 1] for p in edge)) for edge in edges))


def allowed_edges(target):
    return [
        e
        for e in itertools.combinations([p for p in range(1, 17) if p not in ANCHORS[target]], 2)
        if not ((e[0] - 1) // 4 == (e[1] - 1) // 4 and e[0] % 4 and e[1] % 4)
    ]


def validate_link(link, group):
    require(len(link) == len(set(link)) == 7 and tuple(sorted(link)) == link, "bad link shape")
    require(set(link) <= set(allowed_edges(group)), "bad link edge")
    degrees = collections.Counter(p for edge in link for p in edge)
    hub = 4 * group + 4
    require(
        all(degrees[p] == (2 if p == hub else 1) for p in range(1, 17) if p not in ANCHORS[group]),
        "bad link degrees",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output directory must be new")
    representatives_path = ORBIT_DIR / "result.json"
    orbit_path = ORBIT_DIR / "relabelings.json.gz"
    orbit_audit_path = ORBIT_DIR / "independent-result.json"
    lp_audit_path = HERE.parent / "four-seven-link-lp-independent/full-v1.1.0-final-audit.json"
    orbit_audit = json.loads(orbit_audit_path.read_text())
    lp_audit = json.loads(lp_audit_path.read_text())
    screen_metadata = json.loads((SCREEN / "metadata.json").read_text())
    require(
        orbit_audit["complete"] is True
        and orbit_audit["archive_sha256"] == digest(orbit_path)
        and orbit_audit["metadata_sha256"] == digest(representatives_path),
        "orbit audit mismatch",
    )
    require(
        lp_audit["complete_selected_coverage"] is True
        and lp_audit["records"] == 258
        and lp_audit["expected_records"] == 258
        and lp_audit["excluded"] == 100
        and lp_audit["results_sha256"] == digest(SCREEN / "results.json.gz"),
        "LP audit mismatch",
    )
    checked = {r["id"]: r for r in lp_audit["checks"]}
    require(len(checked) == 258, "duplicate certificate record")
    representatives = {c["case"]: c for c in json.loads(representatives_path.read_text())["cases"]}
    orbit_cases = {c["case"]: c for c in load_gzip(orbit_path)}
    blocks = list(itertools.combinations(range(1, 17), 5))
    block_ids = {b: i for i, b in enumerate(blocks)}
    args.output.mkdir(parents=True)
    source = args.output / "build.py"
    source.write_bytes(Path(__file__).read_bytes())
    manifest = dict(
        source_sha256=digest(source),
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        inputs={
            str(p.relative_to(REPO)): digest(p)
            for p in (
                representatives_path,
                orbit_path,
                orbit_audit_path,
                lp_audit_path,
                SCREEN / "results.json.gz",
                SCREEN / "metadata.json",
            )
        },
        cases=[],
        scope="Sparse LP construction only; no solve. Each heavy link lies in the complete convex "
        "hull of all labeled templates not excluded by the original 100 checked certificates.",
    )
    for case in ("cycle", "matching"):
        destination = args.output / case
        destination.mkdir()
        reps = {r["id"]: r for r in representatives[case]["representatives"]}
        require(set(reps) == {r["id"] for r in orbit_cases[case]["orbits"]}, "orbit IDs")
        surviving = {}
        rejected = []
        for orbit in orbit_cases[case]["orbits"]:
            identifier = orbit["id"]
            certificate = checked[identifier]
            require(certificate["case"] == case, "certificate case")
            require(len(orbit["maps"]) == reps[identifier]["orbit_size"], "orbit cardinality")
            if certificate["proves_infeasible"]:
                require(Fraction(*certificate["gap"]) > 0, "exclusion lacks positive gap")
                rejected.append(identifier)
                continue
            for record in orbit["maps"]:
                link = tuple(tuple(e) for e in record["edges"])
                validate_link(link, 0)
                require(link not in surviving, "duplicate surviving link")
                surviving[link] = identifier
        links = sorted(surviving)
        count = len(links)
        require(count == (25020 if case == "cycle" else 14202), "surviving labeled count")
        require(len(rejected) == (27 if case == "cycle" else 73), "excluded orbit count")
        catalog = dict(
            case=case,
            template_count=count,
            ordering="lexicographic base-group edge tuples",
            templates=[
                dict(index=i, edges=link, representative_id=surviving[link])
                for i, link in enumerate(links)
            ],
        )
        write_gzip(destination / "base-catalog.json.gz", catalog)
        base_path = SCREEN / f"{case}-rows.json.gz"
        require(
            digest(base_path) == screen_metadata["models"][case]["rows_sha256"], "base rows hash"
        )
        base = load_gzip(base_path)
        require(base["width"] == 4768 and len(base["rows"]) == 4270, "base dimensions")
        rows = base["rows"].copy()
        transforms = []
        descriptions = []
        all_autos = automorphisms(case)
        block_columns = set()
        lambda_use = collections.Counter()
        for target in range(4):
            choices = [p for p in all_autos if p[0] == target]
            require(len(choices) == 2, "group transitivity")
            chosen = min(choices)
            points = point_permutation(chosen)
            inverse = tuple(points.index(p) + 1 for p in range(1, 17))
            transported = [transform(link, points) for link in links]
            require(len(set(transported)) == count, "transport not injective")
            require(
                all(
                    transform(link, inverse) == original
                    for link, original in zip(transported, links, strict=True)
                ),
                "inverse transport",
            )
            for alternative in choices:
                require(
                    {transform(link, point_permutation(alternative)) for link in links}
                    == set(transported),
                    "catalog depends on chosen group automorphism",
                )
            offset = 4768 + target * count
            row_index = len(rows)
            rows.append([list(range(offset, offset + count)), [1] * count, 1, 1])
            descriptions.append(dict(row=row_index, kind="template_simplex", group=target))
            incidence = {e: [] for e in allowed_edges(target)}
            require(len(incidence) == 69, "heavy block marginal count")
            for i, link in enumerate(transported):
                validate_link(link, target)
                for edge in link:
                    incidence[edge].append(offset + i)
                    lambda_use[offset + i] += 1
            for edge in sorted(
                incidence, key=lambda e: block_ids[tuple(sorted((*ANCHORS[target], *e)))]
            ):
                index = block_ids[tuple(sorted((*ANCHORS[target], *edge)))]
                require(index not in block_columns, "heavy blocks shared between groups")
                block_columns.add(index)
                row_index = len(rows)
                rows.append([[index, *incidence[edge]], [1, *([-1] * len(incidence[edge]))], 0, 0])
                descriptions.append(
                    dict(
                        row=row_index,
                        kind="heavy_block_marginal",
                        group=target,
                        block_index=index,
                        outside_edge=edge,
                    )
                )
            transforms.append(
                dict(
                    group_index=target,
                    anchor_triple=ANCHORS[target],
                    group_permutation=chosen,
                    point_permutation=points,
                    inverse_point_permutation=inverse,
                    template_count=count,
                    lambda_start=offset,
                    lambda_stop_exclusive=offset + count,
                )
            )
        extension = rows[4270:]
        require(len(extension) == 280 and len(block_columns) == 276, "extension row counts")
        require(
            len(lambda_use) == 4 * count and set(lambda_use.values()) == {7}, "one-hot incidence"
        )
        require(
            sum(len(row[0]) for row in extension) == 32 * count + 276, "sparse coefficient count"
        )
        require(rows[:4270] == base["rows"], "base rows changed")
        payload = dict(
            width=4768 + 4 * count,
            base_width=4768,
            base_rows=4270,
            variable_bounds="Every variable has bounds [0,1]; all are continuous in this LP.",
            rows=rows,
            transports=transforms,
            extension_rows=descriptions,
        )
        write_gzip(destination / "extended-rows.json.gz", payload)
        record = dict(
            case=case,
            surviving_orbits=129 - len(rejected),
            templates_per_group=count,
            excluded_orbit_ids=rejected,
            new_variables=4 * count,
            total_variables=payload["width"],
            new_rows=280,
            total_rows=len(rows),
            extension_nonzeros=32 * count + 276,
            base_nonzeros=sum(len(row[0]) for row in base["rows"]),
            transported_catalogs_independent_of_map=True,
            base_rows_sha256=digest(base_path),
            catalog_sha256=digest(destination / "base-catalog.json.gz"),
            extended_rows_sha256=digest(destination / "extended-rows.json.gz"),
            row_semantics="One simplex equality per group; x_(A_i union e) equals the sum "
            "of all group-i template weights containing edge e, for each of 69 allowed edges.",
        )
        manifest["cases"].append(record)
        print(json.dumps(record), flush=True)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (HERE / "prototype-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
