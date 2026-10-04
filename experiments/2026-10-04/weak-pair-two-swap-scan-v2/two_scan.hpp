// Document:    Complete Two Swap Support and Evaluation Kernel
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      1e2c8e886eedd9ac36a70bf825dd5af60378853e08ed8720b0ec92c1ce5a311b
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#pragma once
#include "scan.hpp"
namespace ts {
constexpr std::uint64_t TOTAL=18668272896ULL,OUTERS=8676864ULL,INNER=9260056ULL;
struct Universe:ws::Universe {
  std::vector<std::vector<int>> supersets;
  std::array<int,ws::NP> pair_masks{};
  Universe():supersets(65536) {
    for(int mask=0;mask<65536;++mask) if(pair_rank[mask]>=0) pair_masks[pair_rank[mask]]=mask;
    for(int b=0;b<vc::NB;++b) {
      int mask=0;for(int p:points[b]) mask|=1<<(p-1);
      int sub=mask;for(;;) {supersets[sub].push_back(b);if(sub==0) break;sub=(sub-1)&mask;}
    }
  }
};
struct Support {bool impossible=false;int mask=0,size=0;bool deficit_gt_one=false;};
struct TwoSwapEngine {
  const Universe& u;ws::Counts current;
  std::vector<int> initial_ids;
  std::array<bool,vc::NB> initial_chosen{};
  ws::Metrics baseline;
  std::array<ws::PairMetrics,ws::NP> initial_pair_metrics{};
  int removed_b=-1,removed_c=-1,first_a=-1;
  TwoSwapEngine(const Universe& universe,const std::vector<int>& ids):
    u(universe),current(u,ids),initial_ids(current.ids()),initial_chosen(current.chosen),baseline(ws::full_metrics(current)) {
    if(!baseline.legal()) throw std::runtime_error("initial family violates scan restrictions");
    for(int p=0;p<ws::NP;++p) initial_pair_metrics[p]=ws::pair_metrics(current,p);
  }
  bool valid(int b) const {return b>=0 && b<vc::NB;}
  void begin(int b,int c) {
    if(removed_b!=-1 || !valid(b) || !valid(c) || b>=c || !initial_chosen[b] || !initial_chosen[c])
      throw std::runtime_error("invalid removal pair");
    current.remove(b);current.remove(c);removed_b=b;removed_c=c;
  }
  void add_first(int a) {
    if(removed_b<0 || first_a!=-1 || !valid(a) || initial_chosen[a]) throw std::runtime_error("invalid first addition");
    current.add(a);first_a=a;
  }
  Support support() const {
    if(first_a<0) throw std::runtime_error("support requires63 state");
    Support s;
    for(int p=0;p<ws::NP;++p) {
      int deficit=5-current.pair[p];
      if(deficit>1) s.deficit_gt_one=true;
      if(deficit>0) s.mask|=u.pair_masks[p];
    }
    s.size=__builtin_popcount(static_cast<unsigned>(s.mask));
    s.impossible=s.deficit_gt_one || s.size>5;return s;
  }
  std::vector<int> completions(int a) const {
    if(a!=first_a) throw std::runtime_error("wrong active first addition");
    auto s=support();std::vector<int> out;
    if(!s.impossible) for(int d:u.supersets[s.mask]) if(d>a && !initial_chosen[d]) out.push_back(d);
    return out;
  }
  ws::Metrics evaluate_last(int d) {
    if(first_a<0 || !valid(d) || d<=first_a || initial_chosen[d]) throw std::runtime_error("invalid final addition");
    std::array<bool,ws::NP> changed{};
    for(int b:{removed_b,removed_c,first_a,d}) for(int p:u.pair_members[b]) changed[p]=true;
    current.add(d);ws::Metrics m=baseline;m.cardinality=current.cardinality;m.holes=current.holes;
    m.minimum_pair_count=*std::min_element(current.pair.begin(),current.pair.end());
    for(int p=0;p<ws::NP;++p) if(changed[p]) {
      auto next=ws::pair_metrics(current,p),old=initial_pair_metrics[p];
      m.d2max+=next.d2max-old.d2max;m.d2sum+=next.d2sum-old.d2sum;
      m.d3+=next.d3-old.d3;m.d4+=next.d4-old.d4;
    }
    for(int k=0;k<4;++k) m.core_overlaps[k]+=int(u.core_member[k][first_a])+int(u.core_member[k][d])-
      int(u.core_member[k][removed_b])-int(u.core_member[k][removed_c]);
    current.remove(d);return m;
  }
  void remove_first(int a) {
    if(first_a<0 || a!=first_a) throw std::runtime_error("wrong first removal");
    current.remove(a);first_a=-1;
  }
  void end(int b,int c) {
    if(first_a!=-1 || removed_b!=b || removed_c!=c || b<0) throw std::runtime_error("wrong removal rollback");
    current.add(b);current.add(c);removed_b=removed_c=-1;
  }
  ws::Metrics evaluate(int b,int c,int a,int d) {
    if(removed_b!=-1 || !valid(b) || !valid(c) || b>=c || !initial_chosen[b] || !initial_chosen[c] ||
       !valid(a) || !valid(d) || a>=d || initial_chosen[a] || initial_chosen[d])
      throw std::runtime_error("invalid two swap");
    begin(b,c);add_first(a);auto m=evaluate_last(d);remove_first(a);end(b,c);return m;
  }
};
} // namespace ts
