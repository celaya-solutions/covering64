# Document:    Hub-Block Set Enumeration
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      9589edf6b9517e55f37a253eaca61284b87f55f3ec2113e15b40207cda298cdc
# Chain:       solana-mainnet
# Tx:          3sfumFndG5yPZs31H1Bw4LsDTqFfp7Sq4Dut3EoAyXcUx2LDwAmaUvM8MQn3piks87b9hVJTNQZ9EbDYNGw4ZKdi
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Enumerate all labeled hub-block sets and their G-orbits.

A hub-block set is the set of 6 blocks through the hub 0 in a standard
covering: {0} + T_i, where the T_i are 6 triples on {1..14} with each leaf
1..4 in exactly two triples, each of 5..14 in exactly one, and any two
triples meeting in at most one point (two shared points would cover a
non-excess pair twice: two leaves, or a leaf/non-leaf, since non-leaves
appear once).

usage: hubsets.py <out.npz>
saves: reps (k,6) hub-block masks (sorted), orbit sizes, total labeled count
"""
import sys, itertools, time
import numpy as np
from common import group_G, NP

t0 = time.time()
TRIPLES = list(itertools.combinations(range(1, NP), 3))
cap0 = [0] + [2, 2, 2, 2] + [1] * 10


def enum():
    out = []
    cap = cap0[:]
    chosen = []
    by_point = {x: [t for t in TRIPLES if x in t] for x in range(1, NP)}

    def ok(t):
        if any(cap[y] == 0 for y in t):
            return False
        for s in chosen:
            if len(set(s) & set(t)) > 1:
                return False
        return True

    def rec():
        x = next((y for y in range(1, NP) if cap[y] > 0), None)
        if x is None:
            out.append(tuple(sorted(chosen)))
            return
        r = cap[x]
        cands = by_point[x]

        def pick(start, need):
            if need == 0:
                rec(); return
            for i in range(start, len(cands)):
                t = cands[i]
                if not ok(t):
                    continue
                for y in t: cap[y] -= 1
                chosen.append(t)
                pick(i + 1, need - 1)
                chosen.pop()
                for y in t: cap[y] += 1
        pick(0, r)

    rec()
    return out


H = enum()
assert len(set(H)) == len(H)
assert all(len(h) == 6 for h in H)
print("labeled hub-block sets:", len(H), "time %.1fs" % (time.time() - t0))

# as sorted mask rows of the 6 hub blocks
def hmasks(h):
    return sorted(1 | sum(1 << y for y in t) for t in h)

Hm = np.array([hmasks(h) for h in H], dtype=np.int64)
index = {row.tobytes(): i for i, row in enumerate(Hm)}
G = group_G().astype(np.int64)
seen = np.zeros(len(H), dtype=bool)
reps, sizes = [], []
for i in range(len(H)):
    if seen[i]:
        continue
    h = H[i]
    pts = np.array([(0,) + t for t in h])  # (6,4)
    img = (np.int64(1) << G[:, pts]).sum(axis=-1)
    img = np.unique(np.sort(img, axis=1), axis=0)
    for row in img:
        j = index[row.tobytes()]  # KeyError would mean the set is not G-closed
        assert not seen[j]
        seen[j] = True
    reps.append(Hm[i]); sizes.append(img.shape[0])
assert seen.all()
print("G-orbits of hub-block sets:", len(reps), " sum of sizes:", sum(sizes),
      "time %.1fs" % (time.time() - t0))
np.savez(sys.argv[1], reps=np.array(reps), sizes=np.array(sizes), nlabeled=len(H))
