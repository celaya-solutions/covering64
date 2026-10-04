# Document:    108-Exclusion Template-Hull Refinement Builder
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      f7df431432258a56c196bd0938e1d93c68dcca058a873e72d464db245f5d5266
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Create new catalogs/matrices by removing only independently checked orbit IDs."""

import argparse
import copy
import gzip
import hashlib
import itertools
import json
import subprocess
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ORIGINAL = REPO / "experiments/scratch/four-seven-template-hull-refresh-106-20261003"
ORIGINAL_MANIFEST_SHA256 = "84183ee44ed2916ffd18d64b5f113774e4eda47bad5e82c6c79b1b3a64db5bdf"
EXCLUSION_UNION_SHA256 = "2809b2f39fac1971ca6bf3997e789a4a41463b62394e7525e5d282d084527f88"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def save(path, value):
    data = (json.dumps(value, separators=(",", ":")) + "\n").encode()
    path.write_bytes(gzip.compress(data, mtime=0))


def relabel(edges, points):
    return tuple(sorted(tuple(sorted((points[a - 1], points[b - 1]))) for a, b in edges))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exclusions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "new output directory required")
    require(digest(ORIGINAL / "manifest.json") == ORIGINAL_MANIFEST_SHA256, "original manifest")
    original_manifest = load(ORIGINAL / "manifest.json")
    require(digest(args.exclusions) == EXCLUSION_UNION_SHA256, "frozen checked union")
    registry = load(args.exclusions)
    excluded = sorted(registry["proof_sources"])
    require(
        len(excluded) == registry["excluded_count"] == 108,
        "unique sorted checked exclusions",
    )
    require(registry["passed"] is True, "checked exclusion registry required")
    evidence_hashes = {}
    for identifier, sources in registry["proof_sources"].items():
        require(sources, "exclusion needs checked evidence")
        for relative in sources:
            path = HERE.parent / relative
            proof = load(path)
            evidence_hashes[str(path.relative_to(REPO))] = digest(path)
            if "checks" in proof:
                record = next(c for c in proof["checks"] if c["id"] == identifier)
                valid = (
                    record["proves_infeasible"] is True
                    and record["gap"][0] > 0
                    and record["gap"][1] > 0
                )
            elif "fully_excluded_ids" in proof:
                valid = proof["passed"] is True and identifier in proof["fully_excluded_ids"]
            else:
                valid = (
                    proof["passed"] is True
                    and proof["representative"] == identifier
                    and (
                        proof.get("proves_infeasible") is True
                        or proof.get("fully_excluded") is True
                    )
                )
            require(valid, f"checked proof missing for {identifier}")
    started = time.monotonic()
    args.output.mkdir(parents=True)
    (args.output / "build.py").write_bytes(Path(__file__).read_bytes())
    (args.output / "exclusions.json").write_bytes(args.exclusions.read_bytes())
    manifest = dict(
        source_sha256=digest(Path(__file__)),
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        previous_manifest_sha256=ORIGINAL_MANIFEST_SHA256,
        previous_exclusion_count=original_manifest["exclusion_count"],
        exclusion_registry_sha256=digest(args.exclusions),
        exclusion_count=len(excluded),
        evidence_hashes=evidence_hashes,
        cases=[],
        scope="New complete surviving-template hull after removing only "
        "the checked orbit union. Original catalogs and matrices remain immutable. "
        "No solve or global lower-bound claim.",
    )
    for previous in original_manifest["cases"]:
        case = previous["case"]
        old_directory = ORIGINAL / case
        require(
            digest(old_directory / "base-catalog.json.gz") == previous["catalog_sha256"],
            "original catalog hash",
        )
        require(
            digest(old_directory / "extended-rows.json.gz") == previous["matrix_sha256"],
            "original matrix hash",
        )
        original_catalog = load(old_directory / "base-catalog.json.gz")
        original_matrix = load(old_directory / "extended-rows.json.gz")
        retained = [
            entry
            for entry in original_catalog["templates"]
            if entry["representative_id"] not in excluded
        ]
        removed = [
            entry
            for entry in original_catalog["templates"]
            if entry["representative_id"] in excluded
        ]
        require(
            len(retained) + len(removed) == previous["templates_per_group"], "catalog partition"
        )
        old_n, new_n = len(original_catalog["templates"]), len(retained)
        catalog = copy.deepcopy(original_catalog)
        catalog["template_count"] = new_n
        catalog["templates"] = [{**entry, "index": i} for i, entry in enumerate(retained)]
        require(
            [tuple(map(tuple, e["edges"])) for e in catalog["templates"]]
            == sorted(tuple(map(tuple, e["edges"])) for e in catalog["templates"]),
            "lexicographic survivor order",
        )
        remap = {i: i for i in range(4768)}
        for group in range(4):
            for index, entry in enumerate(retained):
                remap[4768 + group * old_n + entry["index"]] = 4768 + group * new_n + index
        matrix = copy.deepcopy(original_matrix)
        matrix["width"] = 4768 + 4 * new_n
        matrix["rows"] = []
        for ids, coefficients, lower, upper in original_matrix["rows"]:
            terms = [(remap[i], c) for i, c in zip(ids, coefficients, strict=True) if i in remap]
            matrix["rows"].append([[i for i, _ in terms], [c for _, c in terms], lower, upper])
        require(matrix["rows"][:4270] == original_matrix["rows"][:4270], "original base rows")
        require(len(matrix["rows"]) == 4550 and matrix["base_width"] == 4768, "dimensions")
        graph = {(0, 1), (1, 2), (2, 3), (0, 3)} if case == "cycle" else {(0, 1), (2, 3)}
        automorphisms = [
            p
            for p in itertools.permutations(range(4))
            if {tuple(sorted((p[a], p[b]))) for a, b in graph} == graph
        ]
        require(len(automorphisms) == 8, "hub graph automorphisms")
        group_catalogs, transport_checks = [], []
        links = [entry["edges"] for entry in catalog["templates"]]
        for group, transport in enumerate(matrix["transports"]):
            transport["template_count"] = new_n
            transport["lambda_start"] = 4768 + group * new_n
            transport["lambda_stop_exclusive"] = 4768 + (group + 1) * new_n
            points, inverse = transport["point_permutation"], transport["inverse_point_permutation"]
            transported = [relabel(edges, points) for edges in links]
            require(len(set(transported)) == new_n, "injective complete transport")
            require(
                all(
                    relabel(edges, inverse) == tuple(map(tuple, original))
                    for edges, original in zip(transported, links, strict=True)
                ),
                "inverse transport",
            )
            alternatives = [p for p in automorphisms if p[0] == group]
            require(len(alternatives) == 2, "transitive hub groups")
            for groups in alternatives:
                alternative = [4 * groups[p // 4] + p % 4 + 1 for p in range(16)]
                require(
                    {relabel(edges, alternative) for edges in links} == set(transported),
                    "survivors depend on chosen automorphism",
                )
            group_catalogs.append(
                dict(
                    group=group,
                    point_permutation=points,
                    inverse_point_permutation=inverse,
                    templates=transported,
                )
            )
            transport_checks.append(
                dict(
                    group=group,
                    templates=new_n,
                    alternative_maps=2,
                    forward_inverse_checks=new_n,
                    complete=True,
                )
            )
        counts = Counter(i for row in matrix["rows"][4270:] for i in row[0] if i >= 4768)
        require(
            len(counts) == 4 * new_n and set(counts.values()) == {8}, "simplex plus seven marginals"
        )
        destination = args.output / case
        destination.mkdir()
        if not removed:
            for name in ("base-catalog.json.gz", "extended-rows.json.gz"):
                (destination / name).write_bytes((old_directory / name).read_bytes())
        else:
            save(destination / "base-catalog.json.gz", catalog)
            save(destination / "extended-rows.json.gz", matrix)
        save(destination / "group-catalogs.json.gz", group_catalogs)
        manifest["cases"].append(
            dict(
                case=case,
                previous_templates_per_group=old_n,
                templates_per_group=new_n,
                removed_templates_per_group=len(removed),
                removed_by_representative=dict(
                    sorted(Counter(e["representative_id"] for e in removed).items())
                ),
                surviving_orbits=len({e["representative_id"] for e in retained}),
                excluded_orbit_ids=[i for i in excluded if i.startswith(case + "-")],
                total_variables=matrix["width"],
                total_rows=4550,
                base_rows_preserved=4270,
                base_columns_preserved=4768,
                extension_nonzeros=sum(len(row[0]) for row in matrix["rows"][4270:]),
                original_catalog_sha256=previous["catalog_sha256"],
                original_matrix_sha256=previous["matrix_sha256"],
                catalog_sha256=digest(destination / "base-catalog.json.gz"),
                matrix_sha256=digest(destination / "extended-rows.json.gz"),
                group_catalogs_sha256=digest(destination / "group-catalogs.json.gz"),
                transport_checks=transport_checks,
            )
        )
        print(json.dumps(manifest["cases"][-1]), flush=True)
    manifest["build_seconds"] = time.monotonic() - started
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
