# Document:    Independent 108-Exclusion Heavy-Link Hull Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      70a3eb99bb77a03ae69abbf1e102ae4632616bc39b7085a73d8ca612aa044d8c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Re-enumerate complete survivors and reconstruct every transported hull row."""

import copy
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations, permutations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORIGINAL = ROOT / "experiments/scratch/four-seven-template-hull-refresh-106-20261003"
RAW = ROOT / "experiments/scratch/four-seven-template-hull-refresh-108-20261003"


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edge_key(edges):
    return tuple(sorted(tuple(sorted(edge)) for edge in edges))


def check_case(case, catalog, matrix, groups, complete, excluded, old_matrix):
    expected = {}
    for orbit in complete["orbits"]:
        if orbit["id"] not in excluded:
            for mapping in orbit["maps"]:
                key = edge_key(mapping["edges"])
                require(key not in expected, "duplicate complete source link")
                expected[key] = orbit["id"]
    templates = catalog["templates"]
    n = len(expected)
    require(catalog["template_count"] == len(templates) == n, "catalog length")
    require([entry["index"] for entry in templates] == list(range(n)), "catalog indexing")
    actual = [(edge_key(entry["edges"]), entry["representative_id"]) for entry in templates]
    require(actual == sorted(expected.items()), "catalog differs from complete surviving orbits")
    require(matrix["rows"][:4270] == old_matrix["rows"][:4270], "base rows changed")
    require(matrix["base_width"] == 4768 and matrix["base_rows"] == 4270, "base dimensions")
    require(matrix["width"] == 4768 + 4 * n and len(matrix["rows"]) == 4550, "dimensions")
    require(matrix["variable_bounds"] == old_matrix["variable_bounds"], "unit boxes changed")
    require(len(matrix["transports"]) == len(groups) == 4, "four complete transports")
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    ids = {block: i for i, block in enumerate(combinations(range(1, 17), 5))}
    graph = ({(0, 1), (1, 2), (2, 3), (0, 3)} if case == "cycle" else {(0, 1), (2, 3)})
    automorphisms = [p for p in permutations(range(4))
                     if {tuple(sorted((p[a], p[b]))) for a, b in graph} == graph]
    require(len(automorphisms) == 8, "hub graph automorphism count")
    rows = []
    for group, transport in enumerate(matrix["transports"]):
        perm = transport["point_permutation"]
        inverse = transport["inverse_point_permutation"]
        prior = old_matrix["transports"][group]
        require(perm == prior["point_permutation"] and
                inverse == prior["inverse_point_permutation"], "changed audited transport")
        require(sorted(perm) == sorted(inverse) == list(range(1, 17)), "nonbijective map")
        require(all(inverse[perm[p - 1] - 1] == p for p in range(1, 17)), "inverse map")
        start = 4768 + group * n
        require(transport["group_index"] == group and transport["template_count"] == n,
                "transport metadata")
        require((transport["lambda_start"], transport["lambda_stop_exclusive"]) ==
                (start, start + n), "template column interval")
        transformed = [edge_key((perm[a - 1], perm[b - 1]) for a, b in key)
                       for key, _ in actual]
        require(len(set(transformed)) == n, "transport lost templates")
        saved = groups[group]
        require(saved["group"] == group and saved["point_permutation"] == perm and
                saved["inverse_point_permutation"] == inverse, "group catalog map")
        require([edge_key(edges) for edges in saved["templates"]] == transformed,
                "group catalog contents")
        for edges, (original, _) in zip(transformed, actual, strict=True):
            require(edge_key((inverse[a - 1], inverse[b - 1]) for a, b in edges) == original,
                    "round trip changed a template")
        alternatives = [p for p in automorphisms if p[0] == group]
        require(len(alternatives) == 2, "alternative map coverage")
        for gp in alternatives:
            p = [4 * gp[(point - 1) // 4] + (point - 1) % 4 + 1 for point in range(1, 17)]
            alternative = {edge_key((p[a - 1], p[b - 1]) for a, b in key) for key, _ in actual}
            require(alternative == set(transformed), "survivors depend on transport choice")
        rows.append([list(range(start, start + n)), [1] * n, 1, 1])
        incidences = defaultdict(list)
        for index, edges in enumerate(transformed):
            for edge in edges:
                incidences[edge].append(start + index)
        outside = set(range(1, 17)) - anchors[group]
        allowed = [edge for edge in combinations(sorted(outside), 2)
                   if not any(set(edge) <= anchor for anchor in anchors)]
        require(len(allowed) == 69 and set(incidences) <= set(allowed), "illegal heavy edge")
        for edge in allowed:
            block = ids[tuple(sorted(anchors[group] | set(edge)))]
            rows.append([[block, *incidences[edge]], [1, *([-1] * len(incidences[edge]))], 0, 0])
    require(matrix["rows"][4270:] == rows, "simplex or marginal row differs")
    return {"case": case, "passed": True, "templates_per_group": n,
            "complete_transported_catalogs": 4, "alternative_maps_checked": 8,
            "base_rows_preserved": 4270, "hull_rows_reconstructed": len(rows),
            "columns": matrix["width"]}


def main():
    manifest = load(HERE / "manifest.json")
    require(manifest == load(RAW / "manifest.json"), "frozen manifest mismatch")
    require(sha(HERE / "build.py") == sha(RAW / "build.py") == manifest["source_sha256"],
            "builder snapshot mismatch")
    original_audit = load(HERE.parent / "four-seven-template-hull-refresh/independent-audit.json")
    require(original_audit["passed"] and original_audit["manifest_sha256"] ==
            sha(ORIGINAL / "manifest.json") == manifest["previous_manifest_sha256"],
            "original encoding audit missing")
    registry = load(RAW / "exclusions.json")
    require(sha(RAW / "exclusions.json") == manifest["exclusion_registry_sha256"] and
            registry["passed"] and registry["excluded_count"] == 108, "exclusion registry")
    excluded = set()
    for relative, digest in manifest["evidence_hashes"].items():
        path = ROOT / relative
        require(sha(path) == digest, "changed proof evidence")
        proof = load(path)
        if "checks" in proof:
            require(proof["complete_selected_coverage"], "incomplete original screen")
            excluded.update(row["id"] for row in proof["checks"]
                            if row["proves_infeasible"] and row["gap"][0] > 0)
        elif "fully_excluded_ids" in proof:
            require(proof["passed"], "failed hub intersection")
            excluded.update(proof["fully_excluded_ids"])
        else:
            require(proof["passed"] and (proof.get("fully_excluded") or
                    proof.get("proves_infeasible")), "failed single proof")
            excluded.add(proof["representative"])
    require(len(excluded) == 108 and excluded == set(registry["proof_sources"]),
            "registry differs from complete union of checked sources")
    complete = load(HERE.parent / "four-seven-link-orbits/relabelings.json.gz")
    reports, controls = [], []
    for data in manifest["cases"]:
        case = data["case"]
        folder = RAW / case
        for filename, key in (("base-catalog.json.gz", "catalog_sha256"),
                              ("extended-rows.json.gz", "matrix_sha256"),
                              ("group-catalogs.json.gz", "group_catalogs_sha256")):
            require(sha(folder / filename) == data[key], "refreshed artifact hash")
        catalog, matrix, groups = [load(folder / name) for name in
                                   ("base-catalog.json.gz", "extended-rows.json.gz",
                                    "group-catalogs.json.gz")]
        old_matrix = load(ORIGINAL / case / "extended-rows.json.gz")
        old_catalog = load(ORIGINAL / case / "base-catalog.json.gz")
        prior = next(r for r in original_audit["cases"] if r["case"] == case)
        require(prior["passed"] and sha(ORIGINAL / case / "extended-rows.json.gz") ==
                prior["matrix_sha256"], "original matrix disconnected from audit")
        case_complete = next(item for item in complete if item["case"] == case)
        report = check_case(case, catalog, matrix, groups, case_complete, excluded, old_matrix)
        removed = Counter(t["representative_id"] for t in old_catalog["templates"]
                          if t["representative_id"] in excluded)
        require(data["removed_by_representative"] == dict(removed), "removal inventory")
        require(data["excluded_orbit_ids"] == sorted(i for i in excluded if i.startswith(case)),
                "excluded orbit metadata")
        require(data["templates_per_group"] == report["templates_per_group"] and
                data["total_variables"] == report["columns"], "manifest dimensions")
        report.update({key: data[key] for key in
                       ("catalog_sha256", "matrix_sha256", "group_catalogs_sha256")})
        reports.append(report)
        mutations = [
            ("missing template", lambda c, m, g: c["templates"].pop()),
            ("wrong template orbit", lambda c, m, g: c["templates"][0].update(
                representative_id="damaged")),
            ("wrong width", lambda c, m, g: m.update(width=1)),
            ("wrong box", lambda c, m, g: m.update(variable_bounds="[0,2]")),
            ("changed base", lambda c, m, g: m["rows"][0].__setitem__(3, 99)),
            ("changed marginal sign", lambda c, m, g: m["rows"][4271][1].__setitem__(0, -1)),
            ("changed map", lambda c, m, g:
             m["transports"][0]["point_permutation"].__setitem__(0, 2)),
            ("missing transported template", lambda c, m, g: g[0]["templates"].pop()),
        ]
        for name, mutate in mutations:
            c, m, g = copy.deepcopy((catalog, matrix, groups))
            mutate(c, m, g)
            try:
                check_case(case, c, m, g, case_complete, excluded, old_matrix)
            except ValueError:
                controls.append({"case": case, "mutation": name, "rejected": True})
            else:
                raise ValueError("damaged control accepted: " + name)
    report = {"passed": True, "manifest_sha256": sha(HERE / "manifest.json"),
              "checker_sha256": sha(Path(__file__)), "checked_exclusions": len(excluded),
              "original_encoding_audit_sha256": sha(
                  HERE.parent / "four-seven-template-hull-refresh/independent-audit.json"),
              "cases": reports, "damaged_controls": controls,
              "scope": "Complete surviving catalogs and exact projected hull matrices only; "
                       "no solve."}
    (HERE / "independent-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "checked_exclusions": len(excluded),
                      "cases": reports, "damaged_controls": len(controls)}))


if __name__ == "__main__":
    main()
