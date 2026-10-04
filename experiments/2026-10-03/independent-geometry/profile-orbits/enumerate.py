# Document:    Regular Tournament Clebsch Profile Orbit Enumeration
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      6bef3b7a182221828c2cd31628d952479381870bfa508b51d7df16f01e6fe884
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Record all 1,024 orientation profiles and their explicit 80-map orbits.

This is arithmetic enumeration of excess profiles, not a cover solver. Run from
any directory with Python 3.11 or later. The default output is certificate.json
alongside this program. An independent implementation should replay the record
before using the orbit reduction in a nonexistence certificate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import platform
import random
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
GENERATOR = ROOT / "scripts/independent_clebsch_profiles.py"
DATE = "2026-10-03"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_profile(profile: tuple[tuple[int, ...], ...]) -> bytes:
    return "".join(" ".join(map(str, triple)) + "\n" for triple in profile).encode()


class ExplicitChoices:
    """Feed exact orientation bits to the unchanged seeded generator."""

    def __init__(self, bits: int):
        self.bits = bits
        self.index = 0

    def shuffle(self, sequence: list[int]) -> None:
        if sequence != list(range(5)):
            raise AssertionError("unexpected tournament choice")

    def getrandbits(self, count: int) -> int:
        if count != 1 or self.index >= 10:
            raise AssertionError("unexpected orientation choice")
        answer = (self.bits >> self.index) & 1
        self.index += 1
        return answer


def build_record() -> dict:
    spec = importlib.util.spec_from_file_location("profile_generator", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with patch.object(module.random, "Random", ExplicitChoices):
        profiles = {
            tuple(module.make_profile(bits)): bits for bits in range(1024)
        }
    if len(profiles) != 1024:
        raise AssertionError("orientation choices must give distinct profiles")

    words = [word for word in range(32) if word.bit_count() % 2 == 0]
    labels = {word: index + 1 for index, word in enumerate(words)}
    triples = list(itertools.combinations(range(1, 17), 3))
    triple_ids = {triple: index for index, triple in enumerate(triples)}
    pairs = list(itertools.combinations(range(1, 17), 2))
    edges = [pair for pair in pairs if (words[pair[0]-1] ^ words[pair[1]-1]).bit_count() == 4]
    edge_set = set(edges)
    for profile in profiles:
        pair_counts = Counter(
            pair for triple in profile for pair in itertools.combinations(triple, 2)
        )
        if any(pair_counts[pair] != (4 if pair in edge_set else 1) for pair in pairs):
            raise AssertionError("profile has incorrect pair codegrees")
        if any(
            sum(pair in edge_set for pair in itertools.combinations(triple, 2)) != 2
            for triple in profile
        ):
            raise AssertionError("profile contains a non-path triple")

    encoded = {
        tuple(triple_ids[triple] for triple in profile): bits
        for profile, bits in profiles.items()
    }
    all_profiles = set(encoded)
    actions = []
    triple_actions = []
    for shift in range(5):
        for translate in words:
            permutation = []
            for word in words:
                rotated = ((word << shift) | (word >> (5-shift))) & 31
                permutation.append(labels[rotated ^ translate])
            if set(permutation) != set(range(1, 17)):
                raise AssertionError("action is not a permutation")
            if {tuple(sorted(permutation[v-1] for v in edge)) for edge in edges} != edge_set:
                raise AssertionError("action does not preserve the Clebsch graph")
            actions.append({
                "shift": shift, "translation_word": translate, "permutation": permutation
            })
            triple_actions.append(tuple(
                triple_ids[tuple(sorted(permutation[point-1] for point in triple))]
                for triple in triples
            ))
    if len({tuple(action["permutation"]) for action in actions}) != 80:
        raise AssertionError("expected eighty distinct relabelings")

    unseen = set(encoded)
    orbit_records = []
    orbit_of = {}
    witnesses = {}
    while unseen:
        representative = min(unseen)
        orbit = {
            tuple(sorted(action[index] for index in representative))
            for action in triple_actions
        }
        if not orbit <= all_profiles:
            raise AssertionError("profile family is not closed under the action")
        orbit_index = len(orbit_records)
        for profile in orbit:
            if profile in orbit_of:
                raise AssertionError("computed orbits overlap")
            orbit_of[profile] = orbit_index
            witnesses[profile] = next(
                index for index, action in enumerate(triple_actions)
                if tuple(sorted(action[triple] for triple in profile)) == representative
            )
        orbit_records.append({
            "index": orbit_index,
            "representative_bits": encoded[representative],
            "size": len(orbit),
            "member_bits": sorted(encoded[profile] for profile in orbit),
        })
        unseen.difference_update(orbit)

    # Produce convenient representatives through the public seeded API. Its
    # shuffled directions are normalized by the corresponding bit permutation.
    first_seeds = {}
    for seed in range(10000):
        profile = module.make_profile(seed)
        order = list(range(5))
        random.Random(seed).shuffle(order)
        inverse = {old: new for new, old in enumerate(order)}
        point_map = [
            labels[sum(1 << inverse[bit] for bit in range(5) if word & (1 << bit))]
            for word in words
        ]
        normalized = tuple(sorted(
            triple_ids[tuple(sorted(point_map[point-1] for point in triple))]
            for triple in profile
        ))
        first_seeds.setdefault(orbit_of[normalized], (seed, point_map))
        if len(first_seeds) == len(orbit_records):
            break
    if len(first_seeds) != len(orbit_records):
        raise AssertionError("seed scan did not reach every orbit")
    for orbit in orbit_records:
        seed, normalizing_map = first_seeds[orbit["index"]]
        orbit["seed"] = seed
        orbit["seed_normalizing_permutation"] = normalizing_map

    profile_records = []
    for profile, bits in sorted(profiles.items(), key=lambda item: item[1]):
        code = tuple(triple_ids[triple] for triple in profile)
        profile_records.append({
            "bits": bits,
            "sha256": digest(canonical_profile(profile)),
            "orbit": orbit_of[code],
            "action_to_representative": witnesses[code],
        })
    histogram = Counter(orbit["size"] for orbit in orbit_records)
    if dict(histogram) != {80: 12, 16: 4}:
        raise AssertionError("unexpected orbit distribution")
    return {
        "format": "clebsch-regular-tournament-orbits-v1",
        "scope": (
            "All 1024 orientations of one fixed regular tournament; relabelings cover the "
            "24576-profile regular-tournament recipe, "
            "not all Clebsch excess profiles or all covers."
        ),
        "source_base_revision": "c31aea40bb52dddd43532e91c3d62558fcf25cde",
        "generator_path": str(GENERATOR.relative_to(ROOT)),
        "generator_file_sha256": digest(GENERATOR.read_bytes()),
        "enumerator_file_sha256": digest(Path(__file__).read_bytes()),
        "python_version": platform.python_version(),
        "profile_hash_format": (
            "Sorted triples; decimal labels separated by one ASCII space; "
            "one triple per line; final newline; UTF-8."
        ),
        "fixed_tournament_order": list(range(5)),
        "vertex_words": words,
        "clebsch_edges": edges,
        "actions": actions,
        "profiles": profile_records,
        "orbits": orbit_records,
        "counts": {
            "profiles": 1024, "actions": 80, "orbits": 16,
            "orbit_size_histogram": dict(sorted(histogram.items())),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("certificate.json"))
    args = parser.parse_args()
    body = build_record()
    canonical = (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode()
    record = {
        "Document": "Regular Tournament Clebsch Profile Orbit Certificate",
        "Version": "v1.0.0",
        "Author": "Celaya Solutions",
        "Contact": "hello@celayasolutions.com",
        "Date": DATE,
        "SHA256": digest(canonical),
        "Chain": "n/a",
        "Tx": "[not anchored]",
        "License": "All Rights Reserved / Celaya Solutions",
        "body": body,
    }
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({
        "output": str(args.output), "body_sha256": record["SHA256"], **body["counts"]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
