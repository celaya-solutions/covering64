// Document:    Fixed One Swap Kernel Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      b1f9c71c6d88d6d96c0c6f10b8681e29302c43eba9e2f1c993106806f9cfc0ae
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include "scan.hpp"
#include <iostream>
void require(bool value,const char* message) {if(!value) throw std::logic_error(message);}
bool equal(const ws::Metrics& a,const ws::Metrics& b) {
  return a.cardinality==b.cardinality && a.holes==b.holes && a.d2max==b.d2max &&
    a.d2sum==b.d2sum && a.d3==b.d3 && a.d4==b.d4 &&
    a.minimum_pair_count==b.minimum_pair_count && a.core_overlaps==b.core_overlaps;
}
int main(int argc,char** argv) {
try {
  require(argc==3,"usage: control old-H12 new-H12");const ws::Universe u;
  auto old_ids=u.read(argv[1]),new_ids=u.read(argv[2]);
  ws::SwapEngine old(u,old_ids),fresh(u,new_ids);
  std::vector<int> removed,added;
  std::set_difference(old_ids.begin(),old_ids.end(),new_ids.begin(),new_ids.end(),std::back_inserter(removed));
  std::set_difference(new_ids.begin(),new_ids.end(),old_ids.begin(),old_ids.end(),std::back_inserter(added));
  require(removed.size()==1 && added.size()==1,"not a single swap");
  require(removed[0]==3145 && added[0]==3752,"unexpected known swap");
  auto next=old.evaluate(removed[0],added[0]);
  require(next.legal() && equal(next,fresh.baseline),"positive control failed");
  require(old.baseline.rank()==std::pair<int,int>{12,34} && next.rank()==std::pair<int,int>{12,32},"wrong positive rank");
  auto reverse=fresh.evaluate(added[0],removed[0]);require(equal(reverse,old.baseline),"reverse failed");
  old.current.audit();fresh.current.audit();
  require(old.current.ids()==old_ids && fresh.current.ids()==new_ids,"rollback changed family");
  int rejected=0;
  for(auto swap:std::array<std::pair<int,int>,4>{{{-1,0},{vc::NB,0},{3145,3752},{3752,3752}}}) {
    try {fresh.evaluate(swap.first,swap.second);}catch(const std::runtime_error&) {++rejected;}
  }
  require(rejected==4,"invalid swaps accepted");fresh.current.audit();
  require(fresh.current.ids()==new_ids,"invalid swap changed family");
  std::cout<<"{\"passed\":true,\"known_outgoing\":3145,\"known_incoming\":3752,\"positive_rank_before\":[12,34],\"positive_rank_after\":[12,32],\"invalid_rejected\":4,\"full_enumeration_launched\":false}\n";
  return 0;
} catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 2;}
}
