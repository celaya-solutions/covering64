# Document:    Affine Circle Deletion Annealer Preflight
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      7af265b2dc6112548db9ef2434902b2a4f1eaebb73902063af565038a296b764
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check native capacities, swaps, exact rollback, and malformed controls."""

import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-capacity-annealer-20261003"
PRIOR = HERE.parent / "affine-extension-counting-independent"
PRIOR_RAW = ROOT / "experiments/scratch/affine-extension-capacity-20261003"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_oracle():
    spec = importlib.util.spec_from_file_location("capacity_oracle", PRIOR / "run_capacity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_result(result, seconds, removed, seed):
    assert result["removed"] == removed and result["seed"] == seed
    assert result["requested_seconds"] == seconds
    assert result["iterations"] == result["accepted"] + result["rejected"]
    assert result["required_capacity"] == 10 * removed
    assert 0 <= result["elapsed_seconds"] < seconds + 1
    module = load_oracle()
    circles, lines = module.geometry()
    items = [{"mask": result["best_mask"], "capacity": result["best_capacity"]}] + result[
        "survivors"
    ]
    assert len(result["survivors"]) <= 8
    for item in items:
        mask = item["mask"]
        assert type(mask) is int and 0 < mask < 1 << 48 and mask & 1
        assert mask.bit_count() == removed
        assert item["capacity"] == module.oracle(mask, removed - 4, circles, lines)
        assert result["best_capacity"] >= item["capacity"]
    for i, item in enumerate(result["survivors"]):
        assert item["capacity"] >= 10 * removed
        assert all(
            (item["mask"] ^ earlier["mask"]).bit_count() >= 4 for earlier in result["survivors"][:i]
        )


def main():
    assert not (HERE / "preflight.json").exists(), "preserve completed preflight"
    RAW.mkdir(parents=True, exist_ok=True)
    old_gate = json.loads((PRIOR / "preflight.json").read_text())
    assert old_gate["passed"] and old_gate["model_sha256"] == digest(PRIOR_RAW / "incidence.txt")
    assert old_gate["runner_sha256"] == digest(PRIOR / "run_capacity.py")
    assert old_gate["geometry_source_sha256"] == digest(PRIOR / "check.py")
    module = load_oracle()
    circles, lines = module.geometry()
    regenerated = (
        "\n".join(" ".join(map(str, row)) for row in module.incidence(circles, lines)) + "\n"
    )
    assert regenerated == (PRIOR_RAW / "incidence.txt").read_text()
    model = RAW / "incidence.txt"
    model.write_text(regenerated)
    source = HERE / "search.cpp"
    binary = RAW / "search"
    sanitizer = RAW / "search-sanitized"
    base = ["clang++", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pedantic"]
    for output, flags in [
        (binary, ["-O3"]),
        (sanitizer, ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]),
    ]:
        run = subprocess.run(
            base + flags + [str(source), "-o", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=True,
        )
        assert not run.stderr
    samples = (PRIOR_RAW / "samples.txt").read_text()
    queries = [tuple(map(int, line.split())) for line in samples.splitlines()]
    expected = [module.oracle(mask, extra, circles, lines) for mask, extra in queries]
    assert len(expected) == 1000
    (RAW / "samples.txt").write_text(samples)
    (RAW / "sample-oracle.json").write_text(json.dumps(expected) + "\n")
    audits = []
    smoke_results = []
    for executable in (binary, sanitizer):
        run = subprocess.run(
            [str(executable), str(model), "samples"],
            input=samples,
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        assert not run.stderr and list(map(int, run.stdout.split())) == expected
        run = subprocess.run(
            [str(executable), str(model), "selftest", "2026103990"],
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        assert not run.stderr
        audit = json.loads(run.stdout)
        assert audit == {"swaps": 16000, "rollbacks": 16000, "damaged_states_rejected": 48}
        audits.append(audit)
        run = subprocess.run(
            [str(executable), str(model), "run", "9", "2026103990", "0.02"],
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        assert not run.stderr
        result = json.loads(run.stdout)
        verify_result(result, 0.02, 9, 2026103990)
        smoke_results.append(result)
    damaged_models = ["", " ".join(regenerated.split()[:-1]), regenerated + "1\n"]
    damaged_models += [
        regenerated.replace(regenerated.split()[0], v, 1) for v in ("0", str(1 << 48), "bad", "-1")
    ]
    for i, damaged in enumerate(damaged_models):
        path = RAW / f"damaged-{i}.txt"
        path.write_text(damaged)
        for executable in (binary, sanitizer):
            run = subprocess.run(
                [str(executable), str(path), "samples"],
                input="0 0\n",
                text=True,
                capture_output=True,
                timeout=10,
            )
            assert run.returncode == 2
    invalid_arguments = [
        ["run", "8", "1", "1"],
        ["run", "25", "1", "1"],
        ["run", "9", "1", "11"],
        ["run", "9", "1", "nan"],
        ["run", "9", "-1", "1"],
        ["run", "9", "1", "0"],
        ["bad"],
    ]
    for arguments in invalid_arguments:
        for executable in (binary, sanitizer):
            run = subprocess.run(
                [str(executable), str(model), *arguments],
                text=True,
                capture_output=True,
                timeout=10,
            )
            assert run.returncode == 2
    for query in ("0 -1\n", "0 221\n", f"{1 << 48} 0\n", "0\n", "bad\n"):
        for executable in (binary, sanitizer):
            run = subprocess.run(
                [str(executable), str(model), "samples"],
                input=query,
                text=True,
                capture_output=True,
                timeout=10,
            )
            assert run.returncode == 2
    (RAW / "search.cpp").write_bytes(source.read_bytes())
    (RAW / "preflight.py").write_bytes(Path(__file__).read_bytes())
    (RAW / "smoke-results.json").write_text(json.dumps(smoke_results, indent=2) + "\n")
    report = {
        "passed": True,
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": digest(source),
        "preflight_source_sha256": digest(Path(__file__)),
        "model_sha256": digest(model),
        "binary_sha256": digest(binary),
        "sanitizer_sha256": digest(sanitizer),
        "oracle_source_sha256": digest(PRIOR / "run_capacity.py"),
        "geometry_source_sha256": digest(PRIOR / "check.py"),
        "transitivity_sha256": old_gate["symmetry"]["evidence_sha256"],
        "oracle_cases_per_binary": 1000,
        "state_audits": audits,
        "damaged_models_per_binary": len(damaged_models),
        "damaged_arguments_per_binary": len(invalid_arguments),
        "damaged_queries_per_binary": 5,
        "smoke_seconds_per_binary": 0.02,
        "compiler": subprocess.check_output(["clang++", "--version"], text=True).strip(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scope": "Heuristic search for necessary deleted-circle capacity candidates; "
        "not covering witnesses.",
    }
    (HERE / "preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
