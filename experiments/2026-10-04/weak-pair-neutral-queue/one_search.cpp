// Document:    One Swap Scan With Capped Neutral Observations
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      8355e69a42a5ee1a3620e1851f002de3d530f72d764490ce90cd5d9652c4c90a
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include "scan.hpp"
#include <chrono>
#include <csignal>
#include <iostream>
#include "neutral.hpp"
namespace {
volatile std::sig_atomic_t interrupted=0;
void stop(int) {interrupted=1;}
void emit(std::ostream& out,const ws::Metrics& m) {
  out<<"{\"cardinality\":"<<m.cardinality<<",\"holes\":"<<m.holes<<",\"D2max\":"<<m.d2max
    <<",\"D2sum\":"<<m.d2sum<<",\"D3\":"<<m.d3<<",\"D4\":"<<m.d4
    <<",\"minimum_pair_count\":"<<m.minimum_pair_count<<",\"core_overlaps\":[";
  for(int k=0;k<4;++k) out<<(k?",":"")<<m.core_overlaps[k];out<<"]}";
}
struct Tie {int outgoing,incoming;ws::Metrics metrics;};
}
int main(int argc,char** argv) {
try {
  if(argc!=4) throw std::runtime_error("usage: scan family seconds output_prefix");
  auto start=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
  if(std::stod(argv[2])!=120) throw std::runtime_error("scan budget must be120 seconds");
  std::signal(SIGTERM,stop);std::signal(SIGINT,stop);
  const ws::Universe u;ws::SwapEngine engine(u,u.read(argv[1]));
  std::vector<int> incoming_ids;
  for(int b=0;b<vc::NB;++b) if(!engine.initial_chosen[b]) incoming_ids.push_back(b);
  const std::uint64_t total=engine.initial_ids.size()*incoming_ids.size();
  if(total!=275456 || incoming_ids.size()!=4304) throw std::logic_error("bad neighborhood size");
  std::uint64_t evaluated=0,legal=0,improving=0,records=0;
  auto best=engine.baseline.rank();std::vector<Tie> ties;
  nq::Sample<Tie> neutrals;
  std::string reason="complete",prefix=argv[3];bool halted=false;
  std::cout<<"{\"event\":\"start\",\"budget_seconds\":120,\"total\":"<<total<<",\"control_limit\":";
#ifdef WS_CONTROL_LIMIT
  std::cout<<WS_CONTROL_LIMIT;
#else
  std::cout<<"null";
#endif
  std::cout<<",\"baseline\":";emit(std::cout,engine.baseline);std::cout<<"}\n";
  for(int outgoing:engine.initial_ids) {
    for(int incoming:incoming_ids) {
#ifdef WS_CONTROL_LIMIT
      if(evaluated==WS_CONTROL_LIMIT) {reason="control_limit";halted=true;break;}
#endif
      if(interrupted || elapsed()>=120) {reason=interrupted?"interrupted":"time_limit";halted=true;break;}
      auto m=engine.evaluate(outgoing,incoming);++evaluated;
      if(m.legal()) {
        ++legal;
        if(m.rank()==engine.baseline.rank()) {
          ++neutrals.seen;
          if(neutrals.kept.size()<nq::CAP)
            neutrals.keep(nq::family(engine.initial_ids,{outgoing},{incoming}),
                          Tie{outgoing,incoming,m},evaluated);
        }
        if(m.rank()<engine.baseline.rank()) {
          ++improving;
          if(m.rank()<best) {
            best=m.rank();ties.clear();++records;
            std::cout<<"{\"event\":\"improvement\",\"serial\":"<<records<<",\"evaluated\":"<<evaluated
              <<",\"seconds\":"<<elapsed()<<",\"outgoing\":"<<outgoing<<",\"incoming\":"<<incoming<<",\"metrics\":";
            emit(std::cout,m);std::cout<<"}\n"<<std::flush;
          }
          if(m.rank()==best) ties.push_back({outgoing,incoming,m});
        }
      }
      if(evaluated%4096==0) engine.current.audit();
    }
    if(halted) break;
  }
  engine.current.audit();bool complete=evaluated==total;
  std::ofstream output(prefix+"-ties.json");if(!output) throw std::runtime_error("cannot write ties");
  output<<"[\n";
  for(std::size_t i=0;i<ties.size();++i) {
    if(i) output<<",\n";
    output<<"{\"outgoing\":"<<ties[i].outgoing<<",\"incoming\":"<<ties[i].incoming<<",\"metrics\":";
    emit(output,ties[i].metrics);output<<"}";
  }
  output<<"\n]\n";output.close();if(!output) throw std::runtime_error("ties write failed");
  nq::write(prefix,neutrals,engine.baseline.rank(),complete,
    [](std::ostream& out,const Tie& t) {
      out<<"\"outgoing\":"<<t.outgoing<<",\"incoming\":"<<t.incoming<<",\"metrics\":";
      emit(out,t.metrics);
    });
  std::cout<<"{\"event\":\"final\",\"complete\":"<<(complete?"true":"false")<<",\"reason\":\""<<reason
    <<"\",\"total\":"<<total<<",\"evaluated\":"<<evaluated<<",\"legal\":"<<legal
    <<",\"strictly_improving_neighbors\":"<<improving<<",\"strict_improvement_records\":"<<records
    <<",\"best_ties\":"<<ties.size()<<",\"best_rank\":["<<best.first<<","<<best.second
    <<"],\"seconds\":"<<elapsed()<<"}\n";
  return complete?0:1;
} catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 2;}
}
