// Document:    Independent Variable Cardinality Covering Search Kernel
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      e1d5695114e600573efa5ed402868692d2569e0695a1cfd60ababb8d4cc84e04
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#pragma once
// Independent implementation of the algorithm described in post-d2-literature.
// Scientific attribution: Luo et al., NuSC, doi:10.1109/TCYB.2022.3199147.
// No upstream implementation is included or linked.
#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <fstream>
#include <functional>
#include <limits>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace vc {
constexpr int NB = 4368, NT = 560;
using Weight = std::int64_t;
struct Universe {
  std::array<std::array<int, 5>, NB> points{};
  std::array<std::array<int, 10>, NB> members{};
  std::array<std::vector<int>, NT> carriers{};
  std::array<int, 65536> block_rank{}, triple_rank{};
  Universe() {
    block_rank.fill(-1); triple_rank.fill(-1);
    int ti = 0;
    for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b)
      for (int c=b+1;c<=16;++c)
        triple_rank[(1<<(a-1))|(1<<(b-1))|(1<<(c-1))] = ti++;
    int bi = 0;
    for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b)
      for (int c=b+1;c<=16;++c) for (int d=c+1;d<=16;++d)
        for (int e=d+1;e<=16;++e) {
          points[bi]={a,b,c,d,e}; int mask=0, q=0;
          for (int p:points[bi]) mask |= 1<<(p-1);
          block_rank[mask]=bi;
          for(int i=0;i<5;++i) for(int j=i+1;j<5;++j)
            for(int k=j+1;k<5;++k) {
              int t=triple_rank[(1<<(points[bi][i]-1))|
                  (1<<(points[bi][j]-1))|(1<<(points[bi][k]-1))];
              members[bi][q++]=t; carriers[t].push_back(bi);
            }
          ++bi;
        }
    if (bi!=NB || ti!=NT) throw std::logic_error("bad universe dimensions");
    for(const auto& row:carriers) if(row.size()!=78)
      throw std::logic_error("bad triple carrier count");
  }
  std::vector<int> read(const std::string& path) const {
    std::ifstream input(path); if(!input) throw std::runtime_error("cannot read family");
    std::vector<int> out; std::array<bool,NB> used{}; std::string line;
    while(std::getline(input,line)) {
      if(line.empty() || line[0]=='#') continue;
      std::istringstream row(line); std::string token; int mask=0,n=0;
      while(row>>token) {
        int p=0; auto parsed=std::from_chars(token.data(),token.data()+token.size(),p);
        if(parsed.ec!=std::errc{} || parsed.ptr!=token.data()+token.size() ||
            p<1 || p>16 || (mask&(1<<(p-1)))) throw std::runtime_error("malformed label");
        mask |= 1<<(p-1); ++n;
      }
      if(n!=5 || block_rank[mask]<0) throw std::runtime_error("malformed block");
      int b=block_rank[mask]; if(used[b]) throw std::runtime_error("duplicate block");
      used[b]=true; out.push_back(b);
    }
    std::sort(out.begin(),out.end()); return out;
  }
  void write(const std::string& path,const std::vector<int>& ids) const {
    std::ofstream output(path); if(!output) throw std::runtime_error("cannot write family");
    for(int b:ids) {
      if(b<0 || b>=NB) throw std::runtime_error("bad saved block ID");
      for(int i=0;i<5;++i) output << (i?" ":"") << points[b][i];
      output << '\n';
    }
    if(!output) throw std::runtime_error("family write failed");
  }
};

struct Scores { Weight score=0, pscore=0; };
struct SearchState {
  const Universe& u;
  std::array<int,NT> count{};
  std::array<Weight,NT> weight{};
  std::array<bool,NB> chosen{}, cc{};
  std::array<std::uint64_t,NB> last{};
  int cardinality=0, holes=NT;
  SearchState(const Universe& universe,const std::vector<int>& ids):u(universe) {
    weight.fill(1); cc.fill(true);
    for(int b:ids) {
      if(b<0 || b>=NB || chosen[b]) throw std::runtime_error("invalid initial block IDs");
      chosen[b]=true; ++cardinality;
      for(int t:u.members[b]) if(count[t]++==0) --holes;
    }
  }
  Scores scores(int b) const {
    if(b<0 || b>=NB) throw std::runtime_error("invalid score block");
    Scores v;
    for(int t:u.members[b]) {
      if(chosen[b]) {
        if(count[t]==1) v.score-=weight[t];
        else if(count[t]==2) v.pscore-=weight[t];
      } else {
        if(count[t]==0) v.score+=weight[t];
        else if(count[t]==1) v.pscore+=weight[t];
      }
    }
    return v;
  }
  bool better(int a,int b) const {
    if(b<0) return true;
    auto x=scores(a), y=scores(b);
    if(5*x.score+x.pscore!=5*y.score+y.pscore)
      return 5*x.score+x.pscore>5*y.score+y.pscore;
    if(x.pscore!=y.pscore) return x.pscore>y.pscore;
    if(last[a]!=last[b]) return last[a]<last[b];
    return a<b; // Explicit deterministic global-lex tie break.
  }
  void add(int b,std::uint64_t step) {
    if(b<0 || b>=NB || chosen[b]) throw std::runtime_error("invalid add");
    chosen[b]=true; ++cardinality;
    for(int t:u.members[b]) {
      if(count[t]++==0) --holes;
      for(int neighbor:u.carriers[t]) cc[neighbor]=true;
    }
    last[b]=step;
  }
  void remove(int b,std::uint64_t step) {
    if(b<0 || b>=NB || !chosen[b]) throw std::runtime_error("invalid remove");
    chosen[b]=false; --cardinality;
    for(int t:u.members[b]) {
      if(--count[t]==0) ++holes;
      for(int neighbor:u.carriers[t]) cc[neighbor]=true;
    }
    cc[b]=false; last[b]=step;
  }
  void increment_uncovered() {
    for(int t=0;t<NT;++t) if(count[t]==0) {
      if(weight[t]>=std::numeric_limits<Weight>::max()/100)
        throw std::overflow_error("dynamic weight overflow guard");
      ++weight[t];
    }
  }
  std::vector<int> ids() const {
    std::vector<int> out;
    for(int b=0;b<NB;++b) if(chosen[b]) out.push_back(b);
    return out;
  }
  int outgoing() const {
    int best=-1;
    for(int b=0;b<NB;++b) if(chosen[b] && better(b,best)) best=b;
    if(best<0) throw std::runtime_error("cannot remove from empty family");
    return best;
  }
  int redundant() const {
    for(int b=0;b<NB;++b) if(chosen[b] && scores(b).score==0) return b;
    return -1;
  }
  bool eligible(int b,std::uint64_t step) const {
    return !chosen[b] && cc[b] && step>=last[b] && step-last[b]>=4;
  }
  struct Incoming { int id=-1, best=-1, second=-1; bool fallback=false, novelty=false; };
  Incoming incoming(int target,std::uint64_t step,unsigned novelty_draw) const {
    if(target<0 || target>=NT || count[target]!=0 || novelty_draw>=100)
      throw std::runtime_error("invalid incoming choice inputs");
    Incoming out;
    for(int b:u.carriers[target]) if(eligible(b,step)) {
      if(better(b,out.best)) {out.second=out.best;out.best=b;}
      else if(better(b,out.second)) out.second=b;
    }
    if(out.best<0) {
      out.id=u.carriers[target].front(); out.fallback=true;
    } else {
      out.novelty=out.second>=0 && novelty_draw<11;
      out.id=out.novelty?out.second:out.best;
    }
    if(chosen[out.id]) throw std::logic_error("uncovered triple has selected carrier");
    return out;
  }
  void audit() const {
    std::array<int,NT> direct{}; int n=0;
    for(int b=0;b<NB;++b) if(chosen[b]) {++n;for(int t:u.members[b]) ++direct[t];}
    if(n!=cardinality || direct!=count || std::count(direct.begin(),direct.end(),0)!=holes)
      throw std::logic_error("state recount failed");
    for(Weight w:weight) if(w<1) throw std::logic_error("nonpositive dynamic weight");
  }
};

enum class Action { complete_stop, redundant_drop, complete_drop, add_only, swap, double_drop };
inline const char* action_name(Action a) {
  switch(a) {
    case Action::complete_stop:return "complete_stop";
    case Action::redundant_drop:return "redundant_drop";
    case Action::complete_drop:return "complete_drop";
    case Action::add_only:return "add_only";
    case Action::swap:return "swap";
    case Action::double_drop:return "double_drop";
  }
  throw std::logic_error("unknown action");
}
inline bool target_reached(const SearchState& s) { return s.holes==0 && s.cardinality<=64; }
struct StepResult {
  Action action=Action::complete_stop;
  int incoming=-1, first_removed=-1, second_removed=-1;
  bool fallback=false, novelty=false, stopped=false, weights_updated=false;
};
using Observer = std::function<bool(const SearchState&,const char*,int)>;
inline StepResult advance(SearchState& s,std::uint64_t step,int incumbent_size,
    int target,unsigned novelty_draw,const Observer& observe) {
  if(incumbent_size<1) throw std::runtime_error("invalid incumbent");
  StepResult r;
  if(target_reached(s)) {r.stopped=true;return r;}
  auto drop=[&](int b) {s.remove(b,step);return observe(s,"remove",b)||target_reached(s);};
  auto add=[&](int b) {s.add(b,step);return observe(s,"add",b)||target_reached(s);};
  if(s.holes==0) {
    int b=s.redundant();r.action=b>=0?Action::redundant_drop:Action::complete_drop;
    r.first_removed=b>=0?b:s.outgoing();r.stopped=drop(r.first_removed);return r;
  }
  auto next=s.incoming(target,step,novelty_draw);
  r.incoming=next.id;r.fallback=next.fallback;r.novelty=next.novelty;
  if(s.cardinality+1<incumbent_size) {
    r.action=Action::add_only;r.stopped=add(next.id);
    if(!r.stopped) {s.increment_uncovered();r.weights_updated=true;}
    return r;
  }
  int b=s.outgoing();auto gain=s.scores(next.id).score,loss=-s.scores(b).score;
  r.first_removed=b;
  if(gain>loss) {
    r.action=Action::swap;r.stopped=drop(b);
    if(!r.stopped) r.stopped=add(next.id);
  } else {
    r.action=Action::double_drop;r.stopped=drop(b);
    if(!r.stopped) {r.second_removed=s.outgoing();r.stopped=drop(r.second_removed);}
  }
  return r;
}
} // namespace vc
