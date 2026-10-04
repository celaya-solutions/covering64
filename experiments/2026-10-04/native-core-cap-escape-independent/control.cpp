// Document:    Independent Native Core Transition Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      f463c01621167f785cb0048bcc707466ef0c62181cdbb224440302f808ba93d2
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_CORE_NO_MAIN
#include "search.cpp"
#include "expected.hpp"

void demand(bool good, const char* detail) {
  if (!good) throw std::runtime_error(detail);
}

CoreCounts recounted(const State& s) {
  CoreCounts result{};
  for (int id : s.ids) for (int c = 0; c < 3; ++c)
    result[c] += bool(EXPECTED_MEMBERSHIP[id] & (1 << c));
  return result;
}

void independent_state(const State& s, const std::vector<int>& heavy, CoreCounts cores) {
  demand(s.ids.size() == 64, "cardinality");
  std::array<bool,4368> selected{};
  std::array<int,560> counts{};
  for (int id : s.ids) {
    demand(id >= 0 && id < 4368 && !selected[id], "distinct range");
    selected[id] = true;
    for (int t = 0; t < 560; ++t)
      counts[t] += (EXPECTED_BLOCKS[id] & EXPECTED_TRIPLES[t]) == EXPECTED_TRIPLES[t];
  }
  int holes = 0;
  std::vector<int> expected_heavy;
  for (int t = 0; t < 560; ++t) {
    holes += counts[t] == 0;
    if (counts[t] >= 6) expected_heavy.push_back(t);
    demand(s.weight[t] == 1, "weight changed");
  }
  auto sorted = heavy;
  std::sort(sorted.begin(), sorted.end());
  demand(counts == s.count && selected == s.selected && holes == s.deficit, "state recount");
  demand(sorted == expected_heavy && cores == recounted(s), "auxiliary recount");
  for (int c : cores) demand(c >= 0 && c <= 55, "cap");
}

bool same(const State& a, const State& b) {
  return a.ids == b.ids && a.count == b.count && a.weight == b.weight &&
         a.selected == b.selected && a.deficit == b.deficit;
}

State boundary(int c, int count, int old, int next) {
  std::vector<int> ids{old};
  int have = bool(EXPECTED_MEMBERSHIP[old] & (1 << c));
  for (int id = 0; have < count && id < 4368; ++id)
    if (id != old && id != next && (EXPECTED_MEMBERSHIP[id] & (1 << c))) {
      ids.push_back(id); ++have;
    }
  for (int id = 0; ids.size() < 64 && id < 4368; ++id)
    if (id != old && id != next && EXPECTED_MEMBERSHIP[id] == 0) ids.push_back(id);
  demand(ids.size() == 64 && have == count, "boundary construction");
  return State(ids);
}

int main() {
  try {
    universe(); initialize_cores();
    demand(blocks.size() == 4368 && triples.size() == 560, "universe size");
    std::array<std::vector<int>,8> patterns;
    for (int i = 0; i < 4368; ++i) {
      demand(blocks[i].mask == EXPECTED_BLOCKS[i], "block lexicographic order");
      for (int c = 0; c < 3; ++c)
        demand(core_member[c][i] == bool(EXPECTED_MEMBERSHIP[i] & (1 << c)), "membership");
      patterns[EXPECTED_MEMBERSHIP[i]].push_back(i);
    }
    for (int t = 0; t < 560; ++t) demand(triples[t] == EXPECTED_TRIPLES[t], "triple order");
    unsigned cases=0, rejects=0, commits=0, rollbacks=0;
    for (int c=0; c<3; ++c) for (int amount : {54,55})
      for (int a=0; a<8; ++a) for (int b=0; b<8; ++b) {
        if (patterns[a].empty() || patterns[b].empty() || (a==b && patterns[a].size()<2)) continue;
        int old=patterns[a][0], next=patterns[b][a==b ? 1 : 0];
        State s=boundary(c,amount,old,next);
        auto heavy=heavy_ids(s); auto counts=recounted(s);
        independent_state(s,heavy,counts);
        demand(counts[c]==amount && !s.selected[next], "boundary precondition");
        const State before=s; const auto before_heavy=heavy; const auto before_counts=counts;
        auto proposed=proposed_core_counts(counts,old,next);
        State oracle=s; oracle.move(0,next);
        demand(proposed==recounted(oracle), "three simultaneous deltas");
        bool expected=true;
        for (int value : proposed) expected &= value>=0 && value<=55;
        demand(core_caps_pass(proposed)==expected, "cap predicate");
        if (!core_caps_pass(proposed)) {
          demand(same(s,before) && heavy==before_heavy && counts==before_counts, "pre-move rejection");
          ++rejects;
        } else {
          s.move(0,next); update_heavy(heavy,s,old,next);
          if (cases%2) {
            s.move(0,old); update_heavy(heavy,s,old,next);
            auto x=heavy, y=before_heavy; std::sort(x.begin(),x.end()); std::sort(y.begin(),y.end());
            demand(same(s,before) && x==y && counts==before_counts, "energy rollback");
            ++rollbacks;
          } else { counts=proposed; ++commits; }
        }
        independent_state(s,heavy,counts);
        ++cases;
      }
    unsigned caps=0;
    for (int a : {-1,0,54,55,56,60}) for (int b : {-1,0,54,55,56,60})
      for (int c : {-1,0,54,55,56,60}) {
        bool expected=a>=0&&a<=55&&b>=0&&b<=55&&c>=0&&c<=55;
        demand(core_caps_pass({a,b,c})==expected, "joint cap predicate"); ++caps;
      }
    demand(cases==210 && rejects>0 && commits>0 && rollbacks>0, "control coverage");
    std::cout << "{\"passed\":true,\"cases\":" << cases << ",\"rejections\":" << rejects
              << ",\"commits\":" << commits << ",\"rollbacks\":" << rollbacks
              << ",\"joint_cap_vectors\":" << caps << ",\"optimizer_calls\":0}\n";
    return 0;
  } catch(const std::exception& e) { std::cerr << e.what() << '\n'; return 2; }
}
