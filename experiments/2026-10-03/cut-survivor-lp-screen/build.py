# Document:    Generic Twelve-Tuple Completion Builder and Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      bb45bd7cef875e5154137170fd88a8087013bd779136635c37e92c7580d48277
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import importlib.util
import itertools as it
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/cut-survivor-lp-screen-v1.0.0"
INVENTORY = HERE.parent / "cut-pilot-parametric-cut/tuple-inventory.json"
PILOT_RAW = ROOT / "experiments/scratch/four-seven-template-cut-pilot-v1.0.0"
PREVIOUS = HERE.parent / "cut-pilot-heavy-completion"
ORACLE = HERE.parent / "lookahead-cut-independent/check.py"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def canonical(blocks):
    return "".join(" ".join(map(str, b)) + "\n" for b in sorted(map(tuple, blocks)))


def shifted_model(source, old_heavy, new_heavy):
    proto = copy.deepcopy(source)
    subsets = [()] + list(it.combinations(range(1, 17), 3))
    subsets += [(p,) for p in range(1, 17)] + list(it.combinations(range(1, 17), 2))
    assert len(subsets) == len(proto.constraints) == 697
    for row, subset in zip(proto.constraints, subsets, strict=True):
        shift = sum(set(subset) <= set(b) for b in old_heavy)
        shift -= sum(set(subset) <= set(b) for b in new_heavy)
        row.linear.domain[0] += shift
        if row.linear.domain[1] != INF:
            row.linear.domain[1] += shift
    return proto


def main():
    assert not RAW.exists(), "fresh batch preparation required"
    inventory = json.loads(INVENTORY.read_text())
    source_manifest = json.loads((PREVIOUS / "manifest.json").read_text())
    source_model = ROOT / source_manifest["model"]
    source_gate_path = HERE.parent / "cut-pilot-heavy-completion-independent/gate.json"
    source_gate = json.loads(source_gate_path.read_text())
    assert source_gate["passed"]
    assert source_gate["model_sha256"] == source_manifest["model_sha256"] == sha(source_model)
    assert source_gate["oracle_sha256"] == sha(ORACLE)
    assert sha(ORACLE) == "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    pilot_audit_path = HERE.parent / "four-seven-template-cut-pilot/audit.json"
    assert inventory["audit_sha256"] == sha(pilot_audit_path)
    pilot_audit = json.loads(pilot_audit_path.read_text())
    cases = [t for t in inventory["tuples"] if t["lp_batch_candidate"]]
    order = inventory["suggested_additional_lp_priority"]
    cases.sort(key=lambda t: order.index(t["heavy_sha256"]))
    assert len(cases) == len(order) == 12
    source = text_format.Parse(source_model.read_text(), cp_model_pb2.CpModelProto())
    old_heavy = source_manifest["fixed_heavy_blocks"]
    spec = importlib.util.spec_from_file_location("root_generic_gate", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    RAW.mkdir(parents=True)
    records, damages = [], []
    for number, case in enumerate(cases):
        heavy = case["heavy_blocks"]
        assert hashlib.sha256(canonical(heavy).encode()).hexdigest() == case["heavy_sha256"]
        assert case["cut_violation"] == case["second_cut_violation"] == 0
        directory = RAW / f"{number:02d}-{case['heavy_sha256'][:12]}"
        directory.mkdir()
        member = min(case["members"], key=lambda m: (m["holes"], m["score"], m["file"]))
        witness = PILOT_RAW / member["file"]
        assert sha(witness) == member["sha256"] == pilot_audit["snapshots"][str(witness)]["sha256"]
        (directory / "seed.txt").write_bytes(witness.read_bytes())
        (directory / "heavy.txt").write_text(canonical(heavy))
        model = shifted_model(source, old_heavy, heavy)
        path = directory / "model.pbtxt"
        path.write_text(text_format.MessageToString(model))
        oracle.MODEL, oracle.WITNESS = path, directory / "seed.txt"
        _, ordinary, candidates, fixed, rows = oracle.rebuild()
        assert len(ordinary) == 1200 and len(rows) == 697 and len(candidates) == 276
        assert canonical(fixed) == canonical(heavy)
        assert len(fixed) == 28
        if number == 0:
            for mutation in range(6):
                bad = copy.deepcopy(model)
                if mutation == 0:
                    bad.constraints[0].linear.domain[0] += 1
                elif mutation == 1:
                    bad.constraints[2].linear.domain[1] += 1
                elif mutation == 2:
                    bad.constraints[577].linear.domain[0] += 1
                elif mutation == 3:
                    row = next(r for r in bad.constraints[1:561] if r.linear.vars)
                    row.linear.vars[0] += 1
                elif mutation == 4:
                    bad.variables[0].domain[1] = 2
                else:
                    bad.constraints[0].enforcement_literal.append(0)
                damaged = directory / f"damage-{mutation}.pbtxt"
                damaged.write_text(text_format.MessageToString(bad))
                oracle.MODEL = damaged
                try:
                    oracle.rebuild()
                except AssertionError:
                    damages.append(mutation)
                else:
                    raise AssertionError("damaged model accepted")
            oracle.MODEL = path
        record = {
            "index": number,
            "heavy_sha256": case["heavy_sha256"],
            "seed": str((directory / "seed.txt").relative_to(ROOT)),
            "seed_sha256": sha(witness),
            "source_pilot_member": str(witness.relative_to(ROOT)),
            "heavy_blocks": heavy,
            "min_saved_holes": case["min_holes"],
            "model": str(path.relative_to(ROOT)),
            "model_sha256": sha(path),
            "ordinary_variables": 1200,
            "rows": 697,
            "all_six_hub_graphs": True,
            "independent_reconstruction_passed": True,
        }
        save(directory / "manifest.json", record)
        records.append(record)
    manifest = {
        "version": "v1.0.0",
        "builder_sha256": sha(Path(__file__)),
        "inventory_sha256": sha(INVENTORY),
        "source_model_sha256": sha(source_model),
        "source_gate_sha256": sha(source_gate_path),
        "generic_oracle_sha256": sha(ORACLE),
        "pilot_audit_sha256": sha(pilot_audit_path),
        "cases": records,
        "case_count": 12,
        "independent_reconstructions": 12,
        "damaged_models_rejected": len(damages),
        "gate_passed": True,
        "solves_launched": 0,
        "scope": "Twelve fixed-heavy regular-family LP models. No graph-specific restriction, "
        "first-link exclusion or unrestricted claim is added.",
    }
    save(HERE / "manifest.json", manifest)
    save(RAW / "manifest.json", manifest)
    for src, name in [
        (Path(__file__), "build.py"),
        (ORACLE, "root-generic-oracle.py"),
        (INVENTORY, "tuple-inventory.json"),
        (source_gate_path, "source-gate.json"),
    ]:
        (RAW / name).write_bytes(src.read_bytes())
    print(
        json.dumps(
            {
                "gate_passed": True,
                "models": len(records),
                "damaged_models_rejected": len(damages),
                "manifest_sha256": sha(HERE / "manifest.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
