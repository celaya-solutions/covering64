# Document:    Combined Independent Neutral Queue Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      869bbee2a55146f043b3f346ba2a4cf702791c29d7dc6699c74e5f6abb3f6adc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Bind independent native and wrapper controls without invoking a search binary."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-neutral-queue"
MANIFEST = "5a1082e2f28194ee4c90ee0d16bf0d5b22502164e082e757a35842547eae2a82"
RUNNER = "fdc7a9e89f4ce039112a3474d0a656dd246679a6355d6eebae826fbe3b65f085"
ADAPTER = "ada0a960eecb962ea0095e664f3cf21cc9b4b5da7551c6f8c0f3a71a94089371"
INITIAL = "f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d"
NATIVE_PATH = "experiments/2026-10-04/weak-pair-neutral-native-review/review.json"
NATIVE_SHA = "213a27f1940aa49506ccce310a8a333c357f2f6ddbed8ff05b5ccd295bdf9049"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    require(not (HERE / "gate.json").exists(), "preserve combined gate")
    require(sha(PRODUCER / "manifest.json") == MANIFEST, "manifest changed")
    require(
        sha(PRODUCER / "run.py") == RUNNER and sha(PRODUCER / "adapter.py") == ADAPTER,
        "queue/adapter changed",
    )
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    for group in ("input_files", "sources", "files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, "producer artifact changed: " + relative)
    require(
        manifest["status"] == "PREPARED_NOT_RUN"
        and manifest["search_launches"] == 0
        and manifest["native_search_launches"] == 0,
        "premature search",
    )
    require(
        manifest["budget"]
        == {
            "max_centers": 16,
            "max_shell_launches": 32,
            "seconds_per_shell": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "budget_transfer": False,
            "relaunch": False,
            "seed": None,
        },
        "budget changed",
    )
    require(manifest["neutral_cap_per_shell"] == 64, "sample cap")
    require(
        manifest["initial"]["sha256"] == manifest["seed_revisit_exception"] == INITIAL,
        "initial revisit exception",
    )
    require(
        manifest["historical_visited_hashes"] == sorted(set(manifest["historical_visited_hashes"]))
        and INITIAL in manifest["historical_visited_hashes"],
        "historical set",
    )
    require(
        set(manifest["historical_visited_metrics"]) == set(manifest["historical_visited_hashes"]),
        "historical metric keys",
    )
    oracle = load(
        "neutral_gate_independent_oracle", HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    )
    metrics = oracle.analyze(manifest["initial"]["ids"], manifest["core_rows"])
    require(
        metrics["legal"]
        and metrics["metrics"] | {"cardinality": 64} == manifest["initial"]["metrics"],
        "initial direct recount",
    )
    require((metrics["metrics"]["holes"], metrics["metrics"]["D2max"]) == (12, 26), "initial rank")
    runner = load("neutral_gate_queue", PRODUCER / "run.py")
    require(
        not runner.RUN.exists() and not (PRODUCER / "result.json").exists(), "launch preceded GO"
    )
    native_path = ROOT / NATIVE_PATH
    require(sha(native_path) == NATIVE_SHA, "native review changed")
    native = json.loads(native_path.read_text())
    require(
        native["passed"] is True
        and native["manifest_sha256"] == MANIFEST
        and native["production_searches_launched"] == 0
        and native["exact_observer_only_body_delta_confirmed"] is True,
        "native review failed",
    )
    for relative, digest in native["sources"].items():
        require(sha(ROOT / relative) == digest, "native source changed")
    for name, digest in native["unchanged_header_sha256"].items():
        require(sha(PRODUCER / name) == digest, "evaluation header changed")
    require(
        sha(native_path.parent / "synthetic-checks.json") == native["synthetic_checks_sha256"],
        "native synthetic receipt changed",
    )
    controls = json.loads((HERE / "controls.json").read_text())
    require(
        controls["optimizer_launches"] == 0 and controls["recorder"]["optimizer_launches"] == 0,
        "control search launch",
    )
    require(
        len(controls["queue"]["transition_cases"]) == 13
        and len(controls["queue"]["invalid_transitions"]) == 3,
        "queue control coverage",
    )
    require(
        len(controls["recorder"]["shell_controls"]) == 2
        and sum(len(row["rejected_controls"]) for row in controls["recorder"]["shell_controls"])
        == 46,
        "recorder control coverage",
    )
    raw = ROOT / "experiments/scratch/neutral-queue-independent-20261004"
    gate = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": MANIFEST,
        "runner_sha256": RUNNER,
        "adapter_sha256": ADAPTER,
        "initial_sha256": INITIAL,
        **{
            f"{kind}_binary_sha256": spec["binary_sha256"]
            for kind, spec in manifest["shells"].items()
        },
        "budget": manifest["budget"],
        "neutral_cap_per_shell": 64,
        "native_receipt_path": NATIVE_PATH,
        "native_receipt_sha256": NATIVE_SHA,
        "wrapper_controls_sha256": sha(HERE / "controls.json"),
        "wrapper_controls": controls,
        "independent_sources": {p.name: sha(p) for p in (HERE / "check.py", HERE / "controls.py")},
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(raw.rglob("*")) if p.is_file()
        },
        "source_revision": manifest["source_revision"],
        "optimizer_launches": 0,
        "launch_authority": "Root only: one campaign, no restart, transfer, or budget extension.",
        "scope": "At most16 processed centers and32 shell calls, including the initial D26 neutral "
        "collector. Strict improvement takes precedence; lower-ranked improvements clear the old "
        "frontier. Only first64 legal equal-rank families per shell are retained, then ordered "
        "by full IDs. All other historically processed centers are excluded. No full plateau "
        "enumeration or global existence/lower-bound claim.",
        "validation_limits": (
            "Native review covers the sampling delta and unchanged kernels. Wrapper "
            "controls use abstract queue states and synthetic metadata over previously "
            "verified actual families; they are not new search outcomes."
        ),
    }
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "decision": "GO",
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "optimizer_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
