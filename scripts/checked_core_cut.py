# Document:    Checked Core Distance Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Obtain globally necessary core-overlap cuts only from a fresh independent check."""

import gzip
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from covering64.core import normalize_blocks


def core_ids_after_permutation(universe, core, permutation=None):
    core = normalize_blocks(core, 16, 5)
    if len(core) != 60:
        raise ValueError("a core must have60 distinct blocks")
    if permutation is None:
        permutation = {i: i for i in range(1, 17)}
    if (any(type(x) is not int for x in list(permutation) + list(permutation.values()))
            or set(permutation) != set(range(1, 17))
            or set(permutation.values()) != set(range(1, 17))):
        raise ValueError("core relabeling must be a bijection of1..16")
    ids = {block: i for i, block in enumerate(universe.blocks)}
    return sorted(ids[tuple(sorted(permutation[x] for x in block))] for block in core)


def checked_core_cuts(universe, certificate, permutation=None):
    """Check all retained-subset obstructions, then forbid excess core overlap.

    If every retention of60-r core blocks needs more than r+4 additions, any
    <=64 cover has core intersection at most59-r. A point permutation carries
    this necessary condition to the relabeled core without further assumptions.
    """
    if (universe.v, universe.k, universe.t) != (16, 5, 3):
        raise ValueError("this checked core proof applies only to C(16,5,3)")
    path = Path(certificate).resolve()
    checker = Path(__file__).with_name("check_core_orbit_certificate.py").resolve()
    raw = path.read_bytes()
    checker_raw = checker.read_bytes()
    started = time.monotonic()
    run = subprocess.run([sys.executable, "-I", str(checker), str(path)],
                         capture_output=True, text=True, check=False)
    report = json.loads(run.stdout)
    if path.read_bytes() != raw or checker.read_bytes() != checker_raw:
        raise ValueError("proof or checker changed during verification")
    if (run.returncode or report.get("valid_certificate") is not True
            or report.get("complete_obstruction") is not True):
        raise ValueError("independent core proof check failed")
    data = json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)
    limit = report["maximum_core_blocks_in_any_64_cover"]
    if type(limit) is not int or not 0 <= limit < 60:
        raise ValueError("independent checker returned an invalid core limit")
    original = core_ids_after_permutation(universe, data["core_blocks"])
    transformed = core_ids_after_permutation(universe, data["core_blocks"], permutation)
    cuts = [{"block_ids": original, "limit": limit}]
    if transformed != original:
        cuts.append({"block_ids": transformed, "limit": limit})
    return {
        "cuts": cuts, "certificate_sha256": hashlib.sha256(raw).hexdigest(),
        "checker_sha256": hashlib.sha256(checker_raw).hexdigest(), "checker_path": str(checker),
        "verification": report, "check_seconds": time.monotonic() - started,
        "certificate_path": str(path), "core_permutation": permutation,
        "scope": "certified necessary constraints on any<=64-block cover, including relabelings",
    }
