// Document:    H6 Strict-Hole Radius-Three Enumerator
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      f66f4d3028926a828413d904db3b3a8b3c043dcb9e958978b1d47bfb9934f69d
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Block = std::array<int, 5>;
using Cover = std::array<int, 10>;
struct Stats {
  long long deletions=0, excluded=0, tuples=0, candidates=0;
  bool complete=false;
};

int search(int argc, char** argv) {
  if (argc!=7 && argc!=9)
    throw std::runtime_error("input expected_holes target output_directory seconds family_size [--fixture-v v]");
  const auto start=std::chrono::steady_clock::now();
  const int expected=std::stoi(argv[2]), target=std::stoi(argv[3]);
  const int family_size=std::stoi(argv[6]);
  const double seconds=std::stod(argv[5]);
  int v=16;
  if (argc==9) {
    if (std::string(argv[7])!="--fixture-v") throw std::runtime_error("fixture flag");
    v=std::stoi(argv[8]);
    if (v!=7) throw std::runtime_error("fixture v must be7");
  } else if (family_size!=64 || expected!=6 || target!=5)
    throw std::runtime_error("production requires raw H6 exact64 strict H5");
  if (!std::isfinite(seconds) || seconds<0 || seconds>59 || target<0 || target!=expected-1 || family_size<3)
    throw std::runtime_error("budget/strict target/family size");
  auto elapsed=[&]() {return std::chrono::duration<double>(
      std::chrono::steady_clock::now()-start).count();};
  auto expired=[&]() {return elapsed()>=seconds;};
  int triple_id[17][17][17]={};
  std::vector<Block> blocks;
  std::vector<Cover> covers;
  std::vector<std::vector<int>> carriers;
  for (int a=1;a<=v;++a) for (int b=a+1;b<=v;++b) for (int c=b+1;c<=v;++c) {
    triple_id[a][b][c]=static_cast<int>(carriers.size()); carriers.emplace_back();
  }
  for (int a=1;a<=v;++a) for (int b=a+1;b<=v;++b) for (int c=b+1;c<=v;++c)
    for (int d=c+1;d<=v;++d) for (int e=d+1;e<=v;++e) blocks.push_back({a,b,c,d,e});
  for (int id=0;id<static_cast<int>(blocks.size());++id) {
    Cover cover{}; int j=0;
    for (int a=0;a<5;++a) for (int b=a+1;b<5;++b) for (int c=b+1;c<5;++c) {
      int t=triple_id[blocks[id][a]][blocks[id][b]][blocks[id][c]];
      cover[j++]=t; carriers[t].push_back(id);
    }
    covers.push_back(cover);
  }
  std::ifstream input(argv[1]);
  if (!input) throw std::runtime_error("input missing");
  std::vector<int> selected, counts(carriers.size()), scores(blocks.size()), eligible;
  std::vector<bool> chosen(blocks.size());
  std::string line;
  while (std::getline(input,line)) {
    std::istringstream row(line); Block b{}; std::string extra;
    for (int& p:b) if (!(row>>p)) throw std::runtime_error("short/malformed block");
    if (row>>extra) throw std::runtime_error("long block");
    if (b[0]<1 || b[4]>v || std::adjacent_find(b.begin(),b.end(),std::greater_equal<int>())!=b.end())
      throw std::runtime_error("labels/order");
    auto found=std::lower_bound(blocks.begin(),blocks.end(),b);
    if (found==blocks.end() || *found!=b) throw std::runtime_error("unknown block");
    int id=static_cast<int>(found-blocks.begin());
    if (chosen[id] || (!selected.empty() && selected.back()>=id))
      throw std::runtime_error("duplicate/order");
    chosen[id]=true; selected.push_back(id);
    for (int t:covers[id]) ++counts[t];
  }
  if (static_cast<int>(selected.size())!=family_size) throw std::runtime_error("family size");
  int initial_holes=0;
  for (int t=0;t<static_cast<int>(counts.size());++t) if (!counts[t]) {
    ++initial_holes; for (int id:carriers[t]) ++scores[id];
  }
  if (initial_holes!=expected) throw std::runtime_error("initial holes mismatch");
  for (int id=0;id<static_cast<int>(blocks.size());++id) if (!chosen[id]) eligible.push_back(id);
  if (v==16 && (blocks.size()!=4368 || counts.size()!=560 || eligible.size()!=4304))
    throw std::runtime_error("production universe");
  const std::filesystem::path output(argv[4]);
  if (!std::filesystem::is_directory(output) || !std::filesystem::is_empty(output))
    throw std::runtime_error("output must be existing empty directory");
  std::ofstream ledger(output/"candidates.tsv");
  ledger<<"candidate\tdistance\tholes\tdrop_ids\tadd_ids\n";
  ledger.flush();
  if (!ledger) throw std::runtime_error("ledger open/header write failed");
  std::array<Stats,3> stats{};
  long long total=0;
  bool timeout=false;
  std::vector<int> dropped, added;
  for (int k=1;k<=3 && !timeout;++k) {
    Stats& s=stats[k-1];
    std::function<void(int)> choose_drop=[&](int offset) {
      if (timeout) return;
      if (expired()) {timeout=true; return;}
      if (static_cast<int>(dropped.size())!=k) {
        for (int i=offset;i<=family_size-(k-static_cast<int>(dropped.size()));++i) {
          dropped.push_back(selected[i]); choose_drop(i+1); dropped.pop_back();
          if (timeout) return;
        }
        return;
      }
      ++s.deletions;
      for (int id:dropped) for (int t:covers[id]) if (--counts[t]==0)
        for (int a:carriers[t]) ++scores[a];
      std::vector<int> uncovered;
      for (int t=0;t<static_cast<int>(counts.size());++t) if (!counts[t]) uncovered.push_back(t);
      if (uncovered.size()>63) throw std::runtime_error("residual mask too wide");
      const int demand=static_cast<int>(uncovered.size())-target;
      std::array<int,3> top{};
      for (int id:eligible) {
        int value=scores[id];
        for (int j=0;j<k;++j) if (value>top[j]) std::swap(value,top[j]);
      }
      const int upper=std::accumulate(top.begin(),top.begin()+k,0);
      if (upper<demand) ++s.excluded;
      else {
        const int floor=std::max(0,demand-std::accumulate(top.begin(),top.begin()+k-1,0));
        std::vector<int> pool, bit(counts.size(),-1);
        std::vector<uint64_t> masks;
        for (int j=0;j<static_cast<int>(uncovered.size());++j) bit[uncovered[j]]=j;
        for (int id:eligible) if (scores[id]>=floor) {
          uint64_t mask=0;
          for (int t:covers[id]) if (bit[t]>=0) mask|=uint64_t{1}<<bit[t];
          if (__builtin_popcountll(mask)!=scores[id]) throw std::runtime_error("sparse count mismatch");
          pool.push_back(id); masks.push_back(mask);
        }
        std::function<void(int,uint64_t)> choose_add=[&](int offset,uint64_t mask) {
          if (timeout) return;
          if ((s.tuples&255)==0 && expired()) {timeout=true; return;}
          if (static_cast<int>(added.size())!=k) {
            for (int i=offset;i<=static_cast<int>(pool.size())-(k-static_cast<int>(added.size()));++i) {
              added.push_back(pool[i]); choose_add(i+1,mask|masks[i]); added.pop_back();
              if (timeout) return;
            }
            return;
          }
          ++s.tuples;
          const int holes=static_cast<int>(uncovered.size())-__builtin_popcountll(mask);
          if (holes>target) return;
          ++total; ++s.candidates;
          std::vector<int> family;
          for (int id:selected) if (!std::binary_search(dropped.begin(),dropped.end(),id)) family.push_back(id);
          family.insert(family.end(),added.begin(),added.end()); std::sort(family.begin(),family.end());
          std::ofstream witness(output/("candidate-"+std::to_string(total)+".txt"));
          for (int id:family) {
            for (int j=0;j<5;++j) witness<<blocks[id][j]<<(j==4?'\n':' ');
          }
          witness.close();
          if (!witness) throw std::runtime_error("candidate write failed");
          ledger<<total<<'\t'<<k<<'\t'<<holes<<'\t';
          for (int j=0;j<k;++j) ledger<<(j?",":"")<<dropped[j];
          ledger<<'\t';
          for (int j=0;j<k;++j) ledger<<(j?",":"")<<added[j];
          ledger<<'\n'; ledger.flush();
          if (!ledger) throw std::runtime_error("ledger write failed");
        };
        choose_add(0,0);
      }
      for (int id:dropped) for (int t:covers[id]) if (counts[t]++==0)
        for (int a:carriers[t]) --scores[a];
    };
    choose_drop(0); s.complete=!timeout;
  }
  ledger.close();
  if (!ledger) throw std::runtime_error("ledger close failed");
  std::cout<<"{\"status\":\""<<(timeout?"timeout":"complete")<<"\",\"seconds\":"<<elapsed()
           <<",\"candidates\":"<<total<<",\"shells\":[";
  for (int k=1;k<=3;++k) {
    const auto& s=stats[k-1];
    if (k>1) std::cout<<',';
    std::cout<<"{\"distance\":"<<k<<",\"deletions\":"<<s.deletions<<",\"excluded\":"<<s.excluded
             <<",\"tuples\":"<<s.tuples<<",\"candidates\":"<<s.candidates
             <<",\"complete\":"<<(s.complete?"true":"false")<<'}';
  }
  std::cout<<"]}\n";
  return 0;
}

int main(int argc,char** argv) {
  try {return search(argc,argv);}
  catch (const std::exception& error) {std::cerr<<"error: "<<error.what()<<'\n'; return 2;}
}
