"""Independent permutation enumeration and direct recount of the chosen links."""

import copy
import json
import subprocess
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, permutations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAT = ROOT / "experiments/2026-10-04/circulant-chosen-link-catalog"
ALL = ROOT / "experiments/2026-10-04/circulant-all-excess-profiles"
CLASSES = ROOT / "experiments/2026-10-04/clebsch-point-link-construction/classes.json"
BLOCKS = list(combinations(range(1, 17), 5))


def family(blocks):
    return tuple(sorted(tuple(sorted(block)) for block in blocks))


def recount(images, fibers, partials, profiles, classes, expected_profiles):
    assert len(partials) == 5536 and len(fibers) == 38 and len(profiles) == 1300
    image_counts = {}
    for kind, model in classes.items():
        edges = {tuple(edge) for edge in model["canonical_excess_edges"]}
        centers = sorted(v for v in range(1, 16) if sum(v in e for e in edges) == 4)
        assert centers == list(range(1, 6))
        leaves = {
            v: sorted(b if a == v else a for a, b in edges if v in (a, b) and max(a, b) > 5)
            for v in centers
        }
        core = {e for e in edges if max(e) <= 5}
        expected = set()
        maps = set()
        for p in permutations(centers):
            center_map = dict(zip(centers, p))
            if {tuple(sorted(center_map[v] for v in e)) for e in core} != core:
                continue
            targets = [list(permutations(leaves[center_map[v]])) for v in centers]
            for leaf_images in product(*targets):
                mapping = center_map.copy()
                for v, values in zip(centers, leaf_images):
                    mapping.update(zip(leaves[v], values))
                assert len(mapping) == 15 and len(set(mapping.values())) == 15
                assert {tuple(sorted(mapping[v] for v in e)) for e in edges} == edges
                expected.add(family([[mapping[v] for v in b] for b in model["canonical_blocks"]]))
                maps.add(tuple(mapping[v] for v in range(1, 16)))
        actual = {family(row["canonical_blocks"]) for row in images[kind]}
        assert actual == expected and len(actual) == len(images[kind]) == len(maps)
        assert {tuple(row["canonical_permutation"]) for row in images[kind]} == maps
        for row in images[kind]:
            mapping = dict(zip(range(1, 16), row["canonical_permutation"]))
            assert family(row["canonical_blocks"]) == family(
                [[mapping[v] for v in b] for b in model["canonical_blocks"]]
            )
        image_counts[kind] = len(expected)

    expected_fibers = defaultdict(list)
    for i, (profile, expected) in enumerate(zip(profiles, expected_profiles)):
        assert family(profile["excess_triples"]) == expected
        link = tuple(
            sorted(tuple(v for v in triple if v != 1) for triple in expected if 1 in triple)
        )
        expected_fibers[link].append(i)
    assert len(expected_fibers) == 38
    seen_profiles = []
    observed_fibers = set()
    all_families = set()
    expected_id = 0
    pair_count = 0
    for fiber_id, fiber in enumerate(fibers):
        link = family(fiber["actual_excess_edges"])
        assert link not in observed_fibers
        observed_fibers.add(link)
        assert fiber["profile_ids"] == expected_fibers[link]
        seen_profiles.extend(fiber["profile_ids"])
        kind = fiber["class"]
        mapping = dict(zip(range(1, 16), fiber["canonical_to_actual"]))
        assert sorted(mapping.values()) == list(range(2, 17))
        assert (
            family([[mapping[v] for v in e] for e in classes[kind]["canonical_excess_edges"]])
            == link
        )
        assert dict(fiber["actual_to_canonical"]) == {v: k for k, v in mapping.items()}
        start, stop = fiber["partial_id_range_half_open"]
        assert start == expected_id and stop - start == image_counts[kind]
        for image_id, image in enumerate(images[kind]):
            partial = partials[start + image_id]
            assert partial["partial_id"] == start + image_id
            assert partial["excess_link_id"] == fiber_id
            assert partial["canonical_image_id"] == image_id
            ids = partial["global_block_ids"]
            assert len(ids) == len(set(ids)) == 20
            assert all(type(i) is int and 0 <= i < 1365 for i in ids)
            blocks = tuple(BLOCKS[i] for i in ids)
            assert blocks == family(
                [[1] + [mapping[v] for v in b] for b in image["canonical_blocks"]]
            )
            assert blocks not in all_families
            all_families.add(blocks)
            counts = Counter(triple for block in blocks for triple in combinations(block, 3))
            assert len(counts) == 185 and sum(counts.values()) == 200
            assert all(n == 1 for t, n in counts.items() if 1 not in t)
            assert all(
                counts[(1,) + pair] == 1 + (pair in link) for pair in combinations(range(2, 17), 2)
            )
            text = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
            assert sha256(text.encode()).hexdigest() == partial["partial_canonical_sha256"]
        expected_id = stop
        pair_count += (stop - start) * len(fiber["profile_ids"])
    assert expected_id == len(partials)
    assert sorted(seen_profiles) == list(range(1300)) and pair_count == 195296
    return image_counts


def main():
    pins = json.loads((CAT / "files.json").read_text())
    for name, digest in pins.items():
        assert sha256((CAT / name).read_bytes()).hexdigest() == digest
    assert sha256((CAT / "summary.json").read_bytes()).hexdigest() == (
        "524b97a62174a671df5cf3de6c9962b01f1a9713d582ef54e486954518a049a3"
    )
    images = json.loads((CAT / "canonical-images.json").read_text())
    fibers = json.loads((CAT / "link-fibers.json").read_text())
    partials = json.loads((CAT / "partial-catalog.json").read_text())
    profiles = json.loads((CAT / "profiles.json").read_text())
    classes = json.loads(CLASSES.read_text())
    geometry = json.loads((ALL / "geometry.json").read_text())
    masks = json.loads((ALL / "profiles.json").read_text())["choice_masks"]
    expected_profiles = [
        family(
            [[a, b, cs[0]] for a, b, cs in geometry["forced"]]
            + [[a, b, cs[(mask >> i) & 1]] for i, (a, b, cs) in enumerate(geometry["choices"])]
        )
        for mask in masks
    ]
    counts = recount(images, fibers, partials, profiles, classes, expected_profiles)
    controls = []
    for damage in ("missing_image", "duplicate_block", "bool_block_id", "wrong_map", "profile"):
        im, fi, pa, pr = copy.deepcopy((images, fibers, partials, profiles))
        if damage == "missing_image":
            im["C5"].pop()
        elif damage == "duplicate_block":
            pa[0]["global_block_ids"][1] = pa[0]["global_block_ids"][0]
        elif damage == "bool_block_id":
            pa[0]["global_block_ids"][0] = False
        elif damage == "wrong_map":
            fi[0]["canonical_to_actual"][0] = fi[0]["canonical_to_actual"][1]
        else:
            pr[0]["excess_triples"].pop()
        try:
            recount(im, fi, pa, pr, classes, expected_profiles)
        except AssertionError:
            controls.append(damage)
        else:
            raise AssertionError("Damaged input accepted: " + damage)
    audit = {
        "passed": True,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "catalog_pins": pins,
        "inputs_sha256": {
            str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
            for p in (CLASSES, ALL / "geometry.json", ALL / "profiles.json")
        },
        "canonical_image_counts": counts,
        "partial_families": 5536,
        "excess_graphs": 38,
        "profiles": 1300,
        "profile_partial_pairs": 195296,
        "triple_rows_recounted": 5536 * 105,
        "covered_triples_per_partial": 185,
        "damaged_controls_rejected": controls,
        "optimizer_calls": 0,
        "producer_imports": 0,
        "scope": "All isomorphism images of four specific saved local witnesses only",
    }
    (HERE / "catalog-audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "image_counts": counts,
                "partials": 5536,
                "audit_sha256": sha256((HERE / "catalog-audit.json").read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
