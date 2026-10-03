# Document:    Independent Complete Hint Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check actual saved hint values and objective without invoking a solver."""

import ast
import copy
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
RUN = Path("experiments/scratch/first-family-hint-r6-000-20261003")
spec = importlib.util.spec_from_file_location("independent_first", HERE / "check.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def values_for(blocks, model):
    selected = set(blocks)
    coverage = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    local = {
        a: Counter(
            p
            for b in blocks
            if set(b) & {1, 2, 3} == {a}
            for p in itertools.combinations([x for x in b if x >= 4], 2)
        )
        for a in (2, 3)
    }
    values = []
    for variable in model.variables:
        name = variable.name
        if name.startswith("block_"):
            value = int(audit.BLOCKS[int(name[6:])] in selected)
        elif name.startswith("hole_"):
            value = int(coverage[audit.TRIPLES[int(name[5:])]] == 0)
        elif name.startswith("local_hole_"):
            anchor, pair = name[len("local_hole_") :].split("_", 1)
            value = int(local[int(anchor)][ast.literal_eval(pair)] == 0)
        else:
            anchor = int(name[len("local_deficit_") :])
            value = sum(local[anchor][p] == 0 for p in audit.G)
        values.append(value)
    return values


def verify_hint(model, expected):
    hint = model.solution_hint
    audit.require(
        list(hint.vars) == list(range(len(model.variables))),
        "hint is incomplete, repeated, or unordered",
    )
    audit.require(list(hint.values) == expected, "hint differs from independent candidate recount")
    audit.verify_assignment(model, list(hint.values))


def main():
    metadata = json.loads((RUN / "metadata.json").read_text())
    for name, digest in metadata["sources"].items():
        audit.require(
            hashlib.sha256((RUN / name).read_bytes()).hexdigest() == digest,
            "archived source hash mismatch",
        )
    model_path = RUN / "model.pbtxt"
    audit.require(
        hashlib.sha256(model_path.read_bytes()).hexdigest() == metadata["model_sha256"],
        "actual model hash mismatch",
    )
    model = audit.load_model(model_path)
    seed = RUN / "initial.txt"
    raw = seed.read_bytes()
    audit.require(hashlib.sha256(raw).hexdigest() == metadata["hint_sha256"], "hint input hash")
    blocks = [tuple(map(int, line.split())) for line in raw.decode().splitlines()]
    family = sorted(tuple(p for p in b if p != 1) for b in blocks if set(b) & {1, 2, 3} == {1})
    canonical_family = "".join(" ".join(map(str, b)) + "\n" for b in family).encode()
    audit.require(
        hashlib.sha256(canonical_family).hexdigest() == metadata["family_sha256"],
        "hint has wrong fixed family",
    )
    checked = audit.verify_model(model, family, max_missing=27)
    expected = values_for(blocks, model)
    verify_hint(model, expected)
    audit.require(sum(expected[4368:4928]) == 27, "hint objective is not27")
    controls = []
    for name in (
        "omitted_hint",
        "duplicate_hint",
        "block_value",
        "hole_value",
        "local_hole_value",
        "local_deficit_value",
    ):
        damaged = copy.deepcopy(model)
        if name == "omitted_hint":
            del damaged.solution_hint.vars[-1]
            del damaged.solution_hint.values[-1]
        elif name == "duplicate_hint":
            damaged.solution_hint.vars[-1] = 0
        else:
            index = {
                "block_value": 0,
                "hole_value": 4368,
                "local_hole_value": 4928,
                "local_deficit_value": 4935,
            }[name]
            damaged.solution_hint.values[index] += 1
        try:
            verify_hint(damaged, expected)
        except ValueError:
            controls.append({"name": name, "rejected": True})
        else:
            raise ValueError(f"damaged hint accepted: {name}")
    result = {
        "status": "VERIFIED_COMPLETE_HINT_AND_OBJECTIVE",
        **checked,
        "hint_variables": len(expected),
        "objective": 27,
        "controls": controls,
        "model_sha256": metadata["model_sha256"],
        "candidate_sha256": metadata["hint_sha256"],
        "wrapper_source_sha256": metadata["sources"]["first_family_hint_search.py"],
        "builder_source_sha256": metadata["sources"]["first_family_search.py"],
        "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "row_checker_sha256": hashlib.sha256((HERE / "check.py").read_bytes()).hexdigest(),
        "scope": "The actual saved complete hint and exact hole objective; no solver proof.",
    }
    (HERE / "hint-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "hint_variables": len(expected),
                "objective": 27,
                "controls": len(controls),
            }
        )
    )


if __name__ == "__main__":
    main()
