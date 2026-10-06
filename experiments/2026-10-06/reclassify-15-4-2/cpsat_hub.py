# Document:    CP-SAT Hub-Set Completion Count
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      e2b574fb5acecdd5ef4e95554f9b6de6c5bca99855357ccba89d019207bb9635
# Chain:       solana-mainnet
# Tx:          475vCHnJcDbTJe9xiqZcHE6yz6g41Jpj1m6WgsHHTi12cPh8Gt1xYyrzY7JMQEnvcprxaMGn8xJGVv9VauyHryzU
# License:     CC BY 4.0 / Celaya Solutions
# ruff: noqa

"""Second method: OR-Tools CP-SAT enumerate_all_solutions on hub-block sub-cases.

For each of the 206 G-orbit representatives H of labeled hub-block sets
(from hubsets.py), fix the six hub blocks and enumerate every completion
with CP-SAT. Since G maps completions of H bijectively onto completions of
gH, N = sum over reps of |orbit(H)| * #completions(H). Each rep's CP-SAT
solution set is also compared, as a set, with the DFS solutions whose hub
blocks are exactly H.

usage: cpsat_hub.py hubsets.npz dfs.npz [nproc]
"""
import sys, time, itertools
import numpy as np
from multiprocessing import Pool
from ortools.sat.python import cp_model
from common import QUADS, QMASK, PAIRS, PAIR_INDEX, DEMAND


class Collector(cp_model.CpSolverSolutionCallback):
    def __init__(self, x):
        super().__init__()
        self.x = x
        self.sols = []

    def on_solution_callback(self):
        ms = sorted(int(QMASK[i]) for i, v in enumerate(self.x) if self.Value(v))
        self.sols.append(tuple(ms))


QIDX = {int(m): i for i, m in enumerate(QMASK)}


def solve(hub_masks):
    t0 = time.time()
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(len(QUADS))]
    by_pair = [[] for _ in PAIRS]
    for i, q in enumerate(QUADS):
        for p in itertools.combinations(q, 2):
            by_pair[PAIR_INDEX[p]].append(x[i])
    for k, lits in enumerate(by_pair):
        m.Add(sum(lits) == int(DEMAND[k]))
    hub = set(int(h) for h in hub_masks)
    for i, q in enumerate(QUADS):
        if 0 in q:  # blocks through the hub: exactly the given six
            m.Add(x[i] == (1 if int(QMASK[i]) in hub else 0))
    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_workers = 1
    cb = Collector(x)
    st = s.Solve(m, cb)
    assert st in (cp_model.OPTIMAL, cp_model.INFEASIBLE), s.StatusName(st)
    return tuple(sorted(hub)), sorted(set(cb.sols)), len(cb.sols), time.time() - t0


if __name__ == "__main__":
    hs = np.load(sys.argv[1])
    reps, sizes = hs["reps"], hs["sizes"]
    dfs = np.load(sys.argv[2])["sols"]
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    # DFS solutions grouped by hub-block set
    hubpart = np.where((dfs & 1) == 1, dfs, 0)
    hubkey = {}
    for row, hrow in zip(dfs, hubpart):
        k = tuple(sorted(int(v) for v in hrow if v))
        hubkey.setdefault(k, []).append(tuple(int(v) for v in row))
    t0 = time.time()
    total = 0
    mism = 0
    rows = []
    with Pool(nproc) as pool:
        res = pool.map(solve, [list(r) for r in reps], chunksize=1)
    for (hub, sols, nraw, dt), size in zip(res, sizes):
        assert nraw == len(sols), "CP-SAT reported a duplicate solution"
        dset = sorted(hubkey.get(hub, []))
        same = (dset == sols)
        mism += (not same)
        total += int(size) * len(sols)
        rows.append((hub, int(size), len(sols), same, dt))
    nz = [r for r in rows if r[2] > 0]
    print("reps:", len(rows), " reps with completions:", len(nz))
    for hub, size, n, same, dt in nz:
        print("  hub", hub, "orbit size", size, "completions", n, "match DFS", same, "%.1fs" % dt)
    print("max CP-SAT time per rep %.1fs, sum %.1fs" % (max(r[4] for r in rows), sum(r[4] for r in rows)))
    print("set mismatches vs DFS:", mism)
    print("N from CP-SAT = sum |orbit(H)| * completions(H) =", total)
    print("wall %.1fs" % (time.time() - t0))
