// Document:    Independent Fourth Core Partition Map Enumeration
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      f0cde07a6cf6c20fca3e47dbd524dcc5a06370fb4ae1d5662ff1006fe89bd1c2
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include "data.hpp"

std::array<int,5> assignment{0,1,2,3,4};
std::array<int,17> mapping{}, best_map{};
std::array<bool,65536> candidate{};
std::array<uint64_t,61> histogram{};
uint64_t maps=0;
int best=-1;

void enumerate(int group) {
  if (group==5) {
    int overlap=0;
    for (const auto& block : OLD_BLOCKS) {
      unsigned mask=0;
      for (int point : block) mask |= 1u << (mapping[point]-1);
      overlap += candidate[mask];
    }
    ++maps; ++histogram[overlap];
    if (overlap>best) { best=overlap; best_map=mapping; }
    return;
  }
  int target=assignment[group];
  std::array<int,3> order{NEW_TRIPLES[target][0],NEW_TRIPLES[target][1],NEW_TRIPLES[target][2]};
  do {
    for (int i=0;i<3;++i) mapping[OLD_TRIPLES[group][i]]=order[i];
    enumerate(group+1);
  } while (std::next_permutation(order.begin(),order.end()));
}

int main() {
  for (const auto& block : CANDIDATE) {
    unsigned mask=0;
    for (int point : block) mask |= 1u << (point-1);
    if (candidate[mask]) return 2;
    candidate[mask]=true;
  }
  mapping[OLD_UNUSED]=NEW_UNUSED;
  do { enumerate(0); } while (std::next_permutation(assignment.begin(),assignment.end()));
  if (maps!=933120) return 3;
  std::cout << "{\"maps\":" << maps << ",\"best\":" << best
            << ",\"best_map_count\":" << histogram[best] << ",\"map_images\":[";
  for (int p=1;p<=16;++p) { if(p!=1)std::cout<<','; std::cout<<best_map[p]; }
  std::cout << "],\"histogram\":[";
  for (int i=0;i<=60;++i) { if(i)std::cout<<','; std::cout<<histogram[i]; }
  std::cout << "],\"optimizer_calls\":0}\n";
}
