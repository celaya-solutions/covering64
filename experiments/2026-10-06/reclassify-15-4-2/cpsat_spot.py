# Document:    CP-SAT Labeled Hub-Set Spot Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      50ada52b4c8877524b6529444af54d373a1b9bd366c4ce15a47ae80f3ff144e7
# Chain:       solana-mainnet
# Tx:          nTXY18qaXXpKi9myFVS4rojdcwZ1EfnUquuti1B15YVoz62GFxeBR3b4jwaQK6ha489FdAmsxM4Ab4533bCaKgB
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Spot check without symmetry: CP-SAT on uniformly random LABELED hub-block
sets (random rep weighted by orbit size, then a random g in G), plus every
labeled hub-block set used by some DFS solution in a random sample.
Compares each CP-SAT completion set with the DFS solutions having that hub set.
usage: cpsat_spot.py hubsets.npz dfs.npz n_random n_from_dfs [nproc]
"""
import sys, numpy as np, time
from multiprocessing import Pool
from cpsat_hub import solve
from common import group_G, masks_to_points
if __name__ == "__main__":
    rng = np.random.default_rng(20261006)
    hs = np.load(sys.argv[1]); reps, sizes = hs["reps"], hs["sizes"]
    dfs = np.load(sys.argv[2])["sols"]
    nr, nd = int(sys.argv[3]), int(sys.argv[4])
    nproc = int(sys.argv[5]) if len(sys.argv) > 5 else 16
    G = group_G().astype(np.int64)
    hubkey = {}
    for row in dfs:
        k = tuple(sorted(int(v) for v in row if v & 1))
        hubkey.setdefault(k, []).append(tuple(int(v) for v in row))
    cases = set()
    p = sizes / sizes.sum()
    for _ in range(nr):
        r = reps[rng.choice(len(reps), p=p)]
        g = G[rng.integers(len(G))]
        pts = masks_to_points(r)
        cases.add(tuple(sorted(int(m) for m in (np.int64(1) << g[pts]).sum(axis=-1))))
    keys = list(hubkey)
    for i in rng.choice(len(keys), size=nd, replace=False):
        cases.add(keys[i])
    cases = sorted(cases)
    t0 = time.time()
    with Pool(nproc) as pool:
        res = pool.map(solve, [list(c) for c in cases], chunksize=8)
    mism = sum(1 for hub, sols, n, dt in res if sorted(hubkey.get(hub, [])) != sols)
    nz = sum(1 for hub, sols, n, dt in res if sols)
    print(f"labeled hub sets checked: {len(cases)} (with completions: {nz}); mismatches vs DFS: {mism}; wall {time.time()-t0:.1f}s")
