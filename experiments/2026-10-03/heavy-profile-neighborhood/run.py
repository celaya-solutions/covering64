# Document:    Heavy Profile Candidate Neighborhood Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Evidence wrapper around the existing generic neighborhood implementation."""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import lns_search as lns  # noqa: E402

from covering64.core import Universe, read_blocks, verify_cover, write_blocks  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def forbidden_profile(counts):
    """Return a forbidden disjoint five-tuple, including multiplicity-six triples."""
    heavy = sorted(t for t, count in counts.items() if count >= 6)
    for family in combinations(heavy, 5):
        if (len({p for triple in family for p in triple}) == 15
                and sum(counts[triple] >= 7 for triple in family) >= 2):
            return family
    return None


def profile(blocks):
    counts = Counter(t for block in blocks for t in combinations(block, 3))
    return {
        "heavy_triples": [{"triple": t, "multiplicity": count}
                          for t, count in sorted(counts.items()) if count >= 6],
        "forbidden_five_disjoint": forbidden_profile(counts),
    }


def add_profile_cut(model, expressions, hinted_counts, label):
    """Exclude exactly five disjoint six-heavy triples with two seven-heavy triples."""
    if len(expressions) != 5 or len(hinted_counts) != 5:
        raise ValueError("a profile must contain five triples")
    six, seven = [], []
    for i, (count, value) in enumerate(zip(expressions, hinted_counts)):
        for threshold, flags in ((6, six), (7, seven)):
            flag = model.new_bool_var(f"profile_{label}_{i}_atleast_{threshold}")
            model.add(count >= threshold).only_enforce_if(flag)
            model.add(count <= threshold - 1).only_enforce_if(flag.Not())
            model.add_hint(flag, int(value >= threshold))
            flags.append(flag)
    model.add(5 * sum(six) + sum(seven) <= 26)
    return {"hinted_counts": hinted_counts,
            "six_hint": [int(v >= 6) for v in hinted_counts],
            "seven_hint": [int(v >= 7) for v in hinted_counts],
            "hint_satisfies_cut": 5 * sum(v >= 6 for v in hinted_counts)
            + sum(v >= 7 for v in hinted_counts) <= 26}


def verify(blocks, path):
    package = verify_cover(blocks)
    write_blocks(path, blocks)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_cover.py"), str(path),
         "--expected-blocks", str(len(blocks))], capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr)
    standalone = json.loads(proc.stdout)
    if (standalone["uncovered_count"] != len(package["uncovered"])
            or standalone["valid"] != package["valid"]):
        raise RuntimeError("verifiers disagree")
    return {"package": package, "standalone": standalone}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--seed", type=int, default=2026102403)
    parser.add_argument("--profile-cuts", type=Path)
    args = parser.parse_args()
    if not 0 < args.seconds <= 300:
        parser.error("budget must be positive and at most300 seconds")
    args.output.mkdir(parents=True, exist_ok=True)
    universe = Universe.build()
    current = list(read_blocks(args.candidate))
    initial = verify(current, args.output / "initial.txt")
    if len(current) != 64:
        raise ValueError("expected64 seed blocks")
    if profile(current)["forbidden_five_disjoint"] is not None:
        raise ValueError("seed has a forbidden heavy profile")
    best = initial["standalone"]["uncovered_count"]
    write_blocks(args.output / "best.txt", current)
    sources = {}
    for path in [Path(__file__), ROOT / "scripts/lns_search.py", ROOT / "scripts/check_cover.py",
                 ROOT / "src/covering64/core.py"]:
        target = args.output / path.name
        target.write_bytes(path.read_bytes())
        sources[path.name] = digest(target)
    metadata = {
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "sources": sources, "seed": args.seed, "seconds_budget": args.seconds,
        "workers": 2, "solver_version": ortools.__version__,
        "input": str(args.candidate), "input_sha256": digest(args.candidate),
        "initial_check": initial, "command": sys.argv,
        "initial_profile": profile(current),
        "schedule": "First 60 percent partial; rest exact; 15s slices; sizes 8/12/16/20/24/28",
        "scope": "Each result concerns only its retained-block neighborhood; no global inference.",
    }
    profiles = []
    if args.profile_cuts:
        profiles = json.loads(args.profile_cuts.read_text())["profiles"]
        metadata["profile_cuts_input_sha256"] = digest(args.profile_cuts)
    for family in profiles:
        if (len(family) != 5 or any(len(t) != 3 for t in family)
                or any(type(p) is not int or not 1 <= p <= 16 for t in family for p in t)
                or len({p for triple in family for p in triple}) != 15):
            raise ValueError("cut triples must be five disjoint triples")
    metadata["initial_profile_cuts"] = profiles
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    real_solver = lns.cp_model.CpSolver
    folder = None
    retained = set()
    cut_records = []

    class RecordedSolver(real_solver):
        def Solve(self, model):  # noqa: N802
            hints = dict(zip(model.proto.solution_hint.vars, model.proto.solution_hint.values))
            block_variables = {int(v.name[6:]): model.get_int_var_from_proto_index(i)
                               for i, v in enumerate(model.proto.variables)
                               if v.name.startswith("block_")}
            cut_records.clear()
            for number, family in enumerate(profiles):
                expressions, hint_counts = [], []
                for triple in family:
                    fixed = sum(set(triple) <= set(universe.blocks[b]) for b in retained)
                    terms = [x for b, x in block_variables.items()
                             if set(triple) <= set(universe.blocks[b])]
                    expressions.append(fixed + sum(terms))
                    hint_counts.append(fixed + sum(hints[x.index] for x in terms))
                checked = add_profile_cut(model, expressions, hint_counts, number)
                if not checked["hint_satisfies_cut"]:
                    raise ValueError("initial candidate hint violates a profile cut")
                cut_records.append({"triples": family, **checked})
            model.export_to_file(str(folder / "model.pbtxt"))
            self.parameters.log_search_progress = True
            self.parameters.log_to_stdout = False
            with (folder / "solver.log").open("w") as log:
                self.log_callback = lambda line: log.write(line + "\n")
                status = super().Solve(model)
            (folder / "response.txt").write_text(self.response_stats())
            return status

    lns.cp_model.CpSolver = RecordedSolver
    rng = random.Random(args.seed)
    began = time.monotonic()
    records = []
    attempt = 0
    try:
        while time.monotonic() - began < args.seconds and best:
            elapsed = time.monotonic() - began
            exact = elapsed >= args.seconds * 0.6
            sizes = [8, 12, 16, 20, 24, 28]
            size = sizes[attempt % len(sizes)]
            removed = lns.choose_removed(universe, current, rng, size)
            rank = {block: i for i, block in enumerate(universe.blocks)}
            retained = {rank[tuple(block)] for block in current} - set(removed)
            folder = args.output / f"attempt-{attempt:03d}"
            folder.mkdir()
            remaining = args.seconds - (time.monotonic() - began)
            if remaining <= 0:
                break
            result = lns.repair_neighborhood(
                universe, current, removed, 64, min(15, remaining),
                seed=args.seed + attempt, change=not exact, exact=exact,
            )
            witness = result.pop("witness")
            result["profile_cuts"] = list(cut_records)
            if witness is not None:
                result["checks"] = verify(witness, folder / "candidate.txt")
                score = result["checks"]["standalone"]["uncovered_count"]
                result["profile"] = profile(witness)
                eligible = result["profile"]["forbidden_five_disjoint"] is None
                if not eligible:
                    new_profile = [list(t) for t in result["profile"]["forbidden_five_disjoint"]]
                    if new_profile not in profiles:
                        profiles.append(new_profile)
                        result["separation_profile_added"] = new_profile
                result["accepted"] = score == 0 or (eligible and score <= best)
                if result["accepted"]:
                    current = witness
                if result["accepted"] and score < best:
                    best = score
                    write_blocks(args.output / "best.txt", witness)
            result["artifact_hashes"] = {
                p.name: digest(p) for p in folder.iterdir() if p.is_file()
            }
            result["attempt"] = attempt
            (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
            records.append(result)
            print(json.dumps({"attempt": attempt, "status": result["status"],
                              "exact": exact, "best_uncovered": best}), flush=True)
            attempt += 1
    finally:
        lns.cp_model.CpSolver = real_solver
    summary = {"best_uncovered": best, "elapsed_seconds": time.monotonic() - began,
               "attempts": records, "final_check": verify(current, args.output / "final.txt")}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"best_uncovered": best, "elapsed_seconds": summary["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
