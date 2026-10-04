# Document:   Bounded Affine Extension Enumeration Gate and Runner
# Version:    v1.0.0
# Author:     Celaya Solutions
# Contact:    hello@celayasolutions.com
# Date:       2026-10-03
# SHA256:     a59a8da7213b82deffcc32b2a67f013ba2604a36ef9924cb62c59deb635beb5f
# Chain:      n/a
# Tx:         [not anchored]
# License:    All Rights Reserved / Celaya Solutions

"""Compile, independently check, then run a bounded restricted capacity count."""

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-extension-capacity-20261003"
SEED = 2026103981


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry():
    spec = importlib.util.spec_from_file_location("independent_geometry", HERE / "check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lines, families = module.construct()
    module.validate_geometry(families[(1, 2)], lines)
    return families[(1, 2)], lines


def gf16_mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & 16:
            a ^= 19
    return result


def check_symmetry(circles, lines):
    circle_lookup = {c: i for i, c in enumerate(circles)}
    line_set = set(lines)
    maps = []
    for scale in range(1, 16):
        for shift in range(16):
            permutation = [gf16_mul(scale, x) ^ shift for x in range(16)]
            assert sorted(permutation) == list(range(16))
            mapped_lines = {tuple(sorted(permutation[x - 1] + 1 for x in line)) for line in lines}
            mapped_circles = [
                tuple(sorted(permutation[x - 1] + 1 for x in circle)) for circle in circles
            ]
            assert mapped_lines == line_set
            assert set(mapped_circles) == set(circles)
            maps.append(
                {
                    "scale": scale,
                    "shift": shift,
                    "points_one_based": [x + 1 for x in permutation],
                    "circles_zero_based": [circle_lookup[c] for c in mapped_circles],
                }
            )
    assert len({tuple(m["points_one_based"]) for m in maps}) == 240
    assert {m["circles_zero_based"][0] for m in maps} == set(range(48))
    witnesses = []
    for circle in range(48):
        witness = next(m for m in maps if m["circles_zero_based"][circle] == 0)
        witnesses.append({"deleted_circle_zero_based": circle, **witness})
    path = RAW / "affine-transitivity.json"
    path.write_text(
        json.dumps(
            {"fixed_circle": list(circles[0]), "maps": maps, "to_fixed_witnesses": witnesses},
            indent=2,
        )
        + "\n"
    )
    return {
        "automorphisms": 240,
        "circle_orbit_size": 48,
        "fixed_circle_zero_based": 0,
        "fixed_circle": list(circles[0]),
        "evidence_sha256": digest(path),
    }


def incidence(circles, lines):
    result = []
    for line in lines:
        row = []
        for point in range(1, 17):
            if point in line:
                continue
            extension = set(line) | {point}
            mask = 0
            for i, circle in enumerate(circles):
                hit = sum(set(t) <= extension for t in itertools.combinations(circle, 3))
                assert hit in (0, 1)
                if hit:
                    mask |= 1 << i
            assert mask.bit_count() == 6
            row.append(mask)
        result.append(row)
    return result


def oracle(deleted, extra, circles, lines):
    base = 0
    residual = []
    chosen = [set(circles[i]) for i in range(48) if deleted >> i & 1]
    for line in lines:
        weights = []
        for point in range(1, 17):
            if point not in line:
                extension = set(line) | {point}
                weights.append(sum(len(c & extension) == 3 for c in chosen))
        best = max(weights)
        base += best
        weights.remove(best)
        residual.extend(weights)
    return base + sum(sorted(residual, reverse=True)[:extra])


def execute(command, timeout=30, input_text=None):
    return subprocess.run(
        command,
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=True,
    )


def preflight(circles, lines):
    RAW.mkdir(parents=True, exist_ok=True)
    masks = incidence(circles, lines)
    model = RAW / "incidence.txt"
    text = "\n".join(" ".join(map(str, row)) for row in masks) + "\n"
    model.write_text(text)
    symmetry = check_symmetry(circles, lines)
    source = HERE / "capacity.cpp"
    release, sanitized = RAW / "capacity", RAW / "capacity-sanitized"
    base = ["clang++", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pedantic"]
    for binary, options in [
        (release, ["-O3"]),
        (sanitized, ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]),
    ]:
        result = execute(base + options + [str(source), "-o", str(binary)])
        assert not result.stderr
    randomizer = random.Random(SEED)
    samples = []
    for _ in range(1000):
        selected = randomizer.sample(range(48), randomizer.randrange(49))
        samples.append((sum(1 << i for i in selected), randomizer.randrange(221)))
    samples[:4] = [(0, 0), (0, 220), ((1 << 48) - 1, 0), ((1 << 48) - 1, 220)]
    expected = [oracle(d, e, circles, lines) for d, e in samples]
    sample_text = "".join(f"{d} {e}\n" for d, e in samples)
    (RAW / "samples.txt").write_text(sample_text)
    (RAW / "sample-oracle.json").write_text(json.dumps(expected) + "\n")
    for binary in (release, sanitized):
        result = execute([str(binary), str(model), "samples"], input_text=sample_text)
        assert not result.stderr
        assert list(map(int, result.stdout.split())) == expected
    damaged = [
        "",
        " ".join(text.split()[:-1]),
        text + "1\n",
        text.replace(text.split()[0], "0", 1),
        text.replace(text.split()[0], str(1 << 48), 1),
        text.replace(text.split()[0], "bad", 1),
        text.replace(text.split()[0], "-1", 1),
    ]
    for i, damaged_text in enumerate(damaged):
        path = RAW / f"damaged-{i}.txt"
        path.write_text(damaged_text)
        for binary in (release, sanitized):
            result = subprocess.run(
                [str(binary), str(path), "samples"],
                text=True,
                input="0 0\n",
                capture_output=True,
                timeout=10,
            )
            assert result.returncode == 2
    bad_samples = ["0 -1\n", "0 221\n", f"{1 << 48} 0\n", "0\n", "bad\n"]
    for query in bad_samples:
        for binary in (release, sanitized):
            result = subprocess.run(
                [str(binary), str(model), "samples"],
                text=True,
                input=query,
                capture_output=True,
                timeout=10,
            )
            assert result.returncode == 2
    started = time.monotonic()
    timing = json.loads(
        execute([str(release), str(model), "enumerate", "6", "2", "0", "1000"]).stdout
    )
    seconds = time.monotonic() - started
    histogram = {}
    for chosen in itertools.islice(itertools.combinations(range(1, 48), 5), 1000):
        deleted = 1 | sum(1 << i for i in chosen)
        value = oracle(deleted, 2, circles, lines)
        histogram[str(value)] = histogram.get(str(value), 0) + 1
    assert timing["deletion_sets"] == 1000 and timing["histogram"] == histogram
    report = {
        "passed": True,
        "utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "source_sha256": digest(source),
        "runner_sha256": digest(Path(__file__)),
        "geometry_source_sha256": digest(HERE / "check.py"),
        "model_sha256": digest(model),
        "release_sha256": digest(release),
        "sanitized_sha256": digest(sanitized),
        "symmetry": symmetry,
        "random_oracle_cases_per_binary": 1000,
        "damaged_models_per_binary": len(damaged),
        "damaged_queries_per_binary": len(bad_samples),
        "enumeration_prefix_oracle_cases": 1000,
        "prefix_seconds": seconds,
        "compiler": execute(["clang++", "--version"]).stdout.strip(),
        "source_revision": execute(["git", "rev-parse", "HEAD"]).stdout.strip(),
        "solver_calls": 0,
    }
    (HERE / "preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def run(removed, seconds):
    gate = json.loads((HERE / "preflight.json").read_text())
    assert gate["passed"] and gate["source_sha256"] == digest(HERE / "capacity.cpp")
    assert gate["runner_sha256"] == digest(Path(__file__))
    assert gate["geometry_source_sha256"] == digest(HERE / "check.py")
    assert gate["model_sha256"] == digest(RAW / "incidence.txt")
    assert gate["release_sha256"] == digest(RAW / "capacity")
    path = RAW / f"delete-{removed}.json"
    assert not path.exists(), "preserve previous enumeration"
    command = [
        str(RAW / "capacity"),
        str(RAW / "incidence.txt"),
        "enumerate",
        str(removed),
        str(removed - 4),
        "0",
        "0",
    ]
    started = time.monotonic()
    result = execute(command, timeout=seconds)
    elapsed = time.monotonic() - started
    assert not result.stderr
    path.write_text(result.stdout)
    data = json.loads(result.stdout)
    expected = math.comb(47, removed - 1)
    assert data["deletion_sets"] == expected == sum(data["histogram"].values())
    assert data["removed"] == removed and data["extra"] == removed - 4
    assert data["fixed_circle_zero_based"] == 0 and data["limit"] == 0
    assert data["survivors"] == sum(
        v for k, v in data["histogram"].items() if int(k) >= 10 * removed
    )
    report = {
        "passed": True,
        "utc": datetime.now(timezone.utc).isoformat(),
        "extensions": removed + 16,
        "removed_circles": removed,
        "required_capacity": 10 * removed,
        "maximum_capacity": max(map(int, data["histogram"])),
        "histogram": data["histogram"],
        "survivors": data["survivors"],
        "deletion_sets": expected,
        "seconds": elapsed,
        "seconds_budget": seconds,
        "preflight_sha256": digest(HERE / "preflight.json"),
        "raw_sha256": digest(path),
        "solver_calls": 0,
        "scope": "Original48-circle family with exactly64 total blocks and one or more "
        "extensions of each affine line; capacity upper bound only.",
        "global_lower_bound_claim": False,
    }
    (HERE / f"delete-{removed}-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--removed", type=int, choices=(6, 7, 8))
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    assert bool(args.preflight) != bool(args.removed)
    assert 0 < args.seconds <= 180
    if args.preflight:
        circles, lines = geometry()
        print(json.dumps(preflight(circles, lines)))
    else:
        print(json.dumps(run(args.removed, args.seconds)))


if __name__ == "__main__":
    main()
