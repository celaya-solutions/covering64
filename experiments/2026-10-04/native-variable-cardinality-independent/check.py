# Document:    Independent Native Variable Cardinality Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      aeff317f9d4408ec2720b5e5b0b2cb895e44c5592b7bb177be98d7deacf0fcca
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Bind independent naive controls, parser rejections, and dual witness checks."""

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
PRODUCER = HERE.parent / "native-variable-cardinality"
RAW = ROOT / "experiments/scratch/native-variable-cardinality-independent-20261004"
EXPECTED = "f79075467ba41b46e53491c032044a23fe9766c680309055c1ff5d0697ec354b"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output = HERE / "gate.json"
    require(not output.exists(), "gate already exists; never overwrite")
    manifest_path = PRODUCER / "manifest.json"
    require(sha(manifest_path) == EXPECTED, "manifest changed")
    manifest = json.loads(manifest_path.read_text())
    bindings = []
    for group in ("source_files", "input_files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, f"bound artifact changed: {relative}")
            bindings.append({"group": group, "path": relative, "sha256": digest})
    require(len(bindings) == 29, "expected 29 artifact bindings")
    require(sha(manifest["compiler_path"]) == manifest["compiler_sha256"], "compiler binding")
    require(manifest["all_blocks"] == 4368 and manifest["triples"] == 560, "universe size")
    require(manifest["optimization_launched"] is False, "producer already launched")
    budget = manifest["budget"]
    require(
        budget["max_runs"] == 2
        and budget["seconds_per_run"] == 120
        and budget["seeds"] == [2026104701, 2026104702]
        and budget["simultaneous_processes"] == 1
        and budget["stop_after_first_complete_at_most_64"],
        "budget mismatch",
    )
    stats_path = RAW / "final-control/control.json"
    stats = json.loads(stats_path.read_text())
    require(stats["passed"] and stats["optimizer_launches"] == 0, "kernel controls failed")
    require(stats["all_block_score_checks"] == 4368 * stats["snapshots"], "incomplete scores")
    require(
        stats["incoming_choices"] == 500 and stats["operation_rejections"] == 11,
        "missing rejection/selection controls",
    )
    require(
        all(
            stats["branches"][branch] > 0
            for branch in ("complete_drop", "add_only", "swap", "double_drop")
        ),
        "branch coverage",
    )
    binary = RAW / "control-sanitized"
    baseline = ROOT / manifest["start_path"]
    text = baseline.read_text()
    rows = text.splitlines()
    malformed = {
        "duplicate": rows[:-1] + [rows[0]],
        "damaged_label": ["0 " + " ".join(rows[0].split()[1:])] + rows[1:],
        "malformed_size": [" ".join(rows[0].split()[:-1])] + rows[1:],
        "truncated": rows[:-1],
        "duplicate_label": ["1 1 3 4 6"] + rows[1:],
        "damaged_cover": ["1 2 3 4 5"] + rows[1:],
    }
    rejection = []
    for name, lines in malformed.items():
        path = RAW / f"{name}.txt"
        require(not path.exists(), "control fixture exists")
        path.write_text("\n".join(lines) + "\n")
        run = subprocess.run(
            [str(binary), str(path), str(RAW / f"reject-{name}")], capture_output=True, text=True
        )
        (RAW / f"reject-{name}.stdout").write_text(run.stdout)
        (RAW / f"reject-{name}.stderr").write_text(run.stderr)
        require(
            run.returncode == 1
            and "INDEPENDENT:" in run.stderr
            or run.returncode == 1
            and any(
                word in run.stderr
                for word in ("duplicate block", "malformed label", "malformed block")
            ),
            f"expected parser/baseline rejection missing: {name}",
        )
        require(
            "AddressSanitizer" not in run.stderr and "runtime error:" not in run.stderr,
            f"sanitizer error: {name}",
        )
        rejection.append(
            {
                "name": name,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "returncode": run.returncode,
                "stderr": run.stderr.strip(),
            }
        )
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    spec = importlib.util.spec_from_file_location(
        "standalone_vc_gate", ROOT / "scripts/check_cover.py"
    )
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    verified = []
    for path in sorted((RAW / "final-control").glob("*.txt")):
        blocks = [tuple(sorted(map(int, line.split()))) for line in path.read_text().splitlines()]
        require(
            all(
                len(row) == len(set(row)) == 5 and min(row) >= 1 and max(row) <= 16
                for row in blocks
            )
            and len(set(blocks)) == len(blocks),
            "invalid saved family",
        )
        counts = Counter(t for block in blocks for t in itertools.combinations(block, 3))
        holes = [t for t in itertools.combinations(range(1, 17), 3) if not counts[t]]
        package = verify_cover(blocks, 16, 5, 3)
        separate = standalone.verify_cover(blocks, 16, 5, 3, expected_blocks=len(blocks))
        require(
            sorted(map(tuple, package["uncovered"]))
            == holes
            == sorted(map(tuple, separate["uncovered"])),
            "independent holes mismatch",
        )
        require(package["valid"] == separate["valid"] == (not holes), "cover verdict mismatch")
        require(package["canonical_sha256"] == separate["canonical_sha256"], "canonical mismatch")
        verified.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "blocks": len(blocks),
                "holes": len(holes),
                "package": package,
                "standalone": separate,
                "raw_subset_count_pass": True,
            }
        )
    require(len(verified) == 4, "missing saved-family checks")
    receipt = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": EXPECTED,
        "optimizer_launches": 0,
        "launch_authority": "root only",
        "checker_sha256": sha(__file__),
        "control_source_sha256": sha(HERE / "control.cpp"),
        "control_binary_sha256": sha(binary),
        "controls_sha256": sha(stats_path),
        "artifact_bindings": bindings,
        "compiler_hash_checked": True,
        "kernel_controls": stats,
        "parser_and_damaged_controls": rejection,
        "saved_family_verification": verified,
        "approved_budget": budget,
        "independent_reference": "16-bit masks; all scores and counts recounted naively",
        "source_rules": {
            "score_pscore": "weighted exact c0/c1/c2 cases",
            "ranking": "5*score+pscore, pscore, oldest flip, declared global-lex tie",
            "CC": "shared-triple neighbors enabled; removed block disabled last",
            "age": "at least4 with no unsigned underflow",
            "novelty": "11 of100 residues",
            "weights": "only uncovered increments after add-only; no decay",
            "double_drop": "recompute second outgoing after first removal",
            "cardinality": "primitive freedom; strict incumbent guard on trajectory",
            "cores": "diagnostic only; admissible64 label only at cardinality64",
        },
        "driver_review": {
            "reviewer": "separate exact-search agent",
            "search_sha256": "998f48d22bf446d2503d5fe4b37f217a10cd6a0cb699be6520be6cd7ea7bfb87",
            "run_sha256": "ba0ca55309896befe2c8dfabc19a9b8ae4db7243cecfb7e9516b151e4ffd7d2c",
            "blocking_findings": [],
            "findings": "observer after each primitive; immediate stop; final/current saved;"
            " actual cardinality dual verified; deadline checked each advance; watchdog bound",
        },
        "limitations": [
            "Finite controls support source review, not a proof of search quality.",
            "Target predicate unit controls use synthetic scalar metadata, not covering witnesses.",
            "No actual <=64 cover supplied; accepted target path reviewed structurally.",
            "Pre-format manifest retained; old Python source bytes were not separately retained.",
            "No lower bound or theorem is claimed.",
        ],
        "upstream_revision": manifest["upstream_revision"],
        "upstream_reference": "https://github.com/chuanluocs/NuSC-Algorithm/commit/"
        "fdacd80d92e7143b4fe305bddce471a1e8982e90",
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "GO",
                "gate_sha256": sha(output),
                "snapshots": stats["snapshots"],
                "score_checks": stats["all_block_score_checks"],
            }
        )
    )


if __name__ == "__main__":
    main()
