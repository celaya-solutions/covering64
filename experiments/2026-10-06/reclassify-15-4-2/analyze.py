# Document:    Enumeration Validation and G-Orbits
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      60dc0dcce3e39ee212479b995967c32affd8b74755724eaf0b4596ec1e1d3416
# Chain:       solana-mainnet
# Tx:          5YPKSCTzz8CmcSeM8EbeyhcqHc2fNLpG125YKNdADK2pD2z8xMPbfkbUWk7aVZnvAzDKmZ7cwDJJ3VUX54tkxKos
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Load DFS output, validate, dedupe, partition into G-orbits.

usage: analyze.py <dir with s*.bin> [out.npz [orbits.json]]
(orbits.json defaults to out.npz with .npz replaced by _orbits.json)
"""
import sys, glob, time, json
import numpy as np
from common import (QP, DEMAND, MASK_TO_Q, group_G, check_G, images, masks_to_points,
                    LEAVES, NP)

t0 = time.time()
d = sys.argv[1]
outp = sys.argv[2] if len(sys.argv) > 2 else None
orbp = sys.argv[3] if len(sys.argv) > 3 else (outp.replace(".npz", "_orbits.json") if outp else None)
files = sorted(glob.glob(d + "/s*.bin"))
arrs = [np.fromfile(f, dtype=np.uint16).reshape(-1, 19) for f in files]
raw = np.concatenate(arrs).astype(np.int64)
print("files", len(files), "raw solutions", raw.shape[0])

# validate every solution: distinct quads, exact multiplicities
qi = MASK_TO_Q[raw]
assert (qi >= 0).all(), "non-quadruple block"
srt = np.sort(raw, axis=1)
assert (np.diff(srt, axis=1) > 0).all(), "repeated block"
bad = 0
for s in range(0, raw.shape[0], 20000):
    cnt = QP[qi[s:s + 20000]].sum(axis=1)  # (n,105)
    bad += int((cnt != DEMAND).any(axis=1).sum())
print("solutions failing multiplicity check:", bad)
assert bad == 0

uniq = np.unique(srt, axis=0)
print("distinct solutions N =", uniq.shape[0])
assert uniq.shape[0] == raw.shape[0], "duplicate solutions output"
N = uniq.shape[0]

G = group_G()
check_G(G)
print("|G| =", G.shape[0], "(checked: distinct perms preserving excess graph)")

index = {row.tobytes(): i for i, row in enumerate(uniq)}
orbit_of = -np.ones(N, dtype=np.int32)
orbits = []
for i in range(N):
    if orbit_of[i] >= 0:
        continue
    rep = uniq[i]
    img = images(rep, G)  # (92160,19) sorted
    aut = int((img == rep).all(axis=1).sum())
    u = np.unique(img, axis=0)
    k = len(orbits)
    for row in u:
        j = index.get(row.tobytes())
        assert j is not None, "image of a solution is not in the solution set"
        assert orbit_of[j] < 0
        orbit_of[j] = k
    assert u.shape[0] * aut == G.shape[0]
    pts = masks_to_points(rep)
    hub = [tuple(int(x) for x in b) for b in pts if 0 in b]
    leafcounts = sorted((sum(1 for x in b if x in LEAVES) for b in hub), reverse=True)
    orbits.append(dict(rep=[tuple(int(x) for x in b) for b in pts], orbit_size=int(u.shape[0]),
                       aut=aut, hub_blocks=hub, hub_leaf_counts=leafcounts,
                       has_3leaf_hub_block=any(c >= 3 for c in leafcounts)))
    print(f"orbit {k}: size {u.shape[0]}, |Aut| = {aut}, hub leaf counts {leafcounts}")
assert (orbit_of >= 0).all()
print("number of orbits:", len(orbits))
print("sum of orbit sizes:", sum(o["orbit_size"] for o in orbits), " N:", N)
print("sum 92160/|Aut|:", sum(92160 // o["aut"] for o in orbits))
print("time %.1fs" % (time.time() - t0))
if outp:
    np.savez(outp, sols=uniq, orbit_of=orbit_of)
if orbp:
    json.dump(orbits, open(orbp, "w"), indent=1)
