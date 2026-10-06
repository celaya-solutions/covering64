/*
 * Document:    Parallel Labeled (15,4,2) Covering Enumerator
 * Version:     v1.0.0
 * Author:      Celaya Solutions
 * Contact:     hello@celayasolutions.com
 * Date:        2026-10-06
 * SHA256:      1d7a3924201e0a333da4d55e14ab6a1fde4a4ecd6d21e8738c05c27c836d381b
 * Chain:       solana-mainnet
 * Tx:          4oQBwwVJQ5HvJHbHSFtnrmcA7Sa7wn2E2CA27dvVRYNLrzWY6sDTRn8JfRycFdy5pcS9dxPy9Wq5P8y7Pakznwtg
 * License:     CC BY 4.0 / Celaya Solutions
 */
/*
 * enum_par.c: enum.c with a deterministic K-way split, for running K
 * processes in parallel. Enumerates ALL labeled "standard" minimum
 * (15,4,2) coverings.
 *
 * Build: cc -O2 -o enum_par enum_par.c
 * Usage: ./enum_par OUT.bin MODE K k [SPLIT_LEVEL]
 *   MODE 0: branch on the most constrained pair (described below);
 *   MODE 1: branch on the lowest-index pair with remaining demand.
 *   run_enum.sh starts the K workers and sums their logs.
 *
 * Points 0..14. A standard covering is a set of 19 distinct 4-subsets in
 * which every pair is covered exactly m(pair) times, where m = 2 on the
 * nine excess pairs {0,1},{0,2},{0,3},{0,4},{5,6},{7,8},{9,10},{11,12},
 * {13,14} and m = 1 on the other 96 pairs.
 *
 * Method: exact cover with multiplicities. At each node pick the pair e
 * with remaining demand r > 0 that has the fewest r-subsets of valid
 * candidate quadruples (a quadruple is valid if every one of its 6 pairs
 * still has remaining demand >= 1), and branch over all r-subsets of
 * valid quadruples containing e (chosen in increasing index order, the
 * second one checked against the state after the first). After the branch
 * e is fully satisfied, so each solution is produced exactly once.
 *
 * Parallel split: argv[3]=K workers, argv[4]=k; branch-decision nodes at level
 * argv[5] (default 3) are numbered in DFS order and worker k keeps those
 * numbered = k mod K. Every worker walks the same deterministic tree above
 * the split level, so the K outputs partition the solution set.
 *
 * Output: binary file of uint16 point masks, 19 per solution (in the order
 * chosen). Prints count, node count, time.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

typedef unsigned __int128 u128;

#define NP 15
#define NPAIR 105
#define NQ 1365
#define NB 19

static int pid[NP][NP];
static int qpairs[NQ][6];
static u128 qmask[NQ];
static uint16_t qpts[NQ];
static int plist[NPAIR][78];
static int pcnt[NPAIR];
static int rem[NPAIR];
static u128 zmask; /* pairs with rem == 0 */
static int stack_[NB + 2];
static int depth;
static long long nsol, nodes;
static FILE *out;
static int order_mode; /* 0 = most constrained, 1 = lowest-index pair */
static int nworkers = 1, worker = 0, split_level = 3; static long long split_ctr; static int level;

static inline void apply(int q) {
    for (int k = 0; k < 6; k++) {
        int p = qpairs[q][k];
        if (--rem[p] == 0) zmask |= ((u128)1) << p;
    }
    stack_[depth++] = q;
}
static inline void unapply(int q) {
    for (int k = 0; k < 6; k++) {
        int p = qpairs[q][k];
        if (rem[p]++ == 0) zmask &= ~(((u128)1) << p);
    }
    depth--;
}
static inline int valid(int q) { return (qmask[q] & zmask) == 0; }

static void dfs(void) {
    if (level == split_level) { if ((split_ctr++ % nworkers) != worker) return; }
    nodes++;
    int best = -1;
    long best_metric = 1L << 40;
    int any = 0;
    for (int e = 0; e < NPAIR; e++) {
        if (rem[e] == 0) continue;
        any = 1;
        int c = 0;
        for (int i = 0; i < pcnt[e]; i++) c += valid(plist[e][i]);
        if (c < rem[e]) return; /* dead end */
        long metric = (rem[e] == 1) ? c : (long)c * (c - 1) / 2;
        if (order_mode == 1) { best = e; break; }
        if (metric < best_metric) { best_metric = metric; best = e; }
    }
    if (!any) {
        if (depth != NB) { fprintf(stderr, "bad depth %d\n", depth); exit(1); }
        nsol++;
        uint16_t buf[NB];
        for (int i = 0; i < NB; i++) buf[i] = qpts[stack_[i]];
        if (out) fwrite(buf, sizeof(uint16_t), NB, out);
        return;
    }
    int e = best;
    if (rem[e] == 1) {
        for (int i = 0; i < pcnt[e]; i++) {
            int q = plist[e][i];
            if (!valid(q)) continue;
            apply(q); level++; dfs(); level--; unapply(q);
        }
    } else if (rem[e] == 2) {
        for (int i = 0; i < pcnt[e]; i++) {
            int q = plist[e][i];
            if (!valid(q)) continue;
            apply(q);
            for (int j = i + 1; j < pcnt[e]; j++) {
                int q2 = plist[e][j];
                if (!valid(q2)) continue;
                apply(q2); level++; dfs(); level--; unapply(q2);
            }
            unapply(q);
        }
    } else {
        fprintf(stderr, "unexpected demand %d\n", rem[e]); exit(1);
    }
}

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : NULL;
    order_mode = argc > 2 ? atoi(argv[2]) : 0;
    if (argc > 4) { nworkers = atoi(argv[3]); worker = atoi(argv[4]); }
    if (argc > 5) split_level = atoi(argv[5]);
    int n = 0;
    for (int a = 0; a < NP; a++)
        for (int b = a + 1; b < NP; b++) { pid[a][b] = pid[b][a] = n++; }
    int q = 0;
    for (int a = 0; a < NP; a++) for (int b = a + 1; b < NP; b++)
    for (int c = b + 1; c < NP; c++) for (int d = c + 1; d < NP; d++) {
        int pts[4] = {a, b, c, d};
        int k = 0;
        qmask[q] = 0;
        qpts[q] = (uint16_t)((1u << a) | (1u << b) | (1u << c) | (1u << d));
        for (int x = 0; x < 4; x++) for (int y = x + 1; y < 4; y++) {
            int p = pid[pts[x]][pts[y]];
            qpairs[q][k++] = p;
            qmask[q] |= ((u128)1) << p;
            plist[p][pcnt[p]++] = q;
        }
        q++;
    }
    if (q != NQ) { fprintf(stderr, "nq %d\n", q); return 1; }
    for (int p = 0; p < NPAIR; p++) {
        if (pcnt[p] != 78) { fprintf(stderr, "pcnt\n"); return 1; }
        rem[p] = 1;
    }
    int ex[9][2] = {{0,1},{0,2},{0,3},{0,4},{5,6},{7,8},{9,10},{11,12},{13,14}};
    int tot = 0;
    for (int i = 0; i < 9; i++) rem[pid[ex[i][0]][ex[i][1]]] = 2;
    for (int p = 0; p < NPAIR; p++) tot += rem[p];
    if (tot != 6 * NB) { fprintf(stderr, "demand total %d\n", tot); return 1; }
    zmask = 0; depth = 0;
    if (path) { out = fopen(path, "wb"); if (!out) { perror("open"); return 1; } }
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    dfs();
    clock_gettime(CLOCK_MONOTONIC, &t1);
    if (out) fclose(out);
    double sec = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    printf("worker=%d/%d split=%d splitnodes=%lld order_mode=%d solutions=%lld nodes=%lld time=%.3fs\n", worker, nworkers, split_level, split_ctr, order_mode, nsol, nodes, sec);
    return 0;
}
