// Document:    Independent Native Pair-Move Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      [pending]
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_PAIR_NO_MAIN
#include "../native-pair-penalty/search.cpp"
#include <cassert>

int direct_checks=0, committed=0, rolled_back=0, duplicate_cases=0;

void independent(const State& s, const PairMetrics& m) {
  std::array<int,560> tc{};
  std::array<int,120> pc{};
  std::array<int,1820> qc{};
  std::array<bool,4368> chosen{};
  for (int b:s.ids) {
    assert(!chosen[b]); chosen[b]=true;
    unsigned mask=blocks[b].mask;
    for (int t=0;t<560;++t) tc[t]+=(mask&triples[t])==triples[t];
    for (int p=0;p<120;++p) pc[p]+=(mask&pairs[p])==pairs[p];
    for (int q=0;q<1820;++q) qc[q]+=(mask&quads[q])==quads[q];
  }
  assert(tc==s.count && pc==m.count && qc==m.quad && chosen==s.selected);
  int holes=0,d3=0,d4=0;
  for (int n:tc) holes+=n==0;
  assert(holes==s.deficit);
  for (int p=0;p<120;++p) {
    int a=0,b=0;
    for (int t=0;t<560;++t) if ((pairs[p]&triples[t])==pairs[p])
      a+=std::max(0,13-3*pc[p]+tc[t]);
    for (int q=0;q<1820;++q) if ((pairs[p]&quads[q])==pairs[p])
      b+=std::max(0,12-3*pc[p]+2*qc[q]);
    assert(a==m.d3[p] && b==m.d4[p]); d3+=a;d4+=b;
  }
  assert(d3==m.D3 && d4==m.D4);
  for (bool f:{false,true}) assert(integer_energy(s,m,f)==20*holes+5*d3+d4+160*int(f));
  ++direct_checks;
}

int main(int argc,char** argv) {
  assert(argc==2);
  universe(); initialize_cores(); initialize_pairs();
  assert(pairs.size()==120 && quads.size()==1820);
  std::vector<unsigned> expected_pairs,expected_quads;
  for (int a=0;a<16;++a) for (int b=a+1;b<16;++b) {
    expected_pairs.push_back((1u<<a)|(1u<<b));
    for (int c=b+1;c<16;++c) for (int d=c+1;d<16;++d)
      expected_quads.push_back((1u<<a)|(1u<<b)|(1u<<c)|(1u<<d));
  }
  assert(expected_pairs==pairs && expected_quads==quads);
  State seed(read_blocks(argv[1])); PairMetrics sm(seed); independent(seed,sm);
  assert(seed.deficit==6 && sm.D3==4 && sm.D4==0);
  std::array<int,5> intersections{};
  for (int k=0;k<=4;++k) {
    for (int slot=0;slot<64 && intersections[k]<40;++slot) {
      int old=seed.ids[slot];
      for (int next=0;next<4368 && intersections[k]<40;++next) {
        if (seed.selected[next] || __builtin_popcount(blocks[old].mask&blocks[next].mask)!=k) continue;
        State s=seed; PairMetrics m=sm; auto h=heavy_ids(s); auto c=core_counts(s);
        bool f=forbidden_profile(h,s);
        State proposal=s; proposal.move(slot,next); PairMetrics pm(proposal);
        independent(proposal,pm);
        int delta=integer_energy(proposal,pm,forbidden_profile(heavy_ids(proposal),proposal))
                  -integer_energy(s,m,f);
        auto outcome=attempt_move(s,h,c,m,f,slot,next,0.1,1.0);
        assert(outcome==(delta<=0?MoveResult::accepted:MoveResult::energy_rejected));
        if (outcome==MoveResult::accepted) {
          assert(s.ids==proposal.ids); ++committed;
        } else {
          assert(s.ids==seed.ids && m==sm); ++rolled_back;
        }
        independent(s,m);
        auto actual=heavy_ids(s); std::sort(h.begin(),h.end());std::sort(actual.begin(),actual.end());
        assert(h==actual && c==core_counts(s) && f==forbidden_profile(actual,s));
        s=seed;m=sm;h=heavy_ids(s);c=core_counts(s);f=forbidden_profile(h,s);
        assert(attempt_move(s,h,c,m,f,slot,next,1000.0,0.0)==MoveResult::accepted);
        assert(s.ids==proposal.ids); independent(s,m); ++committed;
        ++intersections[k];
      }
    }
    assert(intersections[k]==40);
  }
  State walk=seed; PairMetrics wm(walk); auto wh=heavy_ids(walk); auto wc=core_counts(walk);
  bool wf=forbidden_profile(wh,walk); std::mt19937 gen(2026104499);
  for (int i=0;i<300;++i) {
    int slot=gen()%64,next=gen()%4368;
    State before=walk; auto before_m=wm;
    double uniform=i%3==0?0.0:(gen()%10000)/10000.0;
    auto outcome=attempt_move(walk,wh,wc,wm,wf,slot,next,0.8,uniform);
    if (outcome==MoveResult::duplicate) {assert(walk.ids==before.ids && wm==before_m);++duplicate_cases;}
    if (outcome==MoveResult::accepted) ++committed;
    if (outcome==MoveResult::energy_rejected) {assert(walk.ids==before.ids && wm==before_m);++rolled_back;}
    independent(walk,wm);
    auto h=heavy_ids(walk),got=wh;std::sort(h.begin(),h.end());std::sort(got.begin(),got.end());
    assert(h==got && wc==core_counts(walk) && wf==forbidden_profile(h,walk));
  }
  assert(committed>0 && rolled_back>0);
  std::cout << "{\"passed\":true,\"direct_recounts\":" << direct_checks
            << ",\"commits\":" << committed << ",\"rollbacks\":" << rolled_back
            << ",\"duplicate_cases\":" << duplicate_cases
            << ",\"intersection_cases\":[40,40,40,40,40],\"optimizer_calls\":0}" << std::endl;
}
