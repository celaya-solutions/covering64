"""Problem construction and deterministic witness validation (1-based labels)."""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from math import comb
from pathlib import Path
from typing import Iterable

Block = tuple[int, ...]


def validate_parameters(v: int, k: int, t: int) -> None:
    if any(type(x) is not int for x in (v, k, t)) or not 1 <= t <= k <= v:
        raise ValueError("parameters must be integers with 1 <= t <= k <= v")


def normalize_blocks(blocks: Iterable[Iterable[int]], v: int, k: int) -> tuple[Block, ...]:
    validate_parameters(v, k, 1)
    normalized = []
    for number, block in enumerate(blocks, start=1):
        values = tuple(block)
        if any(type(x) is not int for x in values):
            raise ValueError(f"block {number}: labels must be integers")
        if len(values) != k or len(set(values)) != k:
            raise ValueError(f"block {number}: expected {k} distinct labels")
        if any(x < 1 or x > v for x in values):
            raise ValueError(f"block {number}: labels must be between 1 and {v}")
        normalized.append(tuple(sorted(values)))
    if len(set(normalized)) != len(normalized):
        raise ValueError("duplicate blocks are not allowed")
    return tuple(normalized)


def read_blocks(path: str | Path, v: int = 16, k: int = 5) -> tuple[Block, ...]:
    blocks = []
    for number, line in enumerate(Path(path).read_text().splitlines(), start=1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            blocks.append(tuple(int(value) for value in line.split()))
        except ValueError as exc:
            message = f"line {number}: expected whitespace-separated integer labels"
            raise ValueError(message) from exc
    return normalize_blocks(blocks, v, k)


def canonical_text(blocks: Iterable[Iterable[int]]) -> str:
    ordered = sorted(tuple(sorted(block)) for block in blocks)
    return "".join(" ".join(map(str, block)) + "\n" for block in ordered)


def write_blocks(path: str | Path, blocks: Iterable[Iterable[int]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical_text(blocks))


def schonheim_bound(v: int, k: int, t: int) -> int:
    validate_parameters(v, k, t)
    result = 1
    for offset in reversed(range(t)):
        result = ((v - offset) * result + k - offset - 1) // (k - offset)
    return result


@dataclass(frozen=True)
class Universe:
    v: int
    k: int
    t: int
    blocks: tuple[Block, ...]
    triples: tuple[Block, ...]
    coverage: tuple[tuple[int, ...], ...]
    masks: tuple[int, ...]
    containing: tuple[tuple[int, ...], ...]

    @classmethod
    def build(cls, v: int = 16, k: int = 5, t: int = 3) -> "Universe":
        validate_parameters(v, k, t)
        blocks = tuple(combinations(range(1, v + 1), k))
        triples = tuple(combinations(range(1, v + 1), t))
        triple_indices = {triple: index for index, triple in enumerate(triples)}
        coverage = tuple(tuple(triple_indices[c] for c in combinations(b, t)) for b in blocks)
        masks = tuple(sum(1 << index for index in indices) for indices in coverage)
        containing: list[list[int]] = [[] for _ in triples]
        for index, indices in enumerate(coverage):
            for triple in indices:
                containing[triple].append(index)
        return cls(
            v,
            k,
            t,
            blocks,
            triples,
            coverage,
            masks,
            tuple(tuple(indices) for indices in containing),
        )

    def summary(self) -> dict:
        return {
            "v": self.v,
            "k": self.k,
            "t": self.t,
            "candidate_blocks": len(self.blocks),
            "coverage_requirements": len(self.triples),
            "requirements_per_block": comb(self.k, self.t),
            "blocks_per_requirement": comb(self.v - self.t, self.k - self.t),
            "schonheim_lower_bound": schonheim_bound(self.v, self.k, self.t),
        }


def verify_cover(blocks: Iterable[Iterable[int]], v: int = 16, k: int = 5, t: int = 3) -> dict:
    validate_parameters(v, k, t)
    normalized = normalize_blocks(blocks, v, k)
    counts = Counter(triple for block in normalized for triple in combinations(block, t))
    triples = tuple(combinations(range(1, v + 1), t))
    uncovered = [triple for triple in triples if not counts[triple]]
    point_counts = Counter(point for block in normalized for point in block)
    pair_counts = Counter(pair for block in normalized for pair in combinations(block, 2))
    return {
        "v": v,
        "k": k,
        "t": t,
        "valid": not uncovered,
        "blocks": len(normalized),
        "triples": len(triples),
        "covered": len(triples) - len(uncovered),
        "uncovered": uncovered,
        "multiplicities": dict(sorted(Counter(counts[triple] for triple in triples).items())),
        "total_incidences": sum(counts.values()),
        "replication": {point: point_counts[point] for point in range(1, v + 1)},
        "pair_multiplicities": dict(
            sorted(Counter(pair_counts[pair] for pair in combinations(range(1, v + 1), 2)).items())
        ),
        "canonical_sha256": sha256(canonical_text(normalized).encode()).hexdigest(),
    }
