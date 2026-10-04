# Document:    Independent Bounded Descent Pre-Run Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      8e4186b3392db7c5a22689315944d1830f1f98835cdcf84c6bb13ef55dbb0f60
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit wrapper composition with fixed output replays and abstract control flow."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-d28-deterministic-descent"
MANIFEST = "c985387e9429ca012c001dc03a105b702c8c231b55d005515e478c267cd5c17c"
INITIAL = "c6d132069270ead505488fa863a12a0f16a82e289c989a1c4d5961b13826e06f"
PRIOR = {
    "one": (
        "weak-pair-swap-scan",
        "71c0586872f86f4b367cf410beb6718707266bc55463f84aaf095513ac601764",
    ),
    "two": (
        "weak-pair-two-swap-scan-v2",
        "0f006df5844a67bf5595378e8dc156890a117ecab613b5e2ead9f74b463d9287",
    ),
}
PRIOR_GATES = {
    "weak-pair-swap-scan-independent/gate.json": (
        "3f6247263cb75a0258357e2e356158388fad434e8b89bb6c9210f9871adc889c"
    ),
    "weak-pair-two-swap-scan-v2-independent/gate.json": (
        "77c9f3fa9eccfb89229be8d9a09bdc4e26e64a0a296b19af44179473059a9a64"
    ),
    "weak-pair-two-swap-scan-v2-runtime-independent/postcheck.json": (
        "c2922a53aae7a51154b2006f457d88df886ab115fa6b88993920d04c62eb8d41"
    ),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    require(not (HERE / "gate.json").exists(), "preserve gate")
    require(sha(PRODUCER / "manifest.json") == MANIFEST, "manifest changed")
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    for group in ("input_files", "sources", "raw_files", "files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, "manifest binding changed: " + relative)
    for relative, digest in PRIOR_GATES.items():
        require(sha(HERE.parent / relative) == digest, "prior independent evidence changed")
    require(manifest["status"] == "PREPARED_NOT_RUN" and manifest["search_launches"] == 0, "state")
    require(manifest["max_rounds"] == 4 and manifest["max_shell_launches"] == 8, "campaign bounds")
    require(
        manifest["budget"]
        == {
            "seconds_per_shell": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "budget_transfer": False,
            "relaunch": False,
            "seed": None,
        },
        "budget changed",
    )
    for kind, (folder, digest) in PRIOR.items():
        prior_path = HERE.parent / folder / "manifest.json"
        require(sha(prior_path) == digest, "prior manifest changed")
        prior = json.loads(prior_path.read_text())
        current = manifest["shells"][kind]
        require(current["original_binary_path"] == prior["binary_path"], "wrong original binary")
        require(
            sha(ROOT / current["binary_path"])
            == current["binary_sha256"]
            == prior["binary_sha256"],
            "binary bytes changed",
        )
        require(manifest["core_rows"] == prior["core_rows"], "named filters changed")
        require(
            current["recorder_path"] == str((HERE.parent / folder / "run.py").relative_to(ROOT)),
            "wrong recorder",
        )
        require(
            sha(ROOT / current["recorder_path"]) == current["recorder_sha256"], "recorder changed"
        )
    runner = load("bounded_descent_under_audit", PRODUCER / "run.py")
    controls = load("independent_descent_finite_controls", HERE / "controls.py")
    require(
        not runner.RUN.exists() and not (PRODUCER / "result.json").exists(), "launch preceded gate"
    )
    oracle = load(
        "independent_descent_oracle", HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    )
    ids = oracle.parse(PRODUCER / "center-00.txt")
    require(
        sha(PRODUCER / "center-00.txt") == manifest["initial"]["sha256"] == INITIAL,
        "initial family changed",
    )
    require(ids == manifest["initial"]["ids"] and len(ids) == len(set(ids)) == 64, "initial IDs")
    direct = oracle.analyze(ids, manifest["core_rows"])
    require(
        direct["legal"]
        and direct["metrics"] | {"cardinality": 64} == manifest["initial"]["metrics"],
        "independent baseline metrics",
    )
    recorder = runner.load_recorder(ROOT / manifest["shells"]["one"]["recorder_path"])
    require(
        runner.verify_family(ids, recorder, manifest["core_rows"]) == manifest["initial"],
        "initial wrapper dual verification",
    )
    damaged_families = []
    for label, damaged in (
        ("63 blocks", ids[:-1]),
        ("duplicate block", ids[:-1] + [ids[0]]),
        ("65 blocks", ids + [next(i for i in range(4368) if i not in ids)]),
        ("outside ID", ids[:-1] + [4368]),
    ):
        damaged_families.append(
            controls.expect_failure(
                lambda family=damaged: runner.verify_family(
                    family, recorder, manifest["core_rows"]
                ),
                label,
            )
        )
    pure = controls.pure_controls(runner)
    grammar = controls.grammar_controls(runner)
    processes = controls.process_controls(runner, manifest)
    for group in ("input_files", "sources", "raw_files", "files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, "controls changed producer artifact")
    require(
        not runner.RUN.exists() and not (PRODUCER / "result.json").exists(),
        "controls launched campaign",
    )
    receipt = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": MANIFEST,
        "runner_sha256": sha(PRODUCER / "run.py"),
        "initial_sha256": INITIAL,
        **{
            f"{kind}_binary_sha256": spec["binary_sha256"]
            for kind, spec in manifest["shells"].items()
        },
        "budget": manifest["budget"],
        "max_rounds": 4,
        "max_shell_launches": 8,
        "independent_sources": {p.name: sha(p) for p in (HERE / "check.py", HERE / "controls.py")},
        "prior_evidence": PRIOR_GATES,
        "initial_direct_metrics": direct["metrics"],
        "damaged_families_rejected": damaged_families,
        "abstract_campaign_controls": pure,
        "grammar_controls": grammar,
        "recorded_output_process_controls": processes,
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(controls.RAW.rglob("*")) if p.is_file()
        },
        "optimizer_launches": 0,
        "solver_launches": 0,
        "native_binary_invocations": 0,
        "launch_authority": "Root only; one fixed campaign after binding this gate hash.",
        "scope": "Wrapper composition over unchanged finite-shell kernels. Abstract state fixtures "
        "do not claim real covering families. Replayed terminal logs are explicitly synthetic "
        "process controls and were not generated by new scans. No global lower bound.",
        "closure_rule": "Only both completed shells with no strict rank improvement justify "
        "no improving radius-two neighbor at that exact center under fixed filters. "
        "Round limit, incomplete outcomes, and early covers imply no such closure.",
    }
    (HERE / "gate.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "GO",
                "gate_sha256": sha(HERE / "gate.json"),
                "optimizer_launches": 0,
                "campaign_controls": len(pure["campaigns"]),
                "fake_process_controls": len(processes["controls"]),
            }
        )
    )


if __name__ == "__main__":
    main()
