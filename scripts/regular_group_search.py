# Document:    Regular group covering search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate four-block-orbit unions for explicitly listed regular groups.

These are restricted searches only. No unrestricted lower bound follows.
"""

import hashlib
import json
import subprocess
from itertools import product
from pathlib import Path

from covering64.core import Universe, verify_cover, write_blocks
from scripts.orbit_search import block_orbits


def abelian(moduli):
    points = list(product(*(range(m) for m in moduli)))
    ids = {p: i + 1 for i, p in enumerate(points)}
    generators = []
    for dimension in range(len(moduli)):
        generators.append(tuple(ids[tuple((v + (j == dimension)) % moduli[j]
                                          for j, v in enumerate(p))] for p in points))
    return generators


def extension(moduli, alpha, square):
    """Left-regular action of H extended by b, with b h b^-1=alpha(h)."""
    base = list(product(*(range(m) for m in moduli)))
    points = [(h, e) for h in base for e in range(2)]
    ids = {p: i + 1 for i, p in enumerate(points)}
    generators = []
    for dimension in range(len(moduli)):
        generators.append(tuple(ids[(tuple((v + (j == dimension)) % moduli[j]
                                           for j, v in enumerate(h)), e)]
                                for h, e in points))
    generators.append(tuple(ids[(tuple((v + e * t) % m
                                       for v, t, m in zip(alpha(h), square, moduli)), 1-e)]
                            for h, e in points))
    return generators


def generated_group(generators):
    identity = tuple(range(1, 17))
    seen, queue = {identity}, [identity]
    while queue:
        p = queue.pop()
        for g in generators:
            q = tuple(g[x-1] for x in p)
            if q not in seen:
                seen.add(q)
                queue.append(q)
                if len(seen) > 16:
                    raise ValueError("Generated action is larger than the intended group")
    if len(seen) != 16 or {g[0] for g in seen} != set(range(1, 17)):
        raise ValueError("Action is not a regular group of order 16")
    return seen


def families():
    for moduli in [(16,), (8, 2), (4, 4), (4, 2, 2), (2, 2, 2, 2)]:
        yield "abelian-" + "x".join(map(str, moduli)), abelian(moduli)
    for alpha, square in [(7, 0), (7, 4), (3, 0), (5, 0)]:
        yield f"cyclic8-extension-alpha{alpha}-square{square}", extension(
            (8,), lambda h, a=alpha: ((a*h[0]) % 8,), (square,))
    for square in [(0, 0), (2, 0), (0, 1)]:
        yield f"c4xc2-inversion-square{square[0]}{square[1]}", extension(
            (4, 2), lambda h: ((-h[0]) % 4, h[1]), square)
    for square in [(0, 0), (2, 0), (0, 1), (2, 1)]:
        yield f"c4xc2-shear-square{square[0]}{square[1]}", extension(
            (4, 2), lambda h: (h[0], (h[1]+h[0]) % 2), square)
    yield "c2cubed-swap", extension((2, 2, 2), lambda h: (h[1], h[0], h[2]),
                                    (0, 0, 0))


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    compiler = subprocess.check_output(["clang++", "--version"], text=True).splitlines()[0]
    source = Path("experiments/2026-10-03/orbit-enumerate.cpp")
    executable = output.resolve() / "enumerate"
    subprocess.run(["clang++", "-std=c++17", "-O3", str(source), "-o", str(executable)],
                   check=True)
    universe = Universe.build()
    triples = Universe.build(v=16, k=3, t=3)
    records = []
    for name, generators in families():
        group = generated_group(generators)
        orbits = block_orbits(universe, generators)
        triple_orbits = block_orbits(triples, generators)
        if len(orbits) != 273 or len(triple_orbits) != 35:
            raise RuntimeError("Unexpected orbit partition")
        if any(len(o) != 16 for o in (*orbits, *triple_orbits)):
            raise RuntimeError("Odd subset orbits should have no nontrivial stabilizers")
        orbit_of = {t: i for i, orbit in enumerate(triple_orbits) for t in orbit}
        masks = [sum(1 << i for i in {orbit_of[t] for b in orbit
                                     for t in universe.coverage[b]}) for orbit in orbits]
        mask_path = output / f"{name}-masks.txt"
        mask_path.write_text("\n".join(map(str, masks)) + "\n")
        process = subprocess.run([str(executable), str(mask_path)], capture_output=True,
                                 text=True, check=False)
        if process.returncode not in (0, 1):
            raise RuntimeError(f"Enumerator rejected generated input: {name}")
        (output / f"{name}.log").write_text(process.stdout + process.stderr)
        last = process.stdout.splitlines()[-1]
        best_line = [line for line in process.stdout.splitlines() if line.startswith("best ")][-1]
        best_ids = list(map(int, best_line.split()[3:]))
        blocks = [universe.blocks[b] for i in best_ids for b in orbits[i]]
        witness = output / f"{name}-best64.txt"
        write_blocks(witness, blocks)
        report = verify_cover(blocks)
        checker = subprocess.run(["uv", "run", "python", "scripts/check_cover.py",
                                  str(witness), "--expected-blocks", "64"],
                                 text=True, capture_output=True, check=False)
        independent = json.loads(checker.stdout)
        if report["valid"] != independent["valid"]:
            raise RuntimeError("Independent coverage check disagreed")
        record = {"name": name, "generators": generators, "group_size": len(group),
                  "result": last, "verification": report, "independent": independent,
                  "mask_sha256": hashlib.sha256(mask_path.read_bytes()).hexdigest()}
        records.append(record)
        print(json.dumps({"name": name, "result": last}), flush=True)
        if report["valid"]:
            break
    result = {"scope": "only unions of four orbits for these explicit regular actions",
              "records": records, "compiler": compiler,
              "source_revision": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], text=True).strip(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "enumerator_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    run(Path("experiments/scratch/regular-groups"))
