# Document:    Variable-Cardinality Best-64 Relabeled-Core Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      d5196d06301996b0ff7930d16c26f98e64bece61c394c199c69e7a02348c12ff
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import importlib.util
import itertools
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "native-variable-cardinality"
HELPER = HERE.parent / "six-hole-strong-core-release-independent/relabels.py"
HELPER_SHA = "9cdcd511eb94954bb45c1cf209c5d51517b46c11e46b44a22ce7221d9309f74a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    assert not (HERE / "screen.json").exists(), "preserve completed screen"
    manifest, result = read(SOURCE / "manifest.json"), read(SOURCE / "result.json")
    assert result["manifest_sha256"] == sha(SOURCE / "manifest.json")
    assert result["budget"] == manifest["budget"]
    runs = result["runs"]
    assert len(runs) in (1, 2)
    assert [row["seed"] for row in runs] == result["budget"]["seeds"][: len(runs)]
    assert all(row["validation_passed"] for row in runs)
    if len(runs) < result["budget"]["max_runs"]:
        last = runs[-1]
        assert last["success"] or last["watchdog"]["fired"] or last["returncode"] != 1, (
            "pilot still running"
        )
    raw = (ROOT / manifest["binary_path"]).parent
    gate_path = raw / "frozen-sources/gate.json"
    assert sha(gate_path) == result["gate_sha256"] and read(gate_path)["passed"]
    for path, digest in (
        manifest["source_files"] | manifest["input_files"] | manifest["raw_files"]
    ).items():
        assert sha(ROOT / path) == digest
    assert sha(HELPER) == HELPER_SHA
    spec = importlib.util.spec_from_file_location("pinned_relabel_screen", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    controls = helper.selfcheck()
    assert controls["passed"]
    finals, final_pool = [], []
    for run in runs:
        for stream in ("stdout", "stderr"):
            assert sha(ROOT / run[stream]["path"]) == run[stream]["sha256"]
        row = run["final_rows"]["admissible64"]
        candidates = [
            saved
            for saved in run["snapshots"]
            if saved["role"] in ("admissible64", "final_admissible64")
        ]
        if row is None:
            assert not candidates
            continue
        assert row["metrics"]["cardinality"] == 64 and row["cap_admissible"]
        assert row["metrics"]["holes"] == min(saved["metrics"]["holes"] for saved in candidates)
        assert sha(ROOT / row["path"]) == row["sha256"]
        finals.append({"seed": run["seed"], **row})
        final_pool.append({"seed": run["seed"], **row})
        for role in ("current", "raw64"):
            other = run["final_rows"][role]
            if (
                other is not None
                and other["metrics"]["cardinality"] == 64
                and other["cap_admissible"]
            ):
                assert other["metrics"]["holes"] >= row["metrics"]["holes"]
                final_pool.append({"seed": run["seed"], **other})
    best_holes = min((row["metrics"]["holes"] for row in finals), default=None)
    chosen = [row for row in final_pool if row["metrics"]["holes"] == best_holes]
    unique = {}
    for row in chosen:
        seeds = unique.setdefault(row["sha256"], {"row": row, "seeds": []})["seeds"]
        if row["seed"] not in seeds:
            seeds.append(row["seed"])
    screened = []
    for index, (digest, entry) in enumerate(unique.items()):
        row, path = entry["row"], ROOT / entry["row"]["path"]
        blocks = [
            tuple(map(int, line.split()))
            for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        assert len(blocks) == len(set(blocks)) == 64
        assert all(block in helper.RANK for block in blocks)
        ids = [helper.RANK[block] for block in blocks]
        assert ids == sorted(ids), "preserve lexicographic block order"
        covered = {triple for block in blocks for triple in itertools.combinations(block, 3)}
        holes = 560 - len(covered)
        assert holes == row["metrics"]["holes"] == best_holes
        overlaps = [len(set(ids) & set(core)) for core in manifest["core_rows"]]
        assert overlaps == row["metrics"]["core_overlaps"] and max(overlaps) <= 55
        receipts = []
        for name, command in (
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
        ):
            checked = subprocess.run(
                command + [str(path), "--expected-blocks", "64"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert checked.returncode == int(holes != 0) and not checked.stderr
            payload = json.loads(checked.stdout)
            assert payload["blocks"] == 64 and payload["valid"] == (holes == 0)
            assert len(payload["uncovered"]) == holes
            receipt = HERE / f"best-{index:02d}-{name}.json"
            receipt.write_text(checked.stdout)
            receipts.append(
                {
                    "path": str(receipt.relative_to(ROOT)),
                    "sha256": sha(receipt),
                    "canonical_sha256": payload["canonical_sha256"],
                }
            )
        assert receipts[0]["canonical_sha256"] == receipts[1]["canonical_sha256"]
        screen = helper.check(ids)
        screened.append(
            {
                "path": row["path"],
                "sha256": digest,
                "seeds": entry["seeds"],
                "holes": holes,
                "named_core_overlaps": overlaps,
                "screen": screen,
                "verifiers": receipts,
            }
        )
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "helper_path": str(HELPER.relative_to(ROOT)),
        "helper_sha256": HELPER_SHA,
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "result_sha256": sha(SOURCE / "result.json"),
        "gate_sha256": result["gate_sha256"],
        "helper_controls": controls,
        "admissible64_finals": [
            {
                "seed": row["seed"],
                "path": row["path"],
                "sha256": row["sha256"],
                "metrics": row["metrics"],
            }
            for row in finals
        ],
        "selection": "Minimum hole count among final admissible64 states; retain every distinct "
        "tie among admissible64, current and raw64 final families that pass the named caps.",
        "best_holes": best_holes,
        "screened_unique_families": len(screened),
        "families": screened,
        "scope": "Applies only to saved states with 64 distinct blocks. Empty necessary-partition "
        "set certifies old-core overlap<=55 over every point relabeling. A nonempty partition set "
        "is inconclusive unless an explicit checked image violates the cap. The explicit image "
        "maximum alone is not a global maximum. No 64-core statement is applied to 65-block starts "
        "or other variable-cardinality states; no optimizer was called.",
    }
    (HERE / "screen.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "screen_sha256": sha(HERE / "screen.json"),
                "best_holes": best_holes,
                "families": [
                    {
                        "holes": row["holes"],
                        "necessary_partition_count": row["screen"]["necessary_partition_count"],
                        "all_relabel_cap55": row["screen"][
                            "all_relabel_cap55_certified_by_necessary_condition"
                        ],
                    }
                    for row in screened
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
