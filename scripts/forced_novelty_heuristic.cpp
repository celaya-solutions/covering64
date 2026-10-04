// Document:    Protected Novelty Followed by Unrestricted Tabu Repair
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      c79949f346d7eba4b9285b42b4bca6c5b49f56fc6e51883cf54e58dfd29b26cb
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#define main covering64_preserved_legacy_main
#include "heuristic_search.cpp"
#undef main
#include <set>

void fresh_audit(const State& state) {
  std::array<int,560> counts{};
  std::array<bool,4368> selected{};
  if(state.ids.size()!=64)throw std::runtime_error("cardinality changed");
  for(int b:state.ids) {
    if(b<0||b>=4368||selected[b])throw std::runtime_error("invalid selected block");
    selected[b]=true;
    for(int t=0;t<560;t++)if((triples[t]&blocks[b].mask)==triples[t])counts[t]++;
  }
  if(counts!=state.count||selected!=state.selected||
     std::count(counts.begin(),counts.end(),0)!=state.deficit)
    throw std::runtime_error("independent full recount disagrees");
}
int hole_delta(const State& state,int slot,int incoming) {
  if(slot<0||slot>=64||incoming<0||incoming>=4368||state.selected[incoming])
    throw std::runtime_error("bad replacement");
  int outgoing=state.ids[slot],delta=0;
  for(int t:blocks[outgoing].triples)
    if(state.count[t]==1&&(triples[t]&blocks[incoming].mask)!=triples[t])delta++;
  for(int t:blocks[incoming].triples)if(state.count[t]==0)delta--;
  return delta;
}
void checked_move(State& state,int slot,int incoming) {
  int expected=state.deficit+hole_delta(state,slot,incoming);
  state.move(slot,incoming);
  if(state.deficit!=expected)throw std::runtime_error("move delta mismatch");
}
std::vector<int> sorted_ids(const State& state) {
  auto result=state.ids;std::sort(result.begin(),result.end());return result;
}
void ids_json(const State& state) {
  std::cout<<"[";
  for(int i=0;i<64;i++){if(i)std::cout<<",";std::cout<<state.ids[i];}
  std::cout<<"]";
}
int main(int argc,char** argv) {
 try {
  if(argc!=8)throw std::runtime_error("usage: novelty audit|run START ELITE FORCED SEED SECONDS PREFIX");
  std::string mode=argv[1],prefix=argv[7];
  if(mode!="audit"&&mode!="run")throw std::runtime_error("bad mode");
  universe();auto initial=read_blocks(argv[2]);auto elite=read_blocks(argv[3]);
  if(initial.size()!=64||elite.size()!=66)throw std::runtime_error("expected64 seed and66 elite blocks");
  std::array<bool,4368> in_elite{};for(int b:elite)in_elite[b]=true;
  for(int b:initial)if(!in_elite[b])throw std::runtime_error("seed not contained in elite union");
  int forced=std::stoi(argv[4]);uint64_t seed=std::stoull(argv[5]);double budget=std::stod(argv[6]);
  if((forced!=8&&forced!=16&&forced!=32)||!std::isfinite(budget)||budget<=0)
    throw std::runtime_error("bad forced count or budget");
  rng.seed(seed);State state(initial);fresh_audit(state);
  if(mode=="audit") {
    for(int i=0;i<512;i++) {
      int slot=(i*17)%64,b=(i*73+11)%4368;while(state.selected[b])b=(b+1)%4368;
      State before=state;int old=state.ids[slot],change=hole_delta(state,slot,b);
      checked_move(state,slot,b);fresh_audit(state);int after=state.deficit;
      checked_move(state,slot,old);fresh_audit(state);
      if(state.ids!=before.ids||state.count!=before.count||state.selected!=before.selected)
        throw std::runtime_error("rollback changed state");
      std::cout<<"{\"event\":\"delta_control\",\"slot\":"<<slot<<",\"old\":"<<old
               <<",\"incoming\":"<<b<<",\"delta\":"<<change<<",\"before\":"<<before.deficit
               <<",\"after\":"<<after<<"}"<<std::endl;
    }
    return 0;
  }
  std::signal(SIGTERM,stop_search);std::signal(SIGINT,stop_search);
  auto started=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
  auto checkpoint=[&](const std::string& label) {
    fresh_audit(state);save(prefix+"-"+label+".txt",state.ids);
    int outside=0;for(int b:state.ids)outside+=!in_elite[b];
    std::cout<<"{\"event\":\"saved\",\"label\":\""<<label<<"\",\"holes\":"<<state.deficit
             <<",\"outside_elite\":"<<outside<<",\"seconds\":"<<elapsed()<<"}"<<std::endl;
  };
  std::cout<<"{\"event\":\"start\",\"seed\":"<<seed<<",\"seconds\":"<<budget
           <<",\"forced\":"<<forced<<",\"initial_holes\":"<<state.deficit<<"}"<<std::endl;
  checkpoint("initial");std::array<bool,4368> locked{};int overall=state.deficit;
  for(int step=0;step<forced;step++) {
    if(stopped||elapsed()>=budget)throw std::runtime_error("forced phase exceeded its total budget");
    std::array<int,64> loss{};
    for(int slot=0;slot<64;slot++)for(int t:blocks[state.ids[slot]].triples)
      if(state.count[t]==1)loss[slot]++;
    int best=561,bestslot=-1,incoming=-1,ties=0;
    for(int b=0;b<4368;b++)if(!in_elite[b]&&!state.selected[b]) {
      int gain=0;for(int t:blocks[b].triples)gain+=state.count[t]==0;
      for(int slot=0;slot<64;slot++)if(!locked[state.ids[slot]]) {
        int old=state.ids[slot],score=loss[slot]-gain;
        if(__builtin_popcount(blocks[old].mask&blocks[b].mask)>=3)
          for(int t:blocks[old].triples)if(state.count[t]==1&&(triples[t]&blocks[b].mask)==triples[t])score--;
        if(score<best){best=score;bestslot=slot;incoming=b;ties=1;}
        else if(score==best&&randint(++ties)==0){bestslot=slot;incoming=b;}
      }
    }
    if(bestslot<0||hole_delta(state,bestslot,incoming)!=best)throw std::runtime_error("forced choice mismatch");
    int old=state.ids[bestslot],before=state.deficit;checked_move(state,bestslot,incoming);
    locked[incoming]=true;fresh_audit(state);
    for(int b=0;b<4368;b++)if(locked[b]&&(!state.selected[b]||in_elite[b]))
      throw std::runtime_error("forced protection invariant failed");
    std::cout<<"{\"event\":\"forced_move\",\"step\":"<<step+1<<",\"slot\":"<<bestslot
             <<",\"old\":"<<old<<",\"incoming\":"<<incoming<<",\"delta\":"<<best
             <<",\"before\":"<<before<<",\"after\":"<<state.deficit<<",\"ids\":";
    ids_json(state);std::cout<<"}"<<std::endl;
    if(state.deficit<overall) {
      overall=state.deficit;checkpoint("forced-best-h"+std::to_string(overall));
    }
  }
  checkpoint("forced");locked.fill(false);
  std::array<uint64_t,4368> tabu{},protected_until{};
  uint64_t steps=0,lastbest=0;int repair_best=state.deficit;bool saved_equal=false;
  auto best_ids=sorted_ids(state);checkpoint("repair-best-h"+std::to_string(repair_best));
  while(!stopped&&state.deficit>0&&elapsed()<budget) {
    std::vector<int> uncovered;for(int t=0;t<560;t++)if(state.count[t]==0)uncovered.push_back(t);
    int target=uncovered[randint(int(uncovered.size()))];std::array<int,64> loss{};
    for(int slot=0;slot<64;slot++)for(int t:blocks[state.ids[slot]].triples)
      if(state.count[t]==1)loss[slot]+=state.weight[t];
    int bestscore=std::numeric_limits<int>::max(),incoming=-1,bestslot=-1,ties=0;
    for(int b:containing[target])if(!state.selected[b]) {
      int gain=0;for(int t:blocks[b].triples)if(state.count[t]==0)gain+=state.weight[t];
      for(int slot=0;slot<64;slot++) {
        int old=state.ids[slot];if(protected_until[old]>steps)continue;
        int score=loss[slot]-gain;
        if(__builtin_popcount(blocks[old].mask&blocks[b].mask)>=3)
          for(int t:blocks[old].triples)if(state.count[t]==1&&(triples[t]&blocks[b].mask)==triples[t])score-=state.weight[t];
        if(tabu[b]>steps&&state.deficit+hole_delta(state,slot,b)>=repair_best)continue;
        if(score<bestscore){bestscore=score;incoming=b;bestslot=slot;ties=1;}
        else if(score==bestscore&&randint(++ties)==0){incoming=b;bestslot=slot;}
      }
    }
    if(incoming>=0) {
      int old=state.ids[bestslot];checked_move(state,bestslot,incoming);
      tabu[old]=steps+5+randint(18);protected_until[incoming]=steps+5;
      overall=std::min(overall,state.deficit);
      if(state.deficit<repair_best) {
        repair_best=state.deficit;lastbest=steps;best_ids=sorted_ids(state);saved_equal=false;
        checkpoint("repair-best-h"+std::to_string(repair_best));
      } else if(state.deficit==repair_best&&!saved_equal&&sorted_ids(state)!=best_ids) {
        checkpoint("repair-equal-h"+std::to_string(repair_best));saved_equal=true;
      }
    }
    if(steps-lastbest>40&&steps%8==0)for(int t=0;t<560;t++)if(state.count[t]==0)state.weight[t]++;
    if(steps%3000==2999)for(int& w:state.weight)w=1+(w-1)*3/4;
    ++steps;if(steps%1024==0)fresh_audit(state);
  }
  checkpoint("final");
  std::cout<<"{\"event\":\"finished\",\"seed\":"<<seed<<",\"forced\":"<<forced
           <<",\"seconds\":"<<elapsed()<<",\"repair_steps\":"<<steps<<",\"overall_best\":"<<overall
           <<",\"repair_best\":"<<repair_best<<",\"final_holes\":"<<state.deficit
           <<",\"interrupted\":"<<(stopped?"true":"false")<<"}"<<std::endl;
  return 0;
 } catch(const std::exception& error){std::cerr<<error.what()<<std::endl;return 2;}
}
