# Document:    Independent Complete Circulant Profile Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      25825827bef04881813c9e022a5987b43b11bb0ea53cc8cce503810462a1ed24
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Saved result and response audit only; never execute a solver or subprocess."""

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
PRODUCER = HERE.parent / "circulant-all-profile-global-pilot"
RAW = ROOT / "experiments/scratch/circulant-all-profile-global-pilot-20261004"
GATE = HERE.parent / "circulant-all-profile-global-independent"
MANIFEST_SHA = "c3a70ac81bc5174807c3ba150e6924d295a3b2730bec8947921f2176bcc67b72"
RUNNER_SHA = "ab89c2a66fa72182b70fa59874f303cfc40dfb9432e2245322116ef7111ec3fb"
GATE_SHA = "ea96ba6cff98ddb0723795745d40e7b0d0bebbe42f1126b89773f20be2b5325b"
REVIEW_SHA = "83f3aa3089505bb38e2b06d0322373d0034a987bf591d8962370a8b0a0711ba3"
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
PAIRS = tuple(combinations(range(1, 17), 2))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def exact(actual, expected, name):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), name)


def duration(value, maximum, name):
    require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum, name)


def choices_check(bits, mask, table):
    require(
        type(bits) is list
        and len(bits) == 48
        and all(type(v) is int and v in (0, 1) for v in bits),
        "48 strict Boolean center bits",
    )
    require(type(mask) is int and mask == sum(bit << i for i, bit in enumerate(bits)), "exact mask")
    require({"center_bits": bits, "representative_mask": mask} in table, "allowed representative")
    return mask


def blocks_check(values, excess):
    require(
        type(values) is list
        and len(values) == 4368
        and all(type(v) is int and v in (0, 1) for v in values),
        "4368 strict Boolean blocks",
    )
    require(sum(values) == 64, "exact64 blocks")
    blocks = [block for block, bit in zip(BLOCKS, values, strict=True) if bit]
    triple_load = Counter(t for b in blocks for t in combinations(b, 3))
    require(all(triple_load[t] == 1 + (t in excess) for t in TRIPLES), "all560 exact triple rows")
    return blocks


def candidate_check(child, response, geometry, table, standalone):
    vector = read(RAW / "vector.json")
    bits, values = vector["center_bits"], vector["block_values"]
    mask = choices_check(bits, vector["representative_mask"], table)
    require(child["representative_mask"] == mask, "child selected profile")
    excess = {tuple(sorted((a, b, centers[0]))) for a, b, centers in geometry["forced"]}
    excess.update(
        tuple(sorted((a, b, centers[bits[i]])))
        for i, (a, b, centers) in enumerate(geometry["choices"])
    )
    require(len(excess) == 80, "selected excess size")
    blocks = blocks_check(values, excess)
    require(list(response.solution) == values + bits, "full4416 response values")
    pair_load = Counter(pair for b in blocks for pair in combinations(b, 2))
    edges = {tuple(pair) for pair in geometry["edges"]}
    require(all(pair_load[pair] == 5 + (pair in edges) for pair in PAIRS), "named pair profile")
    require(all(sum(p in b for b in blocks) == 20 for p in range(1, 17)), "point replication20")
    witness = PRODUCER / "witness.txt"
    canonical = "".join(" ".join(map(str, b)) + "\n" for b in blocks).encode()
    require(witness.read_bytes() == canonical, "canonical witness bytes")
    require(sha(witness) == child["witness_sha256"], "witness hash")
    package = verify_cover(blocks)
    separate = standalone.verify_cover(blocks, expected_blocks=64)
    separate["source_sha256"] = sha(witness)
    require(package["valid"] is separate["valid"] is True, "both cover verifiers")
    require(
        package["canonical_sha256"] == separate["canonical_sha256"] == sha(witness), "dual hashes"
    )
    exact(child["package"], package, "saved package verification")
    exact(child["standalone"], separate, "saved standalone verification")
    exact(child["standalone_returncode"], 0, "standalone exit")
    require(
        child["exact_profile_matches"]
        is child["pair_profile_matches"]
        is child["complete64"]
        is True,
        "candidate verdicts",
    )
    return {
        "representative_mask": mask,
        "witness_sha256": sha(witness),
        "blocks": 64,
        "covered_triples": 560,
        "all_exact_demands_passed": True,
        "named_pair_profile_passed": True,
        "point_replication20": True,
        "package_valid": True,
        "standalone_valid": True,
    }


def damage_controls(geometry, table):
    rejected = []
    good_bits, good_mask = table[0]["center_bits"], table[0]["representative_mask"]
    bad_choices = [
        (good_bits[:-1], good_mask),
        (good_bits + [0], good_mask),
        ([True] + good_bits[1:], good_mask),
        ([2] + good_bits[1:], good_mask),
        (good_bits, good_mask + 1),
        ([0] * 48, 0),
        (good_bits, True),
    ]
    for index, (bits, mask) in enumerate(bad_choices):
        try:
            choices_check(bits, mask, table)
        except ValueError:
            rejected.append("choice_" + str(index))
        else:
            raise AssertionError("damaged choice accepted")
    excess = {tuple(sorted((a, b, centers[0]))) for a, b, centers in geometry["forced"]}
    excess.update(
        tuple(sorted((a, b, centers[good_bits[i]])))
        for i, (a, b, centers) in enumerate(geometry["choices"])
    )
    for index, values in enumerate(
        [
            [0] * 4367,
            [0] * 4369,
            [0] * 4368,
            [1] * 4368,
            [True] + [0] * 4367,
            [2] + [0] * 4367,
            [1] * 64 + [0] * 4304,
        ]
    ):
        try:
            blocks_check(values, excess)
        except ValueError:
            rejected.append("blocks_" + str(index))
        else:
            raise AssertionError("damaged block vector accepted")
    return rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-sha256", required=True)
    args = parser.parse_args()
    require(not (HERE / "review.json").exists(), "preserve completed runtime audit")
    require(sha(PRODUCER / "result.json") == args.result_sha256, "terminal result pin")
    for path, digest in [
        (PRODUCER / "manifest.json", MANIFEST_SHA),
        (PRODUCER / "run.py", RUNNER_SHA),
        (GATE / "gate.json", GATE_SHA),
        (GATE / "review.json", REVIEW_SHA),
    ]:
        require(sha(path) == digest, "frozen producer/gate " + path.name)
    manifest = read(PRODUCER / "manifest.json")
    require(len(manifest["pins"]) == 15, "fifteen preparation pins")
    for relative, digest in manifest["pins"].items():
        require(sha(ROOT / relative) == digest, "input pin " + relative)
    launch, result = read(PRODUCER / "launch.json"), read(PRODUCER / "result.json")
    for record in (launch, result):
        require(
            record["manifest_sha256"] == MANIFEST_SHA and record["gate_sha256"] == GATE_SHA,
            "gate binding",
        )
    require(
        launch["command"] == [sys.executable, str(PRODUCER / "run.py"), "--child"],
        "one child command",
    )
    duration(result["elapsed_seconds"], 330, "wrapper elapsed bound")
    require(
        all(type(result[k]) is bool for k in ("watchdog", "terminated", "killed")),
        "watchdog fields",
    )
    require(
        result["watchdog"] == result["terminated"] and (not result["killed"] or result["watchdog"]),
        "watchdog termination order",
    )
    actual_files = {str(p.relative_to(ROOT)): sha(p) for p in RAW.iterdir() if p.is_file()}
    exact(result["raw_files"], actual_files, "complete raw archive hash binding")
    child_path = RAW / "child-result.json"
    child = read(child_path) if child_path.exists() else None
    exact(result["child"], child, "embedded child")
    geometry = read(HERE.parent / "circulant-all-excess-profiles/geometry.json")
    table = read(PRODUCER / "allowed-profile-table.json")
    summary = {
        "returncode": result["returncode"],
        "watchdog": result["watchdog"],
        "elapsed_seconds": result["elapsed_seconds"],
        "status": None,
        "candidate": None,
        "independent_infeasibility_proof": False,
    }
    if child is not None:
        require(child["independent_infeasibility_proof"] is False, "uncertified status")
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse((RAW / "response.pbtxt").read_text(), response)
        status = cp_model_pb2.CpSolverStatus.Name(response.status)
        require(child["status"] == status, "response/child status")
        duration(child["native_seconds"], 310, "native time inside watchdog")
        duration(child["solve_elapsed_seconds"], result["elapsed_seconds"], "solve inside process")
        require(
            math.isclose(child["native_seconds"], response.wall_time, rel_tol=1e-9, abs_tol=1e-12),
            "response native time",
        )
        log = (RAW / "solver.log").read_text()
        require(
            log.count("Starting CP-SAT solver v9.15.6755") == 1
            and log.count("CpSolverResponse summary:") == 1,
            "one solver start/response",
        )
        require(re.findall(r"^status: (\w+)$", log, re.M) == [status], "log final status")
        expected = (
            "random_seed: 2026106501 max_time_in_seconds: 300 log_search_progress: true "
            "num_search_workers: 4 log_to_stdout: false"
        )
        require(re.findall(r"^Parameters: (.*)$", log, re.M) == [expected], "logged parameters")
        require(
            "#Variables: 4'416" in log
            and "- 4'416 Booleans in [0,1]" in log
            and "#kLinearN: 561" in log
            and "#terms: 48'144" in log
            and "#kTable: 1" in log,
            "unfixed global model dimensions",
        )
        require(
            (RAW / "stdout.log").read_text() == "" and (RAW / "stderr.log").read_text() == "",
            "empty captured stdout/stderr",
        )
        final = log[log.index("CpSolverResponse summary:") :]
        for name, value in [
            ("branches", response.num_branches),
            ("conflicts", response.num_conflicts),
            ("propagations", response.num_binary_propagations),
            ("integer_propagations", response.num_integer_propagations),
            ("restarts", response.num_restarts),
            ("lp_iterations", response.num_lp_iterations),
        ]:
            require(
                re.findall(r"^" + name + r": (\d+)$", final, re.M) == [str(value)],
                "response/log counter " + name,
            )
        if status in ("FEASIBLE", "OPTIMAL"):
            spec = importlib.util.spec_from_file_location(
                "standalone_cover", ROOT / "scripts/check_cover.py"
            )
            standalone = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(standalone)
            summary["candidate"] = candidate_check(child, response, geometry, table, standalone)
        else:
            require(
                child["complete64"] is False
                and not response.solution
                and not (RAW / "vector.json").exists()
                and not (PRODUCER / "witness.txt").exists(),
                "no candidate artifact",
            )
        summary.update(
            {
                "status": status,
                "native_seconds": child["native_seconds"],
                "branches": response.num_branches,
                "conflicts": response.num_conflicts,
                "response_sha256": sha(RAW / "response.pbtxt"),
                "solver_log_sha256": sha(RAW / "solver.log"),
            }
        )
    controls = damage_controls(geometry, table)
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "producer_result_sha256": args.result_sha256,
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": RUNNER_SHA,
        "gate_sha256": GATE_SHA,
        "model_gate_review_sha256": REVIEW_SHA,
        "launch_sha256": sha(PRODUCER / "launch.json"),
        "prepared_pins_checked": 15,
        "run": summary,
        "raw_files": actual_files,
        "malformed_candidate_controls_rejected": controls,
        "optimizer_calls": 0,
        "native_requeries": 0,
        "scope": (
            "One complete-profile model for this named circulant pair graph; all52 "
            "representatives of1300 independently enumerated excess patterns. No cover "
            "invariance or fixed link. UNKNOWN is inconclusive; INFEASIBLE without a "
            "separately checked proof is not certified. No unrestricted conclusion."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(HERE / "review.json"),
                "status": summary["status"],
                "candidate": summary["candidate"],
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
