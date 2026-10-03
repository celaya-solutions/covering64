# Document:    Independent Heavy Profile Search Tests
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      336ccd6e0d9cfd60e9ffb1fe0effd37a8aa9872efe230b816c5c33918698fc94
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independent checks of the forbidden heavy-profile detector."""

import itertools
import json
import random
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from covering64.core import read_blocks, write_blocks

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def binary(tmp_path_factory):
    compiler = shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        pytest.skip("C++ compiler unavailable")
    output = tmp_path_factory.mktemp("heavy-profile") / "search"
    subprocess.run(
        [compiler, "-O2", "-std=c++20", str(ROOT / "scripts/heavy_profile_heuristic.cpp"),
         "-o", str(output)], check=True,
    )
    return output


def independent_profile(blocks):
    counts = Counter(t for block in blocks for t in itertools.combinations(block, 3))
    heavy = [t for t, count in counts.items() if count >= 6]
    return any(
        len(set().union(*map(set, choice))) == 15
        and sum(counts[t] >= 7 for t in choice) >= 2
        for choice in itertools.combinations(heavy, 5)
    )


def test_profile_against_independent_oracle(binary, tmp_path):
    blocks = read_blocks(ROOT / "experiments/2026-10-03/heuristic-tabu-2026100301-deficit-3.txt")
    rng = random.Random(2026102401)
    universe = list(itertools.combinations(range(1, 17), 5))
    states = [blocks]
    for amount in (1, 2, 3, 5, 10, 30):
        for _ in range(4):
            changed = set(blocks)
            for _ in range(amount):
                changed.remove(rng.choice(sorted(changed)))
                while len(changed) < 64:
                    changed.add(rng.choice(universe))
            states.append(sorted(changed))
    answers = []
    for index, state in enumerate(states):
        path = tmp_path / f"state-{index}.txt"
        write_blocks(path, state)
        result = subprocess.run([str(binary), "--profile", str(path)],
                                capture_output=True, text=True, check=True)
        actual = json.loads(result.stdout)["forbidden"]
        expected = independent_profile(state)
        assert actual == expected
        answers.append(actual)
    assert any(answers) and not all(answers)


@pytest.mark.parametrize("damage", ["duplicate", "label", "token", "size", "count"])
def test_rejects_damaged_candidates(binary, tmp_path, damage):
    source = ROOT / "experiments/2026-10-03/heuristic-tabu-2026100301-deficit-3.txt"
    lines = source.read_text().splitlines()
    if damage == "duplicate":
        lines[-1] = lines[0]
    elif damage == "label":
        lines[0] = "0 2 3 4 5"
    elif damage == "token":
        lines[0] = "1 2 3 4 nope"
    elif damage == "size":
        lines[0] = "1 2 3 4"
    else:
        present = {tuple(map(int, line.split())) for line in lines}
        extra = next(b for b in itertools.combinations(range(1, 17), 5) if b not in present)
        lines.append(" ".join(map(str, extra)))
    path = tmp_path / "damaged.txt"
    path.write_text("\n".join(lines) + "\n")
    result = subprocess.run([str(binary), "--profile", str(path)], capture_output=True)
    assert result.returncode == 2
