# Document:    Valid cover trade walk
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Explore one-block trades that preserve a verified 65-block cover."""

import argparse
import hashlib
import json
import math
import random
import subprocess
import time
from itertools import combinations
from pathlib import Path

from covering64.core import Universe, read_blocks, verify_cover, write_blocks


def walk(start, seconds, seed, output):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Budget must be finite and positive")
    universe = Universe.build()
    witness = read_blocks(start)
    check = verify_cover(witness)
    if len(witness) != 65 or not check["valid"]:
        raise ValueError("Start must be a valid, distinct 65-block cover")
    lookup = {block: i for i, block in enumerate(universe.blocks)}
    ids = [lookup[block] for block in witness]
    selected = set(ids)
    counts = [0] * len(universe.triples)
    for block in ids:
        for triple in universe.coverage[block]:
            counts[triple] += 1
    masks = [sum(1 << (p - 1) for p in triple) for triple in universe.triples]
    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    steps = 0
    best = 11
    visited = set()
    saved = []
    while time.monotonic() - started < seconds:
        key = tuple(sorted(ids))
        visited.add(key)
        movable = []
        for slot, block in enumerate(ids):
            private = [t for t in universe.coverage[block] if counts[t] == 1]
            if len(private) < best:
                best = len(private)
                candidate = [universe.blocks[b] for i, b in enumerate(ids) if i != slot]
                report = verify_cover(candidate)
                if len(report["uncovered"]) != best:
                    raise RuntimeError("Incremental coverage disagrees with package verifier")
                path = output / f"near64-deficit-{best}.txt"
                write_blocks(path, candidate)
                saved.append(str(path))
                print(json.dumps({"step": steps, "best_deficit": best,
                                  "distinct65": len(visited), "candidate": str(path)}),
                      flush=True)
                if best == 0:
                    subprocess.run(["uv", "run", "python", "scripts/check_cover.py",
                                    str(path), "--expected-blocks", "64"], check=True)
                    break
            required = 0
            for triple in private:
                required |= masks[triple]
            if required.bit_count() < 5:
                fixed = [p for p in range(1, 17) if required & (1 << (p - 1))]
                free = [p for p in range(1, 17) if not required & (1 << (p - 1))]
                choices = [lookup[tuple(sorted(fixed + list(extra)))]
                           for extra in combinations(free, 5 - len(fixed))]
                choices = [b for b in choices if b not in selected]
                if choices:
                    movable.append((slot, choices))
        if best == 0 or not movable:
            break
        slot, choices = rng.choice(movable)
        old, new = ids[slot], rng.choice(choices)
        for triple in universe.coverage[old]:
            counts[triple] -= 1
        for triple in universe.coverage[new]:
            counts[triple] += 1
        if min(counts) < 1:
            raise RuntimeError("Trade damaged a previously complete cover")
        selected.remove(old)
        selected.add(new)
        ids[slot] = new
        steps += 1
    result = {"scope": "random one-block trades preserving 65-block validity",
              "seed": seed, "seconds_budget": seconds,
              "elapsed_seconds": time.monotonic() - started, "steps": steps,
              "distinct65": len(visited), "best_deficit": best, "saved": saved,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "start_sha256": hashlib.sha256(Path(start).read_bytes()).hexdigest(),
              "source_revision": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], text=True).strip()}
    final = [universe.blocks[b] for b in ids]
    result["final_verification"] = verify_cover(final)
    if not result["final_verification"]["valid"]:
        raise RuntimeError("Final 65-block cover failed verification")
    final_path = output / "last65.txt"
    write_blocks(final_path, final)
    checked = subprocess.run(["uv", "run", "python", "scripts/check_cover.py",
                              str(final_path), "--expected-blocks", "65"],
                             capture_output=True, text=True, check=True)
    result["final_independent_verification"] = json.loads(checked.stdout)
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=Path)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    walk(args.start, args.seconds, args.seed, args.output)
