# Document:    Independent Constructive Clebsch Point Link Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3005660c7a8d9c39b8f70071bd88da04281ea8cf04ae933afc6cd9ec1f8ee6ed
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite inclusion and affine-line checks; never import the producer or a solver."""

import copy
import hashlib
import importlib.util
import json
from collections import Counter
from itertools import combinations, product
from pathlib import Path

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "clebsch-point-link-construction"
SEEDS = [0, 1, 9, 40, 19, 8, 4, 18, 16, 12, 3, 10, 11, 26, 60, 25]
PINS = {
    "build.py": "7b6d507bfa1d75088f5a4c4eb4da39e9bd3ca28b49cd785acca6429d19dd1fe8",
    "classes.json": "6916b285c1c53693b4f2f53bd0194afd6f2c936e1a10da3a236c5311ab86a2cc",
    "recipe-point-maps.json": "752b964d5a9de5b05c2f6f453711df12d2da628606ea65c986135583b041a9a2",
    "summary.json": "82f7c7bcd773bfe73fdb97c4f4bef594399e05742b9c9366b8c401df06f9f67b",
    "files.json": "8ae60931682a39e12c73628045b78bf4d51feb0c8ee7d63e79a84407c3a66f90",
}
FIELD_PRODUCT = ((0, 0, 0, 0), (0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))
POINTS = tuple(product(range(4), repeat=2))
NONZERO = POINTS[1:]
LABEL = {p: i + 1 for i, p in enumerate(NONZERO)}
LOCAL_BLOCKS = tuple(combinations(range(1, 16), 4))
LOCAL_RANK = {b: i for i, b in enumerate(LOCAL_BLOCKS)}
ALL_TRIPLES = tuple(combinations(range(1, 17), 3))
WORDS = [n for n in range(32) if n.bit_count() % 2 == 0]
CLEBSCH_EDGES = {
    (a, b)
    for a, b in combinations(range(1, 17), 2)
    if (WORDS[a - 1] ^ WORDS[b - 1]).bit_count() == 4
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def canonical(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode()


def tuples(raw, width, universe, name, count=None):
    require(type(raw) is list, name + " must be a list")
    if count is not None:
        require(len(raw) == count, name + " count")
    rows = []
    for row in raw:
        require(type(row) is list and len(row) == width, name + " row width")
        require(all(type(x) is int and x in universe for x in row), name + " labels")
        require(row == sorted(set(row)), name + " unordered or repeated label")
        rows.append(tuple(row))
    require(len(rows) == len(set(rows)), name + " duplicate rows")
    return tuple(rows)


def permutation(raw, domain, name):
    require(type(raw) is list and len(raw) == len(domain), name + " size")
    require(all(type(x) is int for x in raw), name + " integer labels")
    require(set(raw) == set(domain), name + " bijection")
    return raw


def affine_lines():
    # Independently enumerate every translated one-dimensional field subspace.
    lines = set()
    for origin in POINTS:
        for direction in NONZERO:
            line = frozenset(
                (
                    origin[0] ^ FIELD_PRODUCT[t][direction[0]],
                    origin[1] ^ FIELD_PRODUCT[t][direction[1]],
                )
                for t in range(4)
            )
            require(len(line) == 4, "affine line cardinality")
            lines.add(line)
    require(len(lines) == 20, "affine plane has twenty lines")
    pair_loads = Counter(pair for line in lines for pair in combinations(sorted(line), 2))
    require(len(pair_loads) == 120 and set(pair_loads.values()) == {1}, "AG pair partition")
    return lines


LINES = affine_lines()
RAYS = {tuple(sorted(LABEL[p] for p in line if p != (0, 0))) for line in LINES if (0, 0) in line}
RETAINED = {tuple(sorted(LABEL[p] for p in line)) for line in LINES if (0, 0) not in line}


def classify(excess, vertices):
    degree = Counter(p for pair in excess for p in pair)
    require(sorted(degree[p] for p in vertices) == [1] * 10 + [4] * 5, "excess degrees")
    heavy = {p for p in vertices if degree[p] == 4}
    core = {pair for pair in excess if set(pair) <= heavy}
    require(len(core) == 5, "five core edges")
    require(all(bool(set(pair) & heavy) for pair in excess), "all leaves pendant to core")
    neighbors = {p: {q for edge in core if p in edge for q in edge if q != p} for p in heavy}
    seen, pending = set(), [next(iter(heavy))]
    while pending:
        p = pending.pop()
        if p not in seen:
            seen.add(p)
            pending.extend(neighbors[p] - seen)
    require(seen == heavy, "core connected")
    ds = sorted(len(neighbors[p]) for p in heavy)
    require(max(ds) <= 3, "core maximum degree three")
    triangles = [
        t
        for t in combinations(sorted(heavy), 3)
        if all(pair in core for pair in combinations(t, 2))
    ]
    if not triangles:
        name = "C5" if ds == [2] * 5 else "C4-leaf"
        require(ds in ([2] * 5, [1, 2, 2, 2, 3]), "nontriangular core shape")
    else:
        require(len(triangles) == 1, "unique core triangle")
        name = "triangle-path2" if ds == [1, 2, 2, 2, 3] else "triangle-two-leaves"
        require(ds in ([1, 2, 2, 2, 3], [1, 1, 2, 3, 3]), "triangular core shape")
    return name, heavy, triangles


def check_class(name, data):
    require(data["ag_points_by_label"] == [list(p) for p in NONZERO], "coordinate labels")
    rays = tuples(data["rays_by_zero_based_index"], 3, range(1, 16), "rays", 5)
    require(set(rays) == RAYS, "five true AG origin rays")
    retained = tuples(data["retained_ag_blocks"], 4, range(1, 16), "retained", 15)
    require(set(retained) == RETAINED, "all fifteen AG lines avoiding origin")
    function = data["function_images_zero_based"]
    require(type(function) is list and len(function) == 5, "function size")
    require(all(type(x) is int and 0 <= x < 5 for x in function), "function labels")
    require(
        all(function[i] != i and function[function[i]] != i for i in range(5)),
        "no fixed points or two cycles",
    )
    require(max(Counter(function).values()) <= 2, "function indegree at most two")
    centers = data["centers_by_zero_based_ray"]
    require(type(centers) is list and len(centers) == len(set(centers)) == 5, "five centers")
    require(
        all(type(c) is int and c in rays[function[i]] for i, c in enumerate(centers)),
        "centers lie in image rays",
    )
    extended = tuples(data["extended_ag_blocks"], 4, range(1, 16), "extended", 5)
    require(
        extended
        == tuple(tuple(sorted((*ray, center))) for ray, center in zip(rays, centers, strict=True)),
        "extensions",
    )
    ag_blocks = sorted(retained + extended)
    require(len(set(ag_blocks)) == 20, "twenty distinct affine blocks")
    mapping_rows = data["ag_to_canonical"]
    require(type(mapping_rows) is list and len(mapping_rows) == 15, "AG mapping length")
    require(all(type(r) is list and len(r) == 2 for r in mapping_rows), "AG mapping rows")
    permutation([r[0] for r in mapping_rows], range(1, 16), "AG source")
    permutation([r[1] for r in mapping_rows], range(1, 16), "AG target")
    mapping = dict(mapping_rows)
    blocks = tuples(data["canonical_blocks"], 4, range(1, 16), "canonical blocks", 20)
    require(
        list(blocks) == sorted(tuple(sorted(mapping[x] for x in b)) for b in ag_blocks),
        "canonical blocks exactly map AG construction",
    )
    variable_ids = data["canonical_block_variable_ids_zero_based_lex"]
    require(all(type(x) is int for x in variable_ids), "integer lex variable IDs")
    require(variable_ids == [LOCAL_RANK[b] for b in blocks], "lex variable IDs")
    pair_load = Counter(p for b in blocks for p in combinations(b, 2))
    require(len(pair_load) == 105 and set(pair_load.values()) == {1, 2}, "all105 pair rows")
    excess = {p for p, count in pair_load.items() if count == 2}
    require(len(excess) == 15, "fifteen excess edges")
    require(
        set(tuples(data["canonical_excess_edges"], 2, range(1, 16), "excess", 15)) == excess,
        "saved excess agrees",
    )
    shape, heavy, triangles = classify(excess, range(1, 16))
    require(shape == name, "class name")
    triple_load = Counter(t for b in blocks for t in combinations(b, 3))
    require(len(triple_load) == 80 and max(triple_load.values()) == 1, "eighty outside triples")
    caps = tuples(data["canonical_triangle_caps"], 3, range(1, 16), "triangle caps")
    require(list(caps) == triangles, "exact triangle caps")
    require(data["triangle_block_counts"] == [triple_load[t] for t in triangles], "cap counts")
    require(all(triple_load[t] <= 1 for t in triangles), "triangle upper bound one")
    require(
        data["canonical_block_sha256"] == hashlib.sha256(canonical(blocks)).hexdigest(),
        "canonical witness hash",
    )
    return {
        "name": name,
        "blocks": blocks,
        "excess": excess,
        "caps": caps,
        "pair_histogram": dict(Counter(pair_load.values())),
        "heavy": heavy,
    }


def check_profile(profile):
    rows = tuples(profile, 3, range(1, 17), "profile", 80)
    require(
        all(sum(pair in CLEBSCH_EDGES for pair in combinations(t, 2)) == 2 for t in rows),
        "all excess triples are induced Clebsch paths",
    )
    loads = Counter(pair for t in rows for pair in combinations(t, 2))
    require(
        all(loads[p] == 1 + 3 * (p in CLEBSCH_EDGES) for p in combinations(range(1, 17), 2)),
        "profile pair demands",
    )
    return set(rows)


def check_map(row, classes, profiles):
    seed, point = row["profile_seed"], row["point"]
    require(type(seed) is int and seed in SEEDS, "profile seed")
    require(type(point) is int and 1 <= point <= 16, "point")
    profile = profiles[seed]
    require(
        row["source_profile_canonical_sha256"] == hashlib.sha256(canonical(profile)).hexdigest(),
        "source profile canonical hash",
    )
    others = tuple(p for p in range(1, 17) if p != point)
    inverse = permutation(row["canonical_to_actual"], others, "canonical to actual")
    forward_rows = row["actual_to_canonical"]
    require(type(forward_rows) is list and len(forward_rows) == 15, "forward map length")
    require(all(type(r) is list and len(r) == 2 for r in forward_rows), "forward map rows")
    require([r[0] for r in forward_rows] == list(others), "forward source labels")
    permutation([r[1] for r in forward_rows], range(1, 16), "actual to canonical")
    forward = dict(forward_rows)
    require(all(inverse[forward[p] - 1] == p for p in others), "inverse maps agree")
    data = classes[row["class"]]
    excess = {tuple(p for p in t if p != point) for t in profile if point in t}
    require(
        {tuple(sorted(forward[p] for p in pair)) for pair in excess} == data["excess"],
        "exact excess graph isomorphism",
    )
    name, heavy, triangles = classify(excess, others)
    require(name == row["class"], "mapped class")
    require(
        heavy == {p for p in others if tuple(sorted((p, point))) in CLEBSCH_EDGES},
        "heavy vertices are exactly Clebsch neighbors",
    )
    blocks = sorted(tuple(sorted(inverse[x - 1] for x in b)) for b in data["blocks"])
    require(len(blocks) == len(set(blocks)) == 20, "mapped distinct K4s")
    pair_load = Counter(pair for b in blocks for pair in combinations(b, 2))
    require(
        all(pair_load[pair] == 1 + (pair in excess) for pair in combinations(others, 2)),
        "mapped105 exact pair rows",
    )
    caps = tuples(row["actual_triangle_caps"], 3, others, "mapped caps")
    require(set(caps) == set(triangles), "all and only actual triangles")
    require(all(t not in profile for t in caps), "outside cap demand exactly one")
    outside = Counter(t for b in blocks for t in combinations(b, 3))
    require(len(outside) == 80 and max(outside.values()) == 1, "mapped outside occupancy")
    residual = {t: 1 + (t in profile) - outside[t] for t in combinations(others, 3)}
    require(len(residual) == 455 and min(residual.values()) >= 0, "all455 nonnegative rows")
    require(
        sum(residual.values()) == 440 and row["remaining_block_count"] == 44,
        "440 residual incidences need44 blocks",
    )
    histogram = {str(k): v for k, v in sorted(Counter(residual.values()).items())}
    require(row["residual_histogram"] == histogram, "residual histogram")
    partial = sorted(tuple(sorted((point, *b))) for b in blocks)
    require(
        hashlib.sha256(canonical(partial)).hexdigest() == row["partial_canonical_sha256"],
        "partial witness hash",
    )
    full_load = Counter(t for b in partial for t in combinations(b, 3))
    require(len(full_load) == 185 and sum(full_load.values()) == 200, "partial185 covered")
    require(sum(full_load[t] == 0 for t in ALL_TRIPLES) == 375, "partial375 holes")
    require(all(full_load[t] <= 1 + (t in profile) for t in ALL_TRIPLES), "all560 residual caps")
    return partial


def check_maps(rows, classes, profiles):
    require(type(rows) is list and len(rows) == 256, "256 map rows")
    require(
        [(r["profile_seed"], r["point"]) for r in rows]
        == [(seed, p) for seed in SEEDS for p in range(1, 17)],
        "complete map order",
    )
    return [check_map(row, classes, profiles) for row in rows]


def damage_controls(raw_classes, maps, classes, profiles):
    tests = []

    def reject(label, call):
        try:
            call()
        except (ValueError, KeyError, IndexError, TypeError):
            tests.append(label)
        else:
            raise AssertionError("accepted damaged control: " + label)

    name = "triangle-path2"
    for key, value in [
        ("canonical_blocks", raw_classes[name]["canonical_blocks"][:-1]),
        (
            "canonical_blocks",
            raw_classes[name]["canonical_blocks"] + [raw_classes[name]["canonical_blocks"][0]],
        ),
        ("function_images_zero_based", [True, 2, 0, 0, 3]),
        ("function_images_zero_based", [0, 2, 0, 0, 3]),
        ("centers_by_zero_based_ray", [1] * 5),
        ("canonical_block_variable_ids_zero_based_lex", list(range(20))),
        ("canonical_excess_edges", raw_classes[name]["canonical_excess_edges"][:-1]),
        ("canonical_triangle_caps", []),
        ("triangle_block_counts", [2]),
        ("canonical_block_sha256", "0" * 64),
    ]:
        damaged = copy.deepcopy(raw_classes[name])
        damaged[key] = value
        reject("class_" + key + "_" + str(len(tests)), lambda d=damaged: check_class(name, d))
    for key, value in [
        ("point", True),
        ("profile_seed", False),
        ("class", "C5"),
        ("canonical_to_actual", [2] * 15),
        ("actual_to_canonical", maps[0]["actual_to_canonical"][:-1]),
        ("actual_triangle_caps", []),
        ("remaining_block_count", 45),
        ("residual_histogram", {"0": 455}),
        ("partial_canonical_sha256", "0" * 64),
        ("source_profile_canonical_sha256", "0" * 64),
    ]:
        damaged = copy.deepcopy(maps[0])
        damaged[key] = value
        reject("map_" + key, lambda d=damaged: check_map(d, classes, profiles))
    reject("missing_map", lambda: check_maps(maps[:-1], classes, profiles))
    reject("duplicated_map", lambda: check_maps(maps[:-1] + [maps[0]], classes, profiles))
    return tests


def main():
    require(not (HERE / "review.json").exists(), "preserve existing audit")
    for name, expected in PINS.items():
        require(sha(SOURCE / name) == expected, "frozen file pin: " + name)
    file_index = read(SOURCE / "files.json")
    for name, expected in file_index.items():
        require(sha(SOURCE / name) == expected, "producer index: " + name)
    summary = read(SOURCE / "summary.json")
    profile_path = ROOT / summary["input_file"]
    require(
        sha(profile_path)
        == summary["input_sha256"]
        == "4e5ccb1563991e106f2a40e9c8160059eb48d44930bc53d7d4607d44fca208d5",
        "profile input",
    )
    package_path = ROOT / "src/covering64/core.py"
    standalone_path = ROOT / "scripts/check_cover.py"
    require(
        sha(package_path)
        == summary["package_verifier_sha256"]
        == "3b49b76a0fe243efe8bbba5fdc0887b754e7e3cd24c177dfc7531c2036f22beb",
        "package pin",
    )
    require(
        sha(standalone_path)
        == summary["standalone_verifier_sha256"]
        == "755fecdc6978f94afa7bbaad299fc55bcfd4d4afe831951bdc70d1e81698e950",
        "standalone pin",
    )
    spec = importlib.util.spec_from_file_location("independent_standalone", standalone_path)
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    raw_profiles = read(profile_path)
    require(set(raw_profiles) == set(map(str, SEEDS)), "sixteen source profiles")
    profiles = {seed: check_profile(raw_profiles[str(seed)]) for seed in SEEDS}
    raw_classes = read(SOURCE / "classes.json")
    require(
        set(raw_classes) == {"C5", "C4-leaf", "triangle-path2", "triangle-two-leaves"},
        "four expected classes",
    )
    classes = {name: check_class(name, data) for name, data in raw_classes.items()}
    for name, data in classes.items():
        require(
            (SOURCE / f"{name}-canonical-k4.txt").read_bytes() == canonical(data["blocks"]),
            "saved canonical K4 text",
        )
    maps = read(SOURCE / "recipe-point-maps.json")
    partials = check_maps(maps, classes, profiles)
    census = dict(Counter(row["class"] for row in maps))
    per_profile = {
        str(seed): dict(Counter(row["class"] for row in maps if row["profile_seed"] == seed))
        for seed in SEEDS
    }
    require(
        census
        == summary["class_counts"]
        == {"C5": 16, "C4-leaf": 80, "triangle-path2": 80, "triangle-two-leaves": 80},
        "census",
    )
    require(per_profile == summary["profile_class_counts"], "per-profile census")
    representatives, partial_hashes = {}, []
    for row, partial in zip(maps, partials, strict=True):
        package = verify_cover(partial)
        separate = standalone.verify_cover(partial, expected_blocks=20)
        require(package["blocks"] == separate["blocks"] == 20, "dual count")
        require(package["covered"] == separate["covered_subsets"] == 185, "dual coverage")
        require(len(package["uncovered"]) == separate["uncovered_count"] == 375, "dual holes")
        require(
            package["canonical_sha256"]
            == separate["canonical_sha256"]
            == row["partial_canonical_sha256"],
            "dual hash",
        )
        require(package["valid"] is separate["valid"] is False, "partials never covers")
        partial_hashes.append(row["partial_canonical_sha256"])
        name = row["class"]
        if name not in representatives:
            require(
                (SOURCE / f"{name}-actual-partial.txt").read_bytes() == canonical(partial),
                "saved actual partial",
            )
            require(
                read(SOURCE / f"{name}-package-verifier.json") == json.loads(json.dumps(package)),
                "producer package receipt",
            )
            require(
                read(SOURCE / f"{name}-standalone-verifier.json")
                == json.loads(json.dumps(separate)),
                "producer standalone receipt",
            )
            representatives[name] = {k: row[k] for k in ("profile_seed", "point")}
            representatives[name]["sha256"] = row["partial_canonical_sha256"]
    require(representatives == summary["representatives"], "representatives")
    require(
        summary["verified_recipe_point_maps"] == 256
        and summary["exact_pair_rows_per_map"] == 105
        and summary["outside_residual_rows_per_map"] == 455
        and summary["local_variables_zero_based_lex"] == 1365,
        "summary row counts",
    )
    require(
        summary["all_pair_rows_and_triangle_caps_passed"] is True
        and summary["all_outside_residuals_nonnegative"] is True,
        "summary verdicts",
    )
    require(
        summary["solver_calls"] == summary["solver_seconds"] == 0
        and summary["planned_local_cp_calls_canceled"] is True,
        "finite-only producer metadata",
    )
    controls = damage_controls(raw_classes, maps, classes, profiles)
    output = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "producer_pins": PINS,
        "input_sha256": sha(profile_path),
        "package_sha256": sha(package_path),
        "standalone_sha256": sha(standalone_path),
        "affine_lines_independently_enumerated": 20,
        "affine_pair_partition_rows": 120,
        "canonical_classes_verified": 4,
        "class_census": census,
        "per_profile_census": per_profile,
        "recipe_point_maps_verified": 256,
        "map_pair_rows_verified": 256 * 105,
        "map_outside_residual_rows_verified": 256 * 455,
        "map_all_global_triple_caps_verified": 256 * 560,
        "dual_verified_partials": 256,
        "partial_block_count": 20,
        "partial_covered_triples": 185,
        "partial_holes": 375,
        "remaining_block_count": 44,
        "residual_triple_total": 440,
        "distinct_partial_hashes": len(set(partial_hashes)),
        "partial_hashes": partial_hashes,
        "representatives": representatives,
        "malformed_controls_rejected": controls,
        "optimizer_calls": 0,
        "producer_imported": False,
        "scope": (
            "Explicit local feasibility for four shapes and256 recorded links. "
            "No claim that separate point links are globally compatible; no full64 cover. "
            "A future residual completion run from one chosen link is conditional only."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    require((HERE / "review.json").stat().st_size < 1_000_000, "compact audit receipt")
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(HERE / "review.json"),
                "maps": 256,
                "dual_verified_partials": 256,
                "controls": len(controls),
            }
        )
    )


if __name__ == "__main__":
    main()
