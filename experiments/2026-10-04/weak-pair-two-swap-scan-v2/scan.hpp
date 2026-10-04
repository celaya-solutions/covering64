// Document:    Complete One Swap Neighborhood Evaluation Kernel
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      fdaced0d763a797c8fb4817ca641d686c60e970342fc28719b04bd992ea3465b
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#pragma once
#include "kernel.hpp"
#include "cores.hpp"
namespace ws {
constexpr int NP=120,NQ=1820;
struct Universe:vc::Universe {
  std::array<int,65536> pair_rank{},quad_rank{};
  std::array<std::array<int,10>,vc::NB> pair_members{};
  std::array<std::array<int,5>,vc::NB> quad_members{};
  std::array<std::array<int,14>,NP> pair_triples{};
  std::array<std::array<int,91>,NP> pair_quads{};
  std::array<std::array<bool,vc::NB>,4> core_member{};
  Universe() {
    pair_rank.fill(-1);quad_rank.fill(-1);int n=0;
    for(int a=1;a<=16;++a) for(int b=a+1;b<=16;++b)
      pair_rank[(1<<(a-1))|(1<<(b-1))]=n++;
    if(n!=NP) throw std::logic_error("bad pair universe");n=0;
    for(int a=1;a<=16;++a) for(int b=a+1;b<=16;++b)
      for(int c=b+1;c<=16;++c) for(int d=c+1;d<=16;++d)
        quad_rank[(1<<(a-1))|(1<<(b-1))|(1<<(c-1))|(1<<(d-1))]=n++;
    if(n!=NQ) throw std::logic_error("bad quad universe");
    for(int b=0;b<vc::NB;++b) {
      int i=0;
      for(int a=0;a<5;++a) for(int c=a+1;c<5;++c)
        pair_members[b][i++]=pair_rank[(1<<(points[b][a]-1))|(1<<(points[b][c]-1))];
      for(int omit=0;omit<5;++omit) {
        int mask=0;for(int a=0;a<5;++a) if(a!=omit) mask|=1<<(points[b][a]-1);
        quad_members[b][omit]=quad_rank[mask];
      }
    }
    for(int a=1;a<=16;++a) for(int b=a+1;b<=16;++b) {
      int mask=(1<<(a-1))|(1<<(b-1)),p=pair_rank[mask],ntri=0,nquad=0;
      for(int x=1;x<=16;++x) if(x!=a && x!=b) {
        pair_triples[p][ntri++]=triple_rank[mask|(1<<(x-1))];
        for(int y=x+1;y<=16;++y) if(y!=a && y!=b)
          pair_quads[p][nquad++]=quad_rank[mask|(1<<(x-1))|(1<<(y-1))];
      }
      if(ntri!=14 || nquad!=91) throw std::logic_error("bad pair-row dimensions");
    }
    for(int i=0;i<4;++i) for(int b:vc::core_rows[i]) core_member[i][b]=true;
  }
};
struct Counts {
  const Universe& u;
  std::array<int,NP> pair{};
  std::array<int,vc::NT> triple{};
  std::array<int,NQ> quad{};
  std::array<bool,vc::NB> chosen{};
  int cardinality=0,holes=vc::NT;
  Counts(const Universe& universe,const std::vector<int>& ids):u(universe) {
    for(int b:ids) add(b);
  }
  void add(int b) {
    if(b<0 || b>=vc::NB || chosen[b]) throw std::runtime_error("invalid add");
    chosen[b]=true;++cardinality;
    for(int p:u.pair_members[b]) ++pair[p];
    for(int t:u.members[b]) if(triple[t]++==0) --holes;
    for(int q:u.quad_members[b]) ++quad[q];
  }
  void remove(int b) {
    if(b<0 || b>=vc::NB || !chosen[b]) throw std::runtime_error("invalid remove");
    chosen[b]=false;--cardinality;
    for(int p:u.pair_members[b]) --pair[p];
    for(int t:u.members[b]) if(--triple[t]==0) ++holes;
    for(int q:u.quad_members[b]) --quad[q];
  }
  std::vector<int> ids() const {
    std::vector<int> out;for(int b=0;b<vc::NB;++b) if(chosen[b]) out.push_back(b);return out;
  }
  void audit() const {
    Counts direct(u,ids());
    if(direct.pair!=pair || direct.triple!=triple || direct.quad!=quad ||
       direct.cardinality!=cardinality || direct.holes!=holes)
      throw std::logic_error("count rollback/recount failed");
  }
};
struct PairMetrics {int d2max=0,d2sum=0,d3=0,d4=0;};
inline PairMetrics pair_metrics(const Counts& c,int p) {
  PairMetrics m;std::array<int,14> values{};int first=0,second=0;
  for(int i=0;i<14;++i) {
    int v=c.triple[c.u.pair_triples[p][i]];values[i]=v;
    if(v>=first) {second=first;first=v;} else if(v>second) second=v;
    m.d3+=std::max(0,13-3*c.pair[p]+v);
  }
  m.d2max=std::max(0,12-3*c.pair[p]+first+second);
  int q=0;
  for(int i=0;i<14;++i) for(int j=i+1;j<14;++j) {
    m.d2sum+=std::max(0,12-3*c.pair[p]+values[i]+values[j]);
    m.d4+=std::max(0,12-3*c.pair[p]+2*c.quad[c.u.pair_quads[p][q++]]);
  }
  return m;
}
struct Metrics {
  int cardinality=0,holes=0,d2max=0,d2sum=0,d3=0,d4=0,minimum_pair_count=0;
  std::array<int,4> core_overlaps{};
  bool legal() const {
    return cardinality==64 && minimum_pair_count>=5 && d3==0 && d4==0 &&
      *std::max_element(core_overlaps.begin(),core_overlaps.end())<=55;
  }
  std::pair<int,int> rank() const {return {holes,d2max};}
};
inline Metrics full_metrics(const Counts& c) {
  Metrics m;m.cardinality=c.cardinality;m.holes=c.holes;
  m.minimum_pair_count=*std::min_element(c.pair.begin(),c.pair.end());
  for(int p=0;p<NP;++p) {
    auto x=pair_metrics(c,p);m.d2max+=x.d2max;m.d2sum+=x.d2sum;m.d3+=x.d3;m.d4+=x.d4;
  }
  for(int k=0;k<4;++k) for(int b:vc::core_rows[k]) m.core_overlaps[k]+=c.chosen[b];
  return m;
}
struct SwapEngine {
  const Universe& u;
  Counts current;
  std::vector<int> initial_ids;
  std::array<bool,vc::NB> initial_chosen{};
  Metrics baseline;
  std::array<PairMetrics,NP> initial_pair_metrics{};
  SwapEngine(const Universe& universe,const std::vector<int>& ids):
    u(universe),current(u,ids),initial_ids(current.ids()),initial_chosen(current.chosen),
    baseline(full_metrics(current)) {
      if(!baseline.legal()) throw std::runtime_error("initial family violates scan restrictions");
      for(int p=0;p<NP;++p) initial_pair_metrics[p]=pair_metrics(current,p);
  }
  std::array<bool,NP> affected(int outgoing,int incoming) const {
    if(outgoing<0 || outgoing>=vc::NB || incoming<0 || incoming>=vc::NB)
      throw std::runtime_error("invalid swap ID");
    std::array<bool,NP> a{};
    for(int p:u.pair_members[outgoing]) a[p]=true;
    for(int p:u.pair_members[incoming]) a[p]=true;
    return a;
  }
  Metrics evaluate(int outgoing,int incoming) {
    auto changed=affected(outgoing,incoming);
    if(!initial_chosen[outgoing] || initial_chosen[incoming])
      throw std::runtime_error("swap must remove an initial block and add an initially absent block");
    current.remove(outgoing);current.add(incoming);
    Metrics m=baseline;m.cardinality=current.cardinality;m.holes=current.holes;
    m.minimum_pair_count=*std::min_element(current.pair.begin(),current.pair.end());
    for(int p=0;p<NP;++p) if(changed[p]) {
      auto next=pair_metrics(current,p),old=initial_pair_metrics[p];
      m.d2max+=next.d2max-old.d2max;m.d2sum+=next.d2sum-old.d2sum;
      m.d3+=next.d3-old.d3;m.d4+=next.d4-old.d4;
    }
    for(int k=0;k<4;++k)
      m.core_overlaps[k]+=int(u.core_member[k][incoming])-int(u.core_member[k][outgoing]);
    current.remove(incoming);current.add(outgoing);
    return m;
  }
};
} // namespace ws
