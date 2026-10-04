# Document:    Independent Hard Top-Two Runner Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a015058cfb4332e391a5929ec0e38c659f2bedf02bd78038bbcd61839feb216e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check import HERE, MANIFEST_SHA, ROOT, SOURCE, canonical_hint, read, sha
from ortools.sat.python import cp_model

RUNNER_SHA = "bd3ee87c19233ecdc916700cbc64f22d7435bea302906dec607fc48cebaf7470"
RUNNER_MANIFEST_SHA = "48397e1767b00b5a1fd9519fe98a7af5af19f1906f3b2e82a145c98083cdfe2d"
CONTROLS_SHA = "c4b1ac4c6294d2e787949440714a717b103b04b8bf2edb91bb52418048a6ed1a"


def main():
    model_gate = read(HERE / "model-gate.json")
    assert model_gate["passed"] and model_gate["decision"] == "MODEL_PASS_ONLY"
    assert model_gate["manifest_sha256"] == MANIFEST_SHA == sha(SOURCE / "manifest.json")
    assert sha(HERE / "check.py") == model_gate["checker_sha256"]
    manifest, runner = read(SOURCE / "manifest.json"), read(SOURCE / "runner-manifest.json")
    assert sha(SOURCE / "execute.py") == RUNNER_SHA == runner["runner_sha256"]
    assert sha(SOURCE / "runner-manifest.json") == RUNNER_MANIFEST_SHA
    for relative, digest in (manifest["sources"] | runner["sources"]).items():
        assert sha(ROOT / relative) == digest
    for kind in ("model", "parameters", "guidance"):
        assert sha(ROOT / manifest[f"{kind}_path"]) == model_gate[f"{kind}_sha256"]
    assert runner["manifest_sha256"] == MANIFEST_SHA
    assert (
        runner["budget_seconds"] == 120 and runner["workers"] == 4 and runner["seed"] == 2026104601
    )
    assert runner["stop"] == "actual holes0 with both covering verifiers valid"
    assert runner["optimizer_calls"] == 0
    assert sha(SOURCE / "runner-controls.json") == CONTROLS_SHA
    producer_controls = read(SOURCE / "runner-controls.json")
    assert producer_controls["passed"] and producer_controls["optimizer_calls"] == 0
    assert producer_controls["runtime_directory_absent"] and producer_controls["relaunch_rejected"]
    assert producer_controls["runner_sha256"] == RUNNER_SHA
    assert producer_controls["runner_manifest_sha256"] == RUNNER_MANIFEST_SHA
    assert sha(SOURCE / "check_runner.py") == producer_controls["source_sha256"]
    source = SOURCE / "execute.py"
    tree = ast.parse(source.read_text())
    solve_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "solve"
    ]
    assert len(solve_calls) == 1
    spec = importlib.util.spec_from_file_location("audited_hard_runner", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert not module.RUN.exists() and not (SOURCE / "result.json").exists()
    model = cp_model.CpModel()
    assert model.proto.parse_text_format((ROOT / manifest["model_path"]).read_text())
    guidance = read(ROOT / manifest["guidance_path"])
    values, _ = canonical_hint(guidance["values"], manifest["core_rows"])
    vector_rejections = []
    for label, data in (
        ("H49_no_feasible_extension", values),
        ("incomplete_vector", values[:-1]),
        ("damaged_block_domain", [2] + values[1:]),
    ):
        try:
            module.check_vector(model, data)
        except ValueError as error:
            vector_rejections.append({"label": label, "error": str(error)})
        else:
            raise AssertionError(f"invalid vector accepted: {label}")
    bindings = {
        "manifest_sha256": MANIFEST_SHA,
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "guidance_sha256": manifest["guidance_sha256"],
        "runner_sha256": RUNNER_SHA,
        "runner_manifest_sha256": RUNNER_MANIFEST_SHA,
    }
    gate_refusals = []
    with tempfile.TemporaryDirectory(prefix="hard-top-two-runner-controls-") as temporary:
        directory = Path(temporary)
        for key in ("decision", *bindings):
            invalid = {"passed": True, "decision": "GO", **bindings}
            invalid[key] = "NO_GO" if key == "decision" else "0" * 64
            path = directory / f"bad-{key}.json"
            path.write_text(json.dumps(invalid))
            process = subprocess.run(
                [
                    sys.executable,
                    str(source),
                    "--gate",
                    str(path),
                    "--gate-sha256",
                    sha(path),
                    "--execute",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert process.returncode != 0 and not process.stdout
            marker = (
                "independent GO required" if key == "decision" else f"gate binding mismatch: {key}"
            )
            assert marker in process.stderr
            assert not module.RUN.exists() and not (SOURCE / "result.json").exists()
            gate_refusals.append(
                {"damaged_binding": key, "returncode": process.returncode, "required_error": marker}
            )
    report = {
        "passed": True,
        "decision": "GO",
        "optimizer_calls_by_audit": 0,
        **bindings,
        "checker_sha256": sha(__file__),
        "model_gate_sha256": sha(HERE / "model-gate.json"),
        "producer_runner_controls_sha256": CONTROLS_SHA,
        "vector_rejections": vector_rejections,
        "wrong_gates_rejected": gate_refusals,
        "source_review": "One solve call; exactly120s/4workers/seed2026104601. Every callback "
        "including ties and any feasible final vector saves all7408 actual solver values, the "
        "separate canonical z/y extension, the witness and a hashed receipt. All domains and "
        "active rows are evaluated. Exact first5608 values are recounted; z/y need not be "
        "canonical. Actual D2zero, pair floor, D3/D4, allfour caps and global profile are "
        "checked before accepting a saved state. Both independent cover verifiers run before "
        "a holes0 stop request. Positive-hole feasible hints do not stop this "
        "holes-minimizing run.",
        "positive_feasible_control_available": False,
        "scope": "Gate is technically ready for one root-owned launch with the frozen bindings. "
        "No solve was called by this audit. No reuse, relaunch, additional budget or global "
        "infeasibility claim is authorized by this receipt.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "GO",
                "gate_sha256": sha(HERE / "gate.json"),
                "optimizer_calls_by_audit": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
