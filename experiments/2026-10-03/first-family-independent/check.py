# Document:    Independent First Family Encoding and Orbit Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Reconstruct rows and orbit sets independently; no solver conclusions are used."""

import ast
import copy
import gzip
import hashlib
import importlib.util
import itertools
import json
import platform
import subprocess
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path.cwd()
HERE = Path(__file__).parent
REPS = ROOT / "experiments/2026-10-03/local-template-orbits/first-families.json"
MODELS = ROOT / "experiments/scratch/first-family-batch-20261003"
SCRATCH = ROOT / "experiments/scratch/first-family-audit-20261003"
OUTSIDE = tuple(range(4, 17))
PAIRS = tuple(itertools.combinations(OUTSIDE, 2))
G = {(4, 5), (4, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)}
MATCHING = tuple(sorted(G - {(4, 5), (4, 6)}))
QUADS = tuple(itertools.combinations(OUTSIDE, 4))
QUAD_RANK = {b: i + 1 for i, b in enumerate(QUADS)}
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
LIMIT = 2**63 - 1


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_model(path):
    model = cp_model_pb2.CpModelProto()
    text_format.Parse(path.read_text(), model)
    return model


def linear(terms, lo, hi, enforcement=()):
    return (
        "linear",
        tuple(sorted((i, n) for i, n in terms if n)),
        (lo, hi),
        tuple(sorted(enforcement)),
    )


def table(variable):
    return ("table", (((variable,), (1,), 0),), (0, 4, 6), False, ())


def actual_row(row):
    kind = row.WhichOneof("constraint")
    enforcement = tuple(sorted(row.enforcement_literal))
    if kind == "linear":
        require(len(row.linear.domain) == 2, "noninterval linear domain")
        return linear(zip(row.linear.vars, row.linear.coeffs), *row.linear.domain, enforcement)
    if kind == "table":
        require(not row.table.vars, "unexpected legacy table variables")
        return (
            "table",
            tuple((tuple(e.vars), tuple(e.coeffs), e.offset) for e in row.table.exprs),
            tuple(row.table.values),
            row.table.negated,
            enforcement,
        )
    raise ValueError(f"unexpected constraint kind {kind}")


def expected_model(family, max_missing=0):
    variables = [(f"block_{i}", (0, 1)) for i in range(4368)]
    variables += [(f"hole_{i}", (0, 1)) for i in range(560)]
    rows = []
    incidence = {t: [] for t in TRIPLES}
    for i, block in enumerate(BLOCKS):
        for triple in itertools.combinations(block, 3):
            incidence[triple].append(i)
    for i, triple in enumerate(TRIPLES):
        terms = [(j, 1) for j in incidence[triple]]
        rows.append(linear(terms, 0, 0, (4368 + i,)))
        rows.append(linear(terms, 1, LIMIT, (-4369 - i,)))
    rows.append(linear(enumerate([1] * 4368), 64, 64))
    rows.append(linear(((4368 + i, 1) for i in range(560)), -(2**63), max_missing))
    fixed = {(1, 2, 3, *pair) for pair in G} | {(1, *quad) for quad in family}
    require(len(fixed) == 20, "not twenty fixed blocks")
    for i, block in enumerate(BLOCKS):
        if block in fixed:
            rows.append(linear([(i, 1)], 1, 1))
        elif 1 in block or len(set(block) & {1, 2, 3}) > 1:
            rows.append(linear([(i, 1)], 0, 0))
    for point in range(1, 17):
        rows.append(linear([(i, 1) for i, b in enumerate(BLOCKS) if point in b], 20, 20))
    for pair in itertools.combinations(range(1, 17), 2):
        terms = [(i, 1) for i, b in enumerate(BLOCKS) if set(pair) <= set(b)]
        if pair[0] < 4:
            expected = 7 if pair[1] < 4 else (6 if pair[1] == 4 else 5)
            rows.append(linear(terms, expected, expected))
        else:
            rows.append(linear(terms, 5, LIMIT))
    opposite = []
    for anchor in (2, 3):
        local = []
        spoke = []
        for pair in PAIRS:
            terms = [
                (i, 1)
                for i, b in enumerate(BLOCKS)
                if set(b) & {1, 2, 3} == {anchor} and set(pair) <= set(b)
            ]
            if pair not in G:
                rows.append(linear(terms, 1, LIMIT))
                continue
            variable = len(variables)
            variables.append((f"local_hole_{anchor}_{pair}", (0, 1)))
            local.append(variable)
            rows.extend(
                (linear(terms, 0, 0, (variable,)), linear(terms, 1, LIMIT, (-variable - 1,)))
            )
            if pair in {(4, 5), (4, 6)}:
                spoke.append(variable)
            if pair == (4, 6):
                opposite.append(variable)
        deficit = len(variables)
        variables.append((f"local_deficit_{anchor}", (0, 7)))
        rows.append(linear([(deficit, 1)] + [(i, -1) for i in local], 0, 0))
        rows.append(linear([(i, 1) for i in spoke], -(2**63), 1))
        rows.append(table(deficit))
    rows.append(linear([(i, 1) for i in opposite], 1, LIMIT))
    return variables, Counter(rows)


def verify_model(model, family, max_missing=0):
    variables, rows = expected_model(family, max_missing)
    require(
        [(v.name, tuple(v.domain)) for v in model.variables] == variables,
        "wrong variable order, names, or domains",
    )
    actual = Counter(actual_row(row) for row in model.constraints)
    require(
        actual == rows,
        f"row mismatch: extra {sum((actual - rows).values())}, "
        f"missing {sum((rows - actual).values())}",
    )
    if not max_missing:
        require(not model.HasField("objective"), "unexpected full-cover objective")
    else:
        objective = model.objective
        require(
            dict(zip(objective.vars, objective.coeffs)) == {i: 1 for i in range(4368, 4928)}
            and objective.offset == 0
            and objective.scaling_factor == 1,
            "wrong hole objective",
        )
    return {"variables": len(variables), "constraints": sum(rows.values()), "fixed_blocks": 20}


def rank_family(blocks):
    return tuple(sorted(QUAD_RANK[tuple(sorted(b))] for b in blocks))


def image(family, point_map):
    return rank_family(tuple(point_map[p - 4] for p in QUADS[i - 1]) for i in family)


def holes(family):
    covered = {p for i in family for p in itertools.combinations(QUADS[i - 1], 2)}
    return set(PAIRS) - covered


def validate_map(point_map):
    require(
        all(type(x) is int for x in point_map) and sorted(point_map) == list(OUTSIDE),
        "not an outside-point bijection",
    )


def group_maps():
    for pair_order in itertools.permutations(MATCHING):
        for flips in itertools.product((0, 1), repeat=5):
            point_map = [4, 5, 6] + [None] * 10
            for source, target, flip in zip(MATCHING, pair_order, flips):
                a, b = target if not flip else target[::-1]
                point_map[source[0] - 4], point_map[source[1] - 4] = a, b
            yield point_map


def independent_pool(source, hole_count):
    source_pairs = {p for b in source for p in itertools.combinations(b, 2)}
    source_holes = sorted(set(itertools.combinations(range(1, 14), 2)) - source_pairs)
    require(len(source_holes) == hole_count, "source hole count")
    require(
        len({p for edge in source_holes for p in edge}) == 2 * hole_count,
        "source holes are not a matching",
    )
    free = sorted(set(range(1, 14)) - {p for edge in source_holes for p in edge})
    found = set()
    maps = 0
    for matching in itertools.combinations(MATCHING, hole_count - 1):
        targets = ((4, 5), *matching)
        free_targets = sorted(set(OUTSIDE) - {p for edge in targets for p in edge})
        for edge_order in itertools.permutations(targets):
            for flips in itertools.product((0, 1), repeat=hole_count):
                mapping = [None] * 13
                for (a, b), target, flip in zip(source_holes, edge_order, flips):
                    x, y = target if not flip else target[::-1]
                    mapping[a - 1], mapping[b - 1] = x, y
                for remaining in itertools.permutations(free_targets):
                    for p, target in zip(free, remaining):
                        mapping[p - 1] = target
                    found.add(rank_family(tuple(mapping[p - 1] for p in b) for b in source))
                    maps += 1
    return found, maps


def verify_archive_row(row, representatives, sources):
    label = row["representative"]
    require(label in representatives, "unknown representative")
    family = tuple(row["block_ids"])
    require(
        len(family) == 13
        and tuple(sorted(set(family))) == family
        and all(type(i) is int and 1 <= i <= 715 for i in family),
        "malformed family IDs",
    )
    family_map = row["family_to_representative"]
    source_map = row["source_to_family"]
    validate_map(family_map)
    validate_map(source_map)
    require(
        {tuple(sorted((family_map[a - 4], family_map[b - 4]))) for a, b in G} == G
        and {family_map[0], family_map[1]} == {4, 5},
        "map does not preserve fixed-spoke graph",
    )
    require(image(family, family_map) == representatives[label], "wrong representative map")
    source = sources[int(label[1])]
    require(
        rank_family(tuple(source_map[p - 1] for p in b) for b in source) == family,
        "wrong source map",
    )
    missing = holes(family)
    require((4, 5) in missing and (4, 6) not in missing and missing <= G, "wrong first-spoke holes")
    return family


def verify_assignment(model, values):
    require(len(values) == len(model.variables), "wrong assignment length")
    for variable, value in zip(model.variables, values):
        require(
            type(value) is int
            and any(a <= value <= b for a, b in zip(variable.domain[::2], variable.domain[1::2])),
            "assignment outside domain",
        )
    for row in model.constraints:
        if not all(values[i] if i >= 0 else 1 - values[-i - 1] for i in row.enforcement_literal):
            continue
        if row.HasField("linear"):
            value = sum(values[i] * n for i, n in zip(row.linear.vars, row.linear.coeffs))
            require(
                any(
                    a <= value <= b for a, b in zip(row.linear.domain[::2], row.linear.domain[1::2])
                ),
                "violated linear row",
            )
        else:
            require(row.HasField("table") and len(row.table.exprs) == 1, "unsupported row")
            expression = row.table.exprs[0]
            value = expression.offset + sum(
                values[i] * n for i, n in zip(expression.vars, expression.coeffs)
            )
            require(value in row.table.values, "violated table row")


def positive_control(script, rows, records):
    seed = ROOT / "experiments/scratch/alternate-links-20261003/restart-1-round-3/candidate.txt"
    blocks = [tuple(map(int, line.split())) for line in seed.read_text().splitlines()]
    for anchor in (1, 2, 3):
        family = rank_family(
            tuple(p for p in b if p >= 4) for b in blocks if set(b) & {1, 2, 3} == {anchor}
        )
        if (4, 5) in holes(family):
            break
    else:
        raise ValueError("positive control has no first-spoke omission")
    row = next(row for row in rows if tuple(row["block_ids"]) == family)
    permutation = {p: row["family_to_representative"][p - 4] for p in OUTSIDE}
    permutation.update({p: (anchor if p == 1 else 1 if p == anchor else p) for p in (1, 2, 3)})
    transformed = sorted(tuple(sorted(permutation[p] for p in b)) for b in blocks)
    selected = {i for i, b in enumerate(BLOCKS) if b in set(transformed)}
    multiplicity = Counter(t for b in transformed for t in itertools.combinations(b, 3))
    missing = [t for t in TRIPLES if not multiplicity[t]]
    require(
        len(transformed) == len(selected) == 64 and len(missing) == 27,
        "positive control cardinality or coverage changed",
    )
    record = next(r for r in records if r["id"] == row["representative"])
    expected_family = [tuple(b) for b in record["quadruples"]]
    _, built, _, _ = script.build_model(expected_family, max_missing=len(missing))
    model_path = SCRATCH / "positive-partial.pbtxt"
    built.ExportToFile(str(model_path))
    model = load_model(model_path)
    verify_model(model, expected_family, max_missing=len(missing))
    local_pair_counts = {}
    for point in (2, 3):
        local_pair_counts[point] = Counter(
            pair
            for b in transformed
            if set(b) & {1, 2, 3} == {point}
            for pair in itertools.combinations([p for p in b if p >= 4], 2)
        )
    values = []
    for variable in model.variables:
        name = variable.name
        if name.startswith("block_"):
            value = int(int(name[6:]) in selected)
        elif name.startswith("hole_"):
            value = int(multiplicity[TRIPLES[int(name[5:])]] == 0)
        elif name.startswith("local_hole_"):
            point, pair = name[len("local_hole_") :].split("_", 1)
            value = int(local_pair_counts[int(point)][ast.literal_eval(pair)] == 0)
        else:
            point = int(name[len("local_deficit_") :])
            value = sum(local_pair_counts[point][pair] == 0 for pair in G)
        values.append(value)
    verify_assignment(model, values)
    path = HERE / "positive-partial.txt"
    path.write_text("".join(" ".join(map(str, b)) + "\n" for b in transformed))
    proc = subprocess.run(
        ["uv", "run", "python", "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        capture_output=True,
        text=True,
    )
    standalone = json.loads(proc.stdout)
    require(standalone["uncovered"] == list(map(list, missing)), "positive standalone holes")
    from covering64.core import read_blocks, verify_cover

    package = verify_cover(read_blocks(path))
    require(
        package["canonical_sha256"] == standalone["canonical_sha256"]
        and list(map(tuple, package["uncovered"])) == missing,
        "positive package verification disagrees",
    )
    info = {
        "source_path": str(seed.relative_to(ROOT)),
        "source_sha256": sha(seed.read_bytes()),
        "representative": row["representative"],
        "point_map": permutation,
        "candidate_sha256": sha(path.read_bytes()),
        "holes": len(missing),
        "assignment_rows_satisfied": len(model.constraints),
        "model_sha256": sha(model_path.read_bytes()),
        "standalone": standalone,
        "package": package,
    }
    (HERE / "positive-partial.json").write_text(json.dumps(info, indent=2) + "\n")
    return info, model, values


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    data = json.loads(REPS.read_text())
    require(data["complete"] is True and data["group_order"] == 3840, "incomplete input")
    records = data["representatives"]
    require(
        len(records) == 13 and len({r["id"] for r in records}) == 13, "wrong representative list"
    )
    sources = {}
    representatives = {}
    for record in records:
        raw = (ROOT / record["source"]).read_bytes()
        require(sha(raw) == record["source_sha256"], "source family hash")
        source = tuple(tuple(map(int, line.split())) for line in raw.decode().splitlines())
        sources[int(record["id"][1])] = source
        fam = rank_family(record["quadruples"])
        representatives[record["id"]] = fam
        point_map = record["source_to_representative"]
        validate_map(point_map)
        require(
            rank_family(tuple(point_map[p - 1] for p in b) for b in source) == fam,
            "representative source map",
        )
        require(
            sorted([list((1, 2, 3, *p)) for p in G] + [[1, *q] for q in record["quadruples"]])
            == record["full_twenty_blocks"],
            "twenty-block reconstruction",
        )
        require(sorted(map(list, holes(fam))) == record["missing_pairs"], "representative holes")
    archive_path = ROOT / data["maps_archive"]["path"]
    require(sha(archive_path.read_bytes()) == data["maps_archive"]["sha256"], "archive hash")
    with gzip.open(archive_path, "rt") as stream:
        header = json.loads(next(stream))
        require(header["block_ids"] == "one-based", "archive ordering declaration")
        rows = [json.loads(line) for line in stream]
    require(len(rows) == 44160, "incomplete maps archive")
    by_label = {label: set() for label in representatives}
    all_families = set()
    for row in rows:
        family = verify_archive_row(row, representatives, sources)
        require(family not in all_families, "duplicate family in archive")
        by_label[row["representative"]].add(family)
        all_families.add(family)
    group = list(group_maps())
    require(len(group) == len({tuple(p) for p in group}) == 3840, "group enumeration")
    for record in records:
        family = representatives[record["id"]]
        orbit = {image(family, p) for p in group}
        stabilizer = sum(image(family, p) == family for p in group)
        require(orbit == by_label[record["id"]], "orbit mismatch")
        require(
            len(orbit) == record["orbit_size"] and stabilizer == record["stabilizer_order"],
            "orbit or stabilizer count",
        )
    pool_checks = []
    for hole_count in (4, 6):
        pool, maps = independent_pool(sources[hole_count], hole_count)
        archived = set().union(
            *(by_label[label] for label in by_label if label.startswith(f"r{hole_count}"))
        )
        require(pool == archived, "independent source map exhaustion differs")
        pool_checks.append(
            {"holes": hole_count, "point_maps": maps, "distinct_families": len(pool)}
        )
        print(json.dumps(pool_checks[-1]), flush=True)
    spec = importlib.util.spec_from_file_location(
        "first_family", ROOT / "scripts/first_family_search.py"
    )
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    model_checks = []
    for record in records:
        family = [tuple(b) for b in record["quadruples"]]
        actual_path = MODELS / record["id"] / "model.pbtxt"
        generated = SCRATCH / f"{record['id']}.pbtxt"
        _, built, _, _ = script.build_model(family)
        built.ExportToFile(str(generated))
        control = verify_model(load_model(generated), family)
        if actual_path.exists():
            verify_model(load_model(actual_path), family)
        model_checks.append(
            {
                "id": record["id"],
                **control,
                "generated_sha256": sha(generated.read_bytes()),
                "actual_path": str(actual_path.relative_to(ROOT)),
                "actual_sha256": sha(actual_path.read_bytes()) if actual_path.exists() else None,
            }
        )
    first = [tuple(b) for b in records[0]["quadruples"]]
    model = load_model(SCRATCH / f"{records[0]['id']}.pbtxt")
    controls = []

    def rejected(name, operation):
        try:
            operation()
        except (ValueError, KeyError, IndexError, TypeError):
            controls.append({"name": name, "rejected": True})
            return
        raise ValueError(f"damage accepted: {name}")

    for name in ("missing_row", "wrong_cardinality", "wrong_domain", "wrong_order", "wrong_table"):
        damaged = copy.deepcopy(model)
        if name == "missing_row":
            del damaged.constraints[-1]
        elif name == "wrong_cardinality":
            damaged.constraints[1120].linear.domain[:] = [63, 63]
        elif name == "wrong_domain":
            damaged.variables[0].domain[:] = [0, 2]
        elif name == "wrong_order":
            damaged.variables[0].name, damaged.variables[1].name = "block_1", "block_0"
        else:
            next(c.table for c in damaged.constraints if c.HasField("table")).values[:] = [0, 4]
        rejected(name, lambda damaged=damaged: verify_model(damaged, first))
    for name in ("duplicate_ids", "bad_bijection", "wrong_source_map", "wrong_orbit_map"):
        row = copy.deepcopy(rows[0])
        if name == "duplicate_ids":
            row["block_ids"][1] = row["block_ids"][0]
        elif name == "bad_bijection":
            row["family_to_representative"][0] = row["family_to_representative"][1]
        elif name == "wrong_source_map":
            row["source_to_family"][0], row["source_to_family"][1] = (
                row["source_to_family"][1],
                row["source_to_family"][0],
            )
        else:
            row["family_to_representative"][3], row["family_to_representative"][4] = (
                row["family_to_representative"][4],
                row["family_to_representative"][3],
            )
        rejected(name, lambda row=row: verify_archive_row(row, representatives, sources))
    rejected("duplicate_input_quad", lambda: script.check_family(first[:-1] + [first[0]]))
    rejected("malformed_input_quad", lambda: script.check_family([(4, 4, 5, 6), *first[1:]]))
    positive, partial_model, values = positive_control(script, rows, records)
    damaged_values = values.copy()
    damaged_values[0] = 1 - damaged_values[0]
    rejected("altered_positive_block", lambda: verify_assignment(partial_model, damaged_values))
    result = {
        "status": "VERIFIED_FIRST_FAMILY_ROWS_AND_ORBITS",
        "representatives": 13,
        "archive_maps": len(rows),
        "group_order": len(group),
        "independent_pools": pool_checks,
        "model_checks": model_checks,
        "damage_controls": controls,
        "positive_control": positive,
        "source_sha256": sha(Path(__file__).read_bytes()),
        "audited_script_sha256": sha((ROOT / "scripts/first_family_search.py").read_bytes()),
        "representatives_sha256": sha(REPS.read_bytes()),
        "maps_sha256": sha(archive_path.read_bytes()),
        "python_version": platform.python_version(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "scope": "Complete conditional on the independently checked local classification and "
        "point-essential normalized mu7 branch; other private-point constraints omitted, "
        "broadening the model. No solver status is a proof.",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {"status": result["status"], "models": len(model_checks), "controls": len(controls)}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
