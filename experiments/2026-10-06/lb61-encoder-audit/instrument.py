# Document:    Tagged Fixed-Link Encoder Build
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      8a0323444a21821c564316a2984ebc41f00a7cf57268ce3bcf1f7592160e58a6
# Chain:       solana-mainnet
# Tx:          2nJqGBQsPFhmAvPGYGmBVibZZJ1orbjR14MnXMRhWdpMBgpfgXMUj4sXQdie3anivKLLqGn7vB5WDBWYRtpVRGnN
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

# instrument.py: the encoder of run_case.py (lines 22-72) with bookkeeping lines inserted.
# Every original statement is kept in the same order; inserted lines are marked "# AUDIT".
# build(cls) returns the clause list plus, for every clause, a (family, key) tag, the id range
# of every family, and the metadata of every counter call. The only other change from
# run_case.py: the link file is found relative to this file (LINKS below), so build() works
# from any directory; cls is a file name such as shape-1-class-0.txt.
# usage: python instrument.py shape-1-class-0.txt ...  (prints vars, clauses and the SHA256
# of the DIMACS text built in memory, which must equal gen_cnf.py's file hash)
import sys, hashlib, json
from itertools import combinations
from pathlib import Path
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType

REPO = Path(__file__).resolve().parents[3]
LINKS = REPO / 'experiments' / '2026-10-03' / 'link-classification'


def build(cls):
    link=[tuple(map(int,l.split())) for l in open(LINKS / cls) if l.strip()]
    assert len(link)==19 and all(b[0]==1 for b in link)
    BLOCKS=list(combinations(range(1,17),5)); TR=list(combinations(range(1,17),3)); PR=list(combinations(range(1,17),2))
    pool=IDPool(); clauses=[]
    tags=[]                                   # AUDIT: tags[i] = (family, key) of clauses[i]
    counters={}                               # AUDIT: tag -> (lits, K)
    def tagto(fam,key):                       # AUDIT
        tags.extend([(fam,key)]*(len(clauses)-len(tags)))
    x={B:pool.id(('x',B)) for B in BLOCKS}; d={T:pool.id(('d',T)) for T in TR}
    isA={v:pool.id(('A',v)) for v in range(3,17)}
    mt={p:pool.id(('m',p)) for p in combinations(range(3,17),2)}
    primary_top=pool.top                      # AUDIT
    def counter(lits,K,tag):
        counters[tag]=(list(lits),K)          # AUDIT
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
    ranges={}                                 # AUDIT: family -> list of (lo,hi) new var ids
    def mark(fam,top0):                       # AUDIT
        if pool.top>top0: ranges.setdefault(fam,[]).append((top0+1,pool.top))
    linkset=set(link)
    for B in BLOCKS:
        if 1 in B: clauses.append([x[B]] if B in linkset else [-x[B]]); tagto('fixed',B)
    tin={T:[] for T in TR}
    for B in BLOCKS:
        for T in combinations(B,3): tin[T].append(x[B])
    for T in TR:
        t0=pool.top                           # AUDIT
        s=counter(tin[T],3,('c',T)); tagto('tri_ctr',T)
        clauses += [[s[1]],[-s[3]],[-s[2],d[T]],[s[2],-d[T]]]; tagto('tri_out',T)
        mark('tri',t0)
    t0=pool.top                               # AUDIT
    clauses += CardEnc.equals(lits=list(isA.values()), bound=4, vpool=pool, encoding=EncType.seqcounter).clauses
    tagto('ex4',()); mark('ex4',t0)
    t0=pool.top                               # AUDIT
    for (u,v),m in mt.items(): clauses += [[-m,-isA[u]],[-m,-isA[v]]]; tagto('m_excl',(u,v))
    for v in range(3,17):
        partners=[mt[tuple(sorted((u,v)))] for u in range(3,17) if u!=v]
        clauses += CardEnc.atmost(lits=partners, bound=1, vpool=pool, encoding=EncType.pairwise).clauses
        tagto('m_amo',v)
        clauses.append([isA[v]]+partners)      # M point has a partner
        tagto('m_alo',v)
    mark('match',t0)
    def inE(p):
        u,v=p
        if p==(1,2): return True
        if u==1: return False
        if u==2: return isA[v]
        return mt[p]
    def ptype(p):                             # AUDIT
        return '12' if p==(1,2) else '1v' if p[0]==1 else '2v' if p[0]==2 else 'in'
    for p in PR:
        t0=pool.top                           # AUDIT
        lits=[d[T] for T in TR if set(p)<=set(T)]
        c=counter(lits,5,('p',p)); e=inE(p)
        tagto('pair_ctr_'+ptype(p),p)
        clauses.append([c[1]])
        if e is True: clauses += [[c[4]],[-c[5]]]
        elif e is False: clauses.append([-c[2]])
        else: clauses += [[-e,c[4]],[-e,-c[5]],[e,-c[2]]]
        tagto('pair_out_'+ptype(p),p); mark('pair_'+ptype(p),t0)
    assert len(tags)==len(clauses)
    return dict(link=link, BLOCKS=BLOCKS, TR=TR, PR=PR, pool=pool, clauses=clauses, tags=tags,
                counters=counters, ranges=ranges, x=x, d=d, isA=isA, mt=mt, primary_top=primary_top, inE=inE)


def dimacs_sha(r):
    h=hashlib.sha256()
    h.update(f"p cnf {r['pool'].top} {len(r['clauses'])}\n".encode())
    for c in r['clauses']: h.update((' '.join(map(str,c))+' 0\n').encode())
    return h.hexdigest()


if __name__=='__main__':
    for cls in sys.argv[1:]:
        r=build(cls)
        print(json.dumps({'class':cls,'vars':r['pool'].top,'clauses':len(r['clauses']),'sha256':dimacs_sha(r)}))
