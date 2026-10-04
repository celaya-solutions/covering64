# Document:    Four Auditable Overlap-Five Completion Pilot Models
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2b2b5a02595bda2b83878f6ef8fe60c7a230c4c3e679b968ebcbe17105ca9b92
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Build raw integer and LP models for four explicit unions; do not solve."""

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[3]
FACTORIZATION_SHA256 = "f9a8c81ef8bb7fb7fa113d113be17c446a1efd9ca8bb98b3110272a2d8c20064"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def check_twice(blocks, path, v, k, t, expected, require_cover):
    write_blocks(path, blocks)
    package = verify_cover(blocks, v, k, t)
    completed = subprocess.run([sys.executable, str(ROOT / "scripts/check_cover.py"),
                                str(path), "--v", str(v), "--k", str(k), "--t", str(t),
                                "--expected-blocks", str(expected)], capture_output=True, text=True)
    standalone = json.loads(completed.stdout)
    assert bool(package["valid"]) == bool(standalone["valid"]) == require_cover
    assert completed.returncode == (0 if require_cover else 1)
    assert package["canonical_sha256"] == standalone["canonical_sha256"]
    assert package["covered"] == standalone["covered_subsets"]
    return {"package": package, "standalone": standalone,
            "standalone_returncode": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr,
            "witness_sha256": sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists()
    output.mkdir(parents=True)
    factorization = Path(__file__).with_name("factorization.json.gz")
    assert sha(factorization) == FACTORIZATION_SHA256
    payload = json.loads(gzip.decompress(factorization.read_bytes()))
    sources = {}
    for path in (Path(__file__), Path(__file__).with_name("derive.py"),
                 ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py", factorization):
        shutil.copyfile(path, output / path.name)
        sources[path.name] = sha(path)
    universe = Universe.build()
    assert tuple(universe.blocks) == tuple(combinations(range(1, 17), 5))
    ids = {block: index for index, block in enumerate(universe.blocks)}
    manifest = {"sources": sources,
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                           cwd=ROOT, text=True).strip(),
                "solver_package_version": ortools.__version__,
                "search_launched": False, "seeds": None, "solver_budget": None,
                "scope": "Four explicit conditional 33-block overlap-five unions, not a "
                         "representative screen of all4,578,210 ordered classes. Models preserve "
                         "all2,002 possible avoiding blocks. No solver result is claimed.",
                "cases": []}
    for number, pilot in enumerate(payload["pilots"]):
        name = f"pilot-{number:03d}"
        folder = output / name
        folder.mkdir()
        anchors = tuple(pilot["anchors"])
        fixed = tuple(tuple(block) for block in pilot["fixed_blocks"])
        fixed_ids = sorted(ids[block] for block in fixed)
        assert len(fixed) == len(set(fixed)) == 33
        assert sum(all(point in block for point in anchors) for block in fixed) == 5
        checks = {}
        for anchor in anchors:
            incident = [block for block in fixed if anchor in block]
            assert len(incident) == 19
            labels = {point: index for index, point in enumerate(
                (point for point in range(1, 17) if point != anchor), start=1)}
            link = [tuple(labels[point] for point in block if point != anchor)
                    for block in incident]
            checks[f"anchor-{anchor}"] = check_twice(
                link, folder / f"anchor-{anchor}-link.txt", 15, 4, 2, 19, True)
        checks["union"] = check_twice(fixed, folder / "fixed-union.txt", 16, 5, 3, 33, False)
        free = [index for index, block in enumerate(universe.blocks)
                if not set(anchors).intersection(block)]
        assert len(free) == 2002
        fixed_set = set(fixed_ids)
        free_set = set(free)
        forbidden = [index for index in range(4368) if index not in fixed_set | free_set]
        model = cp_model.CpModel()
        variables = [model.new_bool_var(f"block_{index}") for index in range(4368)]
        for index in fixed_ids:
            model.add(variables[index] == 1)
        for index in forbidden:
            model.add(variables[index] == 0)
        model.add(sum(variables) == 64)
        for containing in universe.containing:
            model.add(sum(variables[index] for index in containing) >= 1)
        for point in range(1, 17):
            degree = sum(variables[index] for index, block in enumerate(universe.blocks)
                         if point in block)
            model.add(degree == 19 if point in anchors else degree >= 19)
        for pair in combinations(range(1, 17), 2):
            model.add(sum(variables[index] for index, block in enumerate(universe.blocks)
                          if set(pair) <= set(block)) >= 5)
        assert model.validate() == ""
        assert len(model.proto.variables) == 4368 and len(model.proto.constraints) == 3063
        model_path = folder / "model.pbtxt"
        model.export_to_file(str(model_path))
        rows = []
        for constraint in model.proto.constraints:
            assert constraint.has_linear() and not constraint.enforcement_literal
            assert len(constraint.linear.domain) == 2
            lower, upper = constraint.linear.domain
            rows.append([list(constraint.linear.vars), list(constraint.linear.coeffs),
                         int(lower) if lower > -(1 << 60) else None,
                         int(upper) if upper < (1 << 60) else None])
        row_path = folder / "lp-rows.json.gz"
        row_path.write_bytes(gzip.compress((json.dumps({"width": 4368, "rows": rows})
                                           + "\n").encode(), mtime=0))
        info = {"id": name, "first_type": pilot["first_type"],
                "source_type": pilot["source_type"], "anchors": anchors,
                "coordinate_mapping": pilot["coordinate_mapping"],
                "source_to_second_point_map": pilot["source_to_second_point_map"],
                "fixed_ids": fixed_ids, "free_ids": free, "forbidden_ids": forbidden,
                "variables": 4368, "rows": 3063, "fixed_count": 33, "free_count": 2002,
                "additions_required": 31, "global_lexicographic_order": True,
                "model_sha256": sha(model_path), "lp_rows_sha256": sha(row_path),
                "verifier_checks": checks, "lp_domain": "Each original block variable in[0,1]",
                "search_launched": False}
        write_json(folder / "metadata.json", info)
        manifest["cases"].append(info)
    write_json(output / "manifest.json", manifest)
    durable = {key: value for key, value in manifest.items() if key != "cases"}
    durable["raw_archive"] = str(output.relative_to(ROOT))
    durable["raw_manifest_sha256"] = sha(output / "manifest.json")
    durable["cases"] = [{key: value for key, value in row.items()
                         if key not in ("free_ids", "forbidden_ids", "verifier_checks")}
                        for row in manifest["cases"]]
    write_json(Path(__file__).with_name("pilot-manifest.json"), durable)
    print(json.dumps({"pilots": len(manifest["cases"]), "search_launched": False,
                      "raw_archive": durable["raw_archive"]}))


if __name__ == "__main__":
    main()
