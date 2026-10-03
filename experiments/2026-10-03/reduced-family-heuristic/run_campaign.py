# Document:    Audited Reduced Family Heuristic Campaign Runner
# Version:     v1.3.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      bed11125814181818d7f941fc7d0a417aeacc7dec2a8a86667a6768abdb29c6c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run a bounded native search and independently verify every saved snapshot."""

import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import platform
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
CHECKER = ROOT / "scripts/verify_reduced_family_heuristic.py"
SPEC = importlib.util.spec_from_file_location("reduced_checker", CHECKER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("seed", type=int)
    parser.add_argument("seconds", type=float)
    parser.add_argument("output", type=Path)
    parser.add_argument("--input", type=Path, default=FOLDER / "inputs" / "seed27.txt")
    parser.add_argument("--heavy-penalty", type=float, default=0)
    parser.add_argument("--family-penalty", type=float, default=0)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    paths = [args.input.resolve(), *(FOLDER / "inputs" / filename
                                   for filename in ["pg.txt", "r4.txt", "r6.txt"])]
    command = [str(args.binary.resolve()), *(str(p) for p in paths), str(args.seed),
               str(args.seconds), str(args.output.resolve() / "search"),
               str(args.heavy_penalty), str(args.family_penalty)]
    sources = [ROOT / "scripts/reduced_family_heuristic.cpp", CHECKER, Path(__file__).resolve()]
    trade_data = FOLDER / "inputs" / "pg-trades.json"
    metadata = {"command": command, "seed": args.seed, "budget_seconds": args.seconds,
                "search_processes": 1, "source_hashes": {str(p.relative_to(ROOT)): sha(p)
                                                          for p in sources},
                "input_hashes": {p.name: sha(p) for p in paths}, "binary_sha256": sha(args.binary),
                "trade_artifact_sha256": sha(trade_data),
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                             cwd=ROOT, text=True).strip(),
                "compiler": subprocess.check_output(["clang++", "--version"], text=True),
                "platform": platform.platform(), "started_utc": datetime.datetime.now(
                    datetime.timezone.utc).isoformat(),
                "scope": "Bounded reduced-family heuristic; no impossibility claim",
                "moves": "65% outside swaps;20% compatible family maps;5% fresh PG/r4/r6 "
                         "families;10% four/six-block PG trades. Fresh families and trades "
                         "each receive64 greedy targeted outside repair proposals",
                "diversity": "At most8 additional states per hole count, within best score+1 when "
                             "saved, with block-set distance at least4 from the live reservoir. "
                             "Half of periodic restarts sample that bounded reservoir",
                "progress_interval_seconds": 45,
                "heavy_penalty_weight": args.heavy_penalty,
                "family_penalty_weight": args.family_penalty,
                "score_version": "1.3",
                "score": "holes + heavy_weight*(old heavy penalty + heavy_overlap + "
                         "repeated_point_excess + repeated_incidence_excess + "
                         "endpoint_shape_distance + hub_inside_heavy + hub_collision + "
                         "internal_pair_deficit + hub_internal_pair_excess + "
                         "hub_cross_pair_deviation + refined_count_overflow + "
                         "generic_pair_deficit) + "
                         "family_weight*sum(pair_row_overflow)",
                "qualification": "Heavy: all documented v1.3 heavy/hub and generic pair "
                                 "penalties zero. Scored filters additionally require zero "
                                 "fixed-family pair-row overflow. Passing these necessary "
                                 "checks does not prove completion or completability",
                "hub_diagnostics": "Legacy sevenfold diagnostic is retained separately. "
                                   "Expanded heavy/hub necessities contribute to score and "
                                   "qualification through their explicit penalty fields"}
    checks = []
    events = []
    start = time.monotonic()
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with ((args.output / "stdout.jsonl").open("w") as log,
          (args.output / "stderr.txt").open("w") as err):
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=err,
                                   text=True, bufsize=1)
        try:
            for line in process.stdout:
                log.write(line)
                log.flush()
                event = json.loads(line)
                events.append(event)
                if event["event"] == "progress":
                    print(json.dumps(event), flush=True)
                if event["event"] == "snapshot":
                    checked = MODULE.verify(Path(event["path"]))
                    if checked["holes"] != event["holes"]:
                        raise ValueError("native and independent hole counts differ")
                    checks.append({"event": event, "independent": checked})
                    if event["role"] in ["initial", "improvement", "qualifying_improvement",
                                         "heavy_qualifying_improvement", "score_improvement"]:
                        print(json.dumps({"event": "verified_" + event["role"],
                                          "holes": event["holes"], "path": event["path"],
                                          "seconds": event["seconds"]}), flush=True)
        except BaseException:
            process.kill()
            process.wait()
            raise
        code = process.wait()
    if code:
        raise RuntimeError(f"native exit{code}; see stderr")
    if not events or events[-1]["event"] != "finish":
        raise ValueError("missing native completion record")
    raw = json.dumps({"scope": "Every saved snapshot independently recounted and checked twice",
                      "checker_sha256": sha(CHECKER), "checks": checks},
                     sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (args.output / "candidate-checks.json.gz").write_bytes(gzip.compress(raw, mtime=0))
    metadata.update(exit=code, wall_seconds=time.monotonic() - start, finish=events[-1],
                    snapshot_count=len(checks), valid_covers=sum(
                        row["independent"]["holes"] == 0 for row in checks),
                    candidate_checks_sha256=sha(args.output / "candidate-checks.json.gz"),
                    stdout_sha256=sha(args.output / "stdout.jsonl"),
                    stderr_sha256=sha(args.output / "stderr.txt"))
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(events[-1]), flush=True)


if __name__ == "__main__":
    main()
