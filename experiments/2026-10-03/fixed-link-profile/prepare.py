# Document:    Fixed Link Profile Pilot Seed Constructor
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d90f91245fb297e56a7a253bbc3465957b3eeeb6745c8f4e0c545fc6cbd38ddc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Build three full cyclic orbits as an initial state, never a move restriction."""

import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TRIPLES = set(it.combinations(range(1, 17), 3))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def covered(blocks):
    return {triple for block in blocks for triple in it.combinations(block, 3)}


def write_blocks(path, blocks):
    path.write_text("".join(" ".join(map(str, b)) + "\n" for b in sorted(blocks)))


def main():
    orbits = {}
    for block in it.combinations(range(15), 5):
        orbit = tuple(
            sorted({tuple(sorted((p + shift) % 15 + 2 for p in block)) for shift in range(15)})
        )
        if len(orbit) == 15:
            orbits[orbit[0]] = orbit
    cases = []
    for shape, high, seed in [
        (1, 2, 2026100351),
        (4, 2, 2026100352),
        (44, 3, 2026100353),
        (47, 3, 2026100354),
    ]:
        link_path = ROOT / f"experiments/2026-10-03/link-classification/shape-{shape}-class-0.txt"
        fixed = [tuple(map(int, line.split())) for line in link_path.read_text().splitlines()]
        require(len(fixed) == 19 and all(1 in b for b in fixed), "invalid fixed link")
        counts = Counter(p for b in fixed for p in b)
        require(counts == {1: 19, 2: 6, **{p: 5 for p in range(3, 17)}}, "wrong link degrees")
        require(all(t in covered(fixed) for t in TRIPLES if 1 in t), "link misses anchor triple")
        free, representatives = [], []
        for _ in range(3):
            options = [
                (len(TRIPLES - covered(fixed + free + list(orbit))), representative)
                for representative, orbit in orbits.items()
                if representative not in representatives
            ]
            _, representative = min(options)
            representatives.append(representative)
            free.extend(orbits[representative])
        require(len(free) == len(set(free)) == 45, "orbit overlap")
        require(
            Counter(p for b in free for p in b) == {p: 15 for p in range(2, 17)},
            "orbits do not have degree15",
        )
        adjustment = None
        if high != 2:
            choices = []
            for index, block in enumerate(free):
                if 2 in block and high not in block:
                    replacement = tuple(sorted((set(block) - {2}) | {high}))
                    if replacement not in free:
                        changed = free[:index] + [replacement] + free[index + 1 :]
                        choices.append(
                            (len(TRIPLES - covered(fixed + changed)), index, replacement)
                        )
            require(bool(choices), "no degree adjustment")
            _, index, replacement = min(choices)
            adjustment = {"removed": free[index], "added": replacement}
            free[index] = replacement
        blocks = sorted(fixed + free)
        require(len(blocks) == len(set(blocks)) == 64, "invalid total seed")
        degree = Counter(p for b in blocks for p in b)
        require(
            degree == {p: 19 if p == 1 else 21 if p == high else 20 for p in range(1, 17)},
            "wrong full degree profile",
        )
        name = f"shape-{shape}-high-{high}"
        path = OUT / f"{name}-seed.txt"
        write_blocks(path, blocks)
        cases.append(
            {
                "name": name,
                "shape": shape,
                "anchor": 1,
                "high_point": high,
                "seed": seed,
                "seconds": 300,
                "workers": 1,
                "seed_path": str(path.relative_to(ROOT)),
                "seed_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "link_path": str(link_path.relative_to(ROOT)),
                "link_sha256": hashlib.sha256(link_path.read_bytes()).hexdigest(),
                "orbit_representatives": representatives,
                "adjustment": adjustment,
                "initial_holes": len(TRIPLES - covered(blocks)),
                "degrees": dict(degree),
            }
        )
    (OUT / "seeds.json").write_text(
        json.dumps(
            {"cases": cases, "scope": "Cyclic structure is seed construction only."}, indent=2
        )
        + "\n"
    )
    print(json.dumps([{k: c[k] for k in ["name", "initial_holes", "seed_sha256"]} for c in cases]))


if __name__ == "__main__":
    main()
