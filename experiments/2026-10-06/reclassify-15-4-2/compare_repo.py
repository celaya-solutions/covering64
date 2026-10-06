# Document:    Repo Classification Comparison
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      5a385e416c939bf4a0e263d410c89b1b28a23b33d72553efd15549a867ad8949
# Chain:       solana-mainnet
# Tx:          pgvsYC9oczeUL5r4xpzkZYxJkT19xR9Qxfwr7psXQ5CoSzwdZt3vNjYKuvaQThUnTvbohLZefEo7xWNFp7vdpED
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Compare my results with automorphisms.json / classification.json (read only after my run).

usage: compare_repo.py [dfs.npz [hubsets.npz [link_dir]]]
defaults: out/dfs1.npz, out/hubsets.npz and the repo's
experiments/2026-10-03/link-classification
"""
import json, itertools, sys
import numpy as np
from common import group_G, images, masks_to_points, LEAVES, LINKS, OUT
dfs_path = sys.argv[1] if len(sys.argv) > 1 else str(OUT / "dfs1.npz")
hub_path = sys.argv[2] if len(sys.argv) > 2 else str(OUT / "hubsets.npz")
D = sys.argv[3] if len(sys.argv) > 3 else str(LINKS)
aj = json.load(open(D + "/automorphisms.json"))
cj = json.load(open(D + "/classification.json"))
sols = np.load(dfs_path)["sols"]; orbit_of = np.load(dfs_path)["orbit_of"]
hs = np.load(hub_path); reps, sizes = hs["reps"], hs["sizes"]
G = group_G().astype(np.int64)
# hub-set orbit lookup: canonical = lexicographically least image under G
def hub_canon(hmasks):
    pts = masks_to_points(np.array(hmasks))
    img = np.sort((np.int64(1) << G[:, pts]).sum(axis=-1), axis=1)
    return tuple(int(v) for v in min(map(tuple, img)))
rep_canon = {hub_canon(r): (i, int(s)) for i, (r, s) in enumerate(zip(reps, sizes))}
for k in range(4):
    j = int(np.where(orbit_of == k)[0][0])
    hub = [int(v) for v in sols[j] if v & 1]
    i, s = rep_canon[hub_canon(hub)]
    # completions of this hub set among all solutions
    hubset = set(hub)
    ncomp = sum(1 for row in sols if set(int(v) for v in row if v & 1) == hubset)
    print(f"class {k}: hub-set orbit #{i}, |orbit(H)|={s}, |Stab_G(H)|={92160//s}, completions of H={ncomp}")
for c in aj["classes"]:
    s = c["shape"]
    blocks = [tuple(sorted(int(t) for t in ln.split()[1:])) for ln in open(f"{D}/shape-{s}-class-0.txt") if ln.strip()]
    B = set(blocks)
    ok = all({tuple(sorted(int(m[str(x)]) for x in b)) for b in blocks} == B for m in c["maps"])
    distinct = len({tuple(sorted(m.items())) for m in c["maps"]}) == len(c["maps"])
    # my own automorphism set by brute force over perms that fix 2 and preserve degrees is
    # equivalent to the G-stabilizer; compare as sets
    pts = list(range(2, 17))
    deg = {p: sum(p in b for b in blocks) for p in pts}
    m2 = {pr: sum(1 for b in blocks if set(pr) <= set(b)) for pr in itertools.combinations(pts, 2)}
    hub = 2; leaves = sorted(u for (a, b), v in m2.items() if v == 2 and hub in (a, b) for u in (a, b) if u != hub)
    match = sorted(pr for pr, v in m2.items() if v == 2 and hub not in pr)
    mp = {hub: 0}; mp.update({l: 1 + i for i, l in enumerate(leaves)})
    for i, (a, b) in enumerate(match): mp[a], mp[b] = 5 + 2 * i, 6 + 2 * i
    inv = {v: k for k, v in mp.items()}
    std = np.array(sorted(sum(1 << mp[x] for x in b) for b in blocks), dtype=np.int64)
    img = images(std, G)
    mine = set()
    for g in np.where((img == std).all(axis=1))[0]:
        mine.add(tuple(sorted((x, inv[int(G[g, mp[x]])]) for x in pts)))
    theirs = {tuple(sorted((int(k), int(v)) for k, v in m.items())) for m in c["maps"]}
    print(f"shape-{s}: repo |Aut|={c['automorphism_count']}, maps listed={len(c['maps'])}, all are automorphisms={ok}, distinct={distinct}, same group as mine={mine == theirs}")
for s in cj["shapes"]:
    print(f"classification.json shape {s['shape']}: input_links={s['input_links']}, hub_automorphisms={s['hub_automorphisms']}, classes={s['classes']}")
print("cross-shape non-isomorphic:", all(not x["isomorphic"] for x in cj["cross_shape_checks"]))
