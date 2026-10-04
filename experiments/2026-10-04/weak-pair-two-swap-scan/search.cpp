// Document:    Bounded Complete Two Swap Enumeration Driver
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      0382c32c277499c916b2fa8c2c14ef249b8e66fb6af95021bd259b06050fc212
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include "two_scan.hpp"
#include <chrono>
#include <csignal>
#include <iostream>
namespace {
volatile std::sig_atomic_t interrupted=0;
void stop(int) {interrupted=1;}
void emit(std::ostream& out,const ws::Metrics& m) {
  out<<"{\"cardinality\":"<<m.cardinality<<",\"holes\":"<<m.holes<<",\"D2max\":"<<m.d2max
    <<",\"D2sum\":"<<m.d2sum<<",\"D3\":"<<m.d3<<",\"D4\":"<<m.d4
    <<",\"minimum_pair_count\":"<<m.minimum_pair_count<<",\"core_overlaps\":[";
  for(int k=0;k<4;++k) out<<(k?",":"")<<m.core_overlaps[k];out<<"]}";
}
struct Tie {int b,c,a,d;std::uint64_t ordinal;ws::Metrics metrics;};
void emit_tie(std::ostream& out,const Tie& t) {
  out<<"\"outgoing\":["<<t.b<<","<<t.c<<"],\"incoming\":["<<t.a<<","<<t.d<<"],\"shell_ordinal\":"<<t.ordinal<<",\"metrics\":";emit(out,t.metrics);
}
}
int main(int argc,char** argv) {
try {
  if(argc!=4) throw std::runtime_error("usage: scan family seconds output_prefix");
  auto start=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
  if(std::stod(argv[2])!=120) throw std::runtime_error("scan budget must be120 seconds");
  std::signal(SIGTERM,stop);std::signal(SIGINT,stop);
  const ts::Universe u;ts::TwoSwapEngine engine(u,u.read(argv[1]));
  std::vector<int> ins;std::array<int,vc::NB> in_rank{};in_rank.fill(-1);
  for(int b=0;b<vc::NB;++b) if(!engine.initial_chosen[b]) {in_rank[b]=ins.size();ins.push_back(b);}
  if(ins.size()!=4304 || engine.initial_ids.size()!=64) throw std::logic_error("bad neighborhood size");
  std::uint64_t evaluated=0,legal=0,improving=0,records=0,pruned=0,generated=0,started=0,completed=0,last_ordinal=0;
  std::array<std::uint64_t,8> bins{},bin_shell{};
  auto best=engine.baseline.rank();std::vector<Tie> ties;
  std::string reason="complete",prefix=argv[3];bool halted=false;
  std::cout<<"{\"event\":\"start\",\"budget_seconds\":120,\"total\":"<<ts::TOTAL<<",\"outer_total\":"<<ts::OUTERS<<",\"control_limit\":";
#ifdef TS_CONTROL_LIMIT
  std::cout<<TS_CONTROL_LIMIT;
#else
  std::cout<<"null";
#endif
  std::cout<<",\"baseline\":";emit(std::cout,engine.baseline);std::cout<<"}\n";
  auto stopping=[&]() {
    if(interrupted || elapsed()>=120) {reason=interrupted?"interrupted":"time_limit";halted=true;return true;}
    return false;
  };
  std::uint64_t pair_index=0;
  for(int bi=0;bi<64 && !halted;++bi) for(int ci=bi+1;ci<64 && !halted;++ci,++pair_index) {
    int b=engine.initial_ids[bi],c=engine.initial_ids[ci];engine.begin(b,c);
    for(int ai=0;ai<4304;++ai) {
#ifdef TS_CONTROL_LIMIT
      if(started==TS_CONTROL_LIMIT) {reason="control_limit";halted=true;break;}
#endif
      if(stopping()) break;
      int a=ins[ai];engine.add_first(a);auto s=engine.support();auto candidates=engine.completions(a);
      ++started;std::uint64_t tail=4303-ai;generated+=candidates.size();pruned+=tail-candidates.size();
      int bin=s.deficit_gt_one?0:(s.size>5?1:2+s.size);++bins[bin];bin_shell[bin]+=tail;
      for(int d:candidates) {
        if(stopping()) break;
        auto m=engine.evaluate_last(d);++evaluated;
        if(m.minimum_pair_count<5) throw std::logic_error("support admitted pair-floor failure");
        last_ordinal=pair_index*ts::INNER+static_cast<std::uint64_t>(ai)*(8607-ai)/2+in_rank[d]-ai;
        if(m.legal()) {
          ++legal;
          if(m.rank()<engine.baseline.rank()) {
            ++improving;Tie t{b,c,a,d,last_ordinal,m};
            if(m.rank()<best) {
              best=m.rank();ties.clear();++records;
              std::cout<<"{\"event\":\"improvement\",\"serial\":"<<records<<",\"evaluated\":"<<evaluated
                <<",\"outer_index\":"<<started<<",\"seconds\":"<<elapsed()<<",";emit_tie(std::cout,t);std::cout<<"}\n"<<std::flush;
            }
            if(m.rank()==best) ties.push_back(t);
          }
        }
        if(evaluated%4096==0) engine.current.audit();
      }
      engine.remove_first(a);
      if(halted) break;
      ++completed;if(completed%4096==0) engine.current.audit();
    }
    engine.end(b,c);
  }
  engine.current.audit();if(engine.current.ids()!=engine.initial_ids) throw std::logic_error("final rollback failed");
  bool complete=completed==ts::OUTERS;
  if(complete && (evaluated+pruned!=ts::TOTAL || generated!=evaluated)) throw std::logic_error("incomplete accounting");
  std::ofstream output(prefix+"-ties.json");if(!output) throw std::runtime_error("cannot write ties");
  output<<"[\n";for(std::size_t i=0;i<ties.size();++i) {if(i) output<<",\n";output<<"{";emit_tie(output,ties[i]);output<<"}";}output<<"\n]\n";
  output.close();if(!output) throw std::runtime_error("ties write failed");
  std::cout<<"{\"event\":\"final\",\"complete\":"<<(complete?"true":"false")<<",\"reason\":\""<<reason
    <<"\",\"total\":"<<ts::TOTAL<<",\"outer_total\":"<<ts::OUTERS<<",\"outer_started\":"<<started<<",\"outer_completed\":"<<completed
    <<",\"evaluated\":"<<evaluated<<",\"pair_floor_pruned\":"<<pruned<<",\"eligible_generated\":"<<generated
    <<",\"pending_eligible\":"<<generated-evaluated<<",\"accounted\":"<<pruned+evaluated<<",\"last_evaluated_ordinal\":"<<last_ordinal
    <<",\"legal\":"<<legal<<",\"strictly_improving_neighbors\":"<<improving<<",\"strict_improvement_records\":"<<records
    <<",\"best_ties\":"<<ties.size()<<",\"best_rank\":["<<best.first<<","<<best.second<<"],\"support_bins\":[";
  for(int i=0;i<8;++i) std::cout<<(i?",":"")<<bins[i];std::cout<<"],\"support_shell_bins\":[";
  for(int i=0;i<8;++i) std::cout<<(i?",":"")<<bin_shell[i];std::cout<<"],\"seconds\":"<<elapsed()<<"}\n";
  return complete?0:1;
} catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 2;}
}
