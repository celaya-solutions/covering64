# Document:    Counter Encoding Brute-Force Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      41c1d0efc7901b2d8b00e9e0810b415e219753725ad297f990202b22803a170a
# Chain:       solana-mainnet
# Tx:          2fHErECidy9Cxko6KtJRpCskwkPptN5MH3vyNU41BSMoF1Ketihb3JdE4X7wA52JPU8DpvnECttVRcP7oYvL2vnp
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

# counter_bf.py: brute-force semantics of run_case.py's counter() (lines 29-44, read from
# experiments/2026-10-05/lb61-certified/run_case.py at run time and exec'd unchanged).
# Part A is solver-free and exhaustive over ALL variables
# (lits and aux) for n + n*K <= 22. Part B uses a SAT solver on the tiny counter CNF
# for larger n (including n=14, K=5, the exact per-pair instance), all 2^n lit assignments.
# usage: python counter_bf.py   (from any directory)
import sys, itertools, numpy as np
from pathlib import Path
from pysat.formula import IDPool
from pysat.solvers import Solver
RUN_CASE=Path(__file__).resolve().parents[3]/'experiments'/'2026-10-05'/'lb61-certified'/'run_case.py'
SRC=''.join(RUN_CASE.read_text().splitlines(keepends=True)[28:44])   # lines 29-44
assert SRC.startswith('def counter(lits,K,tag):\n') and SRC.endswith('    return prev\n'), SRC
print('counter() source: run_case.py lines 29-44,', len(SRC), 'bytes')
def make(n,K):
    ns={'pool':IDPool(),'clauses':[]}
    exec(SRC,ns)
    lits=[ns['pool'].id(('l',i)) for i in range(n)]
    out=ns['counter'](lits,K,('t',))
    pool=ns['pool']
    aux={(i,j):pool.obj2id[(('t',),i,j)] for i in range(n) for j in range(1,K+1)}
    return pool.top, ns['clauses'], lits, aux, out
def canon(bits,i,j): return int(sum(bits[:i+1])>=j)
# Part A: exhaustive, no solver
A=[]
for n in range(1,9):
    for K in range(1,7):
        nv,cls,lits,aux,out=make(n,K)
        if nv>22: continue
        assert nv==n+n*K
        N=1<<nv; v=np.arange(N,dtype=np.int64)
        val=lambda lit: ((v>>(abs(lit)-1))&1).astype(bool) if lit>0 else ~(((v>>(abs(lit)-1))&1).astype(bool))
        sat=np.ones(N,dtype=bool)
        for c in cls:
            cs=np.zeros(N,dtype=bool)
            for lit in c: cs|=val(lit)
            sat&=cs
        idx=np.nonzero(sat)[0]
        ok = len(idx)==(1<<n)
        seen=set()
        for a in idx:
            bits=[(a>>(l-1))&1 for l in lits]; seen.add(tuple(bits))
            for (i,j),vid in aux.items():
                if ((a>>(vid-1))&1)!=canon(bits,i,j): ok=False
        ok = ok and len(seen)==(1<<n)
        A.append((n,K,len(cls),int(ok)))
print('Part A (exhaustive over lits+aux, solver-free): (n,K,clauses,ok)'); print(A)
print('Part A all ok:', all(t[3] for t in A), 'cases', len(A))
# Part B: solver, unique extension equal to canonical, all 2^n lit assignments
B=[]
for n,K in [(n,K) for n in range(1,13) for K in range(1,7)]+[(14,5),(14,3),(14,6)]:
    nv,cls,lits,aux,out=make(n,K)
    ok=True
    with Solver(name='minisat22',bootstrap_with=cls) as s:
        for bits in itertools.product((0,1),repeat=n):
            asm=[l if b else -l for l,b in zip(lits,bits)]
            if not s.solve(assumptions=asm): ok=False; break
            m=set(s.get_model())
            for (i,j),vid in aux.items():
                if (vid in m)!=bool(canon(bits,i,j)): ok=False
            block=[-vid if vid in m else vid for vid in aux.values()]
            # uniqueness: no other aux assignment under the same lit assignment
            with Solver(name='minisat22',bootstrap_with=cls+[block]) as s2:
                if s2.solve(assumptions=asm): ok=False
            if not ok: break
    B.append((n,K,int(ok)))
print('Part B all ok:', all(t[2] for t in B), 'cases', len(B), 'incl. (14,5):', [t for t in B if t[0]==14])
