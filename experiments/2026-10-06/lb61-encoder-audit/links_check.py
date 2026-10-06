# Document:    Link Representative Checks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      4274e4f5aa14c480d3632523af8125e85bec180a4b0d6f59a600a52a5565fc12
# Chain:       solana-mainnet
# Tx:          dui3VvbarEpgGFUW2qWzdY2QgBkiWtXvWafd12BGLZ88UxtiuYjXSeRkFyXwEQwHvhG8tDbQCztmnd266J2h5DM
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

# links_check.py: the fixed part. For each representative: format, (15,4,2) cover, hub = 2,
# excess structure, and that the constants the CNF derives from it are consistent.
# usage: python links_check.py   (from any directory)
from itertools import combinations
from collections import Counter
from pathlib import Path
LINKS=Path(__file__).resolve().parents[3]/'experiments'/'2026-10-03'/'link-classification'
for s in (1,4,44,47):
    raw=[l for l in open(LINKS/f'shape-{s}-class-0.txt') if l.strip()]
    L=[tuple(map(int,l.split())) for l in raw]
    fmt = len(L)==19 and len(set(L))==19 and all(len(b)==5 and b[0]==1 and list(b)==sorted(set(b)) and b[-1]<=16 for b in L)
    Q=[b[1:] for b in L]
    deg=Counter(v for q in Q for v in q)
    m=Counter(p for q in Q for p in combinations(q,2))
    pts=range(2,17)
    covered=all(m[p]>=1 for p in combinations(pts,2))
    maxm=max(m.values())
    dbl=[p for p in combinations(pts,2) if m[p]==2]
    hub=[v for v in pts if deg[v]==6]
    star=[p for p in dbl if 2 in p]; leaves=sorted(v for p in star for v in p if v!=2)
    rest=[p for p in dbl if 2 not in p]
    restpts=sorted(v for p in rest for v in p)
    pm = len(rest)==5 and restpts==sorted(set(pts)-{2}-set(leaves))
    # CNF constants: triples {1,u,v} have mu = m_uv; pair (1,2) needs 4 doubled, (1,v) needs 1
    tri_ok = all(1<=m[p]<=2 for p in combinations(pts,2))
    p12 = sum(1 for w in pts if w!=2 and m[tuple(sorted((2,w)))]==2)
    p1v = {v: sum(1 for w in pts if w!=v and m[tuple(sorted((v,w)))]==2) for v in range(3,17)}
    lemma5 = any(len(set(q)&set(leaves))==3 for q in Q if 2 in q)
    print(f'shape-{s}: format {fmt}; cover {covered}; degrees {dict(Counter(deg.values()))}; hub {hub}; max pair mult {maxm};'
          f' doubled pairs {len(dbl)} = star at 2 with leaves {leaves} + matching {rest} (perfect on rest: {pm});'
          f' triple-through-1 mu in {{1,2}}: {tri_ok}; (1,2) doubled {p12}; (1,v) doubled {sorted(set(p1v.values()))};'
          f' Lemma5 hub block with 3 leaves: {lemma5}')
