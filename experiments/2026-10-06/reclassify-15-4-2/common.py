# Document:    Reclassification Shared Helpers
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      b49ef9527a5219ed5ecc7fe323d049399c4514db8b3b0666a60524dc224dbc6e
# Chain:       solana-mainnet
# Tx:          4yfbhkFURK1ShZXvtaTYtmuX3jur2CWy6nD6412QK4BtsBv6V4fmFaNgkLvQ5Db4t57FYdrg5rhLvC1CKQkhLgLY
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Shared helpers for the (15,4,2) reclassification (written from scratch).

Points 0..14. Standard excess graph: hub 0, leaves 1..4, matching
{5,6},{7,8},{9,10},{11,12},{13,14}.
A covering is stored as a sorted tuple of 19 point masks (15-bit ints).
"""
import itertools
from pathlib import Path

import numpy as np

# Paths: HERE is this folder, REPO the repository root, LINKS the folder with
# the repo's four representatives (read only by check_shapes.py and compare_repo.py).
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LINKS = REPO / "experiments" / "2026-10-03" / "link-classification"
OUT = HERE / "out"

NP = 15
LEAVES = (1, 2, 3, 4)
MATCHING = ((5, 6), (7, 8), (9, 10), (11, 12), (13, 14))
EXCESS = {(0, 1), (0, 2), (0, 3), (0, 4)} | set(MATCHING)

PAIRS = list(itertools.combinations(range(NP), 2))
PAIR_INDEX = {p: i for i, p in enumerate(PAIRS)}
DEMAND = np.array([2 if p in EXCESS else 1 for p in PAIRS], dtype=np.int16)
assert DEMAND.sum() == 6 * 19

QUADS = list(itertools.combinations(range(NP), 4))
QMASK = np.array([sum(1 << x for x in q) for q in QUADS], dtype=np.int64)
MASK_TO_Q = -np.ones(1 << NP, dtype=np.int32)
MASK_TO_Q[QMASK] = np.arange(len(QUADS))
# quad x pair incidence
QP = np.zeros((len(QUADS), len(PAIRS)), dtype=np.int16)
for qi, q in enumerate(QUADS):
    for p in itertools.combinations(q, 2):
        QP[qi, PAIR_INDEX[p]] = 1


def mask_points(m):
    return tuple(i for i in range(NP) if (m >> i) & 1)


def group_G():
    """All 92160 automorphisms of the standard excess graph, as (92160,15) int8.
    perm[g, x] = image of point x."""
    perms = []
    for sig in itertools.permutations(range(4)):
        for tau in itertools.permutations(range(5)):
            for flips in itertools.product((0, 1), repeat=5):
                p = [0] * NP
                p[0] = 0
                for i in range(4):
                    p[1 + i] = 1 + sig[i]
                for i in range(5):
                    a, b = MATCHING[i]
                    c, d = MATCHING[tau[i]]
                    if flips[i]:
                        c, d = d, c
                    p[a], p[b] = c, d
                perms.append(p)
    G = np.array(perms, dtype=np.int8)
    return G


def check_G(G):
    """G has 92160 distinct permutations, each preserving the excess edge set."""
    assert G.shape == (92160, NP)
    assert len({row.tobytes() for row in G}) == 92160
    E = sorted(EXCESS)
    Eset = set(EXCESS)
    for row in G[:: 997]:
        img = {tuple(sorted((int(row[a]), int(row[b])))) for a, b in E}
        assert img == Eset
    # full check vectorized
    Ea = np.array([e[0] for e in E]); Eb = np.array([e[1] for e in E])
    ia = G[:, Ea].astype(np.int64); ib = G[:, Eb].astype(np.int64)
    lo = np.minimum(ia, ib); hi = np.maximum(ia, ib)
    code = np.sort(lo * 16 + hi, axis=1)
    ref = np.sort(np.array([a * 16 + b for a, b in E]))
    assert (code == ref).all()
    for row in G:
        assert sorted(row.tolist()) == list(range(NP))
    return True


def masks_to_points(masks):
    """(..., 19) masks -> (..., 19, 4) points"""
    masks = np.asarray(masks, dtype=np.int64)
    bits = (masks[..., None] >> np.arange(NP)) & 1
    idx = np.argsort(-bits, axis=-1, kind="stable")[..., :4]
    return np.sort(idx, axis=-1)


def images(sol_masks, G):
    """All images of one covering (19 masks) under G: (|G|,19) sorted masks."""
    pts = masks_to_points(np.array(sol_masks))  # (19,4)
    img = G[:, pts].astype(np.int64)  # (|G|,19,4)
    m = (np.int64(1) << img).sum(axis=-1)  # (|G|,19)
    return np.sort(m, axis=1)


def validate(sol_masks):
    """Return True iff 19 distinct quadruples with the exact standard pair multiplicities."""
    ms = list(sol_masks)
    if len(ms) != 19 or len(set(ms)) != 19:
        return False
    qi = MASK_TO_Q[np.array(ms)]
    if (qi < 0).any():
        return False
    cnt = QP[qi].sum(axis=0)
    return bool((cnt == DEMAND).all())


def is_covering(blocks, points):
    """Generic check: every pair of `points` lies in some block."""
    pts = sorted(points)
    for a, b in itertools.combinations(pts, 2):
        if not any(a in B and b in B for B in blocks):
            return False
    return True
