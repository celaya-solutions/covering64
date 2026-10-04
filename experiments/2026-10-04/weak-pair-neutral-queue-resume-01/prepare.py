# Document:    Checked Neutral Queue Resume Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      58a4e34b368e89a8468c1846d355bbd900dced1718132d4e1cf8d96ad4f4d77b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze checked previous frontier; reuse native artifacts without compiling or running them."""

import importlib.util
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent / "weak-pair-neutral-queue"
REVIEW = HERE.parent / "weak-pair-neutral-queue-runtime-independent"
PINS = {
    PRIOR / "manifest.json": "5a1082e2f28194ee4c90ee0d16bf0d5b22502164e082e757a35842547eae2a82",
    PRIOR / "result.json": "086524c3b7f8db6e11ab6b3e321c379facc36b3f51fb163740e7cc7fdac9d048",
    REVIEW / "postcheck.json": "fd044b1f88955403181b2d6ac739526c2d27ded14b0cff66f36a59d40a1cdde3",
    REVIEW / "unscanned-frontier.json": (
        "523ab6b38b23748885d19023d41b0dde5cdbd52b06b920aec6c1418f706ffe06"
    ),
}


def main():
    spec = importlib.util.spec_from_file_location("resume_prepare_runner", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    base = runner.base_module()
    require, sha, dump = base.require, base.sha, base.dump
    require(not (HERE / "manifest.json").exists(), "preserve frozen preparation")
    require(not runner.RUN.exists(), "resume campaign already launched")
    for path, digest in PINS.items():
        require(sha(path) == digest, f"pinned previous artifact changed: {path}")
    prior = json.loads((PRIOR / "manifest.json").read_text())
    result = json.loads((PRIOR / "result.json").read_text())
    post = json.loads((REVIEW / "postcheck.json").read_text())
    source_frontier = json.loads((REVIEW / "unscanned-frontier.json").read_text())
    require(post["passed"] is True and not post["cover_found"], "prior audit did not pass")
    require(post["producer_result_sha256"] == sha(PRIOR / "result.json"), "result audit binding")
    require(
        post["unscanned_frontier_sha256"] == sha(REVIEW / "unscanned-frontier.json"),
        "frontier audit binding",
    )
    require(
        source_frontier["producer_result_sha256"] == sha(PRIOR / "result.json"),
        "frontier result binding",
    )
    require(
        result["stop_reason"] == "center_budget" and result["centers_processed"] == 16,
        "only resume completed campaign",
    )
    require(
        result["shell_launches"] == 32 and all(r["complete"] for r in result["centers"]),
        "prior shells incomplete",
    )
    require(post["best_rank"] == source_frontier["best_rank"] == [11, 25], "resume rank changed")
    historical = sorted(set(source_frontier["visited_hashes"]))
    require(
        historical == sorted(result["visited_hashes"]) == sorted(post["visited_hashes"]),
        "history disagreement",
    )
    inputs = {str(p.relative_to(ROOT)): h for p, h in PINS.items()}
    for group in ("input_files", "sources", "files", "raw_files"):
        inputs.update(prior[group])
    raw_index = ROOT / result["raw_index_path"]
    require(
        sha(raw_index) == result["raw_index_sha256"] == post["raw_index_sha256"],
        "prior raw index binding",
    )
    inputs[str(raw_index.relative_to(ROOT))] = sha(raw_index)
    # This is an archival integrity check, not a replay of any search kernel.
    for path, digest in json.loads(raw_index.read_text()).items():
        require(sha(ROOT / path) == digest, f"prior raw artifact changed: {path}")
    for path, digest in inputs.items():
        require(sha(ROOT / path) == digest, f"inherited artifact changed: {path}")
    adapter = runner.load(PRIOR / "adapter.py", "resume_prepare_adapter")
    recorders = {kind: adapter.Recorder(kind) for kind in ("one", "two")}
    frontier = []
    for state in source_frontier["families"]:
        checked = base.verify_family(state["ids"], recorders["one"], prior["core_rows"])
        require(
            checked == base.verify_family(state["ids"], recorders["two"], prior["core_rows"]),
            "frontier profiles disagree",
        )
        require(
            checked["sha256"] == state["sha256"] and checked["metrics"] == state["metrics"],
            "independent frontier profile differs",
        )
        require(runner.rank(checked) == (11, 25), "frontier rank differs")
        require(checked["sha256"] not in historical, "frontier contains visited center")
        frontier.append(checked)
    require(len(frontier) == post["unscanned_frontier_count"] == 14, "frontier count differs")
    require(len({s["sha256"] for s in frontier}) == 14, "duplicate frontier")
    require(frontier == sorted(frontier, key=lambda s: tuple(s["ids"])), "frontier ordering")
    require(frontier[0]["sha256"] == result["unscanned_next"]["sha256"], "designated next changed")
    controls = json.loads((HERE / "controls.json").read_text())
    require(controls["passed"] and controls["native_search_launches"] == 0, "controls failed")
    require(
        controls["runner_sha256"] == sha(HERE / "run.py")
        and controls["controls_sha256"] == sha(HERE / "controls.py"),
        "controls source binding",
    )
    dump(
        HERE / "frontier.json",
        {
            "frontier": frontier,
            "best_rank": [11, 25],
            "visited_hashes": historical,
            "producer_result_sha256": sha(PRIOR / "result.json"),
            "independent_frontier_sha256": sha(REVIEW / "unscanned-frontier.json"),
        },
    )
    (HERE / "initial.txt").write_text(recorders["one"].family_text(frontier[0]["ids"]))
    sources = {
        str((HERE / p).relative_to(ROOT)): sha(HERE / p)
        for p in ("run.py", "prepare.py", "controls.py")
    }
    files = {
        str((HERE / p).relative_to(ROOT)): sha(HERE / p)
        for p in ("README.md", "controls.json", "frontier.json", "initial.txt")
    }
    manifest = {
        "document": "Resumed Strict-First Neutral Queue Manifest",
        "version": "v1.0.0",
        "author": "Celaya Solutions",
        "contact": "hello@celayasolutions.com",
        "date": "2026-10-04",
        "chain": "n/a",
        "tx": "[not anchored]",
        "license": "All Rights Reserved / Celaya Solutions",
        "status": "PREPARED_NOT_RUN",
        "search_launches": 0,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "prior_manifest_sha256": sha(PRIOR / "manifest.json"),
        "prior_result_sha256": sha(PRIOR / "result.json"),
        "prior_runtime_review_sha256": sha(REVIEW / "postcheck.json"),
        "initial": frontier[0],
        "historical_visited_hashes": historical,
        "seed_revisit_exception": None,
        "resume_frontier_path": str((HERE / "frontier.json").relative_to(ROOT)),
        "resume_frontier_count": len(frontier),
        "resume_rank": [11, 25],
        "budget": {
            "max_centers": 32,
            "max_shell_launches": 64,
            "seconds_per_shell": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "seed": None,
            "relaunch": False,
            "budget_transfer": False,
        },
        "core_rows": prior["core_rows"],
        "shells": prior["shells"],
        "reused_evaluation_headers": prior["reused_evaluation_headers"],
        "input_files": inputs,
        "sources": sources,
        "files": files,
        "raw_files": {},
        "scope": (
            "Resume all 14 retained rank(H11,D2max25) frontier states, "
            "excluding 20 historical centers. At most 32 new centers and 64 exact "
            "one/two-swap shells. Reuse frozen native kernels. Neutral samples remain "
            "capped traversal samples; sample exhaustion is not a global proof."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "manifest_sha256": sha(HERE / "manifest.json"),
                "frontier_count": len(frontier),
                "historical_count": len(historical),
                "initial_sha256": frontier[0]["sha256"],
                "native_search_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
