# Document:    H9 D23 Neutral Queue Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1c5ed1691e0dbe122cc303e5c132e9493d29bfc013c30aaa7187401e949f434d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze the final audited native best; do not launch any search or rebuild binaries."""

import importlib.util
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
PRIOR = DAY / "weak-pair-neutral-queue"
RESUME = DAY / "weak-pair-neutral-queue-resume-01"
NATIVE = DAY / "native-five-core-record-pilot"
REVIEW = DAY / "native-five-core-record-runtime-independent"
HISTORY_REVIEW = DAY / "weak-pair-neutral-queue-resume-01-runtime-independent"
PROOF = DAY / "h11-d25-common-core-cap"
HISTORY_MAP = DAY / "weak-pair-h11-d27-neutral-queue/history-distances.json"
INITIAL_PATH = NATIVE / "seed-2026105601/search-final-weak64.txt"
INITIAL_SHA = "f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681"
PINS = {
    PRIOR / "manifest.json": "5a1082e2f28194ee4c90ee0d16bf0d5b22502164e082e757a35842547eae2a82",
    RESUME / "manifest.json": "aeaa247b3c1f5ba967e968412f59d261659c760e766fd5787637e953ff39b4ba",
    RESUME / "result.json": "be5f44103482a30b80daec84dd44b7fbaaa566adabb20d06ebc446fc033b71e4",
    HISTORY_REVIEW / "postcheck.json": (
        "4393efed14e9281ddc4b72bd43f983f14d384001b9fc16be9205bd9e6440e685"
    ),
    NATIVE / "manifest.json": "32d536037298694fea21fa8207efb328851d9ede135cae2c770833863891ee86",
    NATIVE / "result.json": "5c11a6ee25247bc7b3caf707ae05aba8387d2c5c5a8e26642a483397b451c8f3",
    REVIEW / "postcheck.json": "5d79cdfc0820086e14281538398506c674ce9ecb241e1b3b3739b7aabb067862",
    REVIEW / "postcheck.py": "718e311fe6e1ef50e23d2be7f03e5e6b608b1969fbf926f7f7b1742254937884",
    HISTORY_MAP: "5cbafd3cb65852b91a8973be9f4906cdaa43184a4e186d2d16d61faf7843476e",
    PROOF / "certificate.json": (
        "1006dc7a15b515c075311da4ef8f074d92da60d10ed9fe3b12db23c77dc687ad"
    ),
    PROOF / "core-62.txt": "c2190a6c9fdc0e0f5cc56c991b79c109925e1c3f7ea375ec353535c717415b72",
    INITIAL_PATH: INITIAL_SHA,
}


def main():
    spec = importlib.util.spec_from_file_location("h9_queue_prepare_runner", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    base = runner.base_module()
    require, sha, dump = base.require, base.sha, base.dump
    require(not (HERE / "manifest.json").exists(), "preserve frozen preparation")
    require(not runner.RUN.exists(), "queue campaign already launched")
    inputs = {str(p.relative_to(ROOT)): h for p, h in PINS.items()}

    def inherit(mapping):
        for path, digest in mapping.items():
            require(path not in inputs or inputs[path] == digest, f"conflicting hash: {path}")
            inputs[path] = digest

    for path, digest in PINS.items():
        require(sha(path) == digest, f"pinned artifact changed: {path}")
    prior = json.loads((PRIOR / "manifest.json").read_text())
    resume = json.loads((RESUME / "manifest.json").read_text())
    history = json.loads((RESUME / "result.json").read_text())
    history_post = json.loads((HISTORY_REVIEW / "postcheck.json").read_text())
    native = json.loads((NATIVE / "manifest.json").read_text())
    native_result = json.loads((NATIVE / "result.json").read_text())
    post = json.loads((REVIEW / "postcheck.json").read_text())
    certificate = json.loads((PROOF / "certificate.json").read_text())
    history_map = json.loads(HISTORY_MAP.read_text())
    require(
        post["passed"] and post["campaign_complete"] and not post["cover_found"], "native audit"
    )
    require(post["producer_result_sha256"] == sha(NATIVE / "result.json"), "native result binding")
    require(post["manifest_sha256"] == sha(NATIVE / "manifest.json"), "native manifest binding")
    require(len(native_result["runs"]) == 2 and not native_result["skipped_seeds"], "native finish")
    require(history_post["passed"] and not history_post["cover_found"], "history audit")
    require(
        history_post["producer_result_sha256"] == sha(RESUME / "result.json"),
        "history result binding",
    )
    historical = sorted(history["visited_hashes"])
    require(len(historical) == len(set(historical)) == 34, "expected 34 distinct visited hashes")
    require(sorted(history_post["visited_hashes"]) == historical, "history audit disagreement")
    require(sorted(r["sha256"] for r in history_map["centers"]) == historical, "history path map")
    for manifest in (prior, resume, native):
        for group in ("input_files", "sources", "source_files", "files", "raw_files"):
            inherit(manifest.get(group, {}))
    for group in ("files", "raw_files"):
        inherit(post[group])
    raw_index = ROOT / history["raw_index_path"]
    require(
        sha(raw_index) == history["raw_index_sha256"] == history_post["raw_index_sha256"],
        "history raw index binding",
    )
    inherit({str(raw_index.relative_to(ROOT)): sha(raw_index)})
    inherit(json.loads(raw_index.read_text()))
    for row in history_map["centers"]:
        inherit({row["path"]: row["sha256"]})
    for path, digest in inputs.items():
        require(sha(ROOT / path) == digest, f"inherited artifact changed: {path}")

    qualified = [f for f in post["families"] if f["weak_qualified"] and f["five_caps_pass"]]
    require(bool(qualified), "no independently qualified family")
    selected = min(
        qualified,
        key=lambda f: (f["weak_metrics"]["holes"], f["weak_metrics"]["D2max"], tuple(f["ids"])),
    )
    require(selected["sha256"] == INITIAL_SHA, "audited best selection changed")
    require(post["best_qualified_rank"] == [9, 23], "audited best rank changed")
    adapter = runner.load(PRIOR / "adapter.py", "h9_queue_prepare_adapter")
    recorders = {kind: adapter.Recorder(kind) for kind in ("one", "two")}
    initial = base.verify_family(selected["ids"], recorders["one"], prior["core_rows"])
    require(
        initial == base.verify_family(selected["ids"], recorders["two"], prior["core_rows"]),
        "recorder profiles differ",
    )
    require(initial["sha256"] == sha(INITIAL_PATH) == INITIAL_SHA, "start hash disagreement")
    require(initial["metrics"] == selected["weak_metrics"], "audited profile disagreement")
    require(list(runner.rank(initial)) == [9, 23], "initial rank disagreement")
    require(INITIAL_SHA not in historical, "initial already visited")

    block_ids = {tuple(block): index for index, block in enumerate(recorders["one"].BLOCKS)}
    distance_rows = []
    for row in history_map["centers"]:
        parsed = recorders["one"].STANDALONE.parse_witness((ROOT / row["path"]).read_text())
        ids = [block_ids[tuple(block)] for block in parsed]
        require(len(ids) == len(set(ids)) == 64, "malformed historical family")
        require(
            recorders["one"].family_text(ids) == (ROOT / row["path"]).read_text(),
            "noncanonical historical family",
        )
        distance = 64 - len(set(initial["ids"]) & set(ids))
        distance_rows.append({**row, "one_swap_distance": distance})
    minimum_distance = min(row["one_swap_distance"] for row in distance_rows)
    require(minimum_distance > 32, "historical join policy needs review before freeze")
    require(certificate["passed"] and certificate["exact_64_overlap_cap"] == 56, "fifth core proof")
    fifth_ids = certificate["core_ids"]
    require(len(fifth_ids) == len(set(fifth_ids)) == 62, "fifth core cardinality")
    fifth_overlap = len(set(initial["ids"]) & set(fifth_ids))
    require(fifth_overlap == 1 and fifth_overlap + 32 < 56, "fifth cap radius bound")
    dump(
        HERE / "history-distances.json",
        {
            "initial_sha256": INITIAL_SHA,
            "centers": distance_rows,
            "visited_count": 34,
            "minimum_one_swap_distance": minimum_distance,
            "maximum_center_radius": 30,
            "maximum_inspected_candidate_radius": 32,
            "no_historical_join_within_budget": True,
            "scope": "Named families only; 15 transitions and a final two-swap inspection.",
        },
    )
    controls = json.loads((HERE / "controls.json").read_text())
    require(controls["passed"] and controls["native_search_launches"] == 0, "controls failed")
    require(
        controls["runner_sha256"] == sha(HERE / "run.py")
        and controls["controls_sha256"] == sha(HERE / "controls.py"),
        "controls binding",
    )
    dump(
        HERE / "frontier.json",
        {
            "frontier": [initial],
            "best_rank": [9, 23],
            "visited_hashes": historical,
            "native_result_sha256": sha(NATIVE / "result.json"),
            "native_runtime_audit_sha256": sha(REVIEW / "postcheck.json"),
        },
    )
    (HERE / "initial.txt").write_text(recorders["one"].family_text(initial["ids"]))
    sources = {
        str((HERE / p).relative_to(ROOT)): sha(HERE / p)
        for p in ("run.py", "prepare.py", "controls.py")
    }
    files = {
        str((HERE / p).relative_to(ROOT)): sha(HERE / p)
        for p in (
            "README.md",
            "controls.json",
            "frontier.json",
            "initial.txt",
            "history-distances.json",
        )
    }
    manifest = {
        "document": "H9 D23 Strict-First Neutral Queue Manifest",
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
        "native_manifest_sha256": sha(NATIVE / "manifest.json"),
        "native_result_sha256": sha(NATIVE / "result.json"),
        "native_runtime_audit_sha256": sha(REVIEW / "postcheck.json"),
        "selection": "Minimum audited weak-qualified five-cap (holes,D2max,full block IDs).",
        "initial": initial,
        "historical_visited_hashes": historical,
        "seed_revisit_exception": None,
        "resume_frontier_path": str((HERE / "frontier.json").relative_to(ROOT)),
        "resume_frontier_count": 1,
        "resume_rank": [9, 23],
        "history_distance_path": str((HERE / "history-distances.json").relative_to(ROOT)),
        "budget": {
            "max_centers": 16,
            "max_shell_launches": 32,
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
        "observed_fifth_core": {
            "ids": fifth_ids,
            "threshold": 56,
            "diagnostic_only": True,
            "witness_path": str((PROOF / "core-62.txt").relative_to(ROOT)),
            "witness_sha256": sha(PROOF / "core-62.txt"),
            "certificate_sha256": sha(PROOF / "certificate.json"),
            "initial_overlap": fifth_overlap,
            "maximum_candidate_radius": 32,
            "maximum_overlap_within_budget": fifth_overlap + 32,
            "scope": "Budget-dependent bound only; no fifth filter or all-relabel claim.",
        },
        "neutral_cap_per_shell": prior["neutral_cap_per_shell"],
        "neutral_sampling": prior["neutral_sampling"],
        "input_files": inputs,
        "sources": sources,
        "files": files,
        "raw_files": {},
        "scope": "From audited H9/D2max23, exclude all 34 prior visited hashes. At most "
        "16 centers/32 exact one/two-swap shells with unchanged four cap55 and weak "
        "filters. Fifth cap56 is diagnostic only. First64 neutral traversal samples "
        "are not global lexicographic minima or plateau exhaustion. No global theorem.",
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "manifest_sha256": sha(HERE / "manifest.json"),
                "initial_sha256": INITIAL_SHA,
                "minimum_history_distance": minimum_distance,
                "fifth_overlap_budget_bound": fifth_overlap + 32,
                "search_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
