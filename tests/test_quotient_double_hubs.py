# Document:    Anchor Reversal Mapping Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "quotient", Path(__file__).resolve().parents[1] / "scripts" / "quotient_double_hubs.py")
quotient = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quotient)


def test_reversal_inverts_the_composed_source_map():
    source = {p: 1 if p == 2 else p for p in range(2, 17)}
    stabilizer = {p: p for p in range(1, 17)}
    stabilizer[3], stabilizer[4] = 4, 3
    result = quotient.reverse_map(source, stabilizer)
    assert result[1] == 2 and result[2] == 1
    assert result[3] == 4 and result[4] == 3
    assert all(result[stabilizer[source[p]]] == p for p in source)


def test_damaged_maps_are_rejected():
    source = {p: 1 if p == 2 else p for p in range(2, 17)}
    stabilizer = {p: p for p in range(1, 17)}
    with pytest.raises(ValueError):
        quotient.reverse_map({**source, 3: 1}, stabilizer)
    with pytest.raises(ValueError, match="integers"):
        quotient.reverse_map({**source, 2: True}, stabilizer)
