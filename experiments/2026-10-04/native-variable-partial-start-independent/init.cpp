// Document:    Independent Partial-Start Initialization Control
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      b3999f691280a635738e37f6757c1d0ee870b72d968e052b9f3fc5095d244901
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include "../native-variable-partial-start/kernel.hpp"
#include <iostream>

void need(bool ok,const char* message) {if(!ok) throw std::runtime_error(message);}
int main(int argc,char** argv) {
  try {
    need(argc==4,"incumbent,partial,expected_holes required");
    vc::Universe universe;
    vc::SearchState incumbent(universe,universe.read(argv[1]));
    vc::SearchState live(universe,universe.read(argv[2]));
    need(incumbent.cardinality==65 && incumbent.holes==0,"complete incumbent");
    need(live.cardinality==64 && live.holes==std::stoi(argv[3]),"partial cardinality/holes");
    for(int b=0;b<4368;++b) {
      need(live.cc[b] && live.last[b]==0,"fresh CC and timestamp");
      need(incumbent.cc[b] && incumbent.last[b]==0,"fresh incumbent state");
      for(std::uint64_t step=0;step<4;++step) need(!live.eligible(b,step),"initial age guard");
      need(live.eligible(b,4)==!live.chosen[b],"age-four eligibility");
    }
    int index=0,holes=0;
    for(int a=1;a<=16;++a) for(int b=a+1;b<=16;++b) for(int c=b+1;c<=16;++c) {
      int count=0;
      for(int block:live.ids()) {
        const auto& points=universe.points[block];
        count+=std::find(points.begin(),points.end(),a)!=points.end()
          && std::find(points.begin(),points.end(),b)!=points.end()
          && std::find(points.begin(),points.end(),c)!=points.end();
      }
      need(live.count[index]==count,"independent initial triple count");
      need(live.weight[index]==1 && incumbent.weight[index]==1,"fresh unit weights");
      holes+=count==0;++index;
    }
    need(index==560 && holes==live.holes,"initial recount");
    auto old_counts=incumbent.count;auto old_chosen=incumbent.chosen;
    auto old_weights=incumbent.weight;auto old_cc=incumbent.cc;auto old_last=incumbent.last;
    live.remove(live.ids().front(),0);live.increment_uncovered();
    need(incumbent.count==old_counts && incumbent.chosen==old_chosen
      && incumbent.weight==old_weights && incumbent.cc==old_cc && incumbent.last==old_last,
      "live mutation changed separate complete incumbent");
    std::cout<<"{\"passed\":true,\"initial_live\":64,\"incumbent\":65,\"holes\":"<<holes
      <<",\"weights_one\":true,\"CC_true\":true,\"last_zero\":true,"
      <<"\"age_checks\":21840,\"separate_state\":true,\"timed_searches\":0}\n";
    return 0;
  } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
