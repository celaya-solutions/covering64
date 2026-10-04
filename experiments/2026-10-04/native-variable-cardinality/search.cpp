// Document:    Variable Cardinality Covering Search Driver
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      c9dd26c2d42016efbc3511374a21af5126303b42ffdd91876e0e7d16e25646d4
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include "kernel.hpp"
#include "cores.hpp"
#include <chrono>
#include <csignal>
#include <iostream>
#include <numeric>
namespace {
volatile std::sig_atomic_t interrupted=0;
void on_signal(int) { interrupted=1; }
using Clock=std::chrono::steady_clock;
struct Metrics { int cardinality,holes; std::array<int,4> overlap{}; };
Metrics metrics(const vc::SearchState& s) {
  Metrics m{s.cardinality,s.holes,{}};
  for(int i=0;i<4;++i) for(int b:vc::core_rows[i]) if(s.chosen[b]) ++m.overlap[i];
  return m;
}
void emit(const Metrics& m) {
  std::cout<<"{\"cardinality\":"<<m.cardinality<<",\"holes\":"<<m.holes<<",\"core_overlaps\":[";
  for(int i=0;i<4;++i) std::cout<<(i?",":"")<<m.overlap[i];
  std::cout<<"]}";
}
struct Record { bool present=false;std::vector<int> ids;Metrics m{}; };
}
int main(int argc,char** argv) {
try {
  if(argc!=5) throw std::runtime_error("usage: search start seed seconds output_prefix");
  const vc::Universe u;auto ids=u.read(argv[1]);vc::SearchState state(u,ids);
  if(state.cardinality!=65 || state.holes!=0) throw std::runtime_error("start must be a distinct complete 65-family");
  std::uint64_t seed=std::stoull(argv[2]);double seconds=std::stod(argv[3]);
  if(seconds!=120) throw std::runtime_error("frozen pilot requires 120 seconds");
  std::string prefix=argv[4];std::mt19937_64 rng(seed);std::uniform_int_distribution<unsigned> draw(0,99);
  std::signal(SIGTERM,on_signal);std::signal(SIGINT,on_signal);
  auto begin=Clock::now();auto elapsed=[&](){return std::chrono::duration<double>(Clock::now()-begin).count();};
  std::uint64_t steps=0,mutations=0,serial=0,weight_updates=0,fallbacks=0,novelties=0;
  std::array<std::uint64_t,6> actions{};int min_size=65,max_size=65;
  Record complete,raw,admissible;
  std::cout<<"{\"event\":\"start\",\"seed\":"<<seed<<",\"budget\":120}\n";
  auto save=[&](Record& r,const char* role,const vc::SearchState& s) {
    r.present=true;r.ids=s.ids();r.m=metrics(s);++serial;
    u.write(prefix+"-record-"+std::to_string(serial)+"-"+role+".txt",r.ids);
    std::cout<<"{\"event\":\"record\",\"serial\":"<<serial<<",\"role\":\""<<role
      <<"\",\"step\":"<<steps<<",\"mutations\":"<<mutations<<",\"seconds\":"<<elapsed()<<",\"metrics\":";
    emit(r.m);std::cout<<"}\n"<<std::flush;
  };
  auto observe=[&](const vc::SearchState& s,const char*,int) {
    ++mutations;min_size=std::min(min_size,s.cardinality);max_size=std::max(max_size,s.cardinality);
    if(s.holes==0 && (!complete.present || s.cardinality<complete.m.cardinality)) save(complete,"complete",s);
    if(s.cardinality==64) {
      if(!raw.present || s.holes<raw.m.holes) save(raw,"raw64",s);
      auto m=metrics(s);bool caps=*std::max_element(m.overlap.begin(),m.overlap.end())<=55;
      if(caps && (!admissible.present || s.holes<admissible.m.holes)) save(admissible,"admissible64",s);
    }
    return vc::target_reached(s);
  };
  save(complete,"complete",state);
  while(!interrupted && elapsed()<seconds && !vc::target_reached(state)) {
    int target=-1;
    if(state.holes) {
      std::uniform_int_distribution<int> hole_draw(0,state.holes-1);int rank=hole_draw(rng);
      for(int t=0;t<vc::NT;++t) if(state.count[t]==0 && rank--==0) {target=t;break;}
    }
    unsigned novelty=target<0?99:draw(rng);
    auto r=vc::advance(state,steps,complete.m.cardinality,target,novelty,observe);
    ++actions[static_cast<int>(r.action)];weight_updates+=r.weights_updated;fallbacks+=r.fallback;novelties+=r.novelty;
    if(steps<32) {
      std::cout<<"{\"event\":\"trace\",\"step\":"<<steps<<",\"target\":"<<target<<",\"draw\":"<<novelty
        <<",\"action\":\""<<vc::action_name(r.action)<<"\",\"incoming\":"<<r.incoming<<",\"removed\":["
        <<r.first_removed<<","<<r.second_removed<<"],\"metrics\":";emit(metrics(state));std::cout<<"}\n";
    }
    ++steps;if(steps%4096==0) state.audit();if(r.stopped) break;
  }
  state.audit();u.write(prefix+"-final-current.txt",state.ids());
  for(auto entry:std::array<std::pair<Record*,const char*>,3>{{{&complete,"complete"},{&raw,"raw64"},{&admissible,"admissible64"}}})
    if(entry.first->present) u.write(prefix+"-final-"+entry.second+".txt",entry.first->ids);
  bool success=vc::target_reached(state);
  std::cout<<"{\"event\":\""<<(success?"cover_found":interrupted?"interrupted":"finished")<<"\",\"seconds\":"<<elapsed()
    <<",\"iterations\":"<<steps<<",\"mutations\":"<<mutations<<",\"weight_updates\":"<<weight_updates
    <<",\"fallbacks\":"<<fallbacks<<",\"novelties\":"<<novelties<<",\"min_cardinality\":"<<min_size
    <<",\"max_cardinality\":"<<max_size<<",\"action_counts\":[";
  for(int i=0;i<6;++i) std::cout<<(i?",":"")<<actions[i];
  std::cout<<"],\"max_weight\":"<<*std::max_element(state.weight.begin(),state.weight.end())<<",\"current\":";emit(metrics(state));
  for(auto entry:std::array<std::pair<Record*,const char*>,3>{{{&complete,"complete"},{&raw,"raw64"},{&admissible,"admissible64"}}}) {
    std::cout<<",\""<<entry.second<<"\":";if(entry.first->present) emit(entry.first->m);else std::cout<<"null";
  }
  std::cout<<"}\n";return success?0:interrupted?2:1;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 3;}
}
