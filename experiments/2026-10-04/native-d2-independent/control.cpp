// Document:    Independent Native D2 State and Flow Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      45759e0607fabcb4d60e4bcedd05520b2b00cb8f0a9f639ad96a9108aeef3fff
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_STRONG_NO_MAIN
#include "../native-pair-two-penalty/search.cpp"
#include "expected.hpp"
#include <cassert>
#include <sstream>

int recounts=0,commits=0,rollbacks=0,duplicates=0,core_rejects=0,shared_changed=0,low_pair_accepts=0;
std::array<std::array<bool,4368>,4> expected_member{};

template<class F> void rejects(F call) {
  bool caught=false;
  try {call();} catch(const std::exception&) {caught=true;}
  assert(caught);
}
FourCounts direct_cores(const State& s) {
  FourCounts result{};
  for(int b:s.ids) for(int c=0;c<4;++c) result[c]+=expected_member[c][b];
  return result;
}
void direct(const State& s,const D2Metrics& m,const FourCounts& cores,
            const std::vector<int>& heavy) {
  std::array<int,560> tc{};std::array<int,120> pc{};
  std::array<bool,4368> selected{};
  assert(s.ids.size()==64);
  for(int b:s.ids) {
    assert(b>=0 && b<4368 && !selected[b]);selected[b]=true;
    unsigned mask=blocks[b].mask;
    for(int t=0;t<560;++t) tc[t]+=(mask&triples[t])==triples[t];
    for(int p=0;p<120;++p) pc[p]+=(mask&pairs[p])==pairs[p];
  }
  assert(tc==s.count && pc==m.count && selected==s.selected);
  int holes=0,total=0,sum=0;std::vector<int> expected_heavy;
  for(int t=0;t<560;++t) {holes+=tc[t]==0;if(tc[t]>=6) expected_heavy.push_back(t);}
  assert(holes==s.deficit);
  for(int p=0;p<120;++p) {
    std::vector<int> values;
    for(int t=0;t<560;++t) if((pairs[p]&triples[t])==pairs[p]) values.push_back(tc[t]);
    assert(values.size()==14 && std::accumulate(values.begin(),values.end(),0)==3*pc[p]);
    int maximum=0;
    for(int a=0;a<14;++a) for(int b=a+1;b<14;++b) {
      int deficit=std::max(0,12-3*pc[p]+values[a]+values[b]);
      maximum=std::max(maximum,deficit);sum+=deficit;
    }
    assert(maximum==m.contribution[p]);total+=maximum;
  }
  assert(total==m.D2max && sum==explicit_d2_sum(s,m));
  assert(strong_energy(s,m)==20*total+holes);
  assert(primary_key(s,m)==std::make_pair(total,holes));
  assert(cores==direct_cores(s) && cores==four_counts(s));
  auto sorted=heavy;std::sort(sorted.begin(),sorted.end());assert(sorted==expected_heavy);
  ++recounts;
}
bool same_state(const State& a,const State& b) {
  return a.ids==b.ids && a.count==b.count && a.selected==b.selected && a.deficit==b.deficit;
}
void same_heavy(std::vector<int> a,std::vector<int> b) {
  std::sort(a.begin(),a.end());std::sort(b.begin(),b.end());assert(a==b);
}

int main(int argc,char** argv) {
  assert(argc==4);
  universe();initialize_cores();initialize_pairs();initialize_fourth();
  std::vector<unsigned> ep,et,eb;
  for(int a=0;a<16;++a) for(int b=a+1;b<16;++b) {
    ep.push_back((1u<<a)|(1u<<b));
    for(int c=b+1;c<16;++c) {
      et.push_back((1u<<a)|(1u<<b)|(1u<<c));
      for(int d=c+1;d<16;++d) for(int e=d+1;e<16;++e)
        eb.push_back((1u<<a)|(1u<<b)|(1u<<c)|(1u<<d)|(1u<<e));
    }
  }
  assert(ep==pairs && et==triples && eb.size()==4368);
  for(int b=0;b<4368;++b) assert(eb[b]==blocks[b].mask && bymask[eb[b]]==b);
  for(int c=0;c<4;++c) for(int b:EXPECTED_CORES[c]) {
    assert(!expected_member[c][b]);expected_member[c][b]=true;
  }
  for(int c=0;c<4;++c) for(int b=0;b<4368;++b)
    assert(expected_member[c][b]==(c==3?fourth_member[b]:core_member[c][b]));

  int tie_profiles=0,extremal_profiles=0,flow_controls=0;
  for(int high:{1,2,6,7,63,64}) for(int mask=0;mask<(1<<14);++mask) {
    std::array<int,14> values{};
    for(int i=0;i<14;++i) values[i]=(mask&(1<<i))?high:0;
    auto sorted=values;std::sort(sorted.begin(),sorted.end(),std::greater<int>());
    assert(largest_two(values)==std::make_pair(sorted[0],sorted[1]));++tie_profiles;
  }
  for(int p=0;p<=64;++p) for(int first=0;first<=p;++first) for(int second=0;second<=first;++second) {
    if(first+second>3*p || 3*p>first+13*second) continue;
    std::array<int,14> values{};values[0]=first;values[1]=second;int remaining=3*p-first-second;
    for(int i=2;i<14;++i) {values[i]=std::min(second,remaining);remaining-=values[i];}
    int maximum=0;for(int a=0;a<14;++a) for(int b=a+1;b<14;++b)
      maximum=std::max(maximum,std::max(0,12-3*p+values[a]+values[b]));
    assert(!remaining && compact_deficit(p,values)==maximum);++extremal_profiles;
  }
  for(int holes=0;holes<=560;++holes) for(int d2:{0,1,2,1440}) for(bool interrupted:{false,true}) {
    auto want=d2==0?(holes==0?"cover_found":"qualified_hint_found"):(interrupted?"interrupted":"finished");
    assert(strong_finish_event(holes,d2,interrupted)==want && target_reached(d2)==(d2==0));++flow_controls;
  }
  rejects([]{strong_finish_event(-1,0,false);});rejects([]{strong_finish_event(561,0,false);});
  rejects([]{strong_finish_event(1,-1,false);});

  State first(read_blocks(argv[1])),second(read_blocks(argv[2]));
  assert(first.deficit==48 && second.deficit==49);
  assert(D2Metrics(first).D2max==75 && D2Metrics(second).D2max==74);
  std::array<int,5> intersections{};
  for(const State& seed:{first,second}) {
    D2Metrics baseline(seed);auto seed_h=heavy_ids(seed);auto seed_c=four_counts(seed);
    direct(seed,baseline,seed_c,seed_h);
    for(int k=0;k<=4;++k) {
      int cases=0;
      for(int slot=0;slot<64 && cases<20;++slot) for(int next=0;next<4368 && cases<20;++next) {
        int old=seed.ids[slot];
        if(seed.selected[next] || __builtin_popcount(blocks[old].mask&blocks[next].mask)!=k) continue;
        State proposal=seed;proposal.move(slot,next);D2Metrics fresh(proposal);auto proposal_c=direct_cores(proposal);
        assert(four_caps_pass(proposal_c));direct(proposal,fresh,proposal_c,heavy_ids(proposal));
        for(int p=0;p<120;++p) if((blocks[old].mask&pairs[p])==pairs[p] &&
            (blocks[next].mask&pairs[p])==pairs[p] && baseline.contribution[p]!=fresh.contribution[p]) {
          assert(baseline.count[p]==fresh.count[p]);++shared_changed;
        }
        int delta=strong_energy(proposal,fresh)-strong_energy(seed,baseline);
        for(bool force_accept:{false,true}) {
          State s=seed;D2Metrics m=baseline;auto h=seed_h;auto c=seed_c;
          double u=force_accept?0.0:1.0;
          auto outcome=attempt_strong_move(s,h,c,m,slot,next,0.8,u);
          bool accept=force_accept || delta<=0;
          assert(outcome==(accept?StrongMove::accepted:StrongMove::energy_rejected));
          if(accept) {assert(same_state(s,proposal) && m==fresh);++commits;}
          else {assert(same_state(s,seed) && m==baseline && c==seed_c);same_heavy(h,seed_h);++rollbacks;}
          direct(s,m,c,h);
        }
        if(delta>0) {
          double threshold=std::exp(-double(delta)/20.0/0.8);
          for(bool accept:{false,true}) {
            State s=seed;D2Metrics m=baseline;auto h=seed_h;auto c=seed_c;
            double u=accept?threshold/2:(1+threshold)/2;
            auto result=attempt_strong_move(s,h,c,m,slot,next,0.8,u);
            assert(result==(accept?StrongMove::accepted:StrongMove::energy_rejected));
            direct(s,m,c,h);if(accept) ++commits;else ++rollbacks;
          }
        }
        ++cases;++intersections[k];
      }
      assert(cases==20);
    }
    State walk=seed;D2Metrics m=baseline;auto h=seed_h;auto c=seed_c;std::mt19937 gen(2026104599);
    for(int i=0;i<150;++i) {
      int slot=gen()%64,next=i%7==0?walk.ids[gen()%64]:gen()%4368;
      State before=walk;auto bm=m;auto bh=h;auto bc=c;
      auto result=attempt_strong_move(walk,h,c,m,slot,next,0.8,i%3==0?0.0:1.0);
      if(result==StrongMove::accepted) {
        ++commits;
        if(*std::min_element(m.count.begin(),m.count.end())<5) ++low_pair_accepts;
      }
      else {
        assert(same_state(walk,before) && m==bm && c==bc);same_heavy(h,bh);
        if(result==StrongMove::duplicate) ++duplicates;
        if(result==StrongMove::energy_rejected) ++rollbacks;
      }
      direct(walk,m,c,h);
    }
  }
  assert(shared_changed>0 && duplicates>0 && commits>0 && rollbacks>0 && low_pair_accepts>0);
  for(int core=0;core<4;++core) {
    std::vector<int> ids(EXPECTED_CORES[core].begin(),EXPECTED_CORES[core].begin()+55);
    for(int b=0;ids.size()<64;++b) if(!expected_member[core][b]) ids.push_back(b);
    State s(ids);D2Metrics m(s);auto h=heavy_ids(s);auto c=four_counts(s);
    assert(c[core]==55 && four_caps_pass(c));direct(s,m,c,h);
    audit_strong(s,h,c,m,false);
    State before=s;auto bm=m;auto bh=h;auto bc=c;
    int next=EXPECTED_CORES[core][55];auto proposed=proposed_four_counts(c,s.ids[63],next);
    assert(proposed[core]==56 && !four_caps_pass(proposed));
    assert(attempt_strong_move(s,h,c,m,63,next,1.0,0.0)==StrongMove::core_rejected);
    assert(same_state(s,before) && m==bm && c==bc);same_heavy(h,bh);++core_rejects;
    for(int bad:{-1,56,64}) {auto damaged=c;damaged[core]=bad;assert(!four_caps_pass(damaged));}
  }
  auto m=D2Metrics(first);auto h=heavy_ids(first);auto c=four_counts(first);
  rejects([&]{auto bad=m;bad.D2max=0;audit_strong(first,h,c,bad,true);});
  rejects([&]{auto bad=m;++bad.count[0];audit_strong(first,h,c,bad);});
  rejects([&]{auto bad=m;++bad.contribution[0];audit_strong(first,h,c,bad);});
  rejects([&]{auto bad=c;++bad[3];audit_strong(first,h,bad,m);});
  rejects([&]{auto bad=first;bad.ids[0]=bad.ids[1];audit_strong(bad,h,c,m);});

  std::ostringstream sink;auto* old_output=std::cout.rdbuf(sink.rdbuf());
  std::string prefix=argv[3];StrongRecords records;
  records.consider(prefix,first,h,c,m,0,0);
  records.consider(prefix,second,heavy_ids(second),four_counts(second),D2Metrics(second),0,1);
  assert(records.raw==first.ids && records.primary==second.ids && records.qualified.empty());
  assert(records.serial==3);
  records.consider(prefix,second,heavy_ids(second),four_counts(second),D2Metrics(second),0,2);
  assert(records.serial==3);
  for(int n=0;n<9;++n) assert(records.restart(first.ids,n)==(n%3==0?first.ids:second.ids));
  finish_strong(prefix+"-normal",first,m,h,c,records,"finished",2,0,0,0);
  finish_strong(prefix+"-signal",first,m,h,c,records,"interrupted",2,0,0,0);
  rejects([&]{finish_strong(prefix+"-bad",first,m,h,c,records,"cover_found",2,0,0,0);});
  rejects([&]{finish_strong(prefix+"-bad",first,m,h,c,records,"qualified_hint_found",2,0,0,0);});
  rejects([&]{auto forged=records;forged.qualified=first.ids;
    finish_strong(prefix+"-bad",first,m,h,c,forged,"finished",2,0,0,0);});
  State scalar=first;D2Metrics scalar_m=m;
  scalar.deficit=100;scalar_m.D2max=1;
  State scalar_other=first;D2Metrics scalar_other_m=m;
  scalar_other.deficit=0;scalar_other_m.D2max=2;
  assert(primary_key(scalar,scalar_m)<primary_key(scalar_other,scalar_other_m));
  assert(strong_energy(scalar,scalar_m)>strong_energy(scalar_other,scalar_other_m));
  std::cout.rdbuf(old_output);
  std::ofstream(prefix+"-flow.jsonl")<<sink.str();
  std::cout<<"{\"passed\":true,\"optimizer_calls\":0,\"direct_recounts\":"<<recounts
    <<",\"commits\":"<<commits<<",\"rollbacks\":"<<rollbacks<<",\"duplicates\":"<<duplicates
    <<",\"core_rejections\":"<<core_rejects<<",\"shared_pair_contribution_changes\":"<<shared_changed
    <<",\"accepted_states_below_pair_floor_five\":"<<low_pair_accepts
    <<",\"tie_profiles\":"<<tie_profiles<<",\"extremal_profiles\":"<<extremal_profiles
    <<",\"flow_controls\":"<<flow_controls<<",\"intersection_cases\":[40,40,40,40,40]"
    <<",\"positive_zero_D2_family_control_available\":false}"<<std::endl;
}
