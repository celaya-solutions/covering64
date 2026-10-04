# Document:    Independent Native Partial-Start Variant Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit only changed initialization/driver paths; reuse the exact kernel gate."""

import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "native-variable-partial-start"
RAW = ROOT / "experiments/scratch/native-variable-partial-start-independent-20261004"
MANIFEST = "d66e4f2dfe7604b06dcd9d94ac49efc0c82b748b03977195e4a3924f6b2daaa5"
OLD_GATE = "300677f074664d001cba3c63cb156e13e2648020cfa28908560b5f761ad3c6ff"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
RANK = {block: index for index, block in enumerate(BLOCKS)}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse(path):
    rows = [tuple(map(int, line.split())) for line in path.read_text().splitlines() if line.strip()]
    require(rows == sorted(rows) and len(rows) == len(set(rows)), "order/duplicate")
    require(all(row in RANK for row in rows), "malformed block")
    return rows


def metrics(ids, cores):
    counts = Counter(t for i in ids for t in itertools.combinations(BLOCKS[i], 3))
    return {
        "cardinality": len(ids),
        "holes": 560 - len(counts),
        "core_overlaps": [len(set(ids).intersection(core)) for core in cores],
    }


def main():
    output = HERE / "gate.json"
    require(not output.exists(), "gate exists")
    path = PRODUCER / "manifest.json"
    require(sha(path) == MANIFEST, "manifest changed")
    manifest = json.loads(path.read_text())
    bindings = []
    for group in ("source_files", "input_files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, f"binding changed: {relative}")
            bindings.append({"path": relative, "sha256": digest, "group": group})
    require(
        manifest["reused_kernel_gate_sha256"]
        == OLD_GATE
        == sha(ROOT / manifest["reused_kernel_gate_path"]),
        "old gate changed",
    )
    for name, digest in manifest["reused_kernel_hashes"].items():
        require(
            sha(PRODUCER / name)
            == digest
            == sha(HERE.parent / "native-variable-cardinality" / name),
            "kernel/core bytes changed",
        )
    budget = manifest["budget"]
    require(
        budget["max_runs"] == 2
        and budget["seconds_per_run"] == 300
        and budget["seeds"] == [2026104801, 2026104802]
        and budget["simultaneous_processes"] == 1
        and not budget["relaunch"]
        and budget["stop_after_first_complete_at_most_64"],
        "budget mismatch",
    )
    require(not manifest["timed_optimization_launched"], "unexpected prior timed run")
    require(sha(manifest["compiler_path"]) == manifest["compiler_sha256"], "compiler changed")
    for build in manifest["builds"]:
        if build["binary_sha256"] == manifest["binary_sha256"]:
            require(
                not any("VC_CONTROL_STEPS" in arg for arg in build["command"]),
                "control production binary",
            )
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    spec = importlib.util.spec_from_file_location(
        "partial_standalone", ROOT / "scripts/check_cover.py"
    )
    separate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(separate)
    cores = manifest["core_rows"]
    incumbent = ROOT / manifest["incumbent_path"]
    all_families, results = [], []

    def check_family(path, expected):
        blocks = parse(path)
        ids = [RANK[block] for block in blocks]
        actual = metrics(ids, cores)
        require(actual == expected, f"actual family metric mismatch: {path}")
        package = verify_cover(blocks, 16, 5, 3)
        standalone = separate.verify_cover(blocks, 16, 5, 3, len(blocks))
        require(
            len(package["uncovered"]) == standalone["uncovered_count"] == actual["holes"], "holes"
        )
        require(package["valid"] == standalone["valid"] == (actual["holes"] == 0), "cover verdict")
        require(package["canonical_sha256"] == standalone["canonical_sha256"], "canonical hash")
        all_families.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "metrics": actual,
                "package": package,
                "standalone": standalone,
            }
        )
        return ids

    check_family(incumbent, {"cardinality": 65, "holes": 0, "core_overlaps": [60, 0, 1, 1]})
    for initial, seed, holes in zip(
        manifest["initial_partials"], budget["seeds"], (9, 12), strict=True
    ):
        partial = ROOT / initial["path"]
        require(
            initial["seed"] == seed and initial["metrics"]["holes"] == holes, "start seed/holes"
        )
        require(sha(partial) == initial["sha256"], "initial candidate hash")
        initial_ids = check_family(partial, initial["metrics"])
        require(
            len(initial_ids) == 64 and max(initial["metrics"]["core_overlaps"]) <= 55,
            "partial start",
        )
        init = subprocess.run(
            [str(RAW / "init"), str(incumbent), str(partial), str(holes)],
            capture_output=True,
            text=True,
        )
        require(init.returncode == 0 and not init.stderr, "fresh-state control failed")
        constructor = json.loads(init.stdout)
        require(constructor["passed"] and constructor["timed_searches"] == 0, "constructor result")
        for steps in (0, 8):
            directory = RAW / f"seed-{seed}-steps-{steps}"
            directory.mkdir()
            command = [
                str(RAW / f"control-{steps}"),
                str(incumbent),
                str(partial),
                str(seed),
                "300",
                str(directory / "search"),
            ]
            run = subprocess.run(command, capture_output=True, text=True)
            (directory / "stdout.jsonl").write_text(run.stdout)
            (directory / "stderr.txt").write_text(run.stderr)
            require(run.returncode == 1 and not run.stderr, "fixed-step driver failure")
            events = [json.loads(line) for line in run.stdout.splitlines()]
            require(
                events[0]
                == {
                    "event": "start",
                    "seed": seed,
                    "budget": 300,
                    "mode": "control",
                    "control_step_limit": steps,
                },
                "control identification",
            )
            records = [e for e in events if e["event"] == "record"]
            require(
                [e["role"] for e in records[:3]] == ["complete", "raw64", "admissible64"],
                "initial roles",
            )
            require(all(e["mutations"] == e["step"] == 0 for e in records[:3]), "initial mutations")
            require(
                records[0]["metrics"] == manifest["initial_complete"]["metrics"], "incumbent record"
            )
            require(
                all(e["metrics"] == initial["metrics"] for e in records[1:3]), "partial records"
            )
            latest = {}
            for event in records:
                role = event["role"]
                witness = directory / f"search-record-{event['serial']}-{role}.txt"
                check_family(witness, event["metrics"])
                if role == "admissible64":
                    require(
                        event["metrics"]["cardinality"] == 64
                        and max(event["metrics"]["core_overlaps"]) <= 55,
                        "admissible label",
                    )
                latest[role] = witness
            for event, source in zip(records[:3], (incumbent, partial, partial), strict=True):
                witness = directory / f"search-record-{event['serial']}-{event['role']}.txt"
                require(sha(witness) == sha(source), "initial record bytes differ")
            final = events[-1]
            require(final["iterations"] == steps, "fixed-step iteration count")
            traces = [e for e in events if e["event"] == "trace"]
            require([e["step"] for e in traces] == list(range(steps)), "trace order")
            ids, weights = set(initial_ids), {triple: 1 for triple in TRIPLES}
            sizes, mutations, weight_updates = [64], 0, 0
            for trace in traces:
                before = metrics(sorted(ids), cores)
                require(before["holes"] > 0, "trace after cover")
                target = TRIPLES[trace["target"]]
                require(not any(set(target) <= set(BLOCKS[i]) for i in ids), "target is covered")
                require(trace["fallback"] == (trace["step"] < 4), "first-four fallback behavior")
                if trace["fallback"]:
                    first = next(i for i, block in enumerate(BLOCKS) if set(target) <= set(block))
                    require(trace["incoming"] == first, "fallback not first lex carrier")
                for removed in trace["removed"]:
                    if removed >= 0:
                        require(removed in ids, "remove absent")
                        ids.remove(removed)
                        mutations += 1
                        sizes.append(len(ids))
                if trace["action"] in ("swap", "add_only"):
                    require(trace["incoming"] not in ids, "add duplicate")
                    ids.add(trace["incoming"])
                    mutations += 1
                    sizes.append(len(ids))
                require(metrics(sorted(ids), cores) == trace["metrics"], "trace raw recount")
                require(
                    trace["weights_updated"] == (trace["action"] == "add_only"), "weight policy"
                )
                if trace["weights_updated"]:
                    counts = Counter(t for i in ids for t in itertools.combinations(BLOCKS[i], 3))
                    for triple in TRIPLES:
                        if not counts[triple]:
                            weights[triple] += 1
                    weight_updates += 1
            require(
                final["mutations"] == mutations and final["weight_updates"] == weight_updates,
                "initial/final counter accounting",
            )
            require(
                final["min_cardinality"] == min(sizes) and final["max_cardinality"] == max(sizes),
                "live range polluted by65 incumbent",
            )
            require(
                final["fallbacks"] == min(4, steps)
                and final["max_weight"] == max(weights.values()),
                "fresh age/weight runtime fields",
            )
            for role in ("current", "complete", "raw64", "admissible64"):
                witness = directory / f"search-final-{role}.txt"
                check_family(witness, final[role])
                if role != "current":
                    require(sha(witness) == sha(latest[role]), "final record mismatch")
            results.append(
                {
                    "seed": seed,
                    "steps": steps,
                    "command": command,
                    "constructor": constructor,
                    "returncode": run.returncode,
                    "final": final,
                    "stdout_sha256": sha(directory / "stdout.jsonl"),
                    "stderr_sha256": sha(directory / "stderr.txt"),
                }
            )
    # Wrong-role and wrong-budget calls use the zero-step control executable only.
    partial = ROOT / manifest["initial_partials"][0]["path"]
    refusals = []
    for name, complete_arg, partial_arg, seconds in (
        ("partial_as_incumbent", partial, partial, "300"),
        ("complete_as_partial", incumbent, incumbent, "300"),
        ("wrong_budget", incumbent, partial, "120"),
    ):
        prefix = RAW / f"reject-{name}"
        run = subprocess.run(
            [
                str(RAW / "control-0"),
                str(complete_arg),
                str(partial_arg),
                "2026104801",
                seconds,
                str(prefix),
            ],
            capture_output=True,
            text=True,
        )
        require(
            run.returncode == 3 and not run.stdout and bool(run.stderr),
            "wrong-role/budget accepted",
        )
        refusals.append({"name": name, "returncode": run.returncode, "stderr": run.stderr.strip()})
    receipt = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": MANIFEST,
        "timed_optimizer_launches": 0,
        "launch_authority": "root only",
        "source_sha256": sha(__file__),
        "init_control_sha256": sha(HERE / "init.cpp"),
        "reused_kernel_gate_sha256": OLD_GATE,
        "reused_kernel_hashes": manifest["reused_kernel_hashes"],
        "artifact_bindings": bindings,
        "approved_budget": budget,
        "controls": results,
        "saved_families": all_families,
        "wrong_role_budget_rejections": refusals,
        "control_binaries": {
            str(RAW / name): sha(RAW / name) for name in ("init", "control-0", "control-8")
        },
        "driver_review": {
            "reviewer": "separate exact-search agent",
            "blocking_findings": [],
            "search_sha256": "9516dd7eb67e2f1df84a52a47569ddc0fe2b74938ac0f76c9b5a1410ab25c1d6",
            "run_sha256": "09a812d8ea1af82a1fd9175e212e6c9650d99ebc4d05892d0bff4bebb4510ef1",
        },
        "scope": (
            "Changed initialization/driver/runner only; "
            "exact old kernel proof/control gate reused"
        ),
        "limits": "Fixed0/8-step controls are not timed search runs or covering discoveries.",
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "GO",
                "gate_sha256": sha(output),
                "fixed_step_runs": len(results),
                "saved_family_checks": len(all_families),
            }
        )
    )


if __name__ == "__main__":
    main()
