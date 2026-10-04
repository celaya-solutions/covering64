#!/usr/bin/env python3
# Document:    Multicut Terminal State Saving Supplemental Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bind the three terminal saves to the already independently replayed controls."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "audit-v1.4.1.json"
    assert not output.exists()
    old_source = (ROOT / "scripts/four_seven_template_multicut_heuristic.cpp").read_bytes()
    new_source = (ROOT / "scripts/four_seven_template_multicut_final_heuristic.cpp").read_bytes()
    previous_bytes = (HERE / "audit.json").read_bytes()
    previous = json.loads(previous_bytes)
    assert previous["passed"] and previous["source_sha256"] == sha(old_source)
    primary_bytes = (HERE.parent / "multicut-native-final/audit.json").read_bytes()
    primary = json.loads(primary_bytes)
    assert primary["passed"] and primary["source_sha256"] == sha(new_source)
    assert primary["cut_sha256"] == previous["bundle_sha256"]
    old_body = "\n".join(old_source.decode().splitlines()[11:])
    new_body = "\n".join(new_source.decode().splitlines()[11:])
    removed = re.findall(r'^\s+save\((?:initial|state), prefix \+ "-final.txt"\);$',
                         new_body, flags=re.MULTILINE)
    assert len(removed) == 3
    stripped = re.sub(r'^\s+save\((?:initial|state), prefix \+ "-final.txt"\);\n',
                      '', new_body, flags=re.MULTILINE)
    assert stripped == old_body
    old_raw = ROOT / "experiments/scratch/multicut-native-v1.4.0/controls"
    new_raw = ROOT / "experiments/scratch/multicut-native-v1.4.1/controls"
    old_receipts = {Path(r["path"]).relative_to(old_raw.relative_to(ROOT)): r
                    for r in previous["receipts"]}
    folders, checked = set(), []
    for item in primary["snapshots"]:
        path = ROOT / item["path"]
        relative = path.relative_to(new_raw)
        old = old_receipts[relative]
        data = path.read_bytes()
        detail = path.with_name(path.name + ".lookahead.json").read_bytes()
        assert sha(data) == old["sha256"] == item["sha256"]
        assert sha(detail) == old["detail_sha256"]
        assert (item["score"], item["holes"], item["cut_penalty"]) == (
            old["score"], old["holes"], old["cut_penalty"])
        folders.add(path.parent)
        checked.append({"path": item["path"], "sha256": sha(data),
                        "detail_sha256": sha(detail)})
    assert len(checked) == 286 and primary["operations"] == 88
    traces = {}
    for folder in sorted(folders):
        data = (folder / "stdout.jsonl").read_bytes()
        normalized = data.decode().replace(str(new_raw), str(old_raw)).encode()
        old_folder = old_raw / folder.relative_to(new_raw)
        assert normalized == (old_folder / "stdout.jsonl").read_bytes()
        assert not (folder / "stderr.log").read_bytes()
        traces[str(folder.relative_to(ROOT))] = sha(data)
    result = {"passed": True, "source_sha256": sha(new_source),
              "previous_source_sha256": sha(old_source),
              "previous_gate_sha256": sha(previous_bytes),
              "primary_audit_sha256": sha(primary_bytes), "binaries": primary["binaries"],
              "binary_sha256": primary["binaries"]["search"],
              "terminal_save_calls_added": 3, "other_body_changes": 0,
              "identical_replayed_states": 286, "identical_replayed_operations": 88,
              "state_receipts": checked, "trace_sha256": traces,
              "checker_sha256": sha(Path(__file__).read_bytes()), "optimization_runs": 0,
              "scope": "Source-only terminal-save delta; state serialization already tested. "
                       "No optimization or cover claim."}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("passed", "terminal_save_calls_added", "identical_replayed_states")}))


if __name__ == "__main__":
    main()
