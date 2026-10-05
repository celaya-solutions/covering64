# Document:    Independent Affine Extension Point Variant Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      437686d5369c002c0bdd2d1569e3233fe5ba8c7a592e769302a671265e5dd89e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite enumeration, full graph groups, orbit replay, and dual verification."""

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, permutations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / "experiments/2026-10-04"
RAW = ROOT / "experiments/scratch/affine-extension-point-variants-independent-20261004"
PRODUCER = BASE / "affine-extension-point-variants"
QUADS = tuple(combinations(range(1, 16), 4))
QUAD_IDS = {block: index for index, block in enumerate(QUADS)}
PAIRS = tuple(combinations(range(1, 16), 2))
TRIPLES = tuple(combinations(range(1, 17), 3))
EXPECTED = {
    "C4-leaf": (162, 54, 53, 96, 159),
    "C5": (243, 17, 16, 320, 228),
    "triangle-path2": (162, 54, 53, 96, 159),
    "triangle-two-leaves": (108, 36, 35, 144, 105),
}
PINS = {
    "experiments/2026-10-04/affine-extension-point-variants/build.py": (
        "7b4efecb71a39285104c9bd2cdfbfef316c4ea0c8ae045850700d5e4307c5adc"
    ),
    "experiments/2026-10-04/affine-extension-point-variants/settings.json": (
        "a7c11a554f4dc39a4d8d55caf552dd91b6efc0a3fc63e8b530cc4bab63dcc98b"
    ),
    "experiments/2026-10-04/affine-extension-point-variants/representatives.json": (
        "2db5cd79692f83847e2951fb13b08acb72d4e7b9e7f3fdba1557f931a69b9a7d"
    ),
    "experiments/2026-10-04/affine-extension-point-variants/summary.json": (
        "9c3767f7510862b587374ed5e6bd616eccc533d60eaad619fc6edc36695046a6"
    ),
    "experiments/2026-10-04/clebsch-point-link-construction/classes.json": (
        "6916b285c1c53693b4f2f53bd0194afd6f2c936e1a10da3a236c5311ab86a2cc"
    ),
    "experiments/2026-10-04/circulant-chosen-link-independent/catalog-audit.json": (
        "e832913ef7d0ead42fdcb9c75538654e6dedfdb81091dd44519fa900cfbfe158"
    ),
    "experiments/2026-10-04/circulant-chosen-link-catalog/link-fibers.json": (
        "26bf0612bcf1a17ecc72d2bd214235a2ddc4151e0b07444ba87bc58b5fa82f60"
    ),
    "experiments/2026-10-04/circulant-chosen-link-catalog/profiles.json": (
        "24ccef8eb95cd04e683a575d60fcba854728615ee2ca6495f2bc6028fc56cf0f"
    ),
    "src/covering64/core.py": (
        "3b49b76a0fe243efe8bbba5fdc0887b754e7e3cd24c177dfc7531c2036f22beb"
    ),
    "scripts/check_cover.py": (
        "755fecdc6978f94afa7bbaad299fc55bcfd4d4afe831951bdc70d1e81698e950"
    ),
    "uv.lock": (
        "7c16c4cf38ece8bf42885d1bab9698ced20c0411036f43b2f21f1e8cb2c5e180"
    ),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    require(len(data) < 1_000_000, f"receipt size: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return digest(path)


def ordered(blocks):
    return tuple(sorted(tuple(sorted(block)) for block in blocks))


def image(blocks, mapping):
    return ordered(tuple(mapping[v - 1] for v in block) for block in blocks)


def graph_image(edges, mapping):
    return set(image(edges, mapping))


def check_map(mapping, source, target, labels=tuple(range(1, 16))):
    require(len(mapping) == 15, "mapping length")
    require(all(type(v) is int for v in mapping), "mapping integer labels")
    require(tuple(sorted(mapping)) == labels, "mapping bijection")
    require(graph_image(source, mapping) == target, "mapping graph image")


def graph_group(edges):
    """All automorphisms: degree-four vertices and their degree-one leaves."""
    neighbors = {v: {w for e in edges if v in e for w in e if w != v} for v in range(1, 16)}
    heavy = tuple(v for v in neighbors if len(neighbors[v]) == 4)
    leaves = tuple(v for v in neighbors if len(neighbors[v]) == 1)
    require(len(heavy) == 5 and len(leaves) == 10, "degree partition")
    require(all(next(iter(neighbors[v])) in heavy for v in leaves), "leaf attachment")
    core = {edge for edge in edges if set(edge) <= set(heavy)}
    attached = {v: tuple(sorted(neighbors[v] & set(leaves))) for v in heavy}
    result = []
    for targets in permutations(heavy):
        base = dict(zip(heavy, targets))
        if {tuple(sorted(base[v] for v in edge)) for edge in core} != core:
            continue
        if any(len(attached[v]) != len(attached[base[v]]) for v in heavy):
            continue
        for choices in product(*(permutations(attached[base[v]]) for v in heavy)):
            mapping = dict(base)
            for v, destination in zip(heavy, choices):
                mapping.update(zip(attached[v], destination))
            vector = tuple(mapping[v] for v in range(1, 16))
            check_map(vector, edges, edges)
            result.append(vector)
    require(len(result) == len(set(result)), "unique graph automorphisms")
    return tuple(sorted(result))


def local_check(blocks, expected_edges=None):
    require(isinstance(blocks, (list, tuple)) and len(blocks) == 20, "twenty local blocks")
    for block in blocks:
        require(isinstance(block, (list, tuple)) and len(block) == 4, "quad shape")
        require(all(type(v) is int and 1 <= v <= 15 for v in block), "strict local labels")
        require(len(set(block)) == 4, "distinct labels")
        require(list(block) == sorted(block), "sorted local labels")
    normalized = tuple(tuple(block) for block in blocks)
    require(normalized == tuple(sorted(normalized)), "lex block order")
    require(len(set(normalized)) == 20, "distinct local blocks")
    pair_counts = Counter(pair for block in normalized for pair in combinations(block, 2))
    require(set(pair_counts) == set(PAIRS), "all local pairs")
    require(set(pair_counts.values()) == {1, 2}, "pair demands one or two")
    excess = {edge for edge, count in pair_counts.items() if count == 2}
    require(len(excess) == 15, "fifteen excess edges")
    if expected_edges is not None:
        require(all(pair_counts[p] == 1 + (p in expected_edges) for p in PAIRS), "exact pair rows")
    counts = Counter(triple for block in normalized for triple in combinations(block, 3))
    require(len(counts) == 80 and max(counts.values()) == 1, "all 455 triple caps")
    return excess


def orbit_key(blocks, group):
    return min(tuple(QUAD_IDS[b] for b in image(blocks, mapping)) for mapping in group)


def partition_check(expected, saved, old_key):
    require(len(saved) == len(expected), "orbit count")
    seen = set()
    for row in saved:
        key = tuple(row["quad_ids"])
        require(key in expected and key not in seen, "unique expected orbit key")
        seen.add(key)
        require(row["blocks"] == [list(QUADS[i]) for i in key], "representative block IDs")
        require(row["setting_indices"] == expected[key], "complete setting partition")
        require(type(row["old_witness_orbit"]) is bool, "strict old orbit Boolean")
        require(row["old_witness_orbit"] == (key == old_key), "old orbit membership")
    require(seen == set(expected), "all orbit keys present")


def load_verifiers():
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    spec = importlib.util.spec_from_file_location(
        "variant_standalone", ROOT / "scripts/check_cover.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return verify_cover, module.verify_cover


def controls(blocks, edges, expected, saved, old_key, package, standalone):
    rejected = []

    def reject(label, operation):
        try:
            operation()
        except (AssertionError, ValueError, TypeError):
            rejected.append(label)
        else:
            raise AssertionError(f"damaged control accepted: {label}")

    for label, bad in (
        ("missing_block", blocks[:-1]),
        ("extra_block", blocks + blocks[:1]),
        ("duplicate_block", sorted(blocks[:-1] + blocks[:1])),
        ("unsorted_blocks", list(reversed(blocks))),
    ):
        reject(label, lambda bad=bad: local_check(bad, edges))
    for label, value in (("zero", 0), ("sixteen", 16), ("boolean", True), ("string", "1")):
        bad = [list(block) for block in blocks]
        bad[0][0] = value
        reject(label, lambda bad=bad: local_check(bad, edges))
    bad = [list(block) for block in blocks]
    bad[0][0] = bad[0][1]
    reject("repeated_label", lambda: local_check(bad, edges))
    altered = [list(block) for block in blocks]
    altered[0][0] = next(v for v in range(1, 16) if v not in altered[0])
    altered = [list(block) for block in ordered(altered)]
    reject("valid_labels_damaged_pairs", lambda: local_check(altered, edges))
    reject("missing_orbit", lambda: partition_check(expected, saved[:-1], old_key))
    duplicate = read(PRODUCER / "representatives.json")["C4-leaf"]
    duplicate[1] = duplicate[0]
    reject("duplicate_orbit", lambda: partition_check(expected, duplicate, old_key))
    bad_partition = json.loads(json.dumps(saved))
    bad_partition[0]["setting_indices"] = bad_partition[0]["setting_indices"][:-1]
    reject("missing_setting", lambda: partition_check(expected, bad_partition, old_key))
    bad_old = json.loads(json.dumps(saved))
    bad_old[0]["old_witness_orbit"] = not bad_old[0]["old_witness_orbit"]
    reject("wrong_old_membership", lambda: partition_check(expected, bad_old, old_key))
    reject("nonbijection", lambda: check_map([1] * 15, edges, edges))
    bad_permutation = list(range(1, 16))
    bad_permutation[0], bad_permutation[5] = bad_permutation[5], bad_permutation[0]
    reject("wrong_graph_map", lambda: check_map(bad_permutation, edges, edges))
    for name, verifier in (("package", package), ("standalone", standalone)):
        duplicate_blocks = blocks[:-1] + blocks[:1]
        reject(name + "_duplicate", lambda v=verifier: v(duplicate_blocks, v=15, k=4, t=2))
        malformed = [list(block) for block in blocks]
        malformed[0][0] = 0
        reject(name + "_malformed", lambda v=verifier: v(malformed, v=15, k=4, t=2))
        result = verifier(blocks[:-1], v=15, k=4, t=2)
        require(not result["valid"], name + " damaged cover detection")
        rejected.append(name + "_missing_block")
    return rejected


def main():
    for path, expected in PINS.items():
        require(digest(ROOT / path) == expected, "input pin: " + path)
    classes = read(BASE / "clebsch-point-link-construction/classes.json")
    settings = read(PRODUCER / "settings.json")
    representatives = read(PRODUCER / "representatives.json")
    producer_summary = read(PRODUCER / "summary.json")
    fibers = read(BASE / "circulant-chosen-link-catalog/link-fibers.json")
    profiles = read(BASE / "circulant-chosen-link-catalog/profiles.json")
    package, standalone = load_verifiers()
    require(list(classes) == list(EXPECTED), "fixed recipe class order")
    require(len(settings) == 675, "saved settings count")
    index, summaries, groups, validations, raw_files = 0, {}, {}, [], {}
    for kind, model in classes.items():
        edges = {tuple(edge) for edge in model["canonical_excess_edges"]}
        group = graph_group(edges)
        groups[kind] = group
        old_blocks = tuple(tuple(block) for block in model["canonical_blocks"])
        local_check(old_blocks, edges)
        old_key = orbit_key(old_blocks, group)
        rays = model["rays_by_zero_based_index"]
        retained = model["retained_ag_blocks"]
        require(len(rays) == 5 and len(retained) == 15, "fixed affine line counts")
        require(sorted(v for ray in rays for v in ray) == list(range(1, 16)), "rays partition")
        domains = [tuple(rays[target]) for target in model["function_images_zero_based"]]
        require(all(len(domain) == 3 for domain in domains), "three extension choices per ray")
        replay, raw_count, repeated = defaultdict(list), 0, 0
        for choice in product(*domains):
            raw_count += 1
            if len(set(choice)) != 5:
                skipped_blocks = retained + [list(ray) + [v] for ray, v in zip(rays, choice)]
                skipped_pairs = Counter(
                    pair for block in skipped_blocks for pair in combinations(sorted(block), 2)
                )
                require(set(skipped_pairs) == set(PAIRS), "skipped setting pair universe")
                require(set(skipped_pairs.values()) == {1, 2}, "skipped setting pair loads")
                skipped_degrees = Counter(
                    v for pair, count in skipped_pairs.items() if count == 2 for v in pair
                )
                require(max(skipped_degrees.values()) == 7, "repeated center degree obstruction")
                repeated += 1
                continue
            blocks = ordered(retained + [list(ray) + [v] for ray, v in zip(rays, choice)])
            source_edges = local_check(blocks)
            saved = settings[index]
            require(saved["index"] == index and saved["class"] == kind, "setting identity")
            require(saved["extension_points"] == list(choice), "all extension choices replayed")
            mapping = saved["ag_to_canonical"]
            check_map(mapping, source_edges, edges)
            mapped = image(blocks, mapping)
            local_check(mapped, edges)
            key = orbit_key(mapped, group)
            require(saved["representative_quad_ids"] == list(key), "independent orbit minimum")
            rep_map = saved["canonical_to_representative"]
            require(tuple(rep_map) in group, "saved representative map is full-group member")
            require(tuple(QUAD_IDS[b] for b in image(mapped, rep_map)) == key, "explicit orbit map")
            require(type(saved["old_witness_orbit"]) is bool, "strict membership flag")
            require(saved["old_witness_orbit"] == (key == old_key), "setting old orbit flag")
            replay[key].append(index)
            index += 1
        require(raw_count == 243, "exhaustive three-to-the-fifth settings")
        require(old_key in replay, "old witness orbit present")
        partition_check(replay, representatives[kind], old_key)
        new_settings = sum(len(members) for key, members in replay.items() if key != old_key)
        observed = (raw_count - repeated, len(replay), len(replay) - 1, len(group), new_settings)
        require(observed == EXPECTED[kind], "independently derived class counts")
        summaries[kind] = {
            "raw_settings": raw_count,
            "duplicate_center_settings": repeated,
            "valid_settings": observed[0],
            "orbits": observed[1],
            "new_orbits": observed[2],
            "automorphisms": observed[3],
            "new_settings": observed[4],
            "orbit_setting_size_histogram": dict(
                sorted(Counter(map(len, replay.values())).items())
            ),
        }
        producer_counts = producer_summary["counts"][kind]
        for field, value in (
            ("raw_settings", raw_count),
            ("duplicate_center_settings", repeated),
            ("valid_settings", observed[0]),
            ("orbits", observed[1]),
            ("new_orbits", observed[2]),
            ("automorphism_count", observed[3]),
            ("settings_beyond_old_orbit", observed[4]),
        ):
            require(producer_counts[field] == value, "producer summary field: " + field)
        fiber = next(row for row in fibers if row["class"] == kind)
        mapping = fiber["canonical_to_actual"]
        actual_edges = {tuple(edge) for edge in fiber["actual_excess_edges"]}
        check_map(mapping, edges, actual_edges, tuple(range(2, 17)))
        profile = profiles[fiber["profile_ids"][0]]
        excess_triples = {tuple(triple) for triple in profile["excess_triples"]}
        require(
            {triple[1:] for triple in excess_triples if triple[0] == 1} == actual_edges,
            "point-one profile fiber",
        )
        for number, row in enumerate(representatives[kind]):
            local = row["blocks"]
            local_check(local, edges)
            actual = ordered((1,) + block for block in image(local, mapping))
            counts = Counter(triple for block in actual for triple in combinations(block, 3))
            residual = {
                triple: 1 + (triple in excess_triples) - counts[triple] for triple in TRIPLES
            }
            require(
                min(residual.values()) >= 0 and sum(residual.values()) == 440,
                "nonnegative exact-profile residual",
            )
            require(
                all(value == 0 for triple, value in residual.items() if 1 in triple),
                "point-one demands exhausted",
            )
            receipts = {}
            for label, witness, v, k, t, covered, holes in (
                ("local", local, 15, 4, 2, 105, 0),
                ("actual", actual, 16, 5, 3, 185, 375),
            ):
                pkg = package(witness, v=v, k=k, t=t)
                ind = standalone(witness, v=v, k=k, t=t, expected_blocks=20)
                require(pkg["blocks"] == ind["blocks"] == 20, "dual block count")
                require(pkg["covered"] == ind["covered_subsets"] == covered, "dual covered count")
                require(len(pkg["uncovered"]) == ind["uncovered_count"] == holes, "dual hole count")
                require(pkg["canonical_sha256"] == ind["canonical_sha256"], "dual canonical hash")
                require(pkg["valid"] == ind["valid"] == (holes == 0), "dual validity status")
                receipts[label] = {"blocks": witness, "package": pkg, "standalone": ind}
            raw_path = RAW / kind / f"representative-{number:03d}.json"
            raw_sha = save(raw_path, receipts)
            raw_files[str(raw_path.relative_to(ROOT))] = raw_sha
            validations.append(
                {
                    "class": kind,
                    "representative": number,
                    "old_witness_orbit": row["old_witness_orbit"],
                    "excess_link_id": fiber["excess_link_id"],
                    "profile_id": profile["profile_id"],
                    "local_sha256": receipts["local"]["package"]["canonical_sha256"],
                    "actual_sha256": receipts["actual"]["package"]["canonical_sha256"],
                    "raw_path": str(raw_path.relative_to(ROOT)),
                    "raw_sha256": raw_sha,
                }
            )
        if kind == "C4-leaf":
            rejected = controls(
                representatives[kind][0]["blocks"],
                edges,
                replay,
                representatives[kind],
                old_key,
                package,
                standalone,
            )
    require(index == len(settings), "entire setting list checked")
    require(len(validations) == 161, "all representatives dual checked")
    group_hash = save(HERE / "automorphisms.json", groups)
    validation_hash = save(HERE / "representative-verification.json", validations)
    raw_index_hash = save(HERE / "raw-files.json", raw_files)
    receipt = {
        "passed": True,
        "checker_sha256": digest(Path(__file__)),
        "input_pins": PINS,
        "producer_imports": 0,
        "optimizer_calls": 0,
        "counts": summaries,
        "raw_settings_enumerated": 972,
        "valid_settings": index,
        "distinct_excess_automorphism_orbits": len(validations),
        "new_orbits": 157,
        "new_settings": sum(v[4] for v in EXPECTED.values()),
        "automorphisms_sha256": group_hash,
        "representative_verification_sha256": validation_hash,
        "raw_files_sha256": raw_index_hash,
        "dual_local_pair_covers_checked": len(validations),
        "dual_actual_partials_checked": len(validations),
        "actual_partial_blocks": 20,
        "actual_partial_covered": 185,
        "actual_partial_holes": 375,
        "damaged_controls_rejected": rejected,
        "scope": "Complete for extension-point choices of four fixed ray-target recipes only; "
        "not all affine constructions, not a full cover, and not a global exclusion.",
    }
    save(HERE / "review.json", receipt)
    print(
        json.dumps(
            {
                "passed": True,
                "valid_settings": index,
                "orbits": len(validations),
                "new_orbits": 157,
                "damaged_controls": len(rejected),
                "review_sha256": digest(HERE / "review.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
