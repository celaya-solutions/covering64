# Document:    Checked DRAT and LP First-Link Exclusion Aggregation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      094c61506b490322c2d8879f28e212ed959634d439d5ca4482e06d4a14e552bd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Bind the checked DRAT receipt and replay the other five exact LP certificates."""

import copy
import gzip
import hashlib
import itertools as it
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATE = HERE.parent
CASE = "matching-029"
SIX = set(it.product(range(2), range(3)))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(
        gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    )


def checked_file(path, expected):
    require(sha(path) == expected, "changed artifact: " + str(path.relative_to(ROOT)))
    return {"path": str(path.relative_to(ROOT)), "sha256": expected, "bytes": path.stat().st_size}


def replay(rows, width, certificate):
    require(width == 4768, "wrong LP width")
    for ids, coefs, lower, upper in rows:
        require(ids == sorted(set(ids)) and len(ids) == len(coefs), "row shape")
        require(all(type(i) is int and 0 <= i < width for i in ids), "column ID")
        require(all(type(c) is int and c != 0 for c in coefs), "coefficient")
        require(all(b is None or type(b) is int for b in [lower, upper]), "bound")
        require(lower is None or upper is None or lower <= upper, "bound order")
    denominator = certificate["denominator"]
    require(type(denominator) is int and denominator > 0, "denominator")
    weights = certificate["weights"]
    require(
        [i for i, w in weights] == sorted({i for i, w in weights}), "duplicate or unsorted weight"
    )
    coefficients, rhs = [0] * width, 0
    for row, weight in weights:
        require(type(row) is int and 0 <= row < len(rows), "row ID")
        require(type(weight) is int and weight != 0, "weight")
        ids, coefs, lower, upper = rows[row]
        bound = lower if weight > 0 else upper
        require(bound is not None, "infinite weighted bound")
        rhs += weight * bound
        for column, coefficient in zip(ids, coefs, strict=True):
            coefficients[column] += weight * coefficient
    maximum = sum(max(c, 0) for c in coefficients)
    gap = Fraction(rhs - maximum, denominator)
    require(certificate["rhs_numerator"] == rhs, "weighted lower bound")
    require(certificate["box_max_numerator"] == maximum, "box maximum")
    require(certificate["checked_columns"] == width, "reported width")
    require(certificate["gap"] == [gap.numerator, gap.denominator], "reported gap")
    require(certificate["proves_infeasible"] is True and gap > 0, "nonpositive gap")
    return {
        "gap": [gap.numerator, gap.denominator],
        "rows": len(rows),
        "columns": width,
        "nonzero_weights": len(weights),
    }


def receipt_check(receipt, cnf, restricted, audit):
    require(receipt["case"] == cnf["case"] == restricted["case"] == CASE, "case identity")
    require(receipt["status"] == "UNSAT_DRAT_VERIFIED", "unchecked status")
    require(
        receipt["hub_case"] == cnf["hub_case"] == restricted["hub_case"] == [0, 2], "hub identity"
    )
    require(
        receipt["fixed_ids"] == cnf["fixed_ids"] == restricted["fixed_ids"], "fixed link identity"
    )
    require(receipt["cnf_sha256"] == cnf["cnf_sha256"] == audit["cnf_sha256"], "CNF identity")
    require(
        cnf["source_model_sha256"] == restricted["model_sha256"] == audit["model_sha256"],
        "model identity",
    )
    require(
        receipt["solver"]["exit"] == 20 and not receipt["solver"]["forced_termination"],
        "solver did not complete",
    )
    require(
        receipt["checker"] is not None
        and receipt["checker"]["exit"] == 0
        and receipt["checker"]["verified"] is True
        and not receipt["checker"]["forced_termination"],
        "checker did not accept",
    )


def complete(cases):
    require(
        len(cases) == 6 and set(map(tuple, cases)) == SIX,
        "incomplete or duplicate six-case coverage",
    )


def main():
    bindings = []
    prior_path = (
        DATE / "four-seven-template-hull-refresh-independent/combined-first-link-exclusions.json"
    )
    require(
        sha(prior_path) == "2809b2f39fac1971ca6bf3997e789a4a41463b62394e7525e5d282d084527f88",
        "prior registry changed",
    )
    prior = read(prior_path)
    require(
        prior["passed"]
        and prior["excluded_count"] == len(prior["proof_sources"]) == 108
        and prior["remaining_count"] == len(prior["remaining_ids"]) == 150,
        "prior counts",
    )
    require(
        CASE in prior["remaining_ids"] and CASE not in prior["proof_sources"], "case was not open"
    )
    cnf_dir, cp_dir = DATE / "four-seven-template-cnf", DATE / "four-seven-template-cp-restricted"
    cnf_manifest, cp_manifest = read(cnf_dir / "manifest.json"), read(cp_dir / "manifest.json")
    cnf_audit_path = DATE / "four-seven-template-cnf-independent/audit.json"
    cnf_audit, cp_audit = read(cnf_audit_path), read(cp_dir / "independent-audit.json")
    for folder, manifest, audit, checker in [
        (cnf_dir, cnf_manifest, cnf_audit, cnf_audit_path.parent / "check.py"),
        (cp_dir, cp_manifest, cp_audit, cp_dir / "check_independent.py"),
    ]:
        require(audit["passed"] is True, "model audit failed")
        bindings += [
            checked_file(folder / "manifest.json", audit["manifest_sha256"]),
            checked_file(checker, audit["checker_sha256"]),
            checked_file(folder / "build.py", manifest["builder_sha256"]),
        ]
    bindings += [
        checked_file(cp_dir / "manifest.json", cnf_manifest["restricted_manifest_sha256"]),
        checked_file(cp_dir / "independent-audit.json", cnf_manifest["restricted_audit_sha256"]),
    ]
    base = DATE / "four-seven-template-cp-proposal"
    bindings += [
        checked_file(base / "manifest.json", cp_manifest["base_manifest_sha256"]),
        checked_file(base / "independent-audit.json", cp_manifest["base_independent_audit_sha256"]),
    ]
    require(read(base / "independent-audit.json")["passed"] is True, "base audit")
    cnf = next(c for c in cnf_manifest["cases"] if c["case"] == CASE)
    cp = next(c for c in cp_manifest["cases"] if c["case"] == CASE)
    ca = next(c for c in cnf_audit["cases"] if c["case"] == CASE)
    cpa = next(c for c in cp_audit["cases"] if c["case"] == CASE)
    receipt = read(HERE / (CASE + "-receipt.json"))
    receipt_check(receipt, cnf, cp, ca)
    require(
        cpa["passed"]
        and cpa["model_sha256"] == cp["model_sha256"]
        and cpa["hub_case"] == cp["hub_case"]
        and cpa["fixed_ids"] == cp["fixed_ids"]
        and cpa["prior_checked_hub_cases"] == 5,
        "restricted audit identity",
    )
    universe = list(it.combinations(range(1, 17), 5))
    require(
        [list(universe[i]) for i in cp["fixed_ids"]] == cp["fixed_blocks"],
        "lexicographic fixed blocks",
    )
    for field, hash_field in [
        ("model", "model_sha256"),
        ("source_base", "source_base_sha256"),
        ("added_rows", "added_rows_sha256"),
    ]:
        bindings.append(checked_file(ROOT / cp[field], cp[hash_field]))
    bindings += [
        checked_file(ROOT / cnf["cnf"], cnf["cnf_sha256"]),
        checked_file(ROOT / cnf["row_trace"], cnf["row_trace_sha256"]),
        checked_file(ROOT / receipt["proof"], receipt["proof_sha256"]),
    ]
    require((ROOT / receipt["proof"]).stat().st_size == receipt["proof_bytes"], "proof size")
    raw = (ROOT / receipt["proof"]).parent
    require(read(raw / "result.json") == receipt, "receipt differs from saved result")
    tools = read(cnf_dir / "tools.json")
    require(
        tools["passed"] and [c["verified"] for c in tools["controls"]] == [True, False, False],
        "proof tool controls",
    )
    for tool in tools["tools"]:
        bindings += [
            checked_file(ROOT / tool["binary"], tool["binary_sha256"]),
            checked_file(ROOT / tool["source_archive"], tool["source_archive_sha256"]),
        ]
    for role, tool in [("solver", "cadical"), ("checker", "drat-trim")]:
        command = receipt[role]["command"]
        binary = next(t for t in tools["tools"] if t["name"] == tool)["binary"]
        require(
            Path(command[0]) == ROOT / binary
            and str(ROOT / cnf["cnf"]) in command
            and str(ROOT / receipt["proof"]) in command,
            "command binding",
        )
        for stream in ["stdout", "stderr"]:
            bindings.append(
                checked_file(raw / f"{role}.{stream}.log", receipt[role][f"{stream}_sha256"])
            )
    require((raw / "solution.sol").read_text().strip() == "s UNSATISFIABLE", "saved solver status")
    require(
        "s VERIFIED" in (raw / "checker.stdout.log").read_text().splitlines(),
        "no exact verified line",
    )
    hub = DATE / "four-seven-hub-count-screen"
    hub_split = read(DATE / "four-seven-hub-split-independent/audit.json")
    require(hub_split["passed"] is True, "hub split audit")
    campaign = read(hub / "artifact-manifest.json")
    combined = read(hub / "combined-audit.json")
    require(
        combined["passed"] and set(map(tuple, combined["checked_hub_cases"])) == SIX,
        "hub split coverage",
    )
    evidence, lp_checks, covered = [], [], [cp["hub_case"]]
    for proof in cp["prior_hub_case_proofs"]:
        audit_path = ROOT / proof["audit"]
        bindings.append(checked_file(audit_path, proof["sha256"]))
        audit = read(audit_path)
        m4, z = proof["hub_case"]
        child = f"m4-{m4}-z-{z}"
        require(
            audit["passed"] is True
            and audit["hub_case"] == [m4, z]
            and combined["child_audit_sha256"][child] == proof["sha256"],
            "LP audit identity",
        )
        selected = [c for c in audit["checks"] if c["id"] == CASE]
        require(
            len(selected) == 1 and selected[0]["proves_infeasible"] is True, "missing prior proof"
        )
        folder = ROOT / campaign["raw_directory"] / child
        for filename in [
            "metadata.json",
            "representatives.json",
            "matching-base.pbtxt",
            "matching-rows.json.gz",
            "results.json.gz",
        ]:
            bindings.append(
                checked_file(folder / filename, campaign["children"][child][filename]["sha256"])
            )
        require(
            sha(folder / "metadata.json") == audit["metadata_sha256"]
            and sha(folder / "results.json.gz") == audit["results_sha256"],
            "LP saved archive binding",
        )
        metadata = read(folder / "metadata.json")
        require(metadata["hub_count_split"] == [m4, z], "LP hub identity")
        model = next(a for a in audit["models"] if a["case"] == "matching")
        require(
            model["identical_proto"]
            and sha(folder / "matching-base.pbtxt") == model["model_sha256"],
            "LP base identity",
        )
        require(
            any(
                a["case"] == "matching"
                and a["m4"] == m4
                and a["z"] == z
                and a["model_sha256"] == model["audited_model_sha256"]
                and a["passed"]
                for a in hub_split["models"]
            ),
            "LP split model chain",
        )
        matrix = read(folder / "matching-rows.json.gz")
        result = next(c for c in read(folder / "results.json.gz") if c["id"] == CASE)
        require(
            result["case"] == "matching" and result["fixed_ids"] == cp["fixed_ids"],
            "LP fixed link identity",
        )
        rows = matrix["rows"] + [[[i], [1], 1, 1] for i in cp["fixed_ids"]]
        replayed = replay(rows, matrix["width"], result["certificate"])
        require(replayed["gap"] == selected[0]["gap"], "replayed gap differs")
        evidence.append({"hub_case": [m4, z], "result": result})
        lp_checks.append({"hub_case": [m4, z], "audit_sha256": proof["sha256"], **replayed})
        covered.append([m4, z])
    complete(covered)
    damaged = []
    for name, transform in [
        ("unchecked receipt", lambda r: r.update(status="UNSAT")),
        ("wrong hub", lambda r: r.update(hub_case=[0, 1])),
        ("wrong fixed block", lambda r: r["fixed_ids"].__setitem__(0, 1)),
        ("wrong CNF", lambda r: r.update(cnf_sha256="0" * 64)),
        ("failed checker", lambda r: r["checker"].update(exit=1)),
        ("missing acceptance", lambda r: r["checker"].update(verified=False)),
    ]:
        bad = copy.deepcopy(receipt)
        transform(bad)
        try:
            receipt_check(bad, cnf, cp, ca)
        except ValueError:
            damaged.append({"mutation": name, "rejected": True})
        else:
            raise ValueError("damaged receipt accepted")
    for bad in [covered[:-1], covered[:-1] + [covered[0]]]:
        try:
            complete(bad)
        except ValueError:
            damaged.append({"mutation": "missing or duplicate hub case", "rejected": True})
        else:
            raise ValueError("incomplete split accepted")
    archive = HERE / "prior-five-certificates.json.gz"
    archive.write_bytes(
        gzip.compress(json.dumps(evidence, separators=(",", ":")).encode(), mtime=0)
    )
    audit = {
        "passed": True,
        "case": CASE,
        "checked_hub_cases": sorted(covered),
        "fixed_ids": cp["fixed_ids"],
        "fixed_blocks": cp["fixed_blocks"],
        "cnf_audit_sha256": sha(cnf_audit_path),
        "hub_split_audit_sha256": sha(DATE / "four-seven-hub-split-independent/audit.json"),
        "tools_sha256": sha(cnf_dir / "tools.json"),
        "receipt_sha256": sha(HERE / (CASE + "-receipt.json")),
        "proof_sha256": receipt["proof_sha256"],
        "proof_bytes": receipt["proof_bytes"],
        "prior_five_certificates_sha256": sha(archive),
        "lp_checks": lp_checks,
        "bindings": bindings,
        "damaged_controls": damaged,
        "checker_sha256": sha(Path(__file__)),
        "prior_registry_sha256": sha(prior_path),
        "scope": "All six hub cases excluded for matching-029 within the normalized regular "
        "four-sevenfold branch only. DRAT verification receipt is bound, not rerun. "
        "No unrestricted theorem or cover.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    union = copy.deepcopy(prior)
    union["proof_sources"][CASE] = [str((HERE / "audit.json").relative_to(DATE))]
    union["proof_sources"] = dict(sorted(union["proof_sources"].items()))
    union["remaining_ids"] = [i for i in prior["remaining_ids"] if i != CASE]
    union.update(
        excluded_count=109,
        remaining_count=149,
        prior_union_sha256=sha(prior_path),
        aggregation_audit_sha256=sha(HERE / "audit.json"),
        added_ids=[CASE],
    )
    require(
        len(union["proof_sources"]) == 109
        and len(union["remaining_ids"]) == 149
        and not set(union["proof_sources"]) & set(union["remaining_ids"]),
        "union partition",
    )
    (HERE / "combined-first-link-exclusions.json").write_text(json.dumps(union, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "added": CASE,
                "excluded": 109,
                "remaining": 149,
                "lp_replays": len(lp_checks),
                "damaged_controls": len(damaged),
                "union_sha256": sha(HERE / "combined-first-link-exclusions.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
