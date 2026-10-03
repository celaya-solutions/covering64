# Document:    Checked Core Cut Loading Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import importlib.util
from pathlib import Path

import pytest

from covering64.core import Universe

SPEC = importlib.util.spec_from_file_location(
    "checked_core_cut", Path(__file__).parents[1] / "scripts" / "checked_core_cut.py")
cuts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cuts)


def test_core_relabeling_uses_full_lexicographic_universe_and_rejects_nonbijections():
    universe = Universe.build()
    core = universe.blocks[:60]
    assert cuts.core_ids_after_permutation(universe, core) == list(range(60))
    permutation = {x: 17 - x for x in range(1, 17)}
    result = cuts.core_ids_after_permutation(universe, core, permutation)
    expected = {tuple(sorted(17 - x for x in block)) for block in core}
    assert result == sorted(result)
    assert {universe.blocks[i] for i in result} == expected
    for invalid in [{1: 2}, {x: 1 for x in range(1, 17)}]:
        with pytest.raises(ValueError, match="bijection"):
            cuts.core_ids_after_permutation(universe, core, invalid)


def test_unchecked_or_damaged_certificate_cannot_supply_a_core_cut(tmp_path):
    path = tmp_path / "bad.json.gz"
    path.write_bytes(gzip.compress(b'{"schema":"not-a-certificate"}'))
    with pytest.raises(ValueError, match="independent core proof check failed"):
        cuts.checked_core_cuts(Universe.build(), path)
