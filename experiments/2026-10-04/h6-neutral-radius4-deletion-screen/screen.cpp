// Document:    H6 Neutral Four-Deletion Workload Screen
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      2b0fe982c163d2d4fc227d134959e8df441c8f46578513dd449bda4f6e9b224d
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <vector>
using B=std::array<int,5>;
using U=std::uint64_t;

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
    std::vector<B> blocks;
    std::vector<std::array<int,10>> cover;
    std::array<std::vector<int>,560> carriers;
    int ids[17][17][17]={}, nt=0;
    for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b) for (int c=b+1;c<=16;++c)
      ids[a][b][c]=nt++;
    for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b) for (int c=b+1;c<=16;++c)
      for (int d=c+1;d<=16;++d) for (int e=d+1;e<=16;++e) blocks.push_back({a,b,c,d,e});
    for (int i=0;i<4368;++i) {
      std::array<int,10> row{}; int j=0;
      for (int a=0;a<5;++a) for (int b=a+1;b<5;++b) for (int c=b+1;c<5;++c)
        row[j++]=ids[blocks[i][a]][blocks[i][b]][blocks[i][c]];
      cover.push_back(row);
    }
    std::ifstream input(argv[1]); if (!input) throw std::runtime_error("missing input");
    std::vector<int> family, eligible;
    std::array<bool,4368> selected{};
    std::array<U,560> owners{};
    std::string line;
    while (std::getline(input,line)) {
      B block{}; std::string extra; std::istringstream row(line);
      for (int& label:block) if (!(row>>label)) throw std::runtime_error("short block");
      if (row>>extra) throw std::runtime_error("long block");
      auto found=std::lower_bound(blocks.begin(),blocks.end(),block);
      if (found==blocks.end() || *found!=block) throw std::runtime_error("invalid block");
      int id=static_cast<int>(found-blocks.begin());
      if (selected[id] || (!family.empty() && family.back()>=id) || family.size()>=64)
        throw std::runtime_error("duplicate/order/size");
      for (int t:cover[id]) owners[t]|=U{1}<<family.size();
      family.push_back(id); selected[id]=true;
    }
    if (family.size()!=64 || std::count(owners.begin(),owners.end(),U{0})!=6)
      throw std::runtime_error("not raw exact64 H6");
    for (int id=0;id<4368;++id) if (!selected[id]) {
      eligible.push_back(id); for (int t:cover[id]) carriers[t].push_back(id);
    }
    std::ofstream rows(argv[2]);
    rows<<"delete0\tdelete1\tdelete2\tdelete3\tuncovered\tdemand\ttop0\ttop1\ttop2\ttop3"
        <<"\tupper\tfloor\tpool\texcluded\n";
    rows.flush(); if (!rows) throw std::runtime_error("rows open");
    U completed=0, excluded=0, survivors=0, tuples=0;
    int maximum=0, minimum=4369;
    std::array<int,4> largest{};
    std::map<int,U> pools, floors, residuals;
    bool timeout=false;
    for (int a=0;a<61 && !timeout;++a) for (int b=a+1;b<62 && !timeout;++b)
      for (int c=b+1;c<63 && !timeout;++c) for (int d=c+1;d<64;++d) {
        if (elapsed()>=28) {timeout=true; break;}
        const U deleted=(U{1}<<a)|(U{1}<<b)|(U{1}<<c)|(U{1}<<d);
        // Rebuild all scores from original triple owners; no state from another deletion.
        std::array<unsigned char,4368> scores{};
        int missing=0;
        for (int t=0;t<560;++t) if ((owners[t]&~deleted)==0) {
          ++missing; for (int id:carriers[t]) ++scores[id];
        }
        std::array<int,4> top{};
        std::array<int,11> score_hist{};
        for (int id:eligible) {
          int value=scores[id];
          if (value>10) throw std::runtime_error("score overflow");
          ++score_hist[value];
          for (int j=0;j<4;++j) if (value>top[j]) std::swap(value,top[j]);
        }
        const int upper=top[0]+top[1]+top[2]+top[3], demand=missing-6;
        const int floor=std::max(0,demand-top[0]-top[1]-top[2]);
        int pool=0;
        for (int value=floor;value<=10;++value) pool+=score_hist[value];
        bool ruled_out=upper<demand;
        ++completed; ++residuals[missing];
        if (ruled_out) ++excluded;
        else {
          ++survivors; ++pools[pool]; ++floors[floor]; minimum=std::min(minimum,pool);
          if (pool>maximum) {maximum=pool; largest={family[a],family[b],family[c],family[d]};}
          const U n=pool;
          if (n>=4) tuples+=n*(n-1)*(n-2)*(n-3)/24;
        }
        rows<<family[a]<<'\t'<<family[b]<<'\t'<<family[c]<<'\t'<<family[d]<<'\t'
            <<missing<<'\t'<<demand;
        for (int value:top) rows<<'\t'<<value;
        rows<<'\t'<<upper<<'\t'<<floor<<'\t'<<pool<<'\t'<<ruled_out<<'\n';
      }
    rows.close(); if (!rows) throw std::runtime_error("rows close/write");
    std::cout<<"{\"complete\":"<<(timeout?"false":"true")<<",\"seconds\":"<<elapsed()
             <<",\"completed_deletions\":"<<completed<<",\"excluded\":"<<excluded
             <<",\"survivors\":"<<survivors<<",\"replacement_tuples_upper\":"<<tuples
             <<",\"replacement_tuples_enumerated\":0,\"minimum_pool\":"<<minimum
             <<",\"maximum_pool\":"<<maximum<<",\"largest_pool_drop\":[";
    for (int j=0;j<4;++j) std::cout<<(j?",":"")<<largest[j];
    std::cout<<"],\"pool_histogram\":"; histogram(pools);
    std::cout<<",\"floor_histogram\":"; histogram(floors);
    std::cout<<",\"residual_hole_histogram\":"; histogram(residuals);
    std::cout<<"}\n";
    return 0;
  } catch(const std::exception& error) {std::cerr<<error.what()<<'\n'; return 2;}
}
