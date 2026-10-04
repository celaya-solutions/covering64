# Document:    Strengthened Eight by Eight Runner Delta Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      74d3c60f8572251cbc59e9b7607d5b24b13c7d8d4af6f6b6ae06ddad819e8611
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reuse fake-only original runner tests and exercise new proof hash guards."""

import ast
import contextlib
import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NEW = HERE.parent / "eight-eight-strengthened"
OLD = HERE.parent / "eight-eight-extensions"
AUDITOR = HERE.parent / "eight-eight-extensions-independent/audit.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(path, name):
    return next(
        n
        for n in ast.parse(path.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == name
    )


def main():
    assert sha(AUDITOR) == "8b90b9b02e5e329bb0acf10f72e86407b5cc67e65f65a6c22a472287a39ad027"
    assert sha(NEW / "run.py") == "1638ce606e022bfba1d6539db670369f85d08640d2d22dec2560ad534c21bd4a"
    assert (
        sha(NEW / "manifest.json")
        == "edc82d5213029872ffbf145746675e78808825b7e17152c5926d1586fb012071"
    )
    new_execute = copy.deepcopy(function(NEW / "run.py", "execute"))
    extra = [
        n
        for n in new_execute.body
        if isinstance(n, ast.For) and "proof_files" in ast.unparse(n.iter)
    ]
    assert len(extra) == 1
    assert ast.unparse(extra[0]) == (
        "for path, digest in manifest['proof_files'].items():\n"
        "    assert sha(ROOT / path) == digest"
    )
    new_execute.body.remove(extra[0])
    assert ast.dump(new_execute) == ast.dump(function(OLD / "run.py", "execute"))
    assert ast.dump(function(NEW / "run.py", "child")) == ast.dump(
        function(OLD / "run.py", "child")
    )
    run, audit = load(NEW / "run.py", "strong_runner"), load(AUDITOR, "prior_runner_audit")
    manifest = json.loads((NEW / "manifest.json").read_text())
    assert [e["seed"] for e in manifest["entries"]] == [2026105501, 2026105502, 2026105503]
    assert (manifest["seconds"], manifest["workers"], manifest["watchdog"], manifest["grace"]) == (
        120,
        4,
        145,
        5,
    )
    for path, digest in manifest["proof_files"].items():
        assert sha(ROOT / path) == digest
    original_sha = run.sha

    def mirrored_proof_sha(path):
        path = Path(path)
        # Reused fake runner creates its own temporary root. Its unmodified proof
        # inputs are read from their verified originals; explicit damage tests below
        # use actual scratch copies and the unchanged real hash helper instead.
        try:
            relative = str(path.relative_to(run.ROOT))
        except ValueError:
            relative = ""
        if relative in manifest["proof_files"]:
            return original_sha(ROOT / relative)
        return original_sha(path)

    with contextlib.ExitStack() as stack:
        stack.enter_context(
            patch.object(cp_model.CpSolver, "solve", side_effect=AssertionError("No solver"))
        )
        for name, value in (
            ("RUN", run),
            ("COMMON", run.COMMON),
            ("PRODUCER", NEW / "run.py"),
            ("MANIFEST_PATH", NEW / "manifest.json"),
        ):
            stack.enter_context(patch.object(audit, name, value))
        children = audit.fake_child_controls(manifest)
        with patch.object(run, "sha", mirrored_proof_sha):
            runners = [
                audit.fake_execute_control(manifest, s)
                for s in (
                    "unknown",
                    "timeout",
                    "kill",
                    "error",
                    "missing",
                    "vector",
                    "bad_vector",
                    "partial_atomic",
                    "preflight_decision",
                    "preflight_passed",
                    "preflight_manifest",
                    "preflight_source",
                    "preflight_common",
                    "preflight_model",
                    "preflight_groups",
                    "preflight_raw",
                    "preflight_result",
                )
            ]
        proofs = []
        for damaged_path in manifest["proof_files"]:
            with tempfile.TemporaryDirectory(dir=HERE) as temp:
                root = Path(temp)
                here, raw = root / "prepared", root / "raw"
                here.mkdir()
                raw.mkdir()
                shutil.copyfile(NEW / "manifest.json", here / "manifest.json")
                gate = root / "gate.json"
                gate.write_text(
                    json.dumps(
                        {
                            "passed": True,
                            "decision": "GO",
                            "manifest_sha256": sha(here / "manifest.json"),
                        }
                    )
                )
                for path in manifest["proof_files"]:
                    target = root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / path, target)
                with (root / damaged_path).open("a") as handle:
                    handle.write("\nDAMAGE\n")
                launches = []

                def forbid_process(*args, **kwargs):
                    launches.append(True)
                    raise RuntimeError("Unexpected process launch")

                with (
                    patch.object(run, "ROOT", root),
                    patch.object(run, "HERE", here),
                    patch.object(run, "RAW", raw),
                    patch.object(run.subprocess, "Popen", forbid_process),
                ):
                    try:
                        run.execute(gate)
                    except AssertionError:
                        assert launches == []
                    else:
                        raise AssertionError("Changed proof accepted")
                proofs.append({"path": damaged_path, "rejected_before_process": True})
    receipt = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(NEW / "manifest.json"),
        "runner_sha256": sha(NEW / "run.py"),
        "original_auditor_sha256": sha(AUDITOR),
        "common_sha256": sha(run.COMMON_PATH),
        "child_ast_identical": True,
        "execute_ast_identical_except_proof_guard": True,
        "fake_children": children,
        "fake_runner_cases": runners,
        "proof_damage_cases": proofs,
        "real_solver_launches": 0,
        "production_process_launches": 0,
        "scope": "Runner delta only; strengthened model and mathematical audit is separate",
    }
    (HERE / "checks.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "checks_sha256": sha(HERE / "checks.json"),
                "child_cases": len(children),
                "runner_cases": len(runners),
                "proof_damage_cases": len(proofs),
                "real_solver_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
