# Document:    Four-Case Fully Cut First-Link Integer Pilot
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      8016130f4704ba829bb347d57033a58fdad8114243785d680bd570f95d539e71
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare frozen models separately; launch up to two audited five-minute CP pilots."""

import argparse
import gzip
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
SEEDS = {"matching-029": 2026103301, "matching-113": 2026103302,
         "cycle-069": 2026103303, "cycle-046": 2026103304}
SECONDS = 300
WORKERS = 2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def prepare(output):
    require(not output.exists(), "output archive must be new")
    sys.path.insert(0, str(ROOT / "scripts"))
    from four_seven_blossom_cuts import add_blossom_cuts
    from four_seven_double_cuts import add_double_triple_cuts
    from four_seven_facet_cuts import PROOF_MANIFEST_SHA256 as FACET_PROOF
    from four_seven_facet_cuts import add_facet_cuts
    from four_seven_feature_cuts import PROOF_MANIFEST_SHA256 as FEATURE_PROOF
    from four_seven_feature_cuts import add_feature_cuts
    from four_seven_search import build_model

    output.mkdir(parents=True)
    source_paths = [Path(__file__), ROOT / "src/covering64/core.py",
                    *[ROOT / "scripts" / name for name in (
                        "check_cover.py", "four_seven_search.py", "four_seven_double_cuts.py",
                        "four_seven_feature_cuts.py", "four_seven_facet_cuts.py",
                        "four_seven_blossom_cuts.py")]]
    sources = {}
    for path in source_paths:
        shutil.copyfile(path, output / path.name)
        sources[path.name] = digest(path)
    proof_dir = ROOT / "experiments/2026-10-03/four-seven-link-orbits"
    for filename, expected in (("safe-linear-cuts.json", FEATURE_PROOF),
                               ("safe-feature-facets.json", FACET_PROOF)):
        path = proof_dir / filename
        require(digest(path) == expected, "proof artifact hash mismatch")
        shutil.copyfile(path, output / filename)
        sources[filename] = expected
    original = ROOT / "experiments/scratch/four-seven-link-lp-full/results.json.gz"
    shutil.copyfile(original, output / "input-results.json.gz")
    sources["input-results.json.gz"] = digest(original)
    results = json.loads(gzip.decompress(original.read_bytes()))
    entries = {row["id"]: row for row in results if row["id"] in SEEDS}
    require(set(entries) == set(SEEDS), "missing or duplicate selected case")
    require(sum(row["id"] in SEEDS for row in results) == 4, "duplicate selected case")
    bases = {}
    applications = {}
    for case in ("cycle", "matching"):
        universe, model, xs, _ = build_model(case)
        _, double_info = add_double_triple_cuts(universe, model, xs, case)
        feature_info = add_feature_cuts(universe, model, xs, case)
        facet_info = add_facet_cuts(universe, model, xs, case)
        blossom_info = add_blossom_cuts(universe, model, xs, case)
        require(model.validate() == "", "fully cut base model is invalid")
        require(len(model.proto.variables) == 4768, "unexpected base variables")
        require(len(model.proto.constraints) == (12390 if case == "cycle" else 12414),
                "unexpected fully cut base rows")
        model.export_to_file(str(output / f"{case}-base.pbtxt"))
        bases[case] = model
        applications[case] = {"double": double_info, "feature": feature_info,
                              "facet": facet_info, "blossom": blossom_info}
    write_json(output / "cut-applications.json", applications)
    blocks = list(combinations(range(1, 17), 5))
    source_revision = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                               cwd=ROOT, text=True).strip()
    cases = []
    for rep_id, seed in SEEDS.items():
        entry = entries[rep_id]
        case, fixed_ids = entry["case"], entry["fixed_ids"]
        require(not entry["proves_infeasible"], "selected representative was excluded")
        require(len(set(fixed_ids)) == 7 and len(fixed_ids) == 7, "seven distinct fixes required")
        require(all(type(index) is int and 0 <= index < 4368 for index in fixed_ids),
                "bad fixed variable ID")
        require(all(blocks[index][:3] == (1, 2, 3) for index in fixed_ids),
                "fixed blocks are not first-heavy link")
        directory = output / rep_id
        directory.mkdir()
        model = bases[case].clone()
        for index in fixed_ids:
            model.add(model.get_bool_var_from_proto_index(index) == 1)
        require(model.validate() == "", "fixed-link model is invalid")
        model.export_to_file(str(directory / "model.pbtxt"))
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = SECONDS
        solver.parameters.num_search_workers = WORKERS
        solver.parameters.random_seed = seed
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = False
        (directory / "parameters.txt").write_text(str(solver.parameters))
        metadata = {
            "id": rep_id, "case": case, "fixed_ids": fixed_ids,
            "fixed_blocks": [blocks[index] for index in fixed_ids],
            "source_revision": source_revision, "sources": sources,
            "solver_version": ortools.__version__, "prepared_command": sys.argv,
            "prepared_utc": datetime.now(timezone.utc).isoformat(),
            "base_sha256": digest(output / f"{case}-base.pbtxt"),
            "model_sha256": digest(directory / "model.pbtxt"),
            "parameters_sha256": digest(directory / "parameters.txt"),
            "seconds": SECONDS, "workers": WORKERS, "seed": seed,
            "variables": len(model.proto.variables), "rows": len(model.proto.constraints),
            "hints_added": False, "new_constraints_beyond_cut_base": "Seven block_i ==1 rows",
            "scope": "One first-heavy-link representative in the normalized regular full "
                     "64-block branch with double, five feature, thirteen facet, and blossom cuts. "
                     "No other link or double pattern is fixed. UNKNOWN is inconclusive; "
                     "INFEASIBLE alone is not an independently checked theorem.",
        }
        write_json(directory / "metadata.json", metadata)
        cases.append({"id": rep_id, "seed": seed, "rows": metadata["rows"],
                      "model_sha256": metadata["model_sha256"]})
    for path in source_paths:
        require(digest(path) == sources[path.name], "source changed during preparation")
    summary = {"cases": cases, "sources": sources, "seconds_per_case": SECONDS,
               "workers_per_case": WORKERS, "maximum_simultaneous_cases": 2,
               "source_revision": source_revision, "launched": False}
    write_json(output / "prepared.json", summary)
    print(json.dumps(summary, indent=2))


def solve(directory):
    root = directory.parent
    metadata = json.loads((directory / "metadata.json").read_text())
    require(not (directory / "result.json").exists(), "do not overwrite an existing run")
    require(metadata["id"] in SEEDS and metadata["seed"] == SEEDS[metadata["id"]],
            "unexpected pilot seed")
    require(metadata["seconds"] == SECONDS and metadata["workers"] == WORKERS,
            "unexpected pilot budget")
    require(ortools.__version__ == metadata["solver_version"], "solver version drift")
    require(digest(Path(__file__)) == metadata["sources"]["run.py"], "runner source drift")
    for name, expected in metadata["sources"].items():
        require(digest(root / name) == expected, f"archived source/input changed: {name}")
    require(digest(directory / "model.pbtxt") == metadata["model_sha256"], "model hash mismatch")
    require(digest(directory / "parameters.txt") == metadata["parameters_sha256"],
            "parameters hash mismatch")
    model = cp_model.CpModel()
    require(model.proto.parse_text_format((directory / "model.pbtxt").read_text()),
            "model parse failed")
    require(model.validate() == "", "invalid model")
    solver = cp_model.CpSolver()
    require(solver.parameters.parse_text_format((directory / "parameters.txt").read_text()),
            "parameters parse failed")
    started = datetime.now(timezone.utc).isoformat()
    with (directory / "solver.log").open("x") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        status = solver.solve(model)
    (directory / "response.pbtxt").write_text(str(solver.response_proto))
    result = {"id": metadata["id"], "status": solver.status_name(status),
              "seconds": solver.wall_time, "response_stats": solver.response_stats(),
              "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
              "cover_found": False, "candidate_extracted": False,
              "verifier_outcome": "not applicable: solver supplied no integer solution"}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        spec = importlib.util.spec_from_file_location("frozen_pilot_core", root / "core.py")
        core = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = core
        spec.loader.exec_module(core)
        blocks = list(combinations(range(1, 17), 5))
        candidate = [blocks[index] for index in range(4368)
                     if solver.value(model.get_bool_var_from_proto_index(index))]
        path = directory / "candidate.txt"
        core.write_blocks(path, candidate)
        package = core.verify_cover(candidate)
        completed = subprocess.run([sys.executable, str(root / "check_cover.py"), str(path),
                                    "--expected-blocks", "64"], capture_output=True, text=True)
        (directory / "standalone.stdout.txt").write_text(completed.stdout)
        (directory / "standalone.stderr.txt").write_text(completed.stderr)
        write_json(directory / "package-verifier.json", package)
        standalone = json.loads(completed.stdout) if completed.returncode == 0 else None
        valid = (len(candidate) == 64 and package["valid"] and standalone is not None
                 and standalone["valid"]
                 and package["canonical_sha256"] == standalone["canonical_sha256"])
        result.update(candidate_extracted=True, cover_found=valid, package=package,
                      standalone=standalone, standalone_returncode=completed.returncode,
                      verifier_outcome="both passed" if valid else "candidate rejected")
    result["artifact_sha256"] = {path.name: digest(path) for path in sorted(directory.iterdir())
                                 if path.is_file()}
    write_json(directory / "result.json", result)
    print(json.dumps({key: result[key] for key in (
        "id", "status", "seconds", "cover_found", "verifier_outcome")}), flush=True)
    require(not result["candidate_extracted"] or result["cover_found"],
            "integer candidate failed independent verification")


def batch(output):
    require(not (output / "batch-results.json").exists(), "batch already completed")

    def launch(rep_id):
        directory = output / rep_id
        with (directory / "process.log").open("x") as log:
            command = [sys.executable, str(output / "run.py"), "solve", str(directory)]
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        return {"id": rep_id, "returncode": completed.returncode, "command": command}

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(launch, SEEDS))
    write_json(output / "batch-results.json", outcomes)
    print(json.dumps(outcomes, indent=2))
    require(all(row["returncode"] == 0 for row in outcomes), "at least one pilot process failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "solve", "batch"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    {"prepare": prepare, "solve": solve, "batch": batch}[args.mode](args.output.resolve())


if __name__ == "__main__":
    main()
