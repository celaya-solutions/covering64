# Document:    Exact LP Diagnostic for the Fourteen-Cut Pilot Best
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      18b65be3095820bb1e0b45c37fad212a5b6193654b16aa1c9633010daa3baf8b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/multicut-best-lp-v1.0.0"
PRIOR = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen"
BASE = ROOT / "experiments/2026-10-03/cut-pilot-heavy-completion"
PILOT = HERE.parent / "multicut-pilot"
ORACLE = ROOT / "experiments/2026-10-03/lookahead-cut-independent/check.py"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    pilot_audit = json.loads((PILOT / "audit.json").read_text())
    assert pilot_audit["passed"]
    seed = PILOT / "cycle-raw-best.txt"
    assert sha(seed) == pilot_audit["raw_best"]["sha256"]
    assert pilot_audit["raw_best"]["holes"] == 10
    assert pilot_audit["raw_best"]["all14cuts_pass"]
    base = json.loads((BASE / "manifest.json").read_text())
    base_model = ROOT / base["model"]
    assert sha(base_model) == base["model_sha256"]
    assert sha(ORACLE) == "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    builder = load(PRIOR / "build.py", "frozen_builder")
    lp = load(PRIOR / "lp_core.py", "frozen_lp")
    checker = load(PRIOR / "check.py", "frozen_replay")
    oracle = load(ORACLE, "fixed_heavy_oracle")
    oracle.MODEL, oracle.WITNESS = base_model, BASE / "seed.txt"
    _, _, heavy, old_fixed, _ = oracle.rebuild()
    candidate = [tuple(map(int, line.split())) for line in seed.read_text().splitlines()]
    new_fixed = sorted(b for b in candidate if b in heavy)
    assert len(new_fixed) == 28
    proto = text_format.Parse(base_model.read_text(), cp_model_pb2.CpModelProto())
    proto = builder.shifted_model(proto, old_fixed, new_fixed)
    RAW.mkdir(parents=True)
    model = RAW / "model.pbtxt"
    model.write_text(text_format.MessageToString(proto))
    (HERE / "seed.txt").write_bytes(seed.read_bytes())
    oracle.MODEL, oracle.WITNESS = model, HERE / "seed.txt"
    _, ordinary, heavy, fixed, symbolic = oracle.rebuild()
    assert sorted(fixed) == new_fixed and len(ordinary) == 1200 and len(symbolic) == 697
    heavy_hash = hashlib.sha256(builder.canonical(fixed).encode()).hexdigest()
    manifest = {
        "version": "v1.0.0",
        "model": str(model.relative_to(ROOT)),
        "model_sha256": sha(model),
        "seed_sha256": sha(seed),
        "heavy_sha256": heavy_hash,
        "heavy_blocks": new_fixed,
        "pilot_audit_sha256": sha(PILOT / "audit.json"),
        "source_model_sha256": sha(base_model),
        "generic_oracle_sha256": sha(ORACLE),
        "builder_sha256": sha(PRIOR / "build.py"),
        "lp_core_sha256": sha(PRIOR / "lp_core.py"),
        "checker_sha256": sha(PRIOR / "check.py"),
        "runner_sha256": sha(Path(__file__)),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "rows": 697,
        "ordinary_variables": 1200,
        "all_six_hub_graphs": True,
        "independent_model_gate_passed": True,
        "solver_workers": 1,
        "time_limit_seconds_per_phase": 10,
        "maximum_solver_seconds": 20,
        "solver_seed": 2026104,
        "ortools_version": ortools_version,
        "scope": "One fixed-heavy regular-family LP diagnostic; no CP or global bound.",
    }
    save(HERE / "manifest.json", manifest)
    save(RAW / "manifest.json", manifest)
    (RAW / "run.py").write_bytes(Path(__file__).read_bytes())
    rows = [
        (list(c.linear.vars), list(c.linear.coeffs), *c.linear.domain) for c in proto.constraints
    ]
    first, values, dual = lp.solve(rows)
    result = {
        "manifest_sha256": sha(HERE / "manifest.json"),
        "attempts": [first],
        "exact_status": "UNRESOLVED",
        "source_model_sha256": sha(model),
        "scope": manifest["scope"],
        "cp_solves": 0,
    }
    binding = {
        "model_sha256": sha(model),
        "heavy_sha256": heavy_hash,
        "manifest_sha256": sha(HERE / "manifest.json"),
    }
    if values is not None:
        save(RAW / "numerical-primal.json", values)
        for limit in [100, 10000, 1000000, 1000000000]:
            primal = lp.exact_primal(rows, values, limit)
            if primal is not None:
                primal.update(binding)
                save(HERE / "primal.json", primal)
                result.update(
                    exact_status="RATIONAL_FEASIBLE", primal_sha256=sha(HERE / "primal.json")
                )
                break
    elif first["status"] == "INFEASIBLE":
        phase, values, dual = lp.solve(rows, elastic=True)
        result["attempts"].append(phase)
        if dual is not None:
            save(RAW / "numerical-dual.json", dual)
            for denominator in [1000, 1000000, 1000000000]:
                certificate = lp.exact_dual(rows, dual, denominator)
                if certificate["proves_infeasible"]:
                    certificate.update(binding)
                    save(HERE / "dual.json", certificate)
                    result.update(
                        exact_status="RATIONAL_INFEASIBLE",
                        dual_sha256=sha(HERE / "dual.json"),
                        gap=certificate["gap"],
                    )
                    reconstructed = []
                    for support, hids, lower, upper in symbolic:
                        shift = sum(heavy[i] in fixed for i in hids)
                        reconstructed.append(
                            (support, lower - shift, upper if upper == INF else upper - shift)
                        )
                    replay = checker.replay(
                        certificate, reconstructed, manifest, sha(HERE / "manifest.json")
                    )
                    controls = []
                    for field in [
                        "model_sha256",
                        "heavy_sha256",
                        "manifest_sha256",
                        "rhs_numerator",
                        "box_max_numerator",
                        "gap",
                    ]:
                        damaged = copy.deepcopy(certificate)
                        damaged[field] = "bad" if field.endswith("sha256") else 0
                        try:
                            checker.replay(
                                damaged, reconstructed, manifest, sha(HERE / "manifest.json")
                            )
                        except AssertionError:
                            controls.append(field)
                        else:
                            raise AssertionError("damaged certificate accepted")
                    save(
                        HERE / "dual-audit.json",
                        {
                            "passed": True,
                            "model_sha256": sha(model),
                            "dual_sha256": sha(HERE / "dual.json"),
                            "checker_sha256": sha(PRIOR / "check.py"),
                            "damaged_controls_rejected": len(controls),
                            "controls": controls,
                            "exact_replay": replay,
                        },
                    )
                    break
    result["solver_seconds"] = sum(a["seconds"] for a in result["attempts"])
    save(HERE / "lp-result.json", result)
    save(RAW / "lp-result.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
