# Document:    Complete Affine Five-Cap and Line Extension Pool
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      9bd5922a3084a6b55ebe44e4086cdf73925139949431c41ca00e6469b1a2ceb3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare separate base and necessary-incidence models for all affine five-caps."""

import hashlib
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-cap-extension-pool-20261003"
SOURCE = ROOT / "experiments/scratch/inversive-plane-pool-20261003/pool.json"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    require(not RAW.exists(), "new immutable directory required")
    require(sha(SOURCE) == "733d336edbb793c8fa0fb1c228b8ab72b2dd512e61683c0b7a6600b3318a22ed",
            "audited affine plane source")
    gate_path = HERE.parent / "affine-extension-independent/model-audit.json"
    gate = json.loads(gate_path.read_text())
    require(gate["passed"] and gate["pool_sha256"] == sha(SOURCE), "original pool audit")
    source = json.loads(SOURCE.read_text())
    lines = source["affine_lines"]
    require(len(lines) == len({tuple(line) for line in lines}) == 20, "affine line count")
    pairs = Counter(pair for line in lines for pair in combinations(line, 2))
    require(set(pairs) == set(combinations(range(1, 17), 2)) and
            set(pairs.values()) == {1}, "affine pair partition")
    collinear = {triple for line in lines for triple in combinations(line, 3)}
    all_blocks = list(combinations(range(1, 17), 5))
    collinear_counts = [sum(t in collinear for t in combinations(b, 3)) for b in all_blocks]
    require(Counter(collinear_counts) == {0: 288, 1: 2400, 2: 1440, 4: 240},
            "full universe partition")
    pool_ids = [i for i, n in enumerate(collinear_counts) if n in (0, 4)]
    pool = [all_blocks[i] for i in pool_ids]
    extensions = {tuple(sorted((*line, point))) for line in lines
                  for point in range(1, 17) if point not in line}
    require({all_blocks[i] for i, n in enumerate(collinear_counts) if n == 4} == extensions,
            "four-collinear blocks are exactly the line extensions")
    require(len(pool) == 528 and all(tuple(row["block"]) in pool for row in source["pool"]),
            "strict expansion of original pool")
    triples = list(combinations(range(1, 17), 3))
    supports = [[i for i, b in enumerate(pool) if set(t) <= set(b)] for t in triples]
    require(all(len(support) == (12 if triple in collinear else 9)
                for triple, support in zip(triples, supports, strict=True)), "support sizes")
    point_rows = [[i for i, b in enumerate(pool) if point in b] for point in range(1, 17)]
    pair_labels = list(combinations(range(1, 17), 2))
    pair_rows = [[i for i, b in enumerate(pool) if set(pair) <= set(b)] for pair in pair_labels]
    require(all(len(row) == 165 for row in point_rows) and
            all(len(row) == 44 for row in pair_rows), "incidence row widths")
    base = cp_model.CpModel()
    variables = [base.new_bool_var(f"block_{global_id}") for global_id in pool_ids]
    base.add(sum(variables) == 64)
    for support in supports:
        base.add(sum(variables[i] for i in support) >= 1)
    require(not base.validate(), "base CP validation")
    strengthened = cp_model.CpModel()
    require(strengthened.proto.parse_text_format(str(base.proto)), "base copy")
    variables = [strengthened.get_bool_var_from_proto_index(i) for i in range(528)]
    for row in point_rows:
        strengthened.add(sum(variables[i] for i in row) >= 19)
    for row in pair_rows:
        strengthened.add(sum(variables[i] for i in row) >= 5)
    require(not strengthened.validate(), "strengthened CP validation")
    RAW.mkdir(parents=True)
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    (RAW / "source-pool.json").write_bytes(SOURCE.read_bytes())
    payload = dict(affine_lines=lines, collinear_triples=sorted(collinear),
                   full_universe_collinear_count_distribution=dict(Counter(collinear_counts)),
                   pool=[dict(local_id=i, global_id=global_id, block=all_blocks[global_id],
                              kind="cap" if collinear_counts[global_id] == 0 else "line_extension")
                         for i, global_id in enumerate(pool_ids)],
                   triples=triples, supports=supports,
                   point_labels=list(range(1, 17)), point_rows=point_rows,
                   pair_labels=pair_labels, pair_rows=pair_rows)
    save(RAW / "pool.json", payload)
    models = []
    for name, model, rows in (("base", base, 561), ("incidence-cuts", strengthened, 697)):
        path = RAW / f"exact64-{name}.pbtxt"
        require(model.export_to_file(str(path)), "model export")
        models.append(dict(name=name, path=str(path.relative_to(ROOT)), sha256=sha(path),
                           variables=528, rows=rows, target_blocks=64,
                           added_point_rows=16 if name == "incidence-cuts" else 0,
                           added_pair_rows=120 if name == "incidence-cuts" else 0))
    manifest = dict(version="v1.0.0", created_utc=datetime.now(UTC).isoformat(),
                    builder_sha256=sha(Path(__file__)), source_pool_sha256=sha(SOURCE),
                    source_audit_sha256=sha(gate_path),
                    source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                            cwd=ROOT, text=True).strip(),
                    ortools_version=ortools_version,
                    pool=str((RAW / "pool.json").relative_to(ROOT)),
                    pool_sha256=sha(RAW / "pool.json"), caps=288, extensions=240,
                    full_universe_collinear_count_distribution=dict(Counter(collinear_counts)),
                    triple_support_distribution=dict(Counter(map(len, supports))), models=models,
                    safe_cut_argument="Each pair has 14 triples, while a block through that pair "
                                      "covers only 3, hence pair incidence is at least 5. "
                                      "For a fixed point, summing its 15 pair incidences gives "
                                      "4 times its block "
                                      "incidence, so 4r>=75 and integer r>=19.",
                    solver_calls=0,
                    scope="Only the 528-block cap/line-extension pool. The optional incidence "
                          "inequalities are necessary for every covering; no exact profile, "
                          "cap count, extension count or symmetry is imposed. No global claim.")
    save(HERE / "manifest.json", manifest)
    save(RAW / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
