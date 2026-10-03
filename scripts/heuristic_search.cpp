// Document:    Weighted local search for C(16,5,3)
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      [pending]
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
// Research heuristic only: a positive deficit is not a covering witness.
#include <algorithm>
#include <array>
#include <chrono>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <csignal>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Block { unsigned mask; std::array<int,10> triples; };
std::vector<Block> blocks;
std::vector<unsigned> triples;
std::array<std::vector<int>,560> containing;
std::array<int,65536> bymask{}, tripleid{};
std::mt19937_64 rng;
volatile std::sig_atomic_t stopped=0;
void stop_search(int) { stopped=1; }
int randint(int n) { return int(rng()%n); }
void universe() {
  bymask.fill(-1); tripleid.fill(-1);
  for(int a=0;a<16;a++) for(int b=a+1;b<16;b++) for(int c=b+1;c<16;c++) {
    unsigned m=(1u<<a)|(1u<<b)|(1u<<c);
    tripleid[m]=int(triples.size()); triples.push_back(m);
  }
  for(int a=0;a<16;a++) for(int b=a+1;b<16;b++) for(int c=b+1;c<16;c++)
  for(int d=c+1;d<16;d++) for(int e=d+1;e<16;e++) {
    unsigned m=(1u<<a)|(1u<<b)|(1u<<c)|(1u<<d)|(1u<<e);
    Block v; v.mask=m; int j=0;
    for(unsigned t=m;t;t=(t-1)&m) if(__builtin_popcount(t)==3) v.triples[j++]=tripleid[t];
    int id=int(blocks.size()); bymask[m]=id;
    for(int t:v.triples) containing[t].push_back(id);
    blocks.push_back(v);
  }
}
std::vector<int> read_blocks(const std::string &path) {
  std::ifstream f(path); if(!f) throw std::runtime_error("Cannot read start file");
  std::vector<int> ids; std::string line;
  while(std::getline(f,line)) {
    if(line.empty()||line[0]=='#') continue;
    std::istringstream s(line); unsigned m=0; int n,cnt=0;std::string token;
    while(s>>token) {
      int x=0;auto parsed=std::from_chars(token.data(),token.data()+token.size(),x);
      if(parsed.ec!=std::errc{} || parsed.ptr!=token.data()+token.size())throw std::runtime_error("Malformed block token");
      if(x<1||x>16||(m&(1u<<(x-1))))throw std::runtime_error("Malformed block");
      m|=1u<<(x-1);cnt++;
    }
    if(cnt!=5 || (n=bymask[m])<0) throw std::runtime_error("Malformed block");
    if(std::find(ids.begin(),ids.end(),n)!=ids.end()) throw std::runtime_error("Duplicate block");
    ids.push_back(n);
  }
  if(ids.size()<64) throw std::runtime_error("Start needs at least 64 blocks");
  return ids;
}
void save(const std::string &path,std::vector<int> ids) {
  std::sort(ids.begin(),ids.end()); std::ofstream f(path);
  if(!f)throw std::runtime_error("Cannot open candidate output");
  for(int id:ids) { bool first=true; for(int x=0;x<16;x++) if(blocks[id].mask&(1u<<x)) { if(!first)f<<' ';f<<x+1;first=false;} f<<'\n'; }
  if(!f)throw std::runtime_error("Cannot write candidate output");
}
struct State {
  std::array<int,560> count{}, weight{};
  std::array<bool,4368> selected{};
  std::vector<int> ids;
  int deficit=560;
  explicit State(std::vector<int> start):ids(std::move(start)) {
    weight.fill(1); for(int b:ids) {selected[b]=true;for(int t:blocks[b].triples) if(count[t]++==0)deficit--;}
  }
  void move(int slot,int b) {
    int a=ids[slot];selected[a]=false;selected[b]=true;ids[slot]=b;
    for(int t:blocks[a].triples)if(--count[t]==0)deficit++;
    for(int t:blocks[b].triples)if(count[t]++==0)deficit--;
  }
};
int main(int argc,char **argv) {
 try {
  if(argc<6) {std::cerr<<"usage: heuristic_search START SEED SECONDS OUTPUT_PREFIX MODE [STEPS_PER_RESTART] [BLOCK_COUNT=64] [CORE_DISTANCE=4]\n";return 2;}
  universe(); uint64_t seed=std::stoull(argv[2]);rng.seed(seed);
  std::signal(SIGTERM,stop_search);std::signal(SIGINT,stop_search);
  double budget=std::stod(argv[3]);std::string prefix=argv[4],mode=argv[5];
  uint64_t restart_steps=argc>6?std::stoull(argv[6]):100000;
  int target_count=argc>7?std::stoi(argv[7]):64;
  int core_distance=argc>8?std::stoi(argv[8]):4;
  if(target_count!=64&&target_count!=65)throw std::runtime_error("Block count must be 64 or 65");
  if(!std::isfinite(budget)||budget<=0||restart_steps==0||(mode!="tabu"&&mode!="plain"&&mode!="point"&&mode!="link"&&mode!="escape"&&mode!="escapeplain"&&mode!="cap2"&&mode!="cap2weighted"&&mode!="anneal"&&mode!="threshold"&&mode!="multithreshold"&&mode!="hybrid"&&mode!="regular"&&mode!="dispersion"))throw std::runtime_error("Bad budget or mode");
  auto baseline=read_blocks(argv[1]);auto best=baseline;
  if(int(baseline.size())<target_count)throw std::runtime_error("Too few starting blocks");
  int movable_count=target_count;
  bool escape_mode=mode=="escape"||mode=="escapeplain";
  bool cap_mode=mode=="cap2"||mode=="cap2weighted";
  if(cap_mode) {
    State original(baseline);
    if(target_count!=64||baseline.size()!=64||std::any_of(original.count.begin(),original.count.end(),[](int n){return n>2;}))
      throw std::runtime_error("Multiplicity-cap mode requires64 blocks with no triple covered more than twice");
  }
  std::array<bool,4368> core{};int core_size=0;
  if(escape_mode) {
    State original(baseline);
    if(target_count!=64||baseline.size()!=65||original.deficit!=0)throw std::runtime_error("Escape mode requires a valid65-block seed");
    for(int b:baseline) {
      unsigned private_union=0;for(int t:blocks[b].triples)if(original.count[t]==1)private_union|=triples[t];
      if(__builtin_popcount(private_union)==5){core[b]=true;core_size++;}
    }
    if(core_distance<1||core_distance>core_size)throw std::runtime_error("Invalid core distance");
  }
  if(mode=="link") {
    if(target_count!=64||baseline.size()!=64)throw std::runtime_error("Link mode requires64 starting blocks");
    auto middle=std::stable_partition(baseline.begin(),baseline.end(),[](int b){return !(blocks[b].mask&(1u<<15));});
    movable_count=int(middle-baseline.begin());
    if(movable_count!=45)throw std::runtime_error("Link mode requires exactly19 blocks containing16");
    State seed_state(baseline);
    for(int t=0;t<560;t++)if((triples[t]&(1u<<15)) && seed_state.count[t]==0)
      throw std::runtime_error("Fixed link does not cover all triples containing16");
    best=baseline;
  }
  if(mode=="regular") {
    std::array<int,16> replication{};
    for(int b:baseline)for(int p=0;p<16;p++)if(blocks[b].mask&(1u<<p))replication[p]++;
    if(target_count!=64 || baseline.size()!=64 || std::any_of(replication.begin(),replication.end(),[](int n){return n!=20;}))
      throw std::runtime_error("Regular mode requires 64 distinct blocks and point degrees exactly20");
  }
  int global=561;uint64_t iterations=0,restarts=0;
  auto started=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
  std::cout<<"{\"seed\":"<<seed<<",\"budget_seconds\":"<<budget<<",\"mode\":\""<<mode<<"\",\"restart_steps\":"<<restart_steps<<",\"target_blocks\":"<<target_count<<",\"core_size\":"<<core_size<<",\"minimum_core_changes\":"<<(escape_mode?core_distance:0)<<",\"triple_multiplicity_cap\":"<<(cap_mode?2:0)<<"}"<<std::endl;
  while(elapsed()<budget && !stopped) {
    auto initial=(restarts%3==1 && global<561)?best:baseline;
    while(int(initial.size())>target_count) initial.erase(initial.begin()+randint(int(initial.size())));
    State s(initial);
    if(escape_mode) {
      int retained_core=0;for(int b:s.ids)retained_core+=core[b];
      while(retained_core>core_size-core_distance) {
        int slot;do slot=randint(target_count);while(!core[s.ids[slot]]);
        int b;do b=randint(4368);while(s.selected[b]||core[b]);s.move(slot,b);retained_core--;
      }
    }
    if(restarts%3==1 && mode!="regular" && !cap_mode) for(int j=0;j<2+int(restarts%11);j++){int b;do b=randint(4368);while(s.selected[b]||(escape_mode&&core[b])||(mode=="link"&&(blocks[b].mask&(1u<<15))));s.move(randint(movable_count),b);}
    if(restarts%3==2 && mode=="anneal") for(int j=0;j<target_count;j++){int b;do b=randint(4368);while(s.selected[b]);s.move(j,b);}
    std::array<uint64_t,4368> tabu{};
    std::array<uint64_t,4368> protected_until{};
    std::array<std::array<uint64_t,16>,16> point_tabu{};
    uint64_t lastbest=0;int local=561;
    for(uint64_t step=0;;step++,iterations++) {
      if(s.deficit<global) {
        State audited(s.ids);
        if(audited.deficit!=s.deficit || audited.count!=s.count || audited.selected!=s.selected ||
          std::count(s.selected.begin(),s.selected.end(),true)!=target_count)
          throw std::runtime_error("Incremental coverage audit failed");
        if(cap_mode && std::any_of(s.count.begin(),s.count.end(),[](int n){return n>2;}))
          throw std::runtime_error("Multiplicity-cap invariant failed");
        global=s.deficit;best=s.ids;save(prefix+"-best.txt",best);save(prefix+"-deficit-"+std::to_string(global)+".txt",best);
        std::cout<<"{\"event\":\"best\",\"deficit\":"<<global<<",\"seconds\":"<<elapsed()<<",\"iteration\":"<<iterations<<",\"restart\":"<<restarts<<"}"<<std::endl;
        if(global==0)return 0;
      }
      if(step>=restart_steps || ((step&4095)==0 && (elapsed()>=budget||stopped)))break;
      if(s.deficit<local){local=s.deficit;lastbest=step;}
      if(mode=="regular" || (mode=="hybrid" && randint(2)==0) || (mode=="multithreshold" && randint(3)==0)) {
        int i=randint(target_count),j=randint(target_count-1);if(j>=i)j++;
        int a=s.ids[i],b=s.ids[j]; unsigned am=blocks[a].mask,bm=blocks[b].mask;
        unsigned adiff=am&~bm,bdiff=bm&~am;
        int ax=randint(__builtin_popcount(adiff)),bx=randint(__builtin_popcount(bdiff));
        unsigned ap=0,bp=0;
        for(int p=0;p<16;p++){if(adiff&(1u<<p))if(ax--==0)ap=1u<<p;if(bdiff&(1u<<p))if(bx--==0)bp=1u<<p;}
        int na=bymask[am^ap^bp],nb=bymask[bm^ap^bp];
        if(s.selected[na]||s.selected[nb]||na==nb)continue;
        std::array<int,560> change{};std::array<int,40> touched{};int nt=0;
        auto apply=[&](int id,int dir){for(int t:blocks[id].triples){touched[nt++]=t;change[t]+=dir;}};
        apply(a,-1);apply(b,-1);apply(na,1);apply(nb,1);
        int delta=0;for(int k=0;k<nt;k++){int t=touched[k];if(change[t]){delta+=(s.count[t]+change[t]==0)-(s.count[t]==0);change[t]=0;}}
        double phase=double(step%1000000)/1000000.;double temp=0.05+0.65*std::pow(1-phase,3);
        bool accept=mode=="multithreshold" ? (delta<0||s.deficit+delta<=global+int(step/1000000)%7) :
          (delta<=0||std::generate_canonical<double,53>(rng)<std::exp(-delta/temp));
        if(accept){s.move(i,na);s.move(j,nb);}
        continue;
      }
      if(mode=="anneal"||mode=="threshold"||mode=="multithreshold"||mode=="hybrid"||mode=="dispersion") {
        int slot=randint(target_count),old=s.ids[slot],remove=randint(5),add=randint(11),x=0,y=0;
        for(int p=0;p<16;p++) if(blocks[old].mask&(1u<<p)) {if(remove--==0)x=p;} else {if(add--==0)y=p;}
        unsigned proposal=blocks[old].mask^(1u<<x)^(1u<<y);
        if(mode=="multithreshold" && randint(2)==0) {
          int remove2=randint(4),add2=randint(10),x2=0,y2=0;
          for(int p=0;p<16;p++)if(p!=x && p!=y) {
            if(blocks[old].mask&(1u<<p)){if(remove2--==0)x2=p;}else{if(add2--==0)y2=p;}
          }
          proposal^=(1u<<x2)^(1u<<y2);
        }
        int b=bymask[proposal];if(s.selected[b])continue;
        int delta=0,spread=0;
        for(int t:blocks[old].triples)if((triples[t]&blocks[b].mask)!=triples[t]){if(s.count[t]==1)delta++;spread-=s.count[t]-1;}
        for(int t:blocks[b].triples)if((triples[t]&blocks[old].mask)!=triples[t]){if(s.count[t]==0)delta--;spread+=s.count[t];}
        double phase=double(step%1000000)/1000000.;
        double temp=0.08+0.62*std::pow(1-phase,3);
        double energy=delta+(mode=="dispersion" ? 0.005*(1+int(restarts%8))*spread : 0.0);
        bool accept=(mode=="threshold"||mode=="multithreshold") ? (delta<0||s.deficit+delta<=global+int(step/1000000)%(mode=="multithreshold"?7:5)) :
          (energy<=0 || std::generate_canonical<double,53>(rng)<std::exp(-energy/temp));
        if(accept)s.move(slot,b);
        continue;
      }
      std::vector<int> uncovered;for(int t=0;t<560;t++)if(s.count[t]==0)uncovered.push_back(t);
      int target=uncovered[randint(int(uncovered.size()))];
      int retained_core=0;if(escape_mode)for(int b:s.ids)retained_core+=core[b];
      std::array<int,65> loss{};
      for(int i=0;i<movable_count;i++)for(int t:blocks[s.ids[i]].triples)if(s.count[t]==1)loss[i]+=s.weight[t];
      int bestscore=std::numeric_limits<int>::max(),newb=-1,slot=-1,ties=0;
      for(int b:containing[target]) {
        if(s.selected[b] || (mode=="link" && (blocks[b].mask&(1u<<15))))continue;
        int gain=0;for(int t:blocks[b].triples)if(s.count[t]==0)gain+=s.weight[t];
        for(int i=0;i<movable_count;i++) {
          int old=s.ids[i],score=loss[i]-gain;
          if(escape_mode && core[b] && !core[old] && retained_core>=core_size-core_distance)continue;
          if(cap_mode) {
            bool allowed=true;for(int t:blocks[b].triples)if(s.count[t]>=2 && (triples[t]&blocks[old].mask)!=triples[t]){allowed=false;break;}
            if(!allowed)continue;
          }
          if(protected_until[old]>step)continue;
          int overlap=__builtin_popcount(blocks[b].mask&blocks[old].mask);
          if(mode=="point" && overlap!=4)continue;
          if(__builtin_popcount(blocks[b].mask&blocks[old].mask)>=3)
            for(int t:blocks[old].triples)if(s.count[t]==1 && (triples[t]&blocks[b].mask)==triples[t])score-=s.weight[t];
          if(mode=="point") {
            int x=__builtin_ctz(blocks[old].mask&~blocks[b].mask),y=__builtin_ctz(blocks[b].mask&~blocks[old].mask);
            if(point_tabu[x][y]>step && s.deficit+score>=global)continue;
          }
          if(tabu[b]>step) {
            int delta=0;
            for(int t:blocks[old].triples)if(s.count[t]==1 && (triples[t]&blocks[b].mask)!=triples[t])delta++;
            for(int t:blocks[b].triples)if(s.count[t]==0)delta--;
            if(s.deficit+delta>=global)continue;
          }
          if(score<bestscore){bestscore=score;newb=b;slot=i;ties=1;}
          else if(score==bestscore && randint(++ties)==0){newb=b;slot=i;}
        }
      }
      if(newb<0)continue;
      int old=s.ids[slot];s.move(slot,newb);tabu[old]=step+5+randint(18);
      protected_until[newb]=step+5;
      if(mode=="point") {
        int x=__builtin_ctz(blocks[old].mask&~blocks[newb].mask),y=__builtin_ctz(blocks[newb].mask&~blocks[old].mask);
        point_tabu[x][y]=point_tabu[y][x]=step+10+randint(3);
      }
      if(mode!="plain" && mode!="escapeplain" && mode!="cap2" && mode!="point" && step-lastbest>40 && step%8==0) {
        for(int t=0;t<560;t++)if(s.count[t]==0)s.weight[t]++;
      }
      if(step%3000==2999)for(int &w:s.weight)w=1+(w-1)*3/4;
    }
    if(restarts%10==0)std::cout<<"{\"event\":\"progress\",\"restart\":"<<restarts<<",\"local_best\":"<<local<<",\"current_deficit\":"<<s.deficit<<",\"seconds\":"<<elapsed()<<"}"<<std::endl;
    restarts++;
  }
  std::cout<<"{\"event\":\""<<(stopped?"interrupted":"finished")<<"\",\"best_deficit\":"<<global<<",\"seconds\":"<<elapsed()<<",\"iterations\":"<<iterations<<",\"restarts\":"<<restarts<<"}"<<std::endl;
  return global==0?0:1;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}
}
