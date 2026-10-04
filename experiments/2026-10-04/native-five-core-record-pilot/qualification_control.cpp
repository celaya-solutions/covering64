// Document:    Five Core Record Boundary Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      18a8fc7d2c73e8f7d692642d9e3921febeb2fc0b622615e3e46035b3a119c457
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include "scan.hpp"
#include "new_core.hpp"
#include <iostream>

int main(int argc,char** argv) {
  try {
    if(argc!=3) throw std::runtime_error("usage: qualification initial output_prefix");
    const ws::Universe u;
    std::array<bool,vc::NB> member{};
    for(int b:escape_core::ids) member[b]=true;
    auto check=[&](const std::vector<int>& ids,const std::string& name,bool expected) {
      vc::SearchState s(u,ids);s.audit();
      std::array<int,5> overlaps{};
      for(int i=0;i<4;++i) for(int b:vc::core_rows[i]) overlaps[i]+=s.chosen[b];
      for(int b:escape_core::ids) overlaps[4]+=s.chosen[b];
      bool actual=escape_core::eligible(s.cardinality,overlaps);
      if(actual!=expected) throw std::logic_error("bad qualification boundary");
      u.write(std::string(argv[2])+"-"+name+".txt",ids);
      ws::Counts counts(u,ids);auto m=ws::full_metrics(counts);
      std::cout<<"{\"case\":\""<<name<<"\",\"cardinality\":"<<s.cardinality
        <<",\"holes\":"<<s.holes<<",\"cap_admissible\":"<<(actual?"true":"false")
        <<",\"minimum_pair_count\":"<<m.minimum_pair_count<<",\"D3\":"<<m.d3
        <<",\"D4\":"<<m.d4<<",\"overlaps\":[";
      for(int i=0;i<5;++i) std::cout<<(i?",":"")<<overlaps[i];
      std::cout<<"]}\n";
    };
    for(int overlap: {55,56,57}) {
      std::vector<int> ids(escape_core::ids.begin(),escape_core::ids.begin()+overlap);
      for(int b=0;ids.size()<64 && b<vc::NB;++b) if(!member[b]) ids.push_back(b);
      std::sort(ids.begin(),ids.end());
      check(ids,"overlap-"+std::to_string(overlap),overlap<=56);
      if(overlap==56) {
        auto less=ids;less.pop_back();check(less,"cardinality-63",false);
        auto more=ids;
        for(int b=0;b<vc::NB;++b) if(!std::binary_search(ids.begin(),ids.end(),b)) {
          more.push_back(b);break;
        }
        std::sort(more.begin(),more.end());check(more,"cardinality-65",false);
      }
    }
    check(u.read(argv[1]),"initial-ineligible",false);
    std::array<int,5> synthetic={55,55,55,55,56};
    if(!escape_core::eligible(64,synthetic)) throw std::logic_error("boundary rejected");
    if(escape_core::weak_eligible(64,synthetic,9,4,104,96))
      throw std::logic_error("low-hole ineligible record accepted");
    if(!escape_core::weak_eligible(64,synthetic,11,5,0,0))
      throw std::logic_error("useful weak record suppressed");
    if(escape_core::weak_eligible(64,synthetic,12,5,0,0))
      throw std::logic_error("recording threshold ignored");
    if(escape_core::weak_eligible(63,synthetic,10,5,0,0))
      throw std::logic_error("mixed-cardinality weak record accepted");
    if(!escape_core::weak_rank_improves(11,26,true,11,27))
      throw std::logic_error("equal-hole lower-D2 record suppressed");
    if(escape_core::weak_rank_improves(11,27,true,11,27) ||
       escape_core::weak_rank_improves(11,28,true,11,27))
      throw std::logic_error("nonstrict weak record accepted");
    if(!escape_core::weak_rank_improves(10,99,true,11,27))
      throw std::logic_error("hole priority changed");
    for(int i=0;i<5;++i) {
      ++synthetic[i];
      if(escape_core::eligible(64,synthetic)) throw std::logic_error("wrong cap accepted");
      --synthetic[i];
    }
    return 0;
  } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 3;}
}
