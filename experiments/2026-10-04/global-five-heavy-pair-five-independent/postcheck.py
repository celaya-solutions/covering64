# Document:    Independent Global Five Heavy DP Outcome Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read saved assignments and recount covering/profile data without an optimizer."""

import json
import subprocess
from collections import Counter
from itertools import combinations

from check import HERE, ROOT, SOURCE, base, read, sha

BLOCKS, MASKS, TRIPLES = base.BLOCKS, base.MASKS, base.TRIPLES
check_values, transitions = base.check_values, base.transitions
cp_model_pb2, text_format = base.cp_model_pb2, base.text_format


def main():
    gate = read(HERE / "gate.json")
    manifest = read(SOURCE / "manifest.json")
    result = read(SOURCE / "result.json")
    assert gate["passed"] and result["gate_sha256"] == sha(HERE / "gate.json")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == sha(SOURCE / "manifest.json")
    assert (
        result["runner_source_sha256"] == gate["runner_source_sha256"] == sha(SOURCE / "execute.py")
    )
    assert result["model_sha256"] == gate["model_sha256"] == sha(ROOT / manifest["model_path"])
    assert result["parameters_sha256"] == gate["parameters_sha256"]
    for record in result["raw_files"].values():
        assert sha(ROOT / record["path"]) == record["sha256"]
    model = text_format.Parse(
        (ROOT / manifest["model_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    response_path = ROOT / result["raw_files"]["response.pbtxt"]["path"]
    response = text_format.Parse(response_path.read_text(), cp_model_pb2.CpSolverResponse())
    assert cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"]
    assert result["optimization_calls"] == 1 and result["budget"] == manifest["budget"]
    assert abs(response.wall_time - result["reported_seconds"]) < 1e-6
    assert response.best_objective_bound == result["objective_bound"]
    assert result["seconds"] < 122 and response.wall_time < 122
    assert not result["global_lower_bound_claim"]
    states = read(ROOT / manifest["dag"]["states_path"])
    records = result["records"] + ([result["final"]] if result["final"] else [])
    if result["final"]:
        assert read(ROOT / result["final"]["values_path"]) == list(response.solution)
        assert response.objective_value == result["final"]["composite_objective"]
    else:
        assert not response.solution
    checked = []
    for index, record in enumerate(records):
        path = ROOT / record["path"]
        assert sha(path) == record["sha256"]
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines() if line]
        assert len(blocks) == len(set(blocks)) == 64 and all(b in BLOCKS for b in blocks)
        ids = sorted(BLOCKS.index(b) for b in blocks)
        assert ids == record["ids"]
        vector_path = ROOT / record["values_path"]
        assert sha(vector_path) == record["values_sha256"]
        values = read(vector_path)
        assert [i for i in range(4368) if values[i]] == ids
        check_values(model, values)
        coverage = Counter(t for b in blocks for t in combinations(b, 3))
        holes = [i for i, t in enumerate(TRIPLES) if coverage[t] == 0]
        assert holes == record["hole_triple_ids"]
        assert len(holes) == record["holes"]
        assert values[4368:4928] == [int(coverage[t] == 0) for t in TRIPLES]
        assert values[4958:6078] == [int(coverage[t] >= level) for t in TRIPLES for level in (6, 7)]
        core_counts = [len(set(ids) & set(core)) for core in manifest["core_rows"]]
        assert core_counts == record["core_overlaps"] and max(core_counts) <= 55
        assert 65 * len(holes) + core_counts[0] == record["composite_objective"]
        weights = {
            mask: 5 * (coverage[t] >= 6) + (coverage[t] >= 7)
            for t, mask in zip(TRIPLES, MASKS, strict=True)
        }
        least = {0: 0}
        for state in states[1:]:
            least[state] = max(least[p] + weights[MASKS[t]] for p, t in transitions(state))
        maximum = max(least[s] for s in states if s.bit_count() == 15)
        assert maximum == record["global_partition_maximum"] <= 26
        assert all(values[6078 + i] >= least[s] for i, s in enumerate(states))
        outputs = []
        for name, command in (
            (
                "package",
                ["uv", "run", "covering64", "verify", str(path), "--expected-blocks", "64"],
            ),
            (
                "standalone",
                [
                    "uv",
                    "run",
                    "python",
                    "scripts/check_cover.py",
                    str(path),
                    "--expected-blocks",
                    "64",
                ],
            ),
        ):
            process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            assert process.returncode == (0 if not holes else 1) and not process.stderr
            payload = json.loads(process.stdout)
            assert payload["blocks"] == 64 and payload["valid"] == (not holes)
            count_key = "covered" if name == "package" else "covered_subsets"
            assert payload[count_key] == 560 - len(holes)
            receipt = HERE / f"state-{index:02d}-{name}.json"
            receipt.write_text(process.stdout)
            outputs.append(
                {
                    "path": str(receipt.relative_to(ROOT)),
                    "sha256": sha(receipt),
                    "canonical_sha256": payload["canonical_sha256"],
                }
            )
        assert outputs[0]["canonical_sha256"] == outputs[1]["canonical_sha256"]
        degree = [sum(p in b for b in blocks) for p in range(1, 17)]
        pairs = [sum(set(p) <= set(b) for b in blocks) for p in combinations(range(1, 17), 2)]
        assert min(pairs) == record["minimum_pair_count"] >= 5
        assert min(degree) == record["minimum_point_degree"] >= 19
        assert {str(k): v for k, v in sorted(Counter(pairs).items())} == record["pair_histogram"]
        checked.append(
            {
                "path": record["path"],
                "sha256": record["sha256"],
                "holes": len(holes),
                "core_overlaps": core_counts,
                "maximum_partition_weight": maximum,
                "minimum_point_degree": min(degree),
                "minimum_pair_count": min(pairs),
                "pairs_below_five": sum(n < 5 for n in pairs),
                "verifiers": outputs,
            }
        )
    damages = []
    if records:
        original = read(ROOT / records[-1]["values_path"])
        for label, index, replacement in (
            ("selected_block", records[-1]["ids"][0], 0),
            ("global_threshold", 4958, 1 - original[4958]),
            ("fifteen_point_bound", len(original) - 1, 27),
        ):
            changed = original.copy()
            changed[index] = replacement
            try:
                check_values(model, changed)
            except AssertionError:
                damages.append(label)
            else:
                raise AssertionError("Damaged assignment accepted")
    audit = {
        "passed": True,
        "optimizer_calls": 0,
        "source_sha256": sha(__file__),
        "gate_sha256": sha(HERE / "gate.json"),
        "result_sha256": sha(SOURCE / "result.json"),
        "status": result["status"],
        "seconds": result["seconds"],
        "checked": checked,
        "damaged_assignments_rejected": damages,
        "cover_found": any(c["holes"] == 0 for c in checked),
        "scope": "All saved callbacks and final response. DP auxiliaries may exceed their "
        "least feasible values; all active rows, thresholds, domains and actual maxima checked.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({k: v for k, v in audit.items() if k != "checked"}))


if __name__ == "__main__":
    main()
