# Document:    Certified 61-Block Fixed-Link Runs
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-05
# SHA256:      2f004e558c1dbb0a5a10aedb5b259322f672db56481aa5e6836e3d3b20587480
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild the fixed-link 61-block CNF (encoder copied verbatim from the probe
lb61_link), write it as DIMACS, solve with Lingeling while logging a DRAT proof,
and check the proof with drat-trim. Usage: run_case.py CLASS_FILE OUT_DIR."""
# ruff: noqa
import sys, time, json, subprocess, hashlib, os
from itertools import combinations
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver
cls, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=False)
link=[tuple(map(int,l.split())) for l in open(f'experiments/2026-10-03/link-classification/{cls}') if l.strip()]
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

cnf_path=os.path.join(out,'case.cnf'); proof_path=os.path.join(out,'case.drat')
with open(cnf_path,'w') as f:
    f.write(f'p cnf {pool.top} {len(clauses)}\n')
    for c in clauses: f.write(' '.join(map(str,c))+' 0\n')
t=time.time()
with Solver(name='lingeling', bootstrap_with=clauses, with_proof=True) as sv:
    result=sv.solve(); proof=sv.get_proof() if result is False else []
solve_s=time.time()-t
with open(proof_path,'w') as f:
    f.write('\n'.join(proof)+('\n' if proof else ''))
h=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
record={'class':cls,'vars':pool.top,'clauses':len(clauses),'result':result,'solve_seconds':solve_s,
        'proof_lines':len(proof),'cnf_sha256':h(cnf_path),'proof_sha256':h(proof_path)}
json.dump(record, open(os.path.join(out,'solve.json'),'w'), indent=1)
print(json.dumps(record), flush=True)
if result is False:
    t=time.time()
    r=subprocess.run([os.path.expanduser('~/.local/src/drat-trim/drat-trim'), cnf_path, proof_path, '-t', '1000000'],
                     capture_output=True, text=True)
    open(os.path.join(out,'drat-trim.log'),'w').write(r.stdout+r.stderr)
    verdict=[l for l in r.stdout.splitlines() if l.startswith('s ')]
    record.update(check_seconds=time.time()-t, drat_trim=verdict)
    json.dump(record, open(os.path.join(out,'solve.json'),'w'), indent=1)
    print(json.dumps(record), flush=True)
