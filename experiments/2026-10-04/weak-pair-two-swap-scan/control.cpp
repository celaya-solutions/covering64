// Document:    Fixed Two Swap Kernel Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      84fd7dcdaadc6e8c8bb3513ba524ccc0f76671343670f6dbf0d00a4bd12c31c3
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include "two_scan.hpp"
#include <iostream>
void require(bool v,const char* message) {if(!v) throw std::logic_error(message);}
bool equal(const ws::Metrics& a,const ws::Metrics& b) {
  return a.cardinality==b.cardinality && a.holes==b.holes && a.d2max==b.d2max &&
    a.d2sum==b.d2sum && a.d3==b.d3 && a.d4==b.d4 && a.minimum_pair_count==b.minimum_pair_count && a.core_overlaps==b.core_overlaps;
}
int main(int argc,char** argv) {
try {
  require(argc==3,"usage: control old-H12 new-H12");const ts::Universe u;
  auto old_ids=u.read(argv[1]),new_ids=u.read(argv[2]);ts::TwoSwapEngine old(u,old_ids),fresh(u,new_ids);
  std::vector<int> removed,added;
  std::set_difference(old_ids.begin(),old_ids.end(),new_ids.begin(),new_ids.end(),std::back_inserter(removed));
  std::set_difference(new_ids.begin(),new_ids.end(),old_ids.begin(),old_ids.end(),std::back_inserter(added));
  require(removed.size()==2 && added.size()==2,"not a two swap");
  auto next=old.evaluate(removed[0],removed[1],added[0],added[1]);
  require(next.legal() && equal(next,fresh.baseline),"positive control failed");
  require(old.baseline.rank()==std::pair<int,int>{12,34} && next.rank()==std::pair<int,int>{12,29},"wrong positive rank");
  auto reverse=fresh.evaluate(added[0],added[1],removed[0],removed[1]);require(equal(reverse,old.baseline),"reverse failed");
  old.begin(removed[0],removed[1]);old.add_first(added[0]);auto completions=old.completions(added[0]);
  require(std::find(completions.begin(),completions.end(),added[1])!=completions.end(),"positive completion missing");
  old.current.audit();auto before=old.current.ids();old.evaluate_last(added[1]);require(old.current.ids()==before,"63-state rollback failed");
  old.remove_first(added[0]);old.end(removed[0],removed[1]);
  fresh.begin(1142,1871);fresh.add_first(145);auto support=fresh.support();require(!support.impossible && support.mask==0,"empty support failed");
  auto empty=fresh.completions(145);int expected=0;for(int d=146;d<vc::NB;++d) expected+=!fresh.initial_chosen[d];
  require(int(empty.size())==expected,"empty support incomplete");fresh.remove_first(145);fresh.end(1142,1871);
  int rejected=0;
  for(auto swap:std::array<std::array<int,4>,6>{{{{-1,1,2,3}},{{4368,4369,2,3}},{{added[0],added[0],removed[0],removed[1]}},{{added[0],added[1],removed[0],removed[0]}},{{added[0],added[1],added[0],added[1]}},{{added[1],added[0],removed[0],removed[1]}}}}) {
    try {fresh.evaluate(swap[0],swap[1],swap[2],swap[3]);}catch(const std::runtime_error&) {++rejected;}
  }
  try {fresh.support();}catch(const std::runtime_error&) {++rejected;}
  try {fresh.add_first(0);}catch(const std::runtime_error&) {++rejected;}
  try {fresh.evaluate_last(0);}catch(const std::runtime_error&) {++rejected;}
  try {fresh.end(-1,-1);}catch(const std::runtime_error&) {++rejected;}
  require(rejected==10,"invalid operations accepted");
  old.current.audit();fresh.current.audit();require(old.current.ids()==old_ids && fresh.current.ids()==new_ids,"rollback changed family");
  std::cout<<"{\"passed\":true,\"positive_rank_before\":[12,34],\"positive_rank_after\":[12,29],\"invalid_rejected\":10,\"empty_support_completions\":"<<empty.size()<<",\"full_enumeration_launched\":false}\n";
  return 0;
} catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 2;}
}
