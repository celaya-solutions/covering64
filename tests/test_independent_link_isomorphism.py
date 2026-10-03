# Document:    Independent Hub Isomorphism Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3bcb61c73d7789f9a0b0abbfb1b315c193115818c6647aadca4ded79970ff91d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "independent_isomorphism", ROOT / "scripts/audit_link_isomorphism.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
DATA = json.loads(gzip.decompress((
    ROOT / "experiments/2026-10-03/link-hub-independent/audit-fixture.json.gz"
).read_bytes()))["body"]


@pytest.mark.parametrize("shape,count", [(1, 48), (4, 8), (44, 4), (47, 384)])
def test_automorphisms_form_complete_group_and_one_link_class(shape, count):
    hub = DATA["metadata"]["shapes"][shape]["hub_blocks"]
    group = set(AUDIT.hub_bijections(hub, hub))
    assert len(group) == count
    assert tuple(range(2, 17)) in group
    for mapping in group:
        inverse = tuple(mapping.index(x) + 2 for x in range(2, 17))
        assert inverse in group
    canonical = {min(AUDIT.image(link, mapping) for mapping in group)
                 for link in DATA["cp_solutions"][str(shape)]}
    assert len(canonical) == 1


@pytest.mark.parametrize("left,right", [(1, 4), (1, 44), (1, 47),
                                        (4, 44), (4, 47), (44, 47)])
def test_cross_shape_hub_maps_empty(left, right):
    lhub = DATA["metadata"]["shapes"][left]["hub_blocks"]
    rhub = DATA["metadata"]["shapes"][right]["hub_blocks"]
    assert AUDIT.hub_bijections(lhub, rhub) == []


def test_duplicate_hub_rejected():
    hub = [list(b) for b in DATA["metadata"]["shapes"][1]["hub_blocks"]]
    hub[1] = hub[0].copy()
    with pytest.raises(ValueError, match="six distinct"):
        AUDIT.hub_bijections(hub, hub)
