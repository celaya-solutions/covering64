// Document:    Native Soft Pair Penalty Cover Search
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      43e78dd4f1e9fed1b22676c48003247c7ba1314cea2cb87c35dc5a5d02a9de9d
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_CORE_NO_MAIN
#include "native_core_base.cpp"
#include <tuple>

std::array<int,65536> pair_id{}, quad_id{};
std::vector<unsigned> pairs, quads;
std::array<std::array<int,10>,4368> block_pairs{};
std::array<std::array<int,5>,4368> block_quads{};
std::array<std::vector<int>,120> pair_triples, pair_quads;

void initialize_pairs() {
  pair_id.fill(-1); quad_id.fill(-1);
  for (int a=0;a<16;++a) for (int b=a+1;b<16;++b) {
    unsigned p=(1u<<a)|(1u<<b); pair_id[p]=int(pairs.size()); pairs.push_back(p);
    for (int c=b+1;c<16;++c) for (int d=c+1;d<16;++d) {
      unsigned q=p|(1u<<c)|(1u<<d); quad_id[q]=int(quads.size()); quads.push_back(q);
    }
  }
  for (int b=0;b<4368;++b) {
    int pi=0,qi=0;
    for (unsigned sub=blocks[b].mask;sub;sub=(sub-1)&blocks[b].mask) {
      if (__builtin_popcount(sub)==2) block_pairs[b][pi++]=pair_id[sub];
      if (__builtin_popcount(sub)==4) block_quads[b][qi++]=quad_id[sub];
    }
    if (pi!=10 || qi!=5) throw std::runtime_error("Invalid block subset table");
  }
  for (int p=0;p<120;++p) {
    for (int t=0;t<560;++t) if ((pairs[p]&triples[t])==pairs[p]) pair_triples[p].push_back(t);
    for (int q=0;q<1820;++q) if ((pairs[p]&quads[q])==pairs[p]) pair_quads[p].push_back(q);
    if (pair_triples[p].size()!=14 || pair_quads[p].size()!=91)
      throw std::runtime_error("Invalid pair row table");
  }
}

int deficit3(int pair_count,int triple_count) { return std::max(0,13-3*pair_count+triple_count); }
int deficit4(int pair_count,int quad_count) { return std::max(0,12-3*pair_count+2*quad_count); }

struct PairMetrics {
  std::array<int,120> count{}, d3{}, d4{};
  std::array<int,1820> quad{};
  int D3=0,D4=0;
  explicit PairMetrics(const State& s) {
    for (int b:s.ids) {
      for (int p:block_pairs[b]) ++count[p];
      for (int q:block_quads[b]) ++quad[q];
    }
    for (int p=0;p<120;++p) recount(p,s);
  }
  void recount(int p,const State& s) {
    D3-=d3[p]; D4-=d4[p]; d3[p]=d4[p]=0;
    for (int t:pair_triples[p]) d3[p]+=deficit3(count[p],s.count[t]);
    for (int q:pair_quads[p]) d4[p]+=deficit4(count[p],quad[q]);
    D3+=d3[p]; D4+=d4[p];
  }
  void moved(int old,int next,const State& after) {
    std::array<int,20> affected{}; int n=0;
    for (int p:block_pairs[old]) { --count[p]; affected[n++]=p; }
    for (int p:block_pairs[next]) {
      ++count[p];
      if (std::find(affected.begin(),affected.begin()+n,p)==affected.begin()+n) affected[n++]=p;
    }
    for (int q:block_quads[old]) --quad[q];
    for (int q:block_quads[next]) ++quad[q];
    // Any changed triple/quad lies in old or next, so all its row-pairs are in this union.
    for (int i=0;i<n;++i) recount(affected[i],after);
  }
  bool operator==(const PairMetrics&) const = default;
};

int integer_energy(const State& s,const PairMetrics& m,bool forbidden) {
  return 20*s.deficit+5*m.D3+m.D4+160*int(forbidden);
}
using ScoreKey=std::tuple<int,int,int>;
ScoreKey score_key(const State& s,const PairMetrics& m) {
  return {integer_energy(s,m,false),m.D3+m.D4,s.deficit};
}
void audit_pair_state(const State& s,const std::vector<int>& heavy,const CoreCounts& cores,
                      const PairMetrics& m,bool eligible=false) {
  audit_state(s,heavy); audit_core_state(s,cores);
  if (!(PairMetrics(s)==m)) throw std::runtime_error("Pair metric recount failed");
  if (eligible && forbidden_profile(heavy,s)) throw std::runtime_error("Ineligible profile record");
}

enum class MoveResult { duplicate, core_rejected, accepted, energy_rejected };
MoveResult attempt_move(State& s,std::vector<int>& heavy,CoreCounts& cores,PairMetrics& m,
                        bool& forbidden,int slot,int next,double temperature,double uniform) {
  if (s.selected[next]) return MoveResult::duplicate;
  int old=s.ids[slot]; auto proposed=proposed_core_counts(cores,old,next);
  if (!core_caps_pass(proposed)) return MoveResult::core_rejected;
  int before=integer_energy(s,m,forbidden);
  s.move(slot,next); m.moved(old,next,s); update_heavy(heavy,s,old,next);
  bool next_forbidden=forbidden_profile(heavy,s);
  double delta=double(integer_energy(s,m,next_forbidden)-before)/20.0;
  if (delta<=0 || uniform<std::exp(-delta/temperature)) {
    forbidden=next_forbidden; cores=proposed; return MoveResult::accepted;
  }
  s.move(slot,old); m.moved(next,old,s); update_heavy(heavy,s,old,next);
  return MoveResult::energy_rejected;
}

void print_metrics(const State& s,const PairMetrics& m) {
  bool f=forbidden_profile(heavy_ids(s),s);
  std::cout << "{\"holes\":" << s.deficit << ",\"D3\":" << m.D3 << ",\"D4\":" << m.D4
            << ",\"energy\":" << integer_energy(s,m,f) << ",\"pair_min\":"
            << *std::min_element(m.count.begin(),m.count.end()) << ",\"forbidden\":"
            << (f?"true":"false") << ",\"core_overlaps\":";
  print_cores(core_counts(s)); std::cout << '}';
}
struct Records {
  std::vector<int> raw,score,qualified;
  uint64_t serial=0;
  int raw_holes=561,qualified_holes=561;
  ScoreKey best_key={1000000000,1000000000,561};
  void consider(const std::string& prefix,const State& s,const std::vector<int>& heavy,
                const CoreCounts& cores,const PairMetrics& m,double seconds,uint64_t iterations) {
    if (forbidden_profile(heavy,s)) return;
    auto record=[&](const std::string& role,std::vector<int>& target) {
      audit_pair_state(s,heavy,cores,m,true); target=s.ids; ++serial;
      auto path=prefix+"-record-"+std::to_string(serial)+"-"+role+".txt"; save(path,target);
      std::cout << "{\"event\":\"record\",\"role\":\"" << role << "\",\"serial\":" << serial
                << ",\"seconds\":" << seconds << ",\"iterations\":" << iterations << ",\"metrics\":";
      print_metrics(s,m); std::cout << '}' << std::endl;
    };
    if (s.deficit<raw_holes) { record("raw",raw); raw_holes=s.deficit; }
    if (score_key(s,m)<best_key) { record("score",score); best_key=score_key(s,m); }
    if (m.D3==0 && m.D4==0 && s.deficit<qualified_holes) {
      record("qualified",qualified); qualified_holes=s.deficit;
    }
  }
  const std::vector<int>& restart(const std::vector<int>& initial,uint64_t n) const {
    return n%3==0 || score.empty() ? initial : score;
  }
};

void finish_pair_run(const std::string& prefix,const State& current,const PairMetrics& current_m,
                     const std::vector<int>& heavy,const CoreCounts& cores,const Records& records,
                     const std::string& event,uint64_t iterations,uint64_t restarts,
                     uint64_t core_rejections,double seconds) {
  if (records.raw.empty() || records.score.empty() ||
      (event!="cover_found" && event!="finished" && event!="interrupted"))
    throw std::runtime_error("Invalid final record or status");
  audit_pair_state(current,heavy,cores,current_m);
  if (event=="cover_found" && (current.deficit!=0 || current_m.D3 || current_m.D4 ||
      forbidden_profile(heavy,current))) throw std::runtime_error("False cover status");
  save(prefix+"-final-current.txt",current.ids);
  std::cout << "{\"event\":\"" << event << "\",\"iterations\":" << iterations
            << ",\"restarts\":" << restarts << ",\"core_rejections\":" << core_rejections
            << ",\"seconds\":" << seconds << ",\"current\":";
  print_metrics(current,current_m);
  for (const auto& item : {std::make_pair("raw",&records.raw),std::make_pair("score",&records.score),
                           std::make_pair("qualified",&records.qualified)}) {
    std::cout << ",\"" << item.first << "\":";
    if (item.second->empty()) { std::cout << "null"; continue; }
    State s(*item.second); PairMetrics m(s);
    audit_pair_state(s,heavy_ids(s),core_counts(s),m,true);
    if (std::string(item.first)=="qualified" && (m.D3 || m.D4))
      throw std::runtime_error("Invalid zero deficit record");
    save(prefix+"-final-"+item.first+".txt",s.ids); print_metrics(s,m);
  }
  std::cout << '}' << std::endl;
}

#ifndef NATIVE_PAIR_NO_MAIN
int main(int argc,char** argv) {
  try {
    universe(); initialize_cores(); initialize_pairs();
    if (argc==3 && std::string(argv[1])=="--metrics") {
      State s(read_blocks(argv[2]));
      if (s.ids.size()!=64) throw std::runtime_error("Expected exactly64 blocks");
      print_metrics(s,PairMetrics(s)); std::cout << '\n'; return 0;
    }
    if (argc!=5) throw std::runtime_error("usage: START SEED SECONDS OUTPUT_PREFIX");
    auto initial=read_blocks(argv[1]); State state(initial); PairMetrics metrics(state);
    auto heavy=heavy_ids(state); auto cores=core_counts(state);
    audit_pair_state(state,heavy,cores,metrics,true);
    uint64_t seed=std::stoull(argv[2]); double budget=std::stod(argv[3]);
    if (!std::isfinite(budget) || budget<=0) throw std::runtime_error("Invalid budget");
    std::string prefix=argv[4]; rng.seed(seed);
    std::signal(SIGTERM,stop_search); std::signal(SIGINT,stop_search);
    auto start=std::chrono::steady_clock::now();
    auto elapsed=[&] { return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count(); };
    Records records; uint64_t iterations=0,restarts=0,core_rejections=0; double last_progress=0;
    std::cout << "{\"event\":\"start\",\"seed\":" << seed << ",\"budget\":" << budget << '}' << std::endl;
    records.consider(prefix,state,heavy,cores,metrics,elapsed(),iterations);
    while (elapsed()<budget && !stopped && state.deficit!=0) {
      state=State(records.restart(initial,restarts)); metrics=PairMetrics(state);
      heavy=heavy_ids(state); cores=core_counts(state);
      audit_pair_state(state,heavy,cores,metrics,true); bool forbidden=false;
      for (uint64_t step=0;step<1500000;++step) {
        if ((step&4095)==0) {
          audit_pair_state(state,heavy,cores,metrics);
          if (elapsed()>=budget || stopped) break;
          if (elapsed()-last_progress>=30) {
            last_progress=elapsed();
            std::cout << "{\"event\":\"progress\",\"seconds\":" << last_progress
                      << ",\"iterations\":" << iterations << ",\"restarts\":" << restarts
                      << ",\"metrics\":"; print_metrics(state,metrics); std::cout << '}' << std::endl;
          }
        }
        int slot=randint(64),old=state.ids[slot],next;
        if (randint(8)==0 && state.deficit>0) {
          int target; do target=randint(560); while (state.count[target]!=0);
          next=containing[target][randint(int(containing[target].size()))];
        } else {
          int remove,add;
          do remove=randint(16); while (!(blocks[old].mask&(1u<<remove)));
          do add=randint(16); while (blocks[old].mask&(1u<<add));
          next=bymask[blocks[old].mask^(1u<<remove)^(1u<<add)];
        }
        double phase=double(step)/1500000;
        double temperature=0.06+(0.7+0.1*(restarts%4))*std::pow(1-phase,3);
        auto outcome=attempt_move(state,heavy,cores,metrics,forbidden,slot,next,temperature,
                                  std::generate_canonical<double,53>(rng));
        ++iterations; core_rejections+=outcome==MoveResult::core_rejected;
        if (outcome==MoveResult::accepted) {
          records.consider(prefix,state,heavy,cores,metrics,elapsed(),iterations);
          if (state.deficit==0) break;
        }
      }
      audit_pair_state(state,heavy,cores,metrics); ++restarts;
    }
    auto event=state.deficit==0?"cover_found":(stopped?"interrupted":"finished");
    finish_pair_run(prefix,state,metrics,heavy,cores,records,event,iterations,restarts,core_rejections,elapsed());
    return state.deficit==0?0:1;
  } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 2; }
}
#endif
