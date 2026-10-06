# Document:    Fixed-Link 61-Block CNF Generator
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      27003f6356393f1e28b2e25d72784823e6cb69413a69b67aa8f9d8c143252530
# Chain:       solana-mainnet
# Tx:          3ATdoRTHZo8kM5QVahLLNCVZEEmTGp7n2vF6m2eVx89D98rBU1J1MQAZWDLGc24zSgXY949P9C51f2nVoshQXKkW
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Write the fixed-link 61-block CNF for one link representative as DIMACS and
print its size and SHA256. Generation only: no solver is called.

The encoder is experiments/2026-10-05/lb61-certified/run_case.py, copied
verbatim: line 22 (reading the link file) differs only in that the path comes
from the command line, lines 23-72 (the encoder) and 75-77 (the DIMACS
writer) are byte-identical, and lines 78-97 (the Lingeling solve and the
drat-trim check) are left out. Imports are the subset of run_case.py's that
these lines use.

usage, from the repo root:
  python experiments/2026-10-06/lb61-encoder-audit/gen_cnf.py LINK_FILE OUT.cnf
e.g. LINK_FILE = experiments/2026-10-03/link-classification/shape-1-class-0.txt
"""
import sys, json, hashlib, os
from itertools import combinations
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
link_file, cnf_path = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(cnf_path) or '.', exist_ok=True)
# ---- run_case.py line 22 (link path from argv), then lines 23-72 verbatim ----
link=[tuple(map(int,l.split())) for l in open(link_file) if l.strip()]
assert len(link)==19 and all(b[0]==1 for b in link)
BLOCKS=list(combinations(range(1,17),5)); TR=list(combinations(range(1,17),3)); PR=list(combinations(range(1,17),2))
pool=IDPool(); clauses=[]
x={B:pool.id(('x',B)) for B in BLOCKS}; d={T:pool.id(('d',T)) for T in TR}
isA={v:pool.id(('A',v)) for v in range(3,17)}
mt={p:pool.id(('m',p)) for p in combinations(range(3,17),2)}
def counter(lits,K,tag):
    prev=[None]*(K+1)
    for i,l in enumerate(lits):
        cur=[None]+[pool.id((tag,i,j)) for j in range(1,K+1)]
        for j in range(1,K+1):
            c=cur[j]
            if prev[j] is not None: clauses.append([-prev[j],c])
            if j==1: clauses.append([-l,c])
            elif prev[j-1] is not None: clauses.append([-prev[j-1],-l,c])
            a=[prev[j]] if prev[j] is not None else []
            if j==1: clauses.append([-c]+a+[l])
            elif prev[j-1] is not None:
                clauses.append([-c]+a+[prev[j-1]]); clauses.append([-c]+a+[l])
            else: clauses.append([-c]+a)
        prev=cur
    return prev
linkset=set(link)
for B in BLOCKS:
    if 1 in B: clauses.append([x[B]] if B in linkset else [-x[B]])
tin={T:[] for T in TR}
for B in BLOCKS:
    for T in combinations(B,3): tin[T].append(x[B])
for T in TR:
    s=counter(tin[T],3,('c',T)); clauses += [[s[1]],[-s[3]],[-s[2],d[T]],[s[2],-d[T]]]
# E structure: 1-2 is an E edge; z=2 adjacent to the A points; every other point has one E neighbour.
clauses += CardEnc.equals(lits=list(isA.values()), bound=4, vpool=pool, encoding=EncType.seqcounter).clauses
for (u,v),m in mt.items(): clauses += [[-m,-isA[u]],[-m,-isA[v]]]
for v in range(3,17):
    partners=[mt[tuple(sorted((u,v)))] for u in range(3,17) if u!=v]
    clauses += CardEnc.atmost(lits=partners, bound=1, vpool=pool, encoding=EncType.pairwise).clauses
    clauses.append([isA[v]]+partners)      # M point has a partner
def inE(p):
    u,v=p
    if p==(1,2): return True
    if u==1: return False
    if u==2: return isA[v]
    return mt[p]
for p in PR:
    lits=[d[T] for T in TR if set(p)<=set(T)]
    c=counter(lits,5,('p',p)); e=inE(p)
    clauses.append([c[1]])
    if e is True: clauses += [[c[4]],[-c[5]]]
    elif e is False: clauses.append([-c[2]])
    else: clauses += [[-e,c[4]],[-e,-c[5]],[e,-c[2]]]
# ---- run_case.py lines 75-77 verbatim ----
with open(cnf_path,'w') as f:
    f.write(f'p cnf {pool.top} {len(clauses)}\n')
    for c in clauses: f.write(' '.join(map(str,c))+' 0\n')
# ---- not in run_case.py: report the file ----
print(json.dumps({'link_file':os.path.basename(link_file),'vars':pool.top,'clauses':len(clauses),
                  'cnf_bytes':os.path.getsize(cnf_path),
                  'cnf_sha256':hashlib.sha256(open(cnf_path,'rb').read()).hexdigest()}), flush=True)
