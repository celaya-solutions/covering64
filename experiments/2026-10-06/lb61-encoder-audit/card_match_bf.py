# Document:    Exactly-Four and Matching Clause Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      b6d28d00927f817e2dbebf9e13f5370334bf230331a98581fd3743774e062e2d
# Chain:       solana-mainnet
# Tx:          64nqiWCmLWstHMMZdWmPsahmGMKTNVTrvZk4ECzp1G85M2sC4H8CZHTzCpiHr7xwasBHaa6LbNufgpW2qrLGxW2H
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

# card_match_bf.py: exhaustive checks of the exactly-4 and matching families, using the clauses
# exactly as emitted by the encoder (taken from the tagged build, shape-1; these families do not
# depend on the link).
import sys, itertools, time
sys.path.insert(0, __file__.rsplit('/',1)[0])
from instrument import build
from pysat.solvers import Solver
r=build('shape-1-class-0.txt'); isA=r['isA']; mt=r['mt']
ex4=[c for c,(f,k) in zip(r['clauses'],r['tags']) if f=='ex4']
mat=[c for c,(f,k) in zip(r['clauses'],r['tags']) if f in ('m_excl','m_amo','m_alo')]
pts=list(range(3,17)); A=[isA[v] for v in pts]
# 1) exactly-4: SAT iff popcount == 4, over all 2^14 assignments
bad=0; nsat=0
with Solver(name='minisat22',bootstrap_with=ex4) as s:
    for bits in itertools.product((0,1),repeat=14):
        sat=s.solve(assumptions=[a if b else -a for a,b in zip(A,bits)])
        nsat+=sat; bad+= (sat != (sum(bits)==4))
print('ex4: assignments 16384, satisfiable', nsat, '(C(14,4)=1001), mismatches', bad)
# 2) matching: for every 4-set A, projected models on m_uv are exactly the perfect matchings of the other ten
def pms(S):
    if not S: yield frozenset(); return
    a=S[0]
    for b in S[1:]:
        rest=[v for v in S if v not in (a,b)]
        for m in pms(rest): yield m|{(a,b)}
t=time.time(); bad=0; total=0
mvars={v:k for k,v in mt.items()}
for Aset in itertools.combinations(pts,4):
    asm=[isA[v] if v in Aset else -isA[v] for v in pts]
    expect=set(pms([v for v in pts if v not in Aset]))
    got=set()
    with Solver(name='minisat22',bootstrap_with=mat) as s:
        while s.solve(assumptions=asm):
            m=s.get_model(); on=frozenset(mvars[l] for l in m if l>0 and l in mvars)
            got.add(on); s.add_clause([-mt[p] if p in on else mt[p] for p in mt])
            if len(got)>2000: break
    total+=len(got); bad+= (got!=expect)
print('matching: A-sets 1001, total models', total, '(expect 1001*945 =', 1001*945, '), A-sets with mismatch', bad, f'{time.time()-t:.0f}s')
# Not checked: the matching clauses when |A| != 4; the exactly-4 clauses already exclude that case.
