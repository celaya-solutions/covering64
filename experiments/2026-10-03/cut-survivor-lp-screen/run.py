# Document:    Bounded Sequential LP Screen of Twelve Cut Survivors
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      44ee6cc067280e0f5578ff5a4be22047bdbe9488739e6859135f282abe2c5a66
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

from google.protobuf import text_format
from lp_core import exact_dual, exact_primal, solve
from ortools import __version__ as ortools_version
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/cut-survivor-lp-screen-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["gate_passed"] and manifest["case_count"] == 12
    assert manifest["independent_reconstructions"] == 12
    assert manifest["damaged_models_rejected"] == 6
    assert not (HERE / "results.json").exists()
    assert not (RAW / "lp-start.json").exists(), "Refuse to repeat a started batch."
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    provenance = {
        "version": "v1.0.0",
        "source_revision": revision,
        "manifest_sha256": sha(manifest_path),
        "runner_sha256": sha(Path(__file__)),
        "lp_core_sha256": sha(HERE / "lp_core.py"),
        "builder_sha256": manifest["builder_sha256"],
        "generic_oracle_sha256": manifest["generic_oracle_sha256"],
        "ortools_version": ortools_version,
        "python_version": platform.python_version(),
        "workers": 1,
        "sequential": True,
        "random_seed": 2026104,
        "time_limit_seconds_per_phase": 10,
        "maximum_solver_seconds": 240,
        "wrapper_budget_seconds": 300,
        "scope": (
            "Each result applies only to its fixed-heavy regular family, with all six "
            "hub graphs retained. No covering witness, first-link exclusion or "
            "unrestricted bound is claimed."
        ),
    }
    save(RAW / "lp-start.json", provenance)
    for name in ["run.py", "lp_core.py", "build.py", "manifest.json"]:
        (RAW / ("lp-frozen-" + name)).write_bytes((HERE / name).read_bytes())
    started = time.monotonic()
    results = []
    (HERE / "cases").mkdir()
    for case in manifest["cases"]:
        assert case["independent_reconstruction_passed"]
        assert case["all_six_hub_graphs"]
        source = ROOT / case["model"]
        assert sha(source) == case["model_sha256"]
        assert sha(ROOT / case["seed"]) == case["seed_sha256"]
        proto = cp_model_pb2.CpModelProto()
        text_format.Parse(source.read_text(), proto)
        rows = [
            (list(c.linear.vars), list(c.linear.coeffs), *c.linear.domain)
            for c in proto.constraints
        ]
        assert len(rows) == 697 and len(proto.variables) == 1200
        key = f"{case['index']:02d}-{case['heavy_sha256'][:12]}"
        out = HERE / "cases" / key
        out.mkdir()
        raw = source.parent
        record = {
            "index": case["index"],
            "heavy_sha256": case["heavy_sha256"],
            "seed_sha256": case["seed_sha256"],
            "model_sha256": case["model_sha256"],
            "manifest_sha256": provenance["manifest_sha256"],
            "runner_sha256": provenance["runner_sha256"],
            "lp_core_sha256": provenance["lp_core_sha256"],
            "min_saved_holes": case["min_saved_holes"],
            "exact_status": "UNRESOLVED",
            "attempts": [],
        }
        if time.monotonic() - started > 280:
            record["reason"] = "Wrapper budget exhausted before this case."
        else:
            phase, values, dual = solve(rows)
            record["attempts"].append(phase)
            if values is not None:
                save(raw / "numerical-primal.json", values)
                record["numerical_primal_sha256"] = sha(raw / "numerical-primal.json")
                for limit in [100, 10000, 1000000, 1000000000]:
                    witness = exact_primal(rows, values, limit)
                    if witness is not None:
                        witness.update(
                            {
                                k: record[k]
                                for k in ["heavy_sha256", "model_sha256", "manifest_sha256"]
                            }
                        )
                        save(out / "primal.json", witness)
                        record["exact_status"] = "RATIONAL_FEASIBLE"
                        record["primal"] = str((out / "primal.json").relative_to(ROOT))
                        record["primal_sha256"] = sha(out / "primal.json")
                        record["fractional_variables"] = witness["fractional_variables"]
                        break
            elif phase["status"] == "INFEASIBLE":
                phase, values, dual = solve(rows, elastic=True)
                record["attempts"].append(phase)
                if dual is not None:
                    save(raw / "numerical-dual.json", dual)
                    record["numerical_dual_sha256"] = sha(raw / "numerical-dual.json")
                    for denominator in [1000, 1000000, 1000000000]:
                        certificate = exact_dual(rows, dual, denominator)
                        if certificate["proves_infeasible"]:
                            certificate.update(
                                {
                                    k: record[k]
                                    for k in ["heavy_sha256", "model_sha256", "manifest_sha256"]
                                }
                            )
                            save(out / "dual.json", certificate)
                            record["exact_status"] = "RATIONAL_INFEASIBLE"
                            record["dual"] = str((out / "dual.json").relative_to(ROOT))
                            record["dual_sha256"] = sha(out / "dual.json")
                            record["gap"] = certificate["gap"]
                            break
        save(out / "result.json", record)
        save(raw / "lp-result.json", record)
        results.append(record)
        print(
            json.dumps(
                {
                    "index": case["index"],
                    "heavy": case["heavy_sha256"][:12],
                    "exact_status": record["exact_status"],
                    "gap": record.get("gap"),
                    "seconds": sum(x["seconds"] for x in record["attempts"]),
                }
            ),
            flush=True,
        )
    summary = {
        **provenance,
        "cases": results,
        "case_count": len(results),
        "counts": {
            status: sum(r["exact_status"] == status for r in results)
            for status in ["RATIONAL_INFEASIBLE", "RATIONAL_FEASIBLE", "UNRESOLVED"]
        },
        "solver_seconds": sum(a["seconds"] for r in results for a in r["attempts"]),
        "wrapper_seconds": time.monotonic() - started,
        "cp_solves": 0,
        "native_runs": 0,
    }
    save(HERE / "results.json", summary)
    save(RAW / "lp-results.json", summary)
    print(
        json.dumps({k: summary[k] for k in ["counts", "solver_seconds", "wrapper_seconds"]}),
        flush=True,
    )


if __name__ == "__main__":
    main()
