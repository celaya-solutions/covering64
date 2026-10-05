// Document:    Exact Enumeration of the Degree-20 Point's Link
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-05
// SHA256:      8943866a03d032eac77af0025aa96f0175c1842e615d11ca8e539fea926776ee
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
//
// For one graph X_z, list every set of 20 distinct quadruples on points 1..15
// that covers each pair exactly 1 + [pair in X_z] times, such that for every
// A-point a (11..15) some chosen quadruple contains a and three of a's four
// X_z-neighbours (Lemma 5, hub rule). Branching takes the open pair with the
// fewest candidate quadruples; child i selects candidate i and excludes the
// earlier candidates, so every solution is reached exactly once.
//
// Input (stdin): 15 lines "u v" giving the X_z edges. Arguments: seconds, and
// "nohub" to drop the hub rule (positive controls only).
// Output: one line per solution with the 20 quadruple indices (lexicographic
// order of 4-subsets of 1..15), then a final "DONE nodes solutions" or
// "TIMEOUT nodes solutions" line.

#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

namespace {

constexpr int kPoints = 15;
constexpr int kPairs = 105;
constexpr int kQuads = 1365;
constexpr int kWords = (kQuads + 63) / 64;
using Bits = std::array<uint64_t, kWords>;

int pair_index[16][16];
std::array<std::array<int, 4>, kQuads> quad_points;
std::array<std::array<int, 6>, kQuads> quad_pairs;
std::array<Bits, kPairs> rows_of_pair;
int demand[kPairs];
bool is_a[16];
bool neighbour[16][16];
long long nodes = 0, solutions = 0;
std::chrono::steady_clock::time_point deadline;
bool timed_out = false;
bool use_hub_rule = true;
std::vector<int> chosen;

inline void set_bit(Bits& b, int i) { b[i >> 6] |= uint64_t{1} << (i & 63); }
inline bool test_bit(const Bits& b, int i) { return (b[i >> 6] >> (i & 63)) & 1; }

int count_and(const Bits& a, const Bits& b) {
  int total = 0;
  for (int w = 0; w < kWords; ++w) total += __builtin_popcountll(a[w] & b[w]);
  return total;
}

// Hub rule for every A-point whose six quadruples are all chosen.
bool hub_ok() {
  if (!use_hub_rule) return true;
  for (int a = 11; a <= 15; ++a) {
    int through = 0;
    bool good = false;
    for (int q : chosen) {
      const auto& p = quad_points[q];
      bool has = false;
      int leaves = 0;
      for (int x : p) {
        if (x == a) has = true;
      }
      if (!has) continue;
      ++through;
      for (int x : p) {
        if (x != a && neighbour[a][x]) ++leaves;
      }
      if (leaves == 3) good = true;
    }
    if (through == 6 && !good) return false;
  }
  return true;
}

void search(int residual[kPairs], Bits& available) {
  ++nodes;
  if ((nodes & 0xFFFF) == 0 && std::chrono::steady_clock::now() > deadline) timed_out = true;
  if (timed_out) return;
  int best = -1, best_count = 1 << 30;
  for (int p = 0; p < kPairs; ++p) {
    if (residual[p] == 0) continue;
    int count = count_and(rows_of_pair[p], available);
    if (count < residual[p]) return;
    if (count < best_count) {
      best_count = count;
      best = p;
    }
  }
  if (best < 0) {
    if (chosen.size() == 20 && hub_ok()) {
      ++solutions;
      for (size_t i = 0; i < chosen.size(); ++i) std::printf(i ? " %d" : "%d", chosen[i]);
      std::printf("\n");
    }
    return;
  }
  std::vector<int> candidates;
  for (int q = 0; q < kQuads; ++q) {
    if (test_bit(available, q) && test_bit(rows_of_pair[best], q)) candidates.push_back(q);
  }
  Bits excluded = available;
  for (int q : candidates) {
    // child: select q, exclude every earlier candidate (already cleared from `excluded`)
    Bits child = excluded;
    child[q >> 6] &= ~(uint64_t{1} << (q & 63));
    int saved[6];
    bool ok = true;
    for (int k = 0; k < 6; ++k) {
      int p = quad_pairs[q][k];
      saved[k] = residual[p];
      residual[p] -= 1;
      if (residual[p] < 0) ok = false;
    }
    if (ok) {
      for (int k = 0; k < 6; ++k) {
        int p = quad_pairs[q][k];
        if (residual[p] == 0) {
          for (int w = 0; w < kWords; ++w) child[w] &= ~rows_of_pair[p][w];
        }
      }
      chosen.push_back(q);
      if (hub_ok()) search(residual, child);
      chosen.pop_back();
    }
    for (int k = 0; k < 6; ++k) residual[quad_pairs[q][k]] = saved[k];
    if (timed_out) return;
    excluded[q >> 6] &= ~(uint64_t{1} << (q & 63));
  }
}

}  // namespace

int main(int argc, char** argv) {
  double seconds = argc > 1 ? std::atof(argv[1]) : 3600.0;
  if (argc > 2 && std::strcmp(argv[2], "nohub") == 0) use_hub_rule = false;
  deadline = std::chrono::steady_clock::now() +
             std::chrono::milliseconds(static_cast<long long>(seconds * 1000));
  int index = 0;
  for (int u = 1; u <= kPoints; ++u)
    for (int v = u + 1; v <= kPoints; ++v) pair_index[u][v] = pair_index[v][u] = index++;
  index = 0;
  for (int a = 1; a <= kPoints; ++a)
    for (int b = a + 1; b <= kPoints; ++b)
      for (int c = b + 1; c <= kPoints; ++c)
        for (int d = c + 1; d <= kPoints; ++d) {
          quad_points[index] = {a, b, c, d};
          int pts[4] = {a, b, c, d}, k = 0;
          for (int i = 0; i < 4; ++i)
            for (int j = i + 1; j < 4; ++j) quad_pairs[index][k++] = pair_index[pts[i]][pts[j]];
          ++index;
        }
  for (auto& bits : rows_of_pair) bits.fill(0);
  for (int q = 0; q < kQuads; ++q)
    for (int p : quad_pairs[q]) set_bit(rows_of_pair[p], q);
  for (int p = 0; p < kPairs; ++p) demand[p] = 1;
  for (int a = 11; a <= 15; ++a) is_a[a] = true;
  int u, v, edges = 0;
  while (std::scanf("%d %d", &u, &v) == 2) {
    demand[pair_index[u][v]] = 2;
    neighbour[u][v] = neighbour[v][u] = true;
    ++edges;
  }
  if (edges != 15) {
    std::fprintf(stderr, "expected 15 X_z edges, got %d\n", edges);
    return 2;
  }
  Bits available;
  available.fill(0);
  for (int q = 0; q < kQuads; ++q) set_bit(available, q);
  int residual[kPairs];
  for (int p = 0; p < kPairs; ++p) residual[p] = demand[p];
  search(residual, available);
  std::printf("%s %lld %lld\n", timed_out ? "TIMEOUT" : "DONE", nodes, solutions);
  return timed_out ? 1 : 0;
}
