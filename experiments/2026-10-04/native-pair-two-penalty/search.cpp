// Document:    Native Compact Pair-Two Deficit Hint Search
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      cdbd0160d1f6fe7be10b3bf4b3951686272738f4f0d22552fd7e6d30dc2f12ea
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_PAIR_NO_MAIN
#include "native_pair_base.cpp"
#include "fourth_core.hpp"

using FourCounts=std::array<int,4>;
std::array<bool,4368> fourth_member{};
void initialize_fourth() {
  for (int id:FOURTH_CORE_IDS) {
    if (id<0 || id>=4368 || fourth_member[id]) throw std::runtime_error("Bad fourth core row");
    fourth_member[id]=true;
  }
}
FourCounts four_counts(const State& s) {
  auto old=core_counts(s); FourCounts result{old[0],old[1],old[2],0};
  for (int id:s.ids) result[3]+=fourth_member[id];
  return result;
}
bool four_caps_pass(const FourCounts& c) {
  return std::all_of(c.begin(),c.end(),[](int x){return x>=0 && x<=55;});
}
FourCounts proposed_four_counts(FourCounts c,int old,int next) {
  auto first=proposed_core_counts(CoreCounts{c[0],c[1],c[2]},old,next);
  return {first[0],first[1],first[2],c[3]+int(fourth_member[next])-int(fourth_member[old])};
}
std::pair<int,int> largest_two(const std::array<int,14>& values) {
  int first=-1,second=-1;
  for (int value:values) {
    if (value>=first) {second=first;first=value;} else if (value>second) second=value;
  }
  return {first,second};
}
int compact_deficit(int pair_count,const std::array<int,14>& values) {
  auto [first,second]=largest_two(values);
  return std::max(0,12-3*pair_count+first+second);
}
struct D2Metrics {
  std::array<int,120> count{},contribution{};
  int D2max=0;
  explicit D2Metrics(const State& s) {
    for (int b:s.ids) for (int p:block_pairs[b]) ++count[p];
    for (int p=0;p<120;++p) recount(p,s);
  }
  void recount(int p,const State& s) {
    std::array<int,14> values{};
    for (int i=0;i<14;++i) values[i]=s.count[pair_triples[p][i]];
    D2max-=contribution[p]; contribution[p]=compact_deficit(count[p],values); D2max+=contribution[p];
  }
  void moved(int old,int next,const State& s) {
    std::array<int,20> touched{};int n=0;
    for (int p:block_pairs[old]) {--count[p];touched[n++]=p;}
    for (int p:block_pairs[next]) {
      ++count[p];
      if (std::find(touched.begin(),touched.begin()+n,p)==touched.begin()+n) touched[n++]=p;
    }
    for (int i=0;i<n;++i) recount(touched[i],s);
  }
  bool operator==(const D2Metrics&) const=default;
};
int explicit_d2_sum(const State& s,const D2Metrics& m) {
  int sum=0;
  for (int p=0;p<120;++p) for (int a=0;a<14;++a) for (int b=a+1;b<14;++b)
    sum+=std::max(0,12-3*m.count[p]+s.count[pair_triples[p][a]]+s.count[pair_triples[p][b]]);
  return sum;
}
int strong_energy(const State& s,const D2Metrics& m) {return 20*m.D2max+s.deficit;}
std::pair<int,int> primary_key(const State& s,const D2Metrics& m) {return {m.D2max,s.deficit};}
bool target_reached(int D2max) {return D2max==0;}
std::string strong_finish_event(int holes,int D2max,bool interrupted) {
  if (holes<0 || holes>560 || D2max<0) throw std::runtime_error("Invalid finish metrics");
  if (target_reached(D2max)) return holes==0?"cover_found":"qualified_hint_found";
  return interrupted?"interrupted":"finished";
}
void audit_strong(const State& s,const std::vector<int>& heavy,const FourCounts& cores,
                  const D2Metrics& m,bool qualified=false) {
  audit_state(s,heavy);audit_core_state(s,CoreCounts{cores[0],cores[1],cores[2]});
  if (four_counts(s)!=cores || !four_caps_pass(cores) || !(D2Metrics(s)==m))
    throw std::runtime_error("Four-core or D2 recount failed");
  PairMetrics old(s);
  if (old.count!=m.count) throw std::runtime_error("Pair count baseline mismatch");
  int full=explicit_d2_sum(s,m);
  if (m.D2max>full || full>91*m.D2max || (m.D2max==0)!=(full==0))
    throw std::runtime_error("Compact/full deficit inconsistency");
  if (qualified && (m.D2max!=0 || old.D3!=0 || old.D4!=0 ||
      *std::min_element(m.count.begin(),m.count.end())<5))
    throw std::runtime_error("False qualified hint");
}
enum class StrongMove {duplicate,core_rejected,accepted,energy_rejected};
StrongMove attempt_strong_move(State& s,std::vector<int>& heavy,FourCounts& cores,D2Metrics& m,
                              int slot,int next,double temperature,double uniform) {
  if (s.selected[next]) return StrongMove::duplicate;
  int old=s.ids[slot];auto proposed=proposed_four_counts(cores,old,next);
  if (!four_caps_pass(proposed)) return StrongMove::core_rejected;
  int before=strong_energy(s,m);
  s.move(slot,next);m.moved(old,next,s);update_heavy(heavy,s,old,next);
  double delta=double(strong_energy(s,m)-before)/20.0;
  if (delta<=0 || uniform<std::exp(-delta/temperature)) {cores=proposed;return StrongMove::accepted;}
  s.move(slot,old);m.moved(next,old,s);update_heavy(heavy,s,old,next);
  return StrongMove::energy_rejected;
}
void print_strong_metrics(const State& s,const D2Metrics& m) {
  PairMetrics old(s);auto cores=four_counts(s);
  std::cout << "{\"holes\":" << s.deficit << ",\"D2max\":" << m.D2max
            << ",\"D2sum\":" << explicit_d2_sum(s,m) << ",\"D3\":" << old.D3 << ",\"D4\":" << old.D4
            << ",\"energy\":" << strong_energy(s,m) << ",\"pair_min\":"
            << *std::min_element(m.count.begin(),m.count.end()) << ",\"forbidden\":"
            << (forbidden_profile(heavy_ids(s),s)?"true":"false") << ",\"core_overlaps\":["
            << cores[0] << ',' << cores[1] << ',' << cores[2] << ',' << cores[3] << "]}";
}
struct StrongRecords {
  std::vector<int> raw,primary,qualified;
  int raw_holes=561;std::pair<int,int> best_key{1000000000,561};uint64_t serial=0;
  void consider(const std::string& prefix,const State& s,const std::vector<int>& heavy,
                const FourCounts& cores,const D2Metrics& m,double seconds,uint64_t iterations) {
    auto record=[&](const std::string& role,std::vector<int>& target) {
      audit_strong(s,heavy,cores,m,role=="qualified");target=s.ids;++serial;
      save(prefix+"-record-"+std::to_string(serial)+"-"+role+".txt",target);
      std::cout << "{\"event\":\"record\",\"role\":\"" << role << "\",\"serial\":" << serial
                << ",\"seconds\":" << seconds << ",\"iterations\":" << iterations << ",\"metrics\":";
      print_strong_metrics(s,m);std::cout << '}' << std::endl;
    };
    if (!forbidden_profile(heavy,s) && s.deficit<raw_holes) {record("raw",raw);raw_holes=s.deficit;}
    if (primary_key(s,m)<best_key) {record("primary",primary);best_key=primary_key(s,m);}
    if (target_reached(m.D2max) && qualified.empty()) record("qualified",qualified);
  }
  const std::vector<int>& restart(const std::vector<int>& initial,uint64_t n) const {
    return n%3==0 || primary.empty()?initial:primary;
  }
};
void finish_strong(const std::string& prefix,const State& current,const D2Metrics& m,
                   const std::vector<int>& heavy,const FourCounts& cores,const StrongRecords& records,
                   const std::string& event,uint64_t iterations,uint64_t restarts,
                   uint64_t core_rejections,double seconds) {
  if (records.raw.empty() || records.primary.empty() ||
      event!=strong_finish_event(current.deficit,m.D2max,event=="interrupted"))
    throw std::runtime_error("Invalid final status or records");
  audit_strong(current,heavy,cores,m,target_reached(m.D2max));
  if (target_reached(m.D2max) != !records.qualified.empty())
    throw std::runtime_error("Qualified record/status mismatch");
  save(prefix+"-final-current.txt",current.ids);
  std::cout << "{\"event\":\"" << event << "\",\"iterations\":" << iterations << ",\"restarts\":" << restarts
            << ",\"core_rejections\":" << core_rejections << ",\"seconds\":" << seconds << ",\"current\":";
  print_strong_metrics(current,m);
  for (const auto& item:{std::make_pair("raw",&records.raw),std::make_pair("primary",&records.primary),
                         std::make_pair("qualified",&records.qualified)}) {
    std::cout << ",\"" << item.first << "\":";
    if (item.second->empty()) {std::cout << "null";continue;}
    State s(*item.second);D2Metrics metric(s);
    audit_strong(s,heavy_ids(s),four_counts(s),metric,std::string(item.first)=="qualified");
    save(prefix+"-final-"+item.first+".txt",s.ids);print_strong_metrics(s,metric);
  }
  std::cout << '}' << std::endl;
}
#ifndef NATIVE_STRONG_NO_MAIN
int main(int argc,char** argv) {
  try {
    universe();initialize_cores();initialize_pairs();initialize_fourth();
    if (argc==3 && std::string(argv[1])=="--metrics") {
      State s(read_blocks(argv[2]));
      if (s.ids.size()!=64) throw std::runtime_error("Expected exactly64 blocks");
      print_strong_metrics(s,D2Metrics(s));std::cout << '\n';return 0;
    }
    if (argc!=5) throw std::runtime_error("usage: START SEED SECONDS OUTPUT_PREFIX");
    auto initial=read_blocks(argv[1]);State state(initial);D2Metrics metrics(state);
    auto heavy=heavy_ids(state);auto cores=four_counts(state);
    audit_strong(state,heavy,cores,metrics);
    if (forbidden_profile(heavy,state)) throw std::runtime_error("Expected profile-clear assigned hint");
    uint64_t seed=std::stoull(argv[2]);double budget=std::stod(argv[3]);
    if (!std::isfinite(budget) || budget<=0) throw std::runtime_error("Invalid budget");
    std::string prefix=argv[4];rng.seed(seed);std::signal(SIGTERM,stop_search);std::signal(SIGINT,stop_search);
    auto start=std::chrono::steady_clock::now();
    auto elapsed=[&]{return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
    StrongRecords records;uint64_t iterations=0,restarts=0,core_rejections=0;double last_progress=0;
    std::cout << "{\"event\":\"start\",\"seed\":" << seed << ",\"budget\":" << budget << '}' << std::endl;
    records.consider(prefix,state,heavy,cores,metrics,elapsed(),iterations);
    while (elapsed()<budget && !stopped && !target_reached(metrics.D2max)) {
      state=State(records.restart(initial,restarts));metrics=D2Metrics(state);heavy=heavy_ids(state);cores=four_counts(state);
      audit_strong(state,heavy,cores,metrics);
      for (uint64_t step=0;step<1500000;++step) {
        if ((step&4095)==0) {
          audit_strong(state,heavy,cores,metrics);
          if (elapsed()>=budget || stopped) break;
          if (elapsed()-last_progress>=30) {
            last_progress=elapsed();std::cout << "{\"event\":\"progress\",\"seconds\":" << last_progress
              << ",\"iterations\":" << iterations << ",\"restarts\":" << restarts << ",\"metrics\":";
            print_strong_metrics(state,metrics);std::cout << '}' << std::endl;
          }
        }
        int slot=randint(64),old=state.ids[slot],next;
        if (randint(8)==0 && state.deficit>0) {
          int target;do target=randint(560);while(state.count[target]!=0);
          next=containing[target][randint(int(containing[target].size()))];
        } else {
          int remove,add;do remove=randint(16);while(!(blocks[old].mask&(1u<<remove)));
          do add=randint(16);while(blocks[old].mask&(1u<<add));
          next=bymask[blocks[old].mask^(1u<<remove)^(1u<<add)];
        }
        double phase=double(step)/1500000;
        double temperature=0.06+(0.7+0.1*(restarts%4))*std::pow(1-phase,3);
        auto outcome=attempt_strong_move(state,heavy,cores,metrics,slot,next,temperature,
                                        std::generate_canonical<double,53>(rng));
        ++iterations;core_rejections+=outcome==StrongMove::core_rejected;
        if (outcome==StrongMove::accepted) {
          records.consider(prefix,state,heavy,cores,metrics,elapsed(),iterations);
          if (target_reached(metrics.D2max)) break;
        }
      }
      audit_strong(state,heavy,cores,metrics);++restarts;
    }
    auto event=strong_finish_event(state.deficit,metrics.D2max,stopped);
    finish_strong(prefix,state,metrics,heavy,cores,records,event,iterations,restarts,core_rejections,elapsed());
    return target_reached(metrics.D2max)?0:1;
  } catch(const std::exception& error) {std::cerr << error.what() << '\n';return 2;}
}
#endif
