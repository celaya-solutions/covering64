// Document:    Native Pair Penalty Independent Arithmetic and Transition Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      67279b4fd0050c88675694bf7ae31008bdbd3d4cca1fc03dd8f780fc5a83c2cc
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_PAIR_NO_MAIN
#include "search.cpp"

void require(bool ok,const char* message) { if (!ok) throw std::runtime_error(message); }
template<class F> void reject(F f) {
  bool caught=false; try { f(); } catch (const std::runtime_error&) { caught=true; }
  require(caught,"Expected rejection");
}
void independent(const State& s,const PairMetrics& m) {
  std::array<int,120> pc{},d3{},d4{}; std::array<int,1820> qc{};
  std::array<int,560> tc{};
  for (int b:s.ids) {
    for (int p=0;p<120;++p) pc[p]+=(blocks[b].mask & pairs[p])==pairs[p];
    for (int t=0;t<560;++t) tc[t]+=(blocks[b].mask & triples[t])==triples[t];
    for (int q=0;q<1820;++q) qc[q]+=(blocks[b].mask & quads[q])==quads[q];
  }
  int D3=0,D4=0,rows3=0,rows4=0;
  for (int p=0;p<120;++p) {
    for (int t=0;t<560;++t) if ((pairs[p]&triples[t])==pairs[p]) {
      d3[p]+=std::max(0,13-(3*pc[p]-tc[t])); ++rows3;
    }
    for (int q=0;q<1820;++q) if ((pairs[p]&quads[q])==pairs[p]) {
      d4[p]+=std::max(0,12-(3*pc[p]-2*qc[q])); ++rows4;
    }
    D3+=d3[p]; D4+=d4[p];
  }
  require(rows3==1680 && rows4==10920,"Wrong row totals");
  require(pc==m.count && qc==m.quad && tc==s.count && d3==m.d3 && d4==m.d4 && D3==m.D3 && D4==m.D4,
          "Independent arithmetic mismatch");
  bool f=forbidden_profile(heavy_ids(s),s);
  require(integer_energy(s,m,f)==20*s.deficit+5*D3+D4+160*int(f),"Energy mismatch");
}
bool same(const State& a,const State& b) {
  return a.ids==b.ids && a.count==b.count && a.weight==b.weight && a.selected==b.selected && a.deficit==b.deficit;
}
bool same_heavy(std::vector<int> a,std::vector<int> b) { std::sort(a.begin(),a.end()); std::sort(b.begin(),b.end()); return a==b; }

int main(int argc,char** argv) {
  try {
    require(argc==4,"Expected hint, forbidden control, output prefix");
    universe(); initialize_cores(); initialize_pairs();
    for (int b=0;b<4368;++b) {
      std::vector<int> expected_pairs,expected_quads;
      for (int p=0;p<120;++p) if ((pairs[p]&blocks[b].mask)==pairs[p]) expected_pairs.push_back(p);
      for (int q=0;q<1820;++q) if ((quads[q]&blocks[b].mask)==quads[q]) expected_quads.push_back(q);
      auto actual_pairs=block_pairs[b]; auto actual_quads=block_quads[b];
      std::sort(actual_pairs.begin(),actual_pairs.end()); std::sort(actual_quads.begin(),actual_quads.end());
      require(std::equal(actual_pairs.begin(),actual_pairs.end(),expected_pairs.begin(),expected_pairs.end()) &&
              std::equal(actual_quads.begin(),actual_quads.end(),expected_quads.begin(),expected_quads.end()),"Block subset index mismatch");
    }
    require(deficit3(5,2)==0 && deficit3(5,3)==1 && deficit3(6,5)==0 && deficit3(6,6)==1,"D3 boundary");
    require(deficit4(5,1)==0 && deficit4(5,2)==1 && deficit4(6,3)==0 && deficit4(6,4)==2,"D4 boundary");
    State hint(read_blocks(argv[1])); PairMetrics hm(hint); auto hc=core_counts(hint); auto hh=heavy_ids(hint);
    require(hint.deficit==6 && hm.D3==4 && hm.D4==0 && integer_energy(hint,hm,false)==140 && hc==CoreCounts{2,2,0},"Wrong hint");
    audit_pair_state(hint,hh,hc,hm,true); independent(hint,hm);
    auto damaged=hm; damaged.D3++; reject([&]{audit_pair_state(hint,hh,hc,damaged);});
    damaged=hm; damaged.quad[0]++; reject([&]{audit_pair_state(hint,hh,hc,damaged);});
    damaged=hm; damaged.d4[0]++; reject([&]{audit_pair_state(hint,hh,hc,damaged);});
    State dupe=hint; dupe.ids[1]=dupe.ids[0]; reject([&]{audit_pair_state(dupe,heavy_ids(dupe),core_counts(dupe),PairMetrics(dupe));});
    unsigned transitions=0,shared_pair=0,accepted=0,rollbacks=0,duplicates=0,core_rejections=0;
    std::array<int,5> intersections{};
    for (int intersection=0;intersection<=4;++intersection) {
      int old=hint.ids[0],next=-1;
      for (int b=0;b<4368;++b) if (!hint.selected[b] && __builtin_popcount(blocks[old].mask&blocks[b].mask)==intersection) {next=b;break;}
      require(next>=0,"Missing intersection class");
      State s=hint; PairMetrics m=hm; s.move(0,next); m.moved(old,next,s); independent(s,m);
      for (int p:block_pairs[old]) if ((pairs[p]&blocks[next].mask)==pairs[p]) {
        require(m.count[p]==hm.count[p],"Shared pair count changed"); ++shared_pair;
      }
      s.move(0,old); m.moved(next,old,s); require(same(s,hint) && m==hm,"Intersection rollback");
      ++intersections[intersection]; ++transitions;
    }
    std::mt19937_64 random(2026104400);
    State state=hint; PairMetrics metrics=hm; auto heavy=hh; auto cores=hc; bool forbidden=false;
    for (int trial=0;trial<2500;++trial) {
      if (trial%250==0) {state=hint;metrics=hm;heavy=hh;cores=hc;forbidden=false;}
      int slot=int(random()%64),next=int(random()%4368);
      State before=state; auto oldm=metrics; auto oldh=heavy; auto oldc=cores; bool oldf=forbidden;
      auto outcome=attempt_move(state,heavy,cores,metrics,forbidden,slot,next,trial%2?1e9:0.01,trial%2?0.0:1.0);
      if (outcome==MoveResult::accepted) ++accepted;
      else {
        require(same(state,before) && metrics==oldm && cores==oldc && forbidden==oldf,"Rejected move changed full state");
        require(same_heavy(heavy,oldh),"Rejected move changed heavy set");
        if (outcome==MoveResult::duplicate) {++duplicates;require(heavy==oldh,"Premutation duplicate changed heavy order");}
        if (outcome==MoveResult::energy_rejected) ++rollbacks;
        if (outcome==MoveResult::core_rejected) {++core_rejections;require(heavy==oldh,"Premutation cap changed heavy order");}
      }
      audit_pair_state(state,heavy,cores,metrics); independent(state,metrics); ++transitions;
    }
    // Reach each hard cap boundary without search. An attempted 55 -> 56 must touch nothing.
    for (int c=0;c<3;++c) {
      std::vector<int> ids(CORE_IDS[c].begin(),CORE_IDS[c].begin()+55);
      for (int b=0;ids.size()<64;++b) if (!core_member[0][b] && !core_member[1][b] && !core_member[2][b]) ids.push_back(b);
      State s(ids); PairMetrics m(s); auto h=heavy_ids(s); auto cc=core_counts(s); bool f=forbidden_profile(h,s);
      require(core_caps_pass(cc),"Boundary violates another core cap");
      auto before=s;auto beforem=m;auto beforeh=h;auto beforec=cc;bool beforef=f;
      auto result=attempt_move(s,h,cc,m,f,63,CORE_IDS[c][55],0.5,0.0);
      require(result==MoveResult::core_rejected && same(s,before) && m==beforem && h==beforeh && cc==beforec && f==beforef,"Cap rejection mutated state");
      ++core_rejections;
    }
    Records records; std::ostringstream log; auto* original=std::cout.rdbuf(log.rdbuf());
    std::string prefix=argv[3]; records.consider(prefix,hint,hh,hc,hm,0.0,0);
    require(records.raw==hint.ids && records.score==hint.ids && records.qualified.empty(),"Initial record routing");
    records.consider(prefix,hint,hh,hc,hm,0.1,1);require(records.serial==2,"Equal record tie changed first winner");
    require(records.restart(hint.ids,0)==hint.ids && records.restart(state.ids,1)==hint.ids && records.restart(state.ids,3)==state.ids,"Restart policy");
    State bad(read_blocks(argv[2])); PairMetrics badm(bad);
    require(forbidden_profile(heavy_ids(bad),bad) && core_caps_pass(core_counts(bad)),"Wrong forbidden control");
    records.consider(prefix,bad,heavy_ids(bad),core_counts(bad),badm,0.2,2);require(records.serial==2,"Forbidden state recorded");
    finish_pair_run(prefix,bad,badm,heavy_ids(bad),core_counts(bad),records,"finished",123,4,5,1.25);
    finish_pair_run(prefix,hint,hm,hh,hc,records,"interrupted",456,7,8,2.5);
    reject([&]{finish_pair_run(prefix,hint,hm,hh,hc,records,"cover_found",0,0,0,0);});
    reject([&]{finish_pair_run(prefix,hint,hm,hh,hc,records,"unknown",0,0,0,0);});
    // Synthetic row-clear partial-cover control tests routing only; canonical audit must reject it.
    auto fake=hm;fake.D3=fake.D4=0;
    reject([&]{records.consider(prefix,hint,hh,hc,fake,0.3,3);});
    std::cout.rdbuf(original); std::ofstream output(prefix+"-events.jsonl");output<<log.str();output.close();
    if (!(accepted>0 && rollbacks>0 && core_rejections>=3 && shared_pair==10)) throw std::runtime_error("Insufficient controls accepted="+std::to_string(accepted)+" rollbacks="+std::to_string(rollbacks)+" core="+std::to_string(core_rejections)+" shared="+std::to_string(shared_pair));
    std::cout << "{\"passed\":true,\"row_counts\":[1680,10920],\"slack_boundaries\":8,\"transitions\":" << transitions
              << ",\"intersection_classes\":[0,1,2,3,4],\"shared_pair_controls\":" << shared_pair
              << ",\"accepted\":" << accepted << ",\"rollbacks\":" << rollbacks << ",\"duplicates\":" << duplicates
              << ",\"core_rejections\":" << core_rejections << ",\"restarts\":10,\"damaged_rejections\":5,\"record_finish_controls\":9}" << std::endl;
    return 0;
  } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 2; }
}
