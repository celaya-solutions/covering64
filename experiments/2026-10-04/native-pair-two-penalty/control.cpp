// Document:    Native Compact Pair-Two Direct and Flow Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      613cb8f0cd917d46d528c0383d2b170766d6bf09a6093dfb4e970daf7637b87f
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_STRONG_NO_MAIN
#include "search.cpp"
void require(bool ok,const char* message) {if(!ok) throw std::runtime_error(message);}
template<class F> void reject(F f) {
  bool caught=false;try{f();}catch(const std::runtime_error&){caught=true;}
  require(caught,"Expected control rejection");
}
bool same(const State& a,const State& b) {
  return a.ids==b.ids && a.count==b.count && a.weight==b.weight && a.selected==b.selected && a.deficit==b.deficit;
}
bool same_heavy(std::vector<int> a,std::vector<int> b) {std::sort(a.begin(),a.end());std::sort(b.begin(),b.end());return a==b;}
bool membership(int c,int b) {
  if(c==3)return std::find(FOURTH_CORE_IDS.begin(),FOURTH_CORE_IDS.end(),b)!=FOURTH_CORE_IDS.end();
  return std::find(CORE_IDS[c].begin(),CORE_IDS[c].end(),b)!=CORE_IDS[c].end();
}
FourCounts independent_cores(const State& s) {
  FourCounts c{};for(int b:s.ids)for(int j=0;j<4;++j)c[j]+=membership(j,b);return c;
}
void independent(const State& s,const D2Metrics& m,const FourCounts& cores) {
  std::array<int,120> pc{},contribution{};std::array<int,560> tc{};
  for(int b:s.ids) {
    for(int p=0;p<120;++p)pc[p]+=(pairs[p]&blocks[b].mask)==pairs[p];
    for(int t=0;t<560;++t)tc[t]+=(triples[t]&blocks[b].mask)==triples[t];
  }
  int full=0,compact=0,rows=0;
  for(int p=0;p<120;++p) {
    std::vector<int> values;
    for(int t=0;t<560;++t)if((pairs[p]&triples[t])==pairs[p])values.push_back(tc[t]);
    require(values.size()==14,"Wrong direct row positions");
    for(int a=0;a<14;++a)for(int b=a+1;b<14;++b) {
      int d=std::max(0,12-3*pc[p]+values[a]+values[b]);
      contribution[p]=std::max(contribution[p],d);full+=d;++rows;
    }
    compact+=contribution[p];
  }
  require(rows==10920 && pc==m.count && tc==s.count && contribution==m.contribution && compact==m.D2max,
          "Independent compact recount mismatch");
  require(full==explicit_d2_sum(s,m) && cores==independent_cores(s),"Full deficit or four-core mismatch");
  require(strong_energy(s,m)==20*compact+s.deficit,"Energy arithmetic");
}
int main(int argc,char** argv) {
  try {
    require(argc==6,"Expected H48, H49, forbidden control, fourth-core-bad control, prefix");
    universe();initialize_cores();initialize_pairs();initialize_fourth();
    std::mt19937_64 random(2026104500);unsigned profile_controls=0;
    for(int trial=0;trial<3000;++trial) {
      std::array<int,14> values{};for(int& v:values)v=int(random()%17);int p=int(random()%65),expected=0;
      for(int a=0;a<14;++a)for(int b=a+1;b<14;++b)expected=std::max(expected,std::max(0,12-3*p+values[a]+values[b]));
      require(compact_deficit(p,values)==expected,"Top-two does not equal maximum of91 rows");
      auto before=largest_two(values);std::shuffle(values.begin(),values.end(),random);
      require(largest_two(values)==before,"Top-two changed under permutation");++profile_controls;
    }
    std::array<int,14> ties{};ties.fill(1);ties[0]=ties[1]=2;
    require(largest_two(ties)==std::pair<int,int>{2,2} && compact_deficit(5,ties)==1,"Equal values at different positions");
    ties[1]=1;require(compact_deficit(5,ties)==0,"Pair-five boundary");
    ties.fill(0);ties[4]=3;require(largest_two(ties)==std::pair<int,int>{3,0},"Zero positions discarded");
    uint64_t flow_controls=0;
    for(int holes=0;holes<=560;++holes)for(int d=0;d<=120;++d)for(bool interrupted:{false,true}) {
      std::string expected=d==0?(holes==0?"cover_found":"qualified_hint_found"):(interrupted?"interrupted":"finished");
      require(target_reached(d)==(d==0) && strong_finish_event(holes,d,interrupted)==expected,"Pure finish/stop flow");++flow_controls;
    }
    reject([]{strong_finish_event(-1,0,false);});reject([]{strong_finish_event(561,0,false);});reject([]{strong_finish_event(1,-1,false);});
    State first(read_blocks(argv[1])),second(read_blocks(argv[2]));D2Metrics fm(first),sm(second);
    require(first.deficit==48 && fm.D2max==75 && explicit_d2_sum(first,fm)==175 && four_counts(first)==FourCounts{0,1,1,12},"Wrong H48 hint");
    require(second.deficit==49 && sm.D2max==74 && explicit_d2_sum(second,sm)==170 && four_counts(second)==FourCounts{0,2,2,4},"Wrong H49 hint");
    independent(first,fm,four_counts(first));independent(second,sm,four_counts(second));
    auto damaged=fm;damaged.D2max=0;reject([&]{audit_strong(first,heavy_ids(first),four_counts(first),damaged,true);});
    damaged=fm;++damaged.count[0];reject([&]{audit_strong(first,heavy_ids(first),four_counts(first),damaged);});
    damaged=fm;++damaged.contribution[0];reject([&]{audit_strong(first,heavy_ids(first),four_counts(first),damaged);});
    State duplicate=first;duplicate.ids[1]=duplicate.ids[0];reject([&]{audit_strong(duplicate,heavy_ids(duplicate),four_counts(duplicate),D2Metrics(duplicate));});
    unsigned moves=0,accepted=0,rollbacks=0,duplicates=0,core_rejections=0,shared=0;
    for(int intersection=0;intersection<5;++intersection) {
      int old=first.ids[0],next=-1;
      for(int b=0;b<4368;++b)if(!first.selected[b] && __builtin_popcount(blocks[old].mask&blocks[b].mask)==intersection){next=b;break;}
      require(next>=0,"Missing intersection");State s=first;D2Metrics m=fm;s.move(0,next);m.moved(old,next,s);
      independent(s,m,four_counts(s));
      for(int p:block_pairs[old])if((pairs[p]&blocks[next].mask)==pairs[p]){require(m.count[p]==fm.count[p],"Shared pair net count");++shared;}
      s.move(0,old);m.moved(next,old,s);require(same(s,first) && m==fm,"Intersection rollback");++moves;
    }
    State state=first;D2Metrics metrics=fm;auto heavy=heavy_ids(state);auto cores=four_counts(state);
    for(int trial=0;trial<2500;++trial) {
      if(trial%250==0){state=trial%500?second:first;metrics=D2Metrics(state);heavy=heavy_ids(state);cores=four_counts(state);}
      auto before=state;auto oldm=metrics;auto oldh=heavy;auto oldc=cores;
      int slot=int(random()%64),next=int(random()%4368);
      auto result=attempt_strong_move(state,heavy,cores,metrics,slot,next,trial%2?1e9:0.01,trial%2?0.0:1.0);
      if(result==StrongMove::accepted) {
        ++accepted;require(std::abs(state.deficit-before.deficit)<=10,"Hole swing exceeds10");
        int dd=metrics.D2max-oldm.D2max,de=strong_energy(state,metrics)-strong_energy(before,oldm);
        require((dd>=0 || de<0) && (dd<=0 || de>0),"Weight20 lost single-move priority");
      } else {
        require(same(state,before) && metrics==oldm && cores==oldc && same_heavy(heavy,oldh),"Rejected move changed state");
        if(result==StrongMove::duplicate){++duplicates;require(heavy==oldh,"Duplicate pre-mutation changed heavy vector");}
        if(result==StrongMove::energy_rejected)++rollbacks;
        if(result==StrongMove::core_rejected){++core_rejections;require(heavy==oldh,"Cap pre-mutation changed heavy vector");}
      }
      audit_strong(state,heavy,cores,metrics);independent(state,metrics,cores);++moves;
    }
    unsigned cap_boundaries=0;
    for(int c=0;c<4;++c)for(int amount:{54,55,56}) {
      std::vector<int> core=c==3?std::vector<int>(FOURTH_CORE_IDS.begin(),FOURTH_CORE_IDS.end()):std::vector<int>(CORE_IDS[c].begin(),CORE_IDS[c].end());
      std::vector<int> ids(core.begin(),core.begin()+amount);
      for(int b=0;ids.size()<64;++b)if(!membership(0,b)&&!membership(1,b)&&!membership(2,b)&&!membership(3,b))ids.push_back(b);
      State s(ids);D2Metrics m(s);auto h=heavy_ids(s);auto cc=four_counts(s);
      require(cc[c]==amount && cc==independent_cores(s),"Four-core boundary recount");
      FourCounts isolated{};isolated[c]=amount;require(four_caps_pass(isolated)==(amount<=55),"Four-core boundary predicate");++cap_boundaries;
      if(amount!=55)continue;
      auto before=s;auto beforem=m;auto beforeh=h;auto beforec=cc;
      auto result=attempt_strong_move(s,h,cc,m,63,core[55],1.0,0.0);
      require(result==StrongMove::core_rejected && same(s,before) && m==beforem && h==beforeh && cc==beforec,"Hard fourth/core rejection mutated state");++core_rejections;
    }
    unsigned probability_controls=0;
    for(int next=0;next<4368 && probability_controls==0;++next)if(!first.selected[next]) {
      State proposal=first;D2Metrics pm=fm;proposal.move(0,next);pm.moved(first.ids[0],next,proposal);
      int difference=strong_energy(proposal,pm)-strong_energy(first,fm);
      if(difference<=0 || !four_caps_pass(four_counts(proposal)))continue;
      double probability=std::exp(-(double(difference)/20.0)/100.0);
      for(bool accept:{false,true}) {
        State s=first;D2Metrics m=fm;auto h=heavy_ids(s);auto c=four_counts(s);
        auto result=attempt_strong_move(s,h,c,m,0,next,100.0,accept?std::nextafter(probability,0.0):probability);
        require((result==StrongMove::accepted)==accept,"Acceptance delta or strict threshold mismatch");
        if(!accept)require(same(s,first)&&m==fm,"Probability rejection failed rollback");++probability_controls;
      }
    }
    StrongRecords records;std::string prefix=argv[5];std::ostringstream log;auto* original=std::cout.rdbuf(log.rdbuf());
    records.consider(prefix,first,heavy_ids(first),four_counts(first),fm,0,0);
    records.consider(prefix,second,heavy_ids(second),four_counts(second),sm,1,1);
    require(records.raw==first.ids && records.primary==second.ids && records.qualified.empty() && records.serial==3,"Lex/raw/absence record paths");
    records.consider(prefix,second,heavy_ids(second),four_counts(second),sm,2,2);require(records.serial==3,"First tie not retained");
    require(records.restart(first.ids,0)==first.ids && records.restart(first.ids,1)==second.ids && records.restart(first.ids,3)==first.ids,"Restart source");
    State core_bad(read_blocks(argv[4]));require(four_counts(core_bad)[3]==59,"Expected checked fourth-core-bad hint");
    reject([&]{records.consider(prefix,core_bad,heavy_ids(core_bad),four_counts(core_bad),D2Metrics(core_bad),3,3);});
    require(records.raw==first.ids && records.serial==3,"Rejected record overwrote raw");
    damaged=fm;damaged.D2max=0;reject([&]{records.consider(prefix,first,heavy_ids(first),four_counts(first),damaged,4,4);});
    State forbidden(read_blocks(argv[3]));auto fc=four_counts(forbidden);auto fh=heavy_ids(forbidden);D2Metrics fd(forbidden);
    require(forbidden_profile(fh,forbidden) && four_caps_pass(fc),"Expected profile diagnostic control");
    finish_strong(prefix+"-finished",forbidden,fd,fh,fc,records,"finished",123,4,5,1.25);
    finish_strong(prefix+"-interrupted",first,fm,heavy_ids(first),four_counts(first),records,"interrupted",456,7,8,2.5);
    reject([&]{finish_strong(prefix,first,fm,heavy_ids(first),four_counts(first),records,"qualified_hint_found",0,0,0,0);});
    reject([&]{finish_strong(prefix,first,fm,heavy_ids(first),four_counts(first),records,"cover_found",0,0,0,0);});
    reject([&]{finish_strong(prefix,first,fm,heavy_ids(first),four_counts(first),records,"unknown",0,0,0,0);});
    std::cout.rdbuf(original);std::ofstream file(prefix+"-events.jsonl");file<<log.str();file.close();
    require(accepted>0 && rollbacks>0 && core_rejections>=4 && shared==10 && probability_controls==2,"Insufficient direct controls");
    std::cout << "{\"passed\":true,\"optimizer_calls\":0,\"top_two_profiles\":" << profile_controls
              << ",\"synthetic_scalar_flow_controls\":" << flow_controls << ",\"flow_controls_are_candidate_witnesses\":false"
              << ",\"direct_moves\":" << moves << ",\"accepted\":" << accepted << ",\"rollbacks\":" << rollbacks
              << ",\"duplicates\":" << duplicates << ",\"core_rejections\":" << core_rejections
              << ",\"core_boundaries\":" << cap_boundaries << ",\"shared_pair_controls\":" << shared
              << ",\"acceptance_threshold_controls\":" << probability_controls << ",\"restarts\":10}" << std::endl;
    return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
