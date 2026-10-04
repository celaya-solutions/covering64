// Document:    Five Core Record Only Partial Start Pilot
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      cf54b965e4c2781f7c73658f8507ad5eabf86c6f8643804939aa3c60d6dec88c
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include "kernel.hpp"
#include "cores.hpp"
#include "scan.hpp"
#include "new_core.hpp"
#include <chrono>
#include <csignal>
#include <iostream>
#include <numeric>
namespace {
volatile std::sig_atomic_t interrupted=0;
void on_signal(int) { interrupted=1; }
using Clock=std::chrono::steady_clock;
struct Metrics { int cardinality,holes; std::array<int,5> overlap{}; };
Metrics metrics(const vc::SearchState& s) {
  Metrics m{s.cardinality,s.holes,{}};
  for(int i=0;i<4;++i) for(int b:vc::core_rows[i]) if(s.chosen[b]) ++m.overlap[i];
  for(int b:escape_core::ids) if(s.chosen[b]) ++m.overlap[4];
  return m;
}
void emit(const Metrics& m) {
  std::cout<<"{\"cardinality\":"<<m.cardinality<<",\"holes\":"<<m.holes<<",\"core_overlaps\":[";
  for(int i=0;i<5;++i) std::cout<<(i?",":"")<<m.overlap[i];
  std::cout<<"]}";
}
struct Record { bool present=false;std::vector<int> ids;Metrics m{};int d2=0; };
}
int main(int argc,char** argv) {
try {
  if(argc!=6) throw std::runtime_error("usage: search complete_incumbent partial_start seed seconds output_prefix");
  const ws::Universe u;vc::SearchState incumbent(u,u.read(argv[1]));
  vc::SearchState state(u,u.read(argv[2]));
  if(incumbent.cardinality!=65 || incumbent.holes!=0) throw std::runtime_error("incumbent must be a distinct complete 65-family");
  if(state.cardinality!=64 || state.holes==0) throw std::runtime_error("start must be a distinct incomplete 64-family");
  std::uint64_t seed=std::stoull(argv[3]);double seconds=std::stod(argv[4]);
  if(seconds!=300) throw std::runtime_error("frozen pilot requires 300 seconds");
  std::string prefix=argv[5];std::mt19937_64 rng(seed);std::uniform_int_distribution<unsigned> draw(0,99);
  std::signal(SIGTERM,on_signal);std::signal(SIGINT,on_signal);
  auto begin=Clock::now();auto elapsed=[&](){return std::chrono::duration<double>(Clock::now()-begin).count();};
  std::uint64_t steps=0,mutations=0,serial=0,weight_updates=0,fallbacks=0,novelties=0;
  std::array<std::uint64_t,6> actions{};int min_size=state.cardinality,max_size=state.cardinality;
  Record complete,raw,admissible,weak;
  std::cout<<"{\"event\":\"start\",\"seed\":"<<seed<<",\"budget\":300";
#ifdef VC_CONTROL_STEPS
  std::cout<<",\"mode\":\"control\",\"control_step_limit\":"<<VC_CONTROL_STEPS;
#else
  std::cout<<",\"mode\":\"search\",\"control_step_limit\":null";
#endif
  std::cout<<"}\n";
  auto save=[&](Record& r,const char* role,const vc::SearchState& s) {
    r.present=true;r.ids=s.ids();r.m=metrics(s);++serial;
    u.write(prefix+"-record-"+std::to_string(serial)+"-"+role+".txt",r.ids);
    std::cout<<"{\"event\":\"record\",\"serial\":"<<serial<<",\"role\":\""<<role
      <<"\",\"step\":"<<steps<<",\"mutations\":"<<mutations<<",\"seconds\":"<<elapsed()<<",\"metrics\":";
    emit(r.m);
    if(&r==&weak) std::cout<<",\"weak_D2max\":"<<r.d2;
    std::cout<<"}\n"<<std::flush;
  };
  auto consider=[&](const vc::SearchState& s) {
    if(s.holes==0 && (!complete.present || s.cardinality<complete.m.cardinality)) save(complete,"complete",s);
    if(s.cardinality==64) {
      if(!raw.present || s.holes<raw.m.holes) save(raw,"raw64",s);
      auto m=metrics(s);bool caps=escape_core::eligible(s.cardinality,m.overlap);
      if(caps && (!admissible.present || s.holes<admissible.m.holes)) save(admissible,"admissible64",s);
      if(caps && s.holes<=11 && (!weak.present || s.holes<=weak.m.holes)) {
        ws::Counts counts(u,s.ids());
        if(*std::min_element(counts.pair.begin(),counts.pair.end())>=5) {
          auto profile=ws::full_metrics(counts);
          if(escape_core::weak_eligible(s.cardinality,m.overlap,s.holes,
              profile.minimum_pair_count,profile.d3,profile.d4) &&
              escape_core::weak_rank_improves(s.holes,profile.d2max,weak.present,weak.m.holes,weak.d2)) {
            weak.d2=profile.d2max;save(weak,"weak64",s);
          }
        }
      }
    }
    return vc::target_reached(s);
  };
  auto observe=[&](const vc::SearchState& s,const char*,int) {
    ++mutations;min_size=std::min(min_size,s.cardinality);max_size=std::max(max_size,s.cardinality);
    return consider(s);
  };
  save(complete,"complete",incumbent);
  consider(state); // Initial records do not count as search mutations.
  while(!interrupted && elapsed()<seconds && !vc::target_reached(state)) {
#ifdef VC_CONTROL_STEPS
    if(steps==VC_CONTROL_STEPS) break; // Separate control binary; absent in production build.
#endif
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
        <<r.first_removed<<","<<r.second_removed<<"],\"fallback\":"<<(r.fallback?"true":"false")
        <<",\"novelty\":"<<(r.novelty?"true":"false")<<",\"weights_updated\":"<<(r.weights_updated?"true":"false")<<",\"metrics\":";emit(metrics(state));std::cout<<"}\n";
    }
    ++steps;if(steps%4096==0) state.audit();if(r.stopped) break;
  }
  state.audit();u.write(prefix+"-final-current.txt",state.ids());
  for(auto entry:std::array<std::pair<Record*,const char*>,4>{{{&complete,"complete"},{&raw,"raw64"},{&admissible,"admissible64"},{&weak,"weak64"}}})
    if(entry.first->present) u.write(prefix+"-final-"+entry.second+".txt",entry.first->ids);
  bool success=vc::target_reached(state);
  std::cout<<"{\"event\":\""<<(success?"cover_found":interrupted?"interrupted":"finished")<<"\",\"seconds\":"<<elapsed()
    <<",\"iterations\":"<<steps<<",\"mutations\":"<<mutations<<",\"weight_updates\":"<<weight_updates
    <<",\"fallbacks\":"<<fallbacks<<",\"novelties\":"<<novelties<<",\"min_cardinality\":"<<min_size
    <<",\"max_cardinality\":"<<max_size<<",\"action_counts\":[";
  for(int i=0;i<6;++i) std::cout<<(i?",":"")<<actions[i];
  std::cout<<"],\"max_weight\":"<<*std::max_element(state.weight.begin(),state.weight.end())<<",\"current\":";emit(metrics(state));
  for(auto entry:std::array<std::pair<Record*,const char*>,4>{{{&complete,"complete"},{&raw,"raw64"},{&admissible,"admissible64"},{&weak,"weak64"}}}) {
    std::cout<<",\""<<entry.second<<"\":";if(entry.first->present) emit(entry.first->m);else std::cout<<"null";
  }
  std::cout<<",\"weak_D2max\":";
  if(weak.present) std::cout<<weak.d2; else std::cout<<"null";
  std::cout<<"}\n";return success?0:interrupted?2:1;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 3;}
}
