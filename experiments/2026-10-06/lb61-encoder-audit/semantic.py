# Document:    CNF End-to-End Meaning Test
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      e016fcd3c8bf5d81902df59abb94c71088a942118e704533d755f68206ec8dbb
# Chain:       solana-mainnet
# Tx:          3kPDBfi5bFHLTdD5QVqRAa42FojRxu3pG999dMgkMf19F6TZuetNqcFxbEmyNRrGRtgFHnetYXEPccmQNzzqocRa
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

# semantic.py: end-to-end meaning test of the generated CNF (identical to the certified one).
# For random primary assignments (x, d, isA, m), extend to the auxiliaries canonically
# (counter aux = "at least j of the first i+1 literals"; seqcounter aux from a tiny solve of the
# 160 exactly-4 clauses alone), evaluate all 512,424 clauses, and compare the set of violated
# constraints (keyed by triple, pair, point, block) with the set predicted by the intended
# combinatorial predicates. Equality on every trial means each clause family states exactly
# its intended property, and that a real cover's canonical extension violates nothing.
import sys, random, numpy as np
from itertools import combinations
sys.path.insert(0, __file__.rsplit('/',1)[0])
from instrument import build
from pysat.solvers import Solver

def norm(fam,key):
    if fam.startswith('tri'): return ('tri',key)
    if fam.startswith('pair'): return ('pair',key)
    return (fam,key)

def run(cls, trials, seed):
    rng=random.Random(seed)
    r=build(cls); pool=r['pool']; top=pool.top
    x,d,isA,mt=r['x'],r['d'],r['isA'],r['mt']; TR,PR,BLOCKS=r['TR'],r['PR'],r['BLOCKS']
    linkset=set(r['link'])
    cl=r['clauses']; W=max(len(c) for c in cl)
    M=np.zeros((len(cl),W),dtype=np.int64)
    for i,c in enumerate(cl): M[i,:len(c)]=c
    absM=np.abs(M); neg=M<0; pad=M==0
    keys=[norm(f,k) for f,k in r['tags']]
    ex4=[c for c,(f,k) in zip(cl,r['tags']) if f=='ex4']
    ex4s=Solver(name='minisat22',bootstrap_with=ex4)
    (ex4lo,ex4hi),=r['ranges']['ex4']
    ctr=[(tag,lits,K) for tag,(lits,K) in r['counters'].items()]
    auxid={tag:np.array([[pool.obj2id[(tag,i,j)] for j in range(1,K+1)] for i in range(len(lits))]) for tag,lits,K in ctr}
    tri_blocks={T:[B for B in BLOCKS if set(T)<=set(B)] for T in TR}
    pair_tr={p:[T for T in TR if set(p)<=set(T)] for p in PR}
    pts=list(range(3,17))
    stats={'trials':0,'mismatch':0,'violations_seen':{}}
    for t in range(trials):
        val=np.zeros(top+1,dtype=bool)
        q=rng.choice([0.004,0.01,0.014,0.02,0.03]); flipfix=rng.random()<0.2
        X={}
        for B in BLOCKS:
            X[B]= (B in linkset) if 1 in B else (rng.random()<q)
        if flipfix:
            B=rng.choice([B for B in BLOCKS if 1 in B]); X[B]=not X[B]
        mu={T:sum(X[B] for B in tri_blocks[T]) for T in TR}
        pf=rng.choice([0,0.005,0.02])
        D={T:(mu[T]==2)^(rng.random()<pf) for T in TR}
        if rng.random()<0.85: Aset=set(rng.sample(pts,4))
        else: Aset={v for v in pts if rng.random()<rng.choice([0.2,0.3,0.5])}
        rest=[v for v in pts if v not in Aset]; rng.shuffle(rest)
        Mset={tuple(sorted(rest[i:i+2])) for i in range(0,len(rest)-1,2)}
        for _ in range(rng.choice([0,0,1,2])):
            p=tuple(sorted(rng.sample(pts,2)))
            Mset^={p}
        for B in BLOCKS: val[x[B]]=X[B]
        for T in TR: val[d[T]]=D[T]
        for v in pts: val[isA[v]]= v in Aset
        for p in mt: val[mt[p]]= p in Mset
        # canonical counter aux
        for tag,lits,K in ctr:
            cs=np.cumsum(val[np.array(lits)].astype(np.int64))
            val[auxid[tag]] = cs[:,None] >= np.arange(1,K+1)[None,:]
        # seqcounter aux: any extension if one exists
        asm=[isA[v] if v in Aset else -isA[v] for v in pts]
        if ex4s.solve(assumptions=asm):
            for lit in ex4s.get_model():
                if ex4lo<=abs(lit)<=ex4hi: val[abs(lit)]= lit>0   # only the seqcounter's own aux ids
        lv=val[absM]^neg; lv[pad]=False
        sat=lv.any(axis=1)
        got={keys[i] for i in np.nonzero(~sat)[0]}
        # predicted
        pred=set()
        for B in BLOCKS:
            if 1 in B and X[B]!=(B in linkset): pred.add(('fixed',B))
        for T in TR:
            if not (1<=mu[T]<=2 and D[T]==(mu[T]==2)): pred.add(('tri',T))
        if len(Aset)!=4: pred.add(('ex4',()))
        for (u,v) in mt:
            if (u,v) in Mset and (u in Aset or v in Aset): pred.add(('m_excl',(u,v)))
        for v in pts:
            k=sum(1 for p in Mset if v in p)
            if k>1: pred.add(('m_amo',v))
            if v not in Aset and k==0: pred.add(('m_alo',v))
        def E(p):
            if p==(1,2): return True
            if p[0]==1: return False
            if p[0]==2: return p[1] in Aset
            return p in Mset
        for p in PR:
            cnt=sum(D[T] for T in pair_tr[p])
            if cnt!=(4 if E(p) else 1): pred.add(('pair',p))
        stats['trials']+=1
        if got!=pred:
            stats['mismatch']+=1
            print('MISMATCH', cls, t, sorted(got-pred)[:5], sorted(pred-got)[:5])
        for k in got: stats['violations_seen'][k[0]]=stats['violations_seen'].get(k[0],0)+1
    ex4s.delete()
    return stats

if __name__=='__main__':
    n=int(sys.argv[1])
    for i,cls in enumerate(sys.argv[2:]):
        print(cls, run(cls,n,1000+i), flush=True)
