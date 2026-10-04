// Document:    H6 Neutral Radius-Three Deletion Workload Screen
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      eaadd7f97b8046d29ca5b32903ca0d3b968a2310c79bc31c7032735ade5b3fa5
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
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <vector>
using Block=std::array<int,5>;
using U64=std::uint64_t;
U64 choose(int n,int k) {
  if (n<k) return 0;
  U64 result=1;
  for (int i=1;i<=k;++i) result=result*static_cast<U64>(n-i+1)/static_cast<U64>(i);
  return result;
}
struct Shell {
  U64 deletions=0, excluded=0, survivors=0, tuples=0;
  bool complete=false;
  int minimum=4369, maximum=0;
  std::map<int,U64> pools, floors, holes;
};
template<class T> void histogram(const T& h) {
  std::cout<<'{'; bool first=true;
  for (auto [key,value]:h) {
    if (!first) std::cout<<',';
    first=false; std::cout<<'"'<<key<<"\":"<<value;
  }
  std::cout<<'}';
}
int main(int argc,char** argv) {
  try {
    if (argc!=3) throw std::runtime_error("input and new rows.tsv required");
    const auto start=std::chrono::steady_clock::now();
    auto elapsed=[&](){return std::chrono::duration<double>(
      std::chrono::steady_clock::now()-start).count();};
    int triple_id[17][17][17]={}, triple_count=0;
    for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b) for (int c=b+1;c<=16;++c)
      triple_id[a][b][c]=triple_count++;
    std::vector<Block> blocks;
    std::vector<std::array<int,10>> covers;
    for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b) for (int c=b+1;c<=16;++c)
      for (int d=c+1;d<=16;++d) for (int e=d+1;e<=16;++e) blocks.push_back({a,b,c,d,e});
    for (int id=0;id<4368;++id) {
      std::array<int,10> cover{}; int index=0;
      for (int a=0;a<5;++a) for (int b=a+1;b<5;++b) for (int c=b+1;c<5;++c)
        cover[index++]=triple_id[blocks[id][a]][blocks[id][b]][blocks[id][c]];
      covers.push_back(cover);
    }
    std::ifstream input(argv[1]); if (!input) throw std::runtime_error("missing input");
    std::vector<int> selected, eligible;
    std::array<bool,4368> chosen{};
    std::array<U64,560> owners{};
    std::string line;
    while (std::getline(input,line)) {
      Block block{}; std::string extra; std::istringstream row(line);
      for (int& p:block) if (!(row>>p)) throw std::runtime_error("short/malformed block");
      if (row>>extra) throw std::runtime_error("long block");
      auto found=std::lower_bound(blocks.begin(),blocks.end(),block);
      if (found==blocks.end() || *found!=block) throw std::runtime_error("invalid block");
      const int id=static_cast<int>(found-blocks.begin());
      if (chosen[id] || (!selected.empty() && selected.back()>=id) || selected.size()>=64)
        throw std::runtime_error("duplicate/order/size");
      for (int t:covers[id]) owners[t]|=U64{1}<<selected.size();
      selected.push_back(id); chosen[id]=true;
    }
    if (selected.size()!=64 || std::count(owners.begin(),owners.end(),U64{0})!=6)
      throw std::runtime_error("need exact64 H6");
    std::array<std::vector<int>,560> carriers;
    for (int id=0;id<4368;++id) if (!chosen[id]) {
      eligible.push_back(id); for (int t:covers[id]) carriers[t].push_back(id);
    }
    if (triple_count!=560 || blocks.size()!=4368 || eligible.size()!=4304)
      throw std::runtime_error("universe mismatch");
    std::ofstream rows(argv[2]);
    rows<<"distance\tdrop_ids\tuncovered\tdemand\ttop0\ttop1\ttop2\tupper\tfloor\tpool"
        <<"\texcluded\tnecessary_tuples\n";
    rows.flush(); if (!rows) throw std::runtime_error("rows open/header");
    std::array<Shell,3> stats{};
    std::vector<int> dropped;
    bool timeout=false;
    for (int k=1;k<=3 && !timeout;++k) {
      auto& s=stats[k-1];
      std::function<void(int,U64)> visit=[&](int offset,U64 deletion_mask) {
        if (timeout) return;
        if (elapsed()>=28) {timeout=true; return;}
        if (static_cast<int>(dropped.size())!=k) {
          for (int i=offset;i<=64-(k-static_cast<int>(dropped.size()));++i) {
            dropped.push_back(selected[i]); visit(i+1,deletion_mask|(U64{1}<<i)); dropped.pop_back();
            if (timeout) return;
          }
          return;
        }
        std::array<unsigned char,4368> scores{};
        int missing=0;
        for (int t=0;t<560;++t) if ((owners[t]&~deletion_mask)==0) {
          ++missing; for (int id:carriers[t]) ++scores[id];
        }
        std::array<int,3> top{};
        std::array<int,11> score_hist{};
        for (int id:eligible) {
          int value=scores[id];
          if (value>10) throw std::runtime_error("score overflow");
          ++score_hist[value];
          for (int j=0;j<k;++j) if (value>top[j]) std::swap(value,top[j]);
        }
        const int demand=missing-6;
        const int upper=std::accumulate(top.begin(),top.begin()+k,0);
        const int floor=std::max(0,demand-std::accumulate(top.begin(),top.begin()+k-1,0));
        int pool=0;
        for (int value=floor;value<=10;++value) pool+=score_hist[value];
        const bool excluded=upper<demand;
        const U64 necessary=excluded?0:choose(pool,k);
        ++s.deletions; ++s.holes[missing];
        if (excluded) ++s.excluded;
        else {
          ++s.survivors; s.tuples+=necessary; ++s.pools[pool]; ++s.floors[floor];
          s.minimum=std::min(s.minimum,pool); s.maximum=std::max(s.maximum,pool);
        }
        rows<<k<<'\t';
        for (int j=0;j<k;++j) rows<<(j?",":"")<<dropped[j];
        rows<<'\t'<<missing<<'\t'<<demand;
        for (int value:top) rows<<'\t'<<value;
        rows<<'\t'<<upper<<'\t'<<floor<<'\t'<<pool<<'\t'<<excluded<<'\t'<<necessary<<'\n';
      };
      visit(0,0);
      s.complete=!timeout;
      if (s.complete && s.deletions!=choose(64,k)) throw std::runtime_error("shell incomplete");
    }
    rows.close(); if (!rows) throw std::runtime_error("rows close/write");
    std::cout<<"{\"complete\":"<<(timeout?"false":"true")<<",\"seconds\":"<<elapsed()
             <<",\"target_holes\":6,\"replacement_tuples_enumerated\":0,\"shells\":[";
    for (int k=1;k<=3;++k) {
      const auto& s=stats[k-1];
      if (k>1) std::cout<<',';
      std::cout<<"{\"distance\":"<<k<<",\"complete\":"<<(s.complete?"true":"false")
               <<",\"deletions\":"<<s.deletions<<",\"excluded\":"<<s.excluded
               <<",\"survivors\":"<<s.survivors<<",\"necessary_tuples\":"<<s.tuples
               <<",\"minimum_pool\":"<<(s.survivors?s.minimum:0)<<",\"maximum_pool\":"<<s.maximum
               <<",\"pool_histogram\":"; histogram(s.pools);
      std::cout<<",\"floor_histogram\":"; histogram(s.floors);
      std::cout<<",\"residual_hole_histogram\":"; histogram(s.holes);
      std::cout<<'}';
    }
    std::cout<<"]}\n";
    return 0;
  } catch(const std::exception& error) {std::cerr<<error.what()<<'\n'; return 2;}
}
