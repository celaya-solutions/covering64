// Document:    Variable Cardinality Deterministic Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      d9e361cf242ca51da21b8936ed6045c36544db8b0404e5965080ebcc194c0a36
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include "kernel.hpp"
#include <iostream>
void require(bool ok,const char* message) {if(!ok) throw std::runtime_error(message);}
int main(int argc,char** argv) {
try {
  require(argc==3,"usage: controls start output_prefix");const vc::Universe u;
  auto initial=u.read(argv[1]);vc::SearchState s(u,initial);
  require(s.cardinality==65 && s.holes==0,"wrong initial cover");s.audit();
  int a=initial[0],b=initial[1];auto original=s.count;
  s.remove(a,1);s.audit();u.write(std::string(argv[2])+"-64.txt",s.ids());
  require(!s.cc[a] && s.last[a]==1,"remove CC timestamp");
  s.remove(b,2);s.audit();u.write(std::string(argv[2])+"-63.txt",s.ids());
  s.add(b,3);s.add(a,4);s.audit();require(s.count==original && s.cardinality==65,"inverse counts");
  bool rejected=false;try{s.add(a,5);}catch(const std::runtime_error&){rejected=true;}
  require(rejected && s.count==original && s.last[a]==4,"duplicate add mutation");
  s.remove(a,5);auto before=s.count;rejected=false;
  try{s.remove(a,6);}catch(const std::runtime_error&){rejected=true;}
  require(rejected && s.count==before && s.last[a]==5,"absent remove mutation");
  int t=0;while(s.count[t]!=0) ++t;
  s.cc.fill(true);s.last.fill(0);auto age3=s.incoming(t,3,99);auto age4=s.incoming(t,4,99);
  require(age3.fallback && !age4.fallback && age4.second>=0,"tabu threshold");
  auto novelty=s.incoming(t,4,10),normal=s.incoming(t,4,11);
  require(novelty.id==age4.second && normal.id==age4.best,"novelty boundary");
  s.cc.fill(false);require(s.incoming(t,100,0).id==u.carriers[t].front(),"fallback lex");
  auto oldcc=s.cc;auto weights=s.weight;s.increment_uncovered();
  for(int q=0;q<vc::NT;++q) require(s.weight[q]==weights[q]+(s.count[q]==0),"weight delta");
  require(s.cc==oldcc,"weight changed CC");
  std::array<int,6> seen{};vc::SearchState replay(u,initial);
  std::uint64_t mutation=0;
  for(std::uint64_t step=0;step<48;++step) {
    int target=-1;for(int q=0;q<vc::NT;++q) if(replay.count[q]==0) {target=q;break;}
    auto r=vc::advance(replay,step,65,target,static_cast<unsigned>((step*17)%100),
      [&](const vc::SearchState& state,const char*,int){++mutation;state.audit();return false;});
    replay.audit();++seen[static_cast<int>(r.action)];
    std::cout<<"{\"event\":\"replay\",\"step\":"<<step<<",\"target\":"<<target<<",\"draw\":"<<(step*17)%100
      <<",\"action\":\""<<vc::action_name(r.action)<<"\",\"incoming\":"<<r.incoming<<",\"first_removed\":"<<r.first_removed
      <<",\"second_removed\":"<<r.second_removed<<",\"cardinality\":"<<replay.cardinality<<",\"holes\":"<<replay.holes<<"}\n";
    if(r.stopped) break;
  }
  require(seen[static_cast<int>(vc::Action::complete_drop)]>0,"complete-drop not exercised");
  require(seen[static_cast<int>(vc::Action::double_drop)]>0,"double-drop not exercised");
  require(seen[static_cast<int>(vc::Action::add_only)]>0,"add-only not exercised");
  require(seen[static_cast<int>(vc::Action::swap)]>0,"swap not exercised");
  u.write(std::string(argv[2])+"-replay-final.txt",replay.ids());
  // The callback gate must stop immediately after the first mutation, including a swap.
  vc::SearchState stopped(u,initial);stopped.remove(stopped.outgoing(),0);
  int target=0;while(stopped.count[target]) ++target;int callbacks=0;
  auto result=vc::advance(stopped,10,65,target,99,[&](const vc::SearchState&,const char*,int){++callbacks;return true;});
  require(result.stopped && callbacks==1 && stopped.cardinality==63,"immediate stop gate");
  // Stop predicate uses both coverage and actual cardinality; this is logic only, not a witness.
  vc::SearchState predicate(u,initial);predicate.cardinality=64;
  require(vc::target_reached(predicate),"target predicate");predicate.holes=1;
  require(!vc::target_reached(predicate),"partial accepted");
  std::cout<<"{\"event\":\"controls_passed\",\"deterministic_steps\":48,\"mutations\":"<<mutation<<"}\n";
  return 0;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 2;}
}
