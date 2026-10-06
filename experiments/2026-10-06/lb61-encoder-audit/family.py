# Document:    CNF Family Counts and Variable Ownership
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      6dc044564c9da4d9cea11eccb8c14499b5f611bf90139b3e93b5c94c65975414
# Chain:       solana-mainnet
# Tx:          2p8RuYig9Y1XXCYsCb73jQqZcZ7dhGqJ7C8kmCyr6jvTxs4iT9hBADxfGTkUNoEfQvodpsZDVAYcfY3kRUjAn96s
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

# family.py: per-family variable and clause counts, plus a variable-ownership (no id collision) check.
import sys, json
from itertools import combinations
sys.path.insert(0, __file__.rsplit('/',1)[0])
from instrument import build

def run(cls):
    r=build(cls); pool=r['pool']; x,d,isA,mt=r['x'],r['d'],r['isA'],r['mt']
    clauses,tags=r['clauses'],r['tags']
    # id -> owner
    owner={}
    for obj,i in pool.obj2id.items():
        if obj[0] in ('x','d','A','m'): owner[i]=('prim',obj[0],obj[1])
        else: owner[i]=('aux',obj[0])          # obj = (tag,i,j), tag=('c',T) or ('p',p)
    for fam,rs in r['ranges'].items():
        for lo,hi in rs:
            for i in range(lo,hi+1):
                if i not in owner: owner[i]=('aux',('card',fam))
    assert sorted(owner)==list(range(1,pool.top+1)), 'gap or overlap in ids'
    # ranges must be disjoint
    allr=sorted((lo,hi,f) for f,rs in r['ranges'].items() for lo,hi in rs)
    for (a,b,f),(c,e,g) in zip(allr,allr[1:]): assert b<c,(f,g)
    # ownership/locality check per clause
    def allowed(fam,key):
        if fam=='fixed': return {x[key]}, set()
        if fam.startswith('tri'): return {x[B] for B in r['BLOCKS'] if set(key)<=set(B)}|{d[key]}, {('c',key)}
        if fam=='ex4': return set(isA.values()), {('card','ex4')}
        if fam=='m_excl': return {mt[key],isA[key[0]],isA[key[1]]}, set()
        if fam=='m_amo': return {mt[tuple(sorted((u,key)))] for u in range(3,17) if u!=key}, set()
        if fam=='m_alo': return {mt[tuple(sorted((u,key)))] for u in range(3,17) if u!=key}|{isA[key]}, set()
        if fam.startswith('pair'):
            e=r['inE'](key); s={d[T] for T in r['TR'] if set(key)<=set(T)}
            if e not in (True,False): s.add(e)
            return s, {('p',key)}
        raise ValueError(fam)
    bad=0; cache={}
    for cl,(fam,key) in zip(clauses,tags):
        k=(fam if not fam.startswith(('tri','pair')) else fam.split('_')[0]+fam[-3:] , key)
        if (fam,key) not in cache: cache[(fam,key)]=allowed(fam,key)
        prim,auxo=cache[(fam,key)]
        for lit in cl:
            o=owner[abs(lit)]
            if o[0]=='prim':
                if abs(lit) not in prim: bad+=1
            else:
                if o[1] not in auxo: bad+=1
    # family table
    fixed_ids={x[B] for B in x if 1 in B}
    rows=[]
    def ncl(prefixes): return sum(1 for f,_ in tags if f in prefixes)
    def nr(fam): return sum(hi-lo+1 for lo,hi in r['ranges'].get(fam,[]))
    rows.append(('fixed blocks through point 1 (x_B, 1 in B)', len(fixed_ids), ncl({'fixed'})))
    rows.append(('free block variables (x_B, 1 not in B)', len(x)-len(fixed_ids), 0))
    rows.append(('per-triple: d_T', len(d), 0))
    rows.append(('per-triple: counter aux (K=3, 78 lits)', nr('tri'), ncl({'tri_ctr'})))
    rows.append(('per-triple: mu in {1,2}, d <-> mu=2', 0, ncl({'tri_out'})))
    rows.append(('exactly-4 A among 3..16 (isA + seqcounter aux)', len(isA)+nr('ex4'), ncl({'ex4'})))
    rows.append(('matching vars m_uv (3<=u<v<=16)', len(mt)+nr('match'), 0))
    rows.append(('matching: exclusion m_uv -> not A_u, not A_v', 0, ncl({'m_excl'})))
    rows.append(('matching: at most one partner (pairwise)', 0, ncl({'m_amo'})))
    rows.append(('matching: A_v or some partner', 0, ncl({'m_alo'})))
    for t,name in (('12','(1,2)  [1 pair, E]'),('1v','(1,v)  [14 pairs, non-E]'),('2v','(2,v)  [14 pairs, E iff A_v]'),('in','(u,v) in 3..16  [91 pairs, E iff m_uv]')):
        rows.append((f'per-pair {name}: counter (K=5, 14 lits)', nr('pair_'+t), ncl({'pair_ctr_'+t})))
        rows.append((f'per-pair {name}: output', 0, ncl({'pair_out_'+t})))
    tv=sum(a for _,a,_ in rows); tc=sum(b for _,_,b in rows)
    return dict(cls=cls, rows=rows, total_vars=tv, total_clauses=tc, pool_top=pool.top, n_clauses=len(clauses),
                bad_literals=bad, ranges={k:v[:1]+(['...',v[-1]] if len(v)>1 else []) for k,v in r['ranges'].items()},
                ex4_aux=nr('ex4'), ex4_clauses=ncl({'ex4'}))

if __name__=='__main__':
    for cls in sys.argv[1:]:
        o=run(cls)
        print('==',cls,'pool.top',o['pool_top'],'clauses',o['n_clauses'],'sum vars',o['total_vars'],'sum clauses',o['total_clauses'],'bad literals',o['bad_literals'])
        if cls==sys.argv[1]:
            for name,a,b in o['rows']: print(f'| {name} | {a:,} | {b:,} |')
            print(o['ranges'])
