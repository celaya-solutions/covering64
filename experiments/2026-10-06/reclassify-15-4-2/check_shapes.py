# Document:    Repo Representative Shape Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      994d01b41de7b15d4bbbcb2f83c1ba602e26f60fcb94f698c8ad89bb18fb1095
# Chain:       solana-mainnet
# Tx:          3cBh5qk97XFiz9j5wX8WjUxSnmSUrH2EtBimoAhC3zct3woV7sZoLtXyqRHyXzwcuKYwbYk24ueU2EsgKDPSZQLu
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Step 4: check the repo's four class representatives against my own classification.

Reads shape-{1,4,44,47}-class-0.txt (lines '1 a b c d'), drops the leading 1.
usage: check_shapes.py [dfs.npz [link_dir]]
defaults: out/dfs1.npz (written by analyze.py) and the repo's
experiments/2026-10-03/link-classification
"""
import sys, itertools
import numpy as np
from common import group_G, images, LEAVES, LINKS, OUT

npz = sys.argv[1] if len(sys.argv) > 1 else str(OUT / "dfs1.npz")
d = sys.argv[2] if len(sys.argv) > 2 else str(LINKS)
sols = np.load(npz)["sols"]
orbit_of = np.load(npz)["orbit_of"]
index = {row.tobytes(): i for i, row in enumerate(sols)}
G = group_G()


def generic_aut_count(blocks, pts, target=None):
    """Count bijections pts -> pts mapping the block set `blocks` onto the block
    set `target` (default: itself), by plain backtracking. No use of G."""
    if target is None:
        target = blocks
    B = [frozenset(b) for b in blocks]
    T = set(frozenset(b) for b in target)
    deg = {p: sum(p in b for b in B) for p in pts}
    tdeg = {p: sum(p in b for b in T) for p in pts}
    order = sorted(pts, key=lambda p: -deg[p])
    # blocks that become fully assigned when order[k] is assigned
    pos = {p: i for i, p in enumerate(order)}
    done_at = [[] for _ in order]
    for b in B:
        done_at[max(pos[p] for p in b)].append(b)
    img = {}
    used = set()
    count = 0

    def rec(k):
        nonlocal count
        if k == len(order):
            count += 1
            return
        p = order[k]
        for q in pts:
            if q in used or tdeg[q] != deg[p]:
                continue
            img[p] = q; used.add(q)
            if all(frozenset(img[x] for x in b) in T for b in done_at[k]):
                rec(k + 1)
            del img[p]; used.discard(q)

    rec(0)
    return count


reps = {}
for s in (1, 4, 44, 47):
    lines = open(f"{d}/shape-{s}-class-0.txt").read().split("\n")
    blocks = []
    for ln in lines:
        if not ln.strip():
            continue
        v = [int(t) for t in ln.split()]
        assert len(v) == 5 and v[0] == 1, ln
        blocks.append(tuple(sorted(v[1:])))
    pts = list(range(2, 17))
    assert len(blocks) == 19 and len(set(blocks)) == 19
    assert all(len(set(b)) == 4 and set(b) <= set(pts) for b in blocks)
    m = {pr: sum(1 for b in blocks if pr[0] in b and pr[1] in b) for pr in itertools.combinations(pts, 2)}
    covering = all(v >= 1 for v in m.values())
    deg = {p: sum(p in b for b in blocks) for p in pts}
    hubs = [p for p in pts if deg[p] == 6]
    hub = hubs[0]
    exc = sorted(pr for pr, v in m.items() if v == 2)
    maxm = max(m.values())
    leaves = sorted(u for pr in exc if hub in pr for u in pr if u != hub)
    match = sorted(pr for pr in exc if hub not in pr)
    # standardize: hub->0, leaves->1..4, matching pairs->(5,6),(7,8),...
    mp = {hub: 0}
    for i, l in enumerate(leaves):
        mp[l] = 1 + i
    for i, (a, b) in enumerate(match):
        mp[a], mp[b] = 5 + 2 * i, 6 + 2 * i
    assert sorted(mp) == pts and sorted(mp.values()) == list(range(15))
    std = np.array(sorted(sum(1 << mp[x] for x in b) for b in blocks), dtype=np.int64)
    j = index.get(std.tobytes())
    orb = int(orbit_of[j]) if j is not None else None
    img = images(std, G)
    autG = int((img == std).all(axis=1).sum())
    autgen = generic_aut_count(blocks, pts)
    hubblocks = [b for b in blocks if hub in b]
    lc = sorted((sum(1 for x in b if x in leaves) for b in hubblocks), reverse=True)
    reps[s] = (blocks, pts)
    print(f"shape-{s}: 19 distinct blocks, covering={covering}, max multiplicity={maxm}, "
          f"degrees: {sorted(deg.values(), reverse=True)[:3]}..., hub={hub} (deg {deg[hub]}), "
          f"leaves={leaves}, matching={match}")
    print(f"   in my solution set: {j is not None}, my orbit: {orb}, |Aut| via G: {autG}, "
          f"|Aut| via generic backtracking: {autgen}, hub-block leaf counts {lc}, "
          f"3-leaf hub block: {[b for b in hubblocks if sum(x in leaves for x in b) >= 3]}")

print("pairwise isomorphism counts (generic backtracking, no G):")
keys = list(reps)
for a, b in itertools.combinations(keys, 2):
    n = generic_aut_count(reps[a][0], reps[a][1], target=reps[b][0])
    print(f"   shape-{a} -> shape-{b}: {n} isomorphisms")
