// Document:    H6 Radius Four Deletion Upper Screen
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      42655c9f59a7a23c04416b6ad2f95ac22831649ca2178fe49dc5b314b24214d4
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Block = std::array<int, 5>;
using Cover = std::array<int, 10>;
using U64 = std::uint64_t;

int main(int argc, char** argv) {
  try {
    if (argc != 2) throw std::runtime_error("one pinned input path required");
    const auto start = std::chrono::steady_clock::now();
    auto elapsed = [&]() { return std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count(); };
    int tid[17][17][17] = {};
    std::vector<Block> blocks;
    std::vector<Cover> covers;
    std::vector<std::vector<int>> carriers;
    for (int a=1; a<=16; ++a) for (int b=a+1; b<=16; ++b)
      for (int c=b+1; c<=16; ++c) {
        tid[a][b][c] = static_cast<int>(carriers.size()); carriers.emplace_back();
      }
    for (int a=1; a<=16; ++a) for (int b=a+1; b<=16; ++b)
      for (int c=b+1; c<=16; ++c) for (int d=c+1; d<=16; ++d)
        for (int e=d+1; e<=16; ++e) blocks.push_back({a,b,c,d,e});
    for (int id=0; id<4368; ++id) {
      Cover q{}; int j=0;
      for (int a=0; a<5; ++a) for (int b=a+1; b<5; ++b)
        for (int c=b+1; c<5; ++c) {
          int t=tid[blocks[id][a]][blocks[id][b]][blocks[id][c]];
          q[j++]=t; carriers[t].push_back(id);
        }
      covers.push_back(q);
    }
    std::ifstream input(argv[1]);
    if (!input) throw std::runtime_error("input missing");
    std::vector<int> selected, counts(560), scores(4368);
    std::vector<bool> chosen(4368);
    std::string line;
    while (std::getline(input,line)) {
      std::istringstream row(line); Block b{}; std::string extra;
      for (int& p:b) if (!(row>>p)) throw std::runtime_error("malformed block");
      if (row>>extra) throw std::runtime_error("long block");
      auto found=std::lower_bound(blocks.begin(),blocks.end(),b);
      if (found==blocks.end() || *found!=b) throw std::runtime_error("invalid block");
      int id=static_cast<int>(found-blocks.begin());
      if (chosen[id] || (!selected.empty() && selected.back()>=id))
        throw std::runtime_error("duplicate or unsorted block");
      chosen[id]=true; selected.push_back(id);
      for (int t:covers[id]) ++counts[t];
    }
    if (selected.size()!=64) throw std::runtime_error("not exact64");
    int holes=0;
    for (int t=0; t<560; ++t) if (!counts[t]) {
      ++holes;
      for (int id:carriers[t]) if (!chosen[id]) ++scores[id];
    }
    if (holes!=6) throw std::runtime_error("not H6");
    std::array<int,11> histogram{};
    for (int id=0; id<4368; ++id) if (!chosen[id]) ++histogram[scores[id]];
    const auto initial_counts=counts, initial_scores=scores;
    const auto initial_histogram=histogram;
    auto change = [&](int id, bool remove) {
      for (int t:covers[id]) {
        const bool crossing=remove ? (--counts[t]==0) : (counts[t]++==0);
        if (!crossing) continue;
        holes += remove ? 1 : -1;
        for (int a:carriers[t]) if (!chosen[a]) {
          --histogram[scores[a]];
          scores[a] += remove ? 1 : -1;
          ++histogram[scores[a]];
        }
      }
    };
    U64 completed=0, excluded=0, survivors=0, tuples=0;
    int maximum_pool=0, minimum_pool=4369;
    std::map<int,U64> pool_histogram, floor_histogram, hole_histogram;
    std::array<int,4> drop{}, largest_pool_drop{};
    bool timeout=false;
    std::function<void(int,int)> visit = [&](int depth,int offset) {
      if (timeout) return;
      if (elapsed()>=28.0) { timeout=true; return; }
      if (depth<4) {
        for (int i=offset; i<=64-(4-depth); ++i) {
          drop[depth]=selected[i]; change(selected[i],true);
          visit(depth+1,i+1);
          change(selected[i],false);
          if (timeout) return;
        }
        return;
      }
      ++completed; ++hole_histogram[holes];
      int used=0, upper=0, top3=0;
      for (int value=10; value>=0 && used<4; --value) {
        const int take=std::min(histogram[value],4-used);
        for (int j=0; j<take; ++j) {
          upper+=value;
          if (used<3) top3+=value;
          ++used;
        }
      }
      const int demand=holes-5;
      if (upper<demand) ++excluded;
      else {
        ++survivors;
        const int floor=std::max(0,demand-top3);
        int pool=0;
        for (int value=floor; value<=10; ++value) pool+=histogram[value];
        ++pool_histogram[pool]; ++floor_histogram[floor];
        if (pool>maximum_pool) { maximum_pool=pool; largest_pool_drop=drop; }
        minimum_pool=std::min(minimum_pool,pool);
        const U64 n=static_cast<U64>(pool);
        if (n>=4) tuples+=n*(n-1)*(n-2)*(n-3)/24;
      }
      if (completed%10000==0)
        std::cout<<"{\"progress_completed\":"<<completed<<",\"seconds\":"<<elapsed()
                 <<",\"survivors\":"<<survivors<<",\"replacement_tuples_upper\":"
                 <<tuples<<"}"<<std::endl;
    };
    visit(0,0);
    if (counts!=initial_counts || scores!=initial_scores || histogram!=initial_histogram || holes!=6)
      throw std::runtime_error("restoration mismatch");
    if (!timeout && completed!=635376) throw std::runtime_error("incomplete deletion count");
    auto emit_histogram = [](const auto& hist) {
      std::cout<<'{'; bool first=true;
      for (const auto& [key,value]:hist) {
        if (!first) std::cout<<',';
        first=false; std::cout<<'"'<<key<<"\":"<<value;
      }
      std::cout<<'}';
    };
    std::cout<<"{\"complete\":"<<(timeout?"false":"true")<<",\"seconds\":"<<elapsed()
             <<",\"completed_deletions\":"<<completed<<",\"expected_deletions\":635376"
             <<",\"excluded\":"<<excluded<<",\"survivors\":"<<survivors
             <<",\"replacement_tuples_enumerated\":0,\"replacement_tuples_upper\":"<<tuples
             <<",\"minimum_pool\":"<<(survivors?minimum_pool:0)
             <<",\"maximum_pool\":"<<maximum_pool<<",\"largest_pool_drop\":[";
    for (int i=0; i<4; ++i) std::cout<<(i?",":"")<<largest_pool_drop[i];
    std::cout<<"],\"pool_histogram\":"; emit_histogram(pool_histogram);
    std::cout<<",\"floor_histogram\":"; emit_histogram(floor_histogram);
    std::cout<<",\"residual_hole_histogram\":"; emit_histogram(hole_histogram);
    std::cout<<",\"restoration_verified\":true}"<<std::endl;
    return 0;
  } catch (const std::exception& error) {
    std::cerr<<error.what()<<'\n'; return 2;
  }
}
