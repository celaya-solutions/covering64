# Document:    Affine Extension Point Variants for Four Chosen Link Recipes
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      441cc75b277f623e86994e67d3601a22a8749aabb5610482abc17192a6896bec
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite constructions and complete excess-automorphism orbits of this catalog."""

import json
import subprocess
import time
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, permutations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CLASSES = ROOT / "experiments/2026-10-04/clebsch-point-link-construction/classes.json"
IMAGES = ROOT / "experiments/2026-10-04/circulant-chosen-link-catalog/canonical-images.json"
QUADS = list(combinations(range(1, 16), 4))
QUAD_ID = {b: i for i, b in enumerate(QUADS)}


def family(blocks):
    return tuple(sorted(tuple(sorted(b)) for b in blocks))


def transport(blocks, mapping):
    return family([[mapping[v] for v in block] for block in blocks])


def isomorphism(excess, target):
    centers = sorted(v for v in range(1, 16) if sum(v in e for e in excess) == 4)
    assert len(centers) == 5
    core = {e for e in excess if all(v in centers for v in e)}
    for p in permutations(range(1, 6)):
        mapping = dict(zip(centers, p))
        if {tuple(sorted(mapping[v] for v in e)) for e in core} != {
            e for e in target if max(e) <= 5
        }:
            continue
        for v in centers:
            source = sorted(
                b if a == v else a
                for a, b in excess
                if v in (a, b) and (b if a == v else a) not in centers
            )
            t = mapping[v]
            destination = sorted(
                b if a == t else a for a, b in target if t in (a, b) and max(a, b) > 5
            )
            mapping.update(zip(source, destination))
        if len(mapping) == 15 and {tuple(sorted(mapping[v] for v in e)) for e in excess} == target:
            return mapping
    raise AssertionError("An extension setting left its stated excess-graph class")


def main():
    started = time.monotonic()
    assert not (HERE / "summary.json").exists()
    classes = json.loads(CLASSES.read_text())
    images = json.loads(IMAGES.read_text())
    assert sha256(CLASSES.read_bytes()).hexdigest() == (
        "6916b285c1c53693b4f2f53bd0194afd6f2c936e1a10da3a236c5311ab86a2cc"
    )
    assert sha256(IMAGES.read_bytes()).hexdigest() == (
        "18a7eff11931df2dc25c17e2beb3ccb588c6fe29aaf753ece024c20e59607f8b"
    )
    settings, representatives, counts = [], {}, {}
    for kind, model in classes.items():
        target = {tuple(e) for e in model["canonical_excess_edges"]}
        automorphisms = [
            dict(zip(range(1, 16), row["canonical_permutation"])) for row in images[kind]
        ]
        old_families = {family(row["canonical_blocks"]) for row in images[kind]}
        old_key = min(tuple(QUAD_ID[b] for b in f) for f in old_families)
        rays = model["rays_by_zero_based_index"]
        domains = [rays[i] for i in model["function_images_zero_based"]]
        orbit_members = defaultdict(list)
        kind_settings = []
        duplicate_centers = 0
        for extension_points in product(*domains):
            if time.monotonic() - started > 60:
                raise TimeoutError("Incomplete finite enumeration; no completion receipt")
            if len(set(extension_points)) != 5:
                duplicate_centers += 1
                continue
            blocks = family(
                model["retained_ag_blocks"] + [ray + [v] for ray, v in zip(rays, extension_points)]
            )
            assert len(blocks) == len(set(blocks)) == 20
            pairs = Counter(e for b in blocks for e in combinations(b, 2))
            triples = Counter(t for b in blocks for t in combinations(b, 3))
            assert len(pairs) == 105 and set(pairs.values()) == {1, 2}
            assert len(triples) == 80 and set(triples.values()) == {1}
            excess = {e for e, n in pairs.items() if n == 2}
            assert len(excess) == 15
            mapping = isomorphism(excess, target)
            mapped = transport(blocks, mapping)
            options = [tuple(QUAD_ID[b] for b in transport(mapped, a)) for a in automorphisms]
            key = min(options)
            best = options.index(key)
            index = len(settings)
            setting = {
                "index": index,
                "class": kind,
                "extension_points": extension_points,
                "ag_to_canonical": [mapping[v] for v in range(1, 16)],
                "canonical_to_representative": images[kind][best]["canonical_permutation"],
                "representative_quad_ids": key,
                "old_witness_orbit": key == old_key,
            }
            assert (mapped in old_families) == (key == old_key)
            settings.append(setting)
            kind_settings.append(setting)
            orbit_members[key].append(index)
        representatives[kind] = [
            {
                "quad_ids": key,
                "blocks": [QUADS[i] for i in key],
                "setting_indices": indices,
                "old_witness_orbit": key == old_key,
            }
            for key, indices in sorted(orbit_members.items())
        ]
        counts[kind] = {
            "raw_settings": 243,
            "duplicate_center_settings": duplicate_centers,
            "valid_settings": len(kind_settings),
            "settings_beyond_old_orbit": sum(not s["old_witness_orbit"] for s in kind_settings),
            "orbits": len(orbit_members),
            "new_orbits": sum(key != old_key for key in orbit_members),
            "automorphism_count": len(automorphisms),
        }
    for name, value in (("settings.json", settings), ("representatives.json", representatives)):
        (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    summary = {
        "scope": "All extension-point choices for four fixed ray-target recipes only",
        "complete_for_stated_settings": True,
        "all_affine_constructions_claimed": False,
        "counts": counts,
        "total_valid_settings": len(settings),
        "total_orbits": sum(row["orbits"] for row in counts.values()),
        "total_new_orbits": sum(row["new_orbits"] for row in counts.values()),
        "optimizer_calls": 0,
        "cover_found": False,
        "finite_processing_budget_seconds": 60,
        "elapsed_seconds": time.monotonic() - started,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_hashes": {
            str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in (CLASSES, IMAGES)
        },
        "output_hashes": {
            name: sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("settings.json", "representatives.json")
        },
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
