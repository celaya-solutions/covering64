# Document:    Independent Circulant Offset Choice Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6ed41ede51e46e53106baa12c6e4149ca5a36fc938c6c57fedc5044ebc75663d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay the producer's 24 center-offset choices with the independent checker."""

import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("arithmetic_reference", HERE / "check.py")
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)
review = reference.read(HERE / "review.json")
reference.require(
    reference.sha(HERE / "review.json")
    == "d83b9a199c51088a3242e9d42c303aa86ee1b5a0b1cd47846577f4bb78e7e928",
    "frozen arithmetic review",
)
reference.require(reference.sha(HERE / "check.py") == review["checker_sha256"], "checker binding")
reference.require(not (HERE / "offset-review.json").exists(), "preserve offset receipt")
edges, adjacent = reference.graph(1, 3)
geometry = reference.read(reference.PRODUCER / "geometry.json")
reference.require(
    reference.sha(reference.PRODUCER / "geometry.json") == reference.PINS["geometry.json"],
    "geometry pin",
)
forbidden = {tuple(t) for t in geometry["forbidden_excess_paths"]}
differences = [2, 4, 5, 6, 7]
choices = [sorted(p - 1 for p in adjacent[1] & adjacent[d + 1]) for d in differences]
accepted, rejected = [], []
for offsets in itertools.product(*choices):
    profile = sorted(
        {
            tuple(sorted((1 + x, 1 + (x + d) % 16, 1 + (x + c) % 16)))
            for x in range(16)
            for d, c in zip(differences, offsets, strict=True)
        }
    )
    raw = list(map(list, profile))
    if set(profile) & forbidden:
        rejected.append({"center_offsets": list(offsets), "reason": "tight-cut internal excess"})
        try:
            reference.validate_profile(raw, edges, forbidden)
        except ValueError:
            pass
        else:
            raise AssertionError("forbidden excess accepted")
    else:
        reference.validate_profile(raw, edges, forbidden)
        accepted.append(list(offsets))
reference.exact(
    reference.read(reference.PRODUCER / "rejected-orbit-choices.json"),
    rejected,
    "every rejected choice and reason",
)
reference.exact(
    [p["center_offsets"] for p in reference.read(reference.PRODUCER / "profiles.json")],
    accepted,
    "every accepted offset choice",
)
reference.require(len(accepted) == 8 and len(rejected) == 16, "complete24 partition")
result = {
    "passed": True,
    "checker_sha256": reference.sha(Path(__file__)),
    "arithmetic_review_sha256": reference.sha(HERE / "review.json"),
    "choice_count": 24,
    "accepted_count": 8,
    "rejected_count": 16,
    "accepted_offsets": accepted,
    "rejected_choices": rejected,
    "optimizer_calls": 0,
}
(HERE / "offset-review.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"passed": True, "review_sha256": reference.sha(HERE / "offset-review.json")}))
