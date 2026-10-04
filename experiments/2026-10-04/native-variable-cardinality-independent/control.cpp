// Document:    Independent Native Variable Cardinality Kernel Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      429ae428530eeab49533228a463de42c42747c202f4503cb547b6fb0d56a57e7
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include "../native-variable-cardinality/kernel.hpp"
#include <bit>
#include <filesystem>
#include <iostream>
#include <map>
#include <numeric>
#include <set>

namespace independent {
constexpr int B=4368,T=560;
void need(bool ok,const std::string& message) {
  if(!ok) throw std::runtime_error("INDEPENDENT: "+message);
}
std::vector<int> points(unsigned mask) {
  std::vector<int> out;
  for(int p=1;p<=16;++p) if(mask&(1u<<(p-1))) out.push_back(p);
  return out;
}
struct Universe {
  std::vector<unsigned> blocks,triples;
  Universe() {
    for(unsigned mask=0;mask<65536;++mask) {
      if(std::popcount(mask)==5) blocks.push_back(mask);
      if(std::popcount(mask)==3) triples.push_back(mask);
    }
    auto less=[](unsigned a,unsigned b){return points(a)<points(b);};
    std::sort(blocks.begin(),blocks.end(),less);
    std::sort(triples.begin(),triples.end(),less);
    need(blocks.size()==B && triples.size()==T,"universe sizes");
  }
  bool incident(int b,int t) const {return (blocks[b]&triples[t])==triples[t];}
};
struct Reference {
  const Universe& u;
  std::vector<bool> chosen=std::vector<bool>(B),cc=std::vector<bool>(B,true);
  std::vector<std::uint64_t> last=std::vector<std::uint64_t>(B);
  std::vector<std::int64_t> weight=std::vector<std::int64_t>(T,1);
  std::vector<int> counts=std::vector<int>(T);
  Reference(const Universe& universe,const std::vector<int>& ids):u(universe) {
    for(int b:ids) {need(b>=0 && b<B && !chosen[b],"reference initial IDs");chosen[b]=true;}
    recount();
  }
  void recount() {
    std::fill(counts.begin(),counts.end(),0);
    for(int t=0;t<T;++t) for(int b=0;b<B;++b)
      if(chosen[b] && u.incident(b,t)) ++counts[t];
  }
  int cardinality() const {return std::count(chosen.begin(),chosen.end(),true);}
  int holes() const {return std::count(counts.begin(),counts.end(),0);}
  void flip(int b,bool value,std::uint64_t step) {
    need(b>=0 && b<B && chosen[b]!=value,"reference flip precondition");
    chosen[b]=value;
    for(int other=0;other<B;++other)
      if(std::popcount(u.blocks[b]&u.blocks[other])>=3) cc[other]=true;
    if(!value) cc[b]=false;
    last[b]=step;
    recount();
  }
  void increment() {for(int t=0;t<T;++t) if(!counts[t]) ++weight[t];}
  std::pair<std::int64_t,std::int64_t> score(int b) const {
    std::int64_t first=0,second=0;
    for(int t=0;t<T;++t) if(u.incident(b,t)) {
      if(chosen[b]) {if(counts[t]==1) first-=weight[t];if(counts[t]==2) second-=weight[t];}
      else {if(counts[t]==0) first+=weight[t];if(counts[t]==1) second+=weight[t];}
    }
    return {first,second};
  }
  auto key(int b) const {
    auto [score,pscore]=this->score(b);
    return std::tuple{-5*score-pscore,-pscore,last[b],b};
  }
  int outgoing() const {
    int best=-1;
    for(int b=0;b<B;++b) if(chosen[b] && (best<0 || key(b)<key(best))) best=b;
    need(best>=0,"reference outgoing empty");return best;
  }
  int redundant() const {
    for(int b=0;b<B;++b) if(chosen[b] && score(b).first==0) return b;
    return -1;
  }
  std::vector<int> candidates(int target,std::uint64_t step) const {
    std::vector<int> out;
    for(int b=0;b<B;++b) if(u.incident(b,target) && !chosen[b] && cc[b]
        && step>=last[b] && step-last[b]>=4) out.push_back(b);
    std::sort(out.begin(),out.end(),[&](int a,int b){return key(a)<key(b);});return out;
  }
  int first_carrier(int target) const {
    for(int b=0;b<B;++b) if(u.incident(b,target)) return b;
    throw std::logic_error("no carrier");
  }
};
int snapshots=0,score_checks=0,selection_checks=0,rejections=0,observations=0;
std::map<std::string,int> branches;
void compare(const vc::SearchState& s,Reference& r) {
  r.recount();++snapshots;
  need(s.cardinality==r.cardinality() && s.holes==r.holes(),"cardinality/holes");
  for(int t=0;t<T;++t) need(s.count[t]==r.counts[t] && s.weight[t]==r.weight[t],"counts/weights");
  for(int b=0;b<B;++b) {
    need(s.chosen[b]==r.chosen[b] && s.cc[b]==r.cc[b] && s.last[b]==r.last[b],"choice/CC/age");
    auto expected=r.score(b);auto actual=s.scores(b);++score_checks;
    need(expected.first==actual.score && expected.second==actual.pscore,"score/pscore");
  }
  s.audit();
}
void check_incoming(const vc::SearchState& s,const Reference& r,int target,std::uint64_t step) {
  auto candidates=r.candidates(target,step);
  int best=candidates.empty()?-1:candidates[0];
  int second=candidates.size()<2?-1:candidates[1];
  int novelty_count=0;
  for(unsigned draw=0;draw<100;++draw) {
    auto actual=s.incoming(target,step,draw);++selection_checks;
    bool novelty=second>=0 && draw<=10;
    int expected=best<0?r.first_carrier(target):(novelty?second:best);
    need(actual.id==expected && actual.best==best && actual.second==second,"incoming ranking");
    need(actual.fallback==(best<0) && actual.novelty==novelty,"fallback/novelty");
    novelty_count+=actual.novelty;
  }
  need(novelty_count==(second<0?0:11),"quantized novelty count");
}
template<class F> void rejection(F call,vc::SearchState& s,Reference& r) {
  bool rejected=false;try {call();} catch(const std::exception&) {rejected=true;}
  need(rejected,"invalid operation accepted");++rejections;compare(s,r);
}
void controlled_step(vc::SearchState& s,Reference& r,std::uint64_t step,
    int incumbent,int target,unsigned draw,bool halt_first=false) {
  auto before_count=r.cardinality();auto before_holes=r.holes();
  auto candidates=before_holes?r.candidates(target,step):std::vector<int>{};
  int incoming=before_holes?(candidates.empty()?r.first_carrier(target):
    candidates[(candidates.size()>1 && draw<11)?1:0]):-1;
  std::string expected_action;
  std::vector<std::pair<std::string,int>> expected;
  if(before_holes==0) {
    int redundant=r.redundant();int drop=redundant<0?r.outgoing():redundant;
    expected_action=redundant<0?"complete_drop":"redundant_drop";
    expected.push_back({"remove",drop});
  } else if(before_count+1<incumbent) {
    expected_action="add_only";expected.push_back({"add",incoming});
  } else {
    int drop=r.outgoing();expected.push_back({"remove",drop});
    expected_action=r.score(incoming).first>-r.score(drop).first?"swap":"double_drop";
  }
  int seen=0;
  auto result=vc::advance(s,step,incumbent,target,draw,[&](const vc::SearchState& state,
      const char* action,int block) {
    if(seen==0) need(expected[0]==std::pair{std::string(action),block},"first transition");
    if(seen==1 && expected_action=="swap") need(std::string(action)=="add" && block==incoming,"swap add");
    if(seen==1 && expected_action=="double_drop")
      need(std::string(action)=="remove" && block==r.outgoing(),"second removal must be recomputed");
    r.flip(block,std::string(action)=="add",step);compare(state,r);++seen;++observations;
    return halt_first;
  });
  need(vc::action_name(result.action)==expected_action,"trajectory branch");++branches[expected_action];
  if(halt_first) need(result.stopped && seen==1 && !result.weights_updated,"immediate observer stop");
  else if(expected_action=="add_only" && !result.stopped) {
    r.increment();need(result.weights_updated,"missing post-add uncovered increment");
  } else need(!result.weights_updated,"unexpected weight increment");
  compare(s,r);
  if(!halt_first && (expected_action=="swap" || expected_action=="double_drop"))
    need(seen==2 || result.stopped,"missing second transition");
}
} // namespace independent

int main(int argc,char** argv) {
  using namespace independent;
  try {
    need(argc==3,"arguments: baseline output-directory");
    std::filesystem::path out=argv[2];std::filesystem::create_directories(out);
    Universe u;vc::Universe producer;auto ids=producer.read(argv[1]);
    need(ids.size()==65 && std::set<int>(ids.begin(),ids.end()).size()==65,"baseline cardinality");
    for(int b=0;b<B;++b) {
      need(std::vector<int>(producer.points[b].begin(),producer.points[b].end())==points(u.blocks[b]),
           "global lexicographic block order");
      std::vector<int> expected;
      for(int t=0;t<T;++t) if(u.incident(b,t)) expected.push_back(t);
      auto members=std::vector<int>(producer.members[b].begin(),producer.members[b].end());
      std::sort(members.begin(),members.end());need(members==expected && members.size()==10,"members");
    }
    for(int t=0;t<T;++t) {
      need(producer.triple_rank[u.triples[t]]==t,"triple rank");std::vector<int> expected;
      for(int b=0;b<B;++b) if(u.incident(b,t)) expected.push_back(b);
      need(producer.carriers[t]==expected && expected.size()==78,"carrier universe");
    }
    vc::SearchState s(producer,ids);Reference r(u,ids);compare(s,r);need(s.holes==0,"Belic65 cover");
    producer.write((out/"initial65.txt").string(),s.ids());
    int first=ids[0],second=ids[1],absent=0;while(r.chosen[absent]) ++absent;
    rejection([&]{s.add(first,1);},s,r);rejection([&]{s.remove(absent,1);},s,r);
    rejection([&]{s.add(-1,1);},s,r);rejection([&]{s.remove(B,1);},s,r);
    rejection([&]{s.scores(-1);},s,r);
    rejection([&]{vc::SearchState duplicate(producer,{first,first});},s,r);
    rejection([&]{vc::SearchState damaged(producer,{-1});},s,r);
    s.remove(first,1);r.flip(first,false,1);compare(s,r);
    producer.write((out/"drop64.txt").string(),s.ids());
    int target=std::find(r.counts.begin(),r.counts.end(),0)-r.counts.begin();
    check_incoming(s,r,target,3);check_incoming(s,r,target,4);check_incoming(s,r,target,5);
    rejection([&]{s.incoming(-1,4,0);},s,r);rejection([&]{s.incoming(target,4,100);},s,r);
    int covered=0;while(r.counts[covered]==0) ++covered;
    rejection([&]{s.incoming(covered,4,0);},s,r);
    s.remove(second,2);r.flip(second,false,2);compare(s,r);
    s.increment_uncovered();r.increment();compare(s,r);
    producer.write((out/"drop63.txt").string(),s.ids());
    s.add(first,3);r.flip(first,true,3);compare(s,r);
    s.add(second,4);r.flip(second,true,4);compare(s,r);
    s.add(absent,5);r.flip(absent,true,5);compare(s,r);need(s.cardinality==66,"primitive cardinality freedom");
    s.remove(absent,6);r.flip(absent,false,6);compare(s,r);
    std::mt19937 generator(2026104801u);
    for(std::uint64_t step=10;step<106;++step) {
      int b=static_cast<int>(generator()%B);bool add=!r.chosen[b];
      if(add) s.add(b,step);else s.remove(b,step);
      r.flip(b,add,step);compare(s,r);
      if(step%7==0) {s.increment_uncovered();r.increment();compare(s,r);}
    }
    for(int b=0;b<B;++b) {
      bool age_expected=!r.chosen[b] && r.cc[b] && r.last[b]<=109 && 109-r.last[b]>=4;
      need(s.eligible(b,109)==age_expected,"age eligibility");
    }
    vc::SearchState trajectory(producer,ids);Reference reference(u,ids);
    for(std::uint64_t step=1;step<=32;++step) {
      if(vc::target_reached(trajectory)) break;
      int hole=std::find(reference.counts.begin(),reference.counts.end(),0)-reference.counts.begin();
      controlled_step(trajectory,reference,step,65,hole==T?0:hole,step%100);
    }
    need(branches["complete_drop"]>0 && branches["add_only"]>0,"missing basic trajectory branch");
    vc::SearchState stopped(producer,ids);Reference stopped_ref(u,ids);
    controlled_step(stopped,stopped_ref,1,65,0,99,true);
    need(!vc::target_reached(stopped),"do not claim a cover after arbitrary early stop");
    for(auto [holes,cardinality,expected]:std::vector<std::tuple<int,int,bool>>{
        {0,64,true},{0,63,true},{0,65,false},{1,64,false},{1,63,false}}) {
      auto synthetic=stopped;synthetic.holes=holes;synthetic.cardinality=cardinality;
      need(vc::target_reached(synthetic)==expected,"target predicate scalar unit control");
    }
    producer.write((out/"final-control.txt").string(),trajectory.ids());
    need(producer.read((out/"final-control.txt").string())==trajectory.ids(),"save round trip");
    vc::SearchState empty(producer,{});Reference empty_ref(u,{});compare(empty,empty_ref);
    rejection([&]{empty.outgoing();},empty,empty_ref);
    check_incoming(empty,empty_ref,0,3);check_incoming(empty,empty_ref,0,4);
    std::ofstream log(out/"control.json");
    log<<"{\"passed\":true,\"optimizer_launches\":0,\"snapshots\":"<<snapshots
       <<",\"all_block_score_checks\":"<<score_checks<<",\"incoming_choices\":"<<selection_checks
       <<",\"operation_rejections\":"<<rejections<<",\"observer_events\":"<<observations
       <<",\"initial_blocks\":65,\"initial_holes\":0,\"final_control_blocks\":"<<trajectory.cardinality
       <<",\"final_control_holes\":"<<trajectory.holes<<",\"branches\":{";
    bool comma=false;for(auto [name,count]:branches) {if(comma) log<<',';comma=true;log<<'"'<<name<<"\":"<<count;}
    log<<"},\"target_predicate_controls_are_synthetic\":true}\n";
    std::cout<<"independent kernel controls passed\n";return 0;
  } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
