# Document:    Independent Circulant Exact Profile Runtime Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      95004643423d83355b8b5b0930c610b288d8a53fedfdf429dbfebdf14abf2ae3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read-only saved result audit; parse protobufs and verify candidates without solving."""

import argparse
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "circulant-exact-profile-pilot"
RAW = ROOT / "experiments/scratch/circulant-exact-profile-pilot-20261004"
GATE = HERE.parent / "circulant-exact-profile-independent"
MANIFEST_SHA = "129002dca2ab140a5be66a8879fd7d97fee41f4203ba186d93ca720b335aa7da"
RUNNER_SHA = "68fbd3cd539d9d12589de39bef55ff66605f2d3d9227a86b5ed4773253cae0fc"
GATE_SHA = "63ac723a471129048deba2a1aaed69c010f76885f1538c61083ac13971ae5337"
GATE_REVIEW_SHA = "5075df441f50626f7ccc861d72411901dcc3bcc32276fa9de240dd82efe760c8"
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def exact(actual, expected, message):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), message)


def duration(value, maximum, message):
    require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum, message)


def vector_check(values, excess):
    require(type(values) is list and len(values) == 4368, "vector length")
    require(all(type(v) is int and v in (0, 1) for v in values), "strict Boolean vector")
    require(sum(values) == 64, "exact64 vector")
    blocks = [b for b, v in zip(BLOCKS, values, strict=True) if v]
    counts = Counter(t for b in blocks for t in combinations(b, 3))
    require(all(counts[t] == 1 + (t in excess) for t in TRIPLES), "all560 exact profile demands")
    return blocks


def candidate_check(index, child, response, excess, standalone):
    folder = RAW / f"case-{index + 1:02d}"
    values = read(folder / "vector.json")
    blocks = vector_check(values, excess)
    require(list(response.solution) == values, "response/vector agreement")
    witness = PRODUCER / f"witness-{index + 1:02d}.txt"
    canonical = "".join(" ".join(map(str, b)) + "\n" for b in blocks).encode()
    require(witness.read_bytes() == canonical, "exact lex witness bytes")
    require(sha(witness) == child["witness_sha256"], "witness hash")
    package = verify_cover(blocks)
    separate = standalone.verify_cover(blocks, expected_blocks=64)
    separate["source_sha256"] = sha(witness)
    require(package["valid"] is separate["valid"] is True, "dual cover verification")
    require(
        package["canonical_sha256"] == separate["canonical_sha256"] == sha(witness),
        "dual canonical hashes",
    )
    exact(child["package"], package, "saved package verifier")
    exact(child["standalone"], separate, "saved standalone verifier")
    exact(child["standalone_returncode"], 0, "saved standalone exit")
    require(
        child["exact_profile_matches"] is child["complete64"] is True, "candidate declared exact"
    )
    return {
        "witness_sha256": sha(witness),
        "blocks": 64,
        "covered": 560,
        "package_valid": True,
        "standalone_valid": True,
        "exact_profile_matches": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-sha256", required=True)
    args = parser.parse_args()
    require(not (HERE / "review.json").exists(), "preserve runtime review")
    require(sha(PRODUCER / "result.json") == args.result_sha256, "terminal result pin")
    for path, digest in [
        (PRODUCER / "manifest.json", MANIFEST_SHA),
        (PRODUCER / "run.py", RUNNER_SHA),
        (GATE / "gate.json", GATE_SHA),
        (GATE / "review.json", GATE_REVIEW_SHA),
    ]:
        require(sha(path) == digest, "frozen source/gate " + path.name)
    manifest = read(PRODUCER / "manifest.json")
    require(len(manifest["pins"]) == 27, "27 preparation pins")
    for path, digest in manifest["pins"].items():
        require(sha(ROOT / path) == digest, "input pin " + path)
    launch = read(PRODUCER / "launch.json")
    require(
        launch["manifest_sha256"] == MANIFEST_SHA and launch["gate_sha256"] == GATE_SHA,
        "launch gate binding",
    )
    exact(launch["seeds"], list(range(2026106401, 2026106409)), "launch seed order")
    require(launch["sequential"] is True, "sequential launch declaration")
    result = read(PRODUCER / "result.json")
    require(
        result["manifest_sha256"] == MANIFEST_SHA and result["gate_sha256"] == GATE_SHA,
        "result bindings",
    )
    exact(result["planned_calls"], 8, "eight-call maximum")
    runs = result["runs"]
    require(1 <= len(runs) <= 8 and result["finished_calls"] == len(runs), "run count")
    profiles = read(HERE.parent / "circulant-pair-graph-screen/profiles.json")
    standalone_path = ROOT / "scripts/check_cover.py"
    spec = importlib.util.spec_from_file_location("standalone_cover_checker", standalone_path)
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    summaries, raw_files, witnesses = [], {}, []
    for index, run in enumerate(runs):
        case = manifest["cases"][index]
        exact(run["index"], index, "consecutive run indices")
        exact(run["seed"], 2026106401 + index, "run seed")
        require(
            run["command"]
            == [sys.executable, str(PRODUCER / "run.py"), "--child", "--profile", str(index)],
            "exact child command",
        )
        duration(run["elapsed_seconds"], 55, "bounded child elapsed")
        require(
            all(type(run[k]) is bool for k in ("watchdog", "terminated", "killed")),
            "Boolean watchdog fields",
        )
        require(
            run["terminated"] == run["watchdog"] and (not run["killed"] or run["watchdog"]),
            "watchdog sequence",
        )
        folder = RAW / case["name"]
        expected_hashes = {
            str(p.relative_to(ROOT)): sha(p) for p in folder.iterdir() if p.is_file()
        }
        exact(run["raw_files"], expected_hashes, "complete raw archive binding")
        raw_files.update(expected_hashes)
        child_path = folder / "child-result.json"
        child = read(child_path) if child_path.exists() else None
        exact(run["child"], child, "embedded child receipt")
        stops_batch = run["returncode"] != 0 or run["watchdog"] or child is None
        if child is not None:
            stops_batch |= child["status"] == "MODEL_INVALID"
        if stops_batch:
            require(index == len(runs) - 1, "no launch after stop condition")
        if index < 7 and not stops_batch:
            require(index + 1 < len(runs), "no unexplained early stop")
        summary = {
            "index": index,
            "seed": run["seed"],
            "returncode": run["returncode"],
            "watchdog": run["watchdog"],
            "elapsed_seconds": run["elapsed_seconds"],
            "status": None,
            "candidate": None,
            "independent_infeasibility_proof": False,
        }
        if child is not None:
            exact(child["index"], index, "child index")
            exact(child["seed"], run["seed"], "child seed")
            require(child["independent_infeasibility_proof"] is False, "uncertified status")
            response = cp_model_pb2.CpSolverResponse()
            text_format.Parse((folder / "response.pbtxt").read_text(), response)
            status = cp_model_pb2.CpSolverStatus.Name(response.status)
            require(child["status"] == status, "response status")
            duration(child["native_seconds"], 31, "native30-second budget")
            duration(child["solve_elapsed_seconds"], run["elapsed_seconds"], "child solve elapsed")
            require(
                math.isclose(
                    response.wall_time, child["native_seconds"], rel_tol=1e-9, abs_tol=1e-12
                ),
                "response native time",
            )
            log = (folder / "solver.log").read_text()
            require(log.count("Starting CP-SAT solver v9.15.6755") == 1, "single solver launch")
            require(log.count("CpSolverResponse summary:") == 1, "single final response")
            logged_status = re.findall(r"^status: (\w+)$", log, re.M)
            require(logged_status == [status], "logged final status")
            expected_parameters = (
                f"random_seed: {run['seed']} max_time_in_seconds: 30 "
                "log_search_progress: true num_search_workers: 1 log_to_stdout: false"
            )
            require(
                re.findall(r"^Parameters: (.*)$", log, re.M) == [expected_parameters],
                "logged seed and budgets",
            )
            require(
                "#Variables: 4'368" in log
                and "- 4'368 Booleans in [0,1]" in log
                and "#kLinearN: 561" in log
                and "#terms: 48'048" in log,
                "unfixed model log shape",
            )
            require(
                (folder / "stdout.log").read_text() == ""
                and (folder / "stderr.log").read_text() == "",
                "empty captured stdout/stderr",
            )
            final_text = log[log.index("CpSolverResponse summary:") :]
            for name, value in [
                ("conflicts", response.num_conflicts),
                ("branches", response.num_branches),
                ("propagations", response.num_binary_propagations),
                ("integer_propagations", response.num_integer_propagations),
                ("restarts", response.num_restarts),
                ("lp_iterations", response.num_lp_iterations),
            ]:
                values = re.findall(r"^" + name + r": (\d+)$", final_text, re.M)
                require(values == [str(value)], "response/log counter " + name)
            excess = {tuple(t) for t in profiles[index]["excess_triples"]}
            if status in ("FEASIBLE", "OPTIMAL"):
                summary["candidate"] = candidate_check(index, child, response, excess, standalone)
                witnesses.append(f"witness-{index + 1:02d}.txt")
            else:
                require(
                    child["complete64"] is False
                    and not response.solution
                    and not (folder / "vector.json").exists()
                    and not (PRODUCER / f"witness-{index + 1:02d}.txt").exists(),
                    "no candidate",
                )
            summary.update(
                {
                    "status": status,
                    "native_seconds": child["native_seconds"],
                    "branches": response.num_branches,
                    "conflicts": response.num_conflicts,
                    "model_sha256": case["model_sha256"],
                    "parameters_sha256": case["parameters_sha256"],
                    "response_sha256": sha(folder / "response.pbtxt"),
                    "solver_log_sha256": sha(folder / "solver.log"),
                }
            )
        summaries.append(summary)
    exact(
        sorted(p.name for p in PRODUCER.glob("witness-*.txt")),
        sorted(witnesses),
        "no stray witness",
    )
    require(
        all(
            not (RAW / manifest["cases"][i]["name"] / "child-result.json").exists()
            for i in range(len(runs), 8)
        ),
        "no omitted later calls",
    )
    require(
        result["elapsed_seconds"] + 0.01 >= sum(r["elapsed_seconds"] for r in runs),
        "sequential process budget accounting",
    )
    damaged = []
    vectors = [
        [0] * 4367,
        [0] * 4369,
        [0] * 4368,
        [1] * 4368,
        [True] + [0] * 4367,
        [2] + [0] * 4367,
        [1] * 64 + [0] * (4368 - 64),
    ]
    for index, vector in enumerate(vectors):
        try:
            vector_check(vector, {tuple(t) for t in profiles[0]["excess_triples"]})
        except ValueError:
            damaged.append(index)
        else:
            raise AssertionError("damaged candidate vector accepted")
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "producer_result_sha256": args.result_sha256,
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": RUNNER_SHA,
        "gate_sha256": GATE_SHA,
        "model_gate_review_sha256": GATE_REVIEW_SHA,
        "launch_sha256": sha(PRODUCER / "launch.json"),
        "prepared_pins_checked": 27,
        "runs": summaries,
        "status_counts": dict(Counter(r["status"] for r in summaries)),
        "native_seconds_total": sum(r.get("native_seconds", 0) for r in summaries),
        "process_elapsed_seconds_total": sum(r["elapsed_seconds"] for r in summaries),
        "candidate_count": len(witnesses),
        "raw_files": raw_files,
        "damaged_vectors_rejected": len(damaged),
        "optimizer_calls": 0,
        "scope": (
            "Eight fixed non-Clebsch circulant excess profiles only; no selected link "
            "or block-family invariance. UNKNOWN remains inconclusive; INFEASIBLE "
            "without a separately checked proof is not independently certified. "
            "Reflection pairs remain duplicated as authorized. Any candidate above "
            "was checked against exact demands and both cover verifiers."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(HERE / "review.json"),
                "status_counts": receipt["status_counts"],
                "candidate_count": len(witnesses),
                "native_seconds_total": receipt["native_seconds_total"],
            }
        )
    )


if __name__ == "__main__":
    main()
