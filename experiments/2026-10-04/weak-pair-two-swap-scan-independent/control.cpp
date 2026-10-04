// Document:    Independent Two-Swap Native State Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      2d2ff43b95003587ca0d8015e61fb1030298e419a463c2c29c500cd1eb406b6a
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include "../weak-pair-two-swap-scan/two_scan.hpp"
#include <fstream>
#include <iostream>
#include <memory>

static void require(bool ok,const char* why) {if(!ok) throw std::runtime_error(why);}
template<class Values> static void array(const Values& values) {
  std::cout<<'[';bool first=true;for(auto value:values) {
    if(!first)std::cout<<',';first=false;std::cout<<value;
  }std::cout<<']';
}
static void metric(const ws::Metrics& m) {
  std::cout<<"{\"cardinality\":"<<m.cardinality<<",\"holes\":"<<m.holes
    <<",\"D2max\":"<<m.d2max<<",\"D2sum\":"<<m.d2sum
    <<",\"D3\":"<<m.d3<<",\"D4\":"<<m.d4
    <<",\"minimum_pair_count\":"<<m.minimum_pair_count<<",\"core_overlaps\":";
  array(m.core_overlaps);std::cout<<",\"legal\":"<<(m.legal()?"true":"false")<<'}';
}
static void state(const ws::Counts& c) {
  std::cout<<"{\"ids\":";array(c.ids());std::cout<<",\"counts\":{\"2\":";
  array(c.pair);std::cout<<",\"3\":";array(c.triple);std::cout<<",\"4\":";
  array(c.quad);std::cout<<"},\"metrics\":";metric(ws::full_metrics(c));
  std::cout<<",\"pair_metrics\":[";
  for(int p=0;p<ws::NP;++p) {
    if(p)std::cout<<',';auto m=ws::pair_metrics(c,p);
    std::cout<<"{\"single_deficit\":"<<m.d3<<",\"quad_deficit\":"<<m.d4
      <<",\"D2max\":"<<m.d2max<<",\"D2sum\":"<<m.d2sum<<'}';
  }std::cout<<"]}";
}
static bool same(const ws::Counts& a,const ws::Counts& b) {
  return a.pair==b.pair && a.triple==b.triple && a.quad==b.quad && a.chosen==b.chosen
    && a.cardinality==b.cardinality && a.holes==b.holes;
}
static void universe(const ts::Universe& u) {
  std::cout<<"{\"event\":\"universe\",\"supersets\":[";bool first=true;
  for(int mask=0;mask<65536;++mask) {
    if(!u.supersets[mask].empty()) {
      if(!first)std::cout<<',';first=false;std::cout<<'['<<mask<<',';
      array(u.supersets[mask]);std::cout<<']';
    }
  }
  std::cout<<"],\"pair_masks\":";array(u.pair_masks);std::cout<<"}\n";
}
int main(int argc,char** argv) {
  try {
    require(argc==3,"usage: control BASE CASES");
    auto u=std::make_unique<ts::Universe>();universe(*u);
    auto ids=u->read(argv[1]);ts::TwoSwapEngine e(*u,ids);const ws::Counts baseline=e.current;
    std::cout<<"{\"event\":\"initial\",\"state\":";state(e.current);std::cout<<"}\n";
    std::ifstream file(argv[2]);require(bool(file),"missing cases");int b,c,a,n=0,finals=0;
    while(file>>b>>c>>a) {
      e.begin(b,c);e.add_first(a);const ws::Counts partial=e.current;
      auto support=e.support();auto candidates=e.completions(a);
      std::cout<<"{\"event\":\"partial\",\"outgoing\":["<<b<<','<<c
        <<"],\"first_incoming\":"<<a<<",\"support\":{\"impossible\":"
        <<(support.impossible?"true":"false")<<",\"mask\":"<<support.mask
        <<",\"size\":"<<support.size<<",\"deficit_gt_one\":"
        <<(support.deficit_gt_one?"true":"false")<<"},\"completions\":";array(candidates);
      std::cout<<",\"state\":";state(e.current);std::cout<<"}\n";
      std::vector<int> controls;
      if(!candidates.empty()) {controls.push_back(candidates.front());controls.push_back(candidates.back());}
      for(int d=a+1;d<vc::NB;++d) if(!e.initial_chosen[d] &&
          !std::binary_search(candidates.begin(),candidates.end(),d)) {controls.push_back(d);break;}
      std::sort(controls.begin(),controls.end());controls.erase(std::unique(controls.begin(),controls.end()),controls.end());
      for(int d:controls) {
        auto m=e.evaluate_last(d);require(same(e.current,partial),"last-add rollback failed");
        e.current.add(d);
        std::cout<<"{\"event\":\"final_control\",\"outgoing\":["<<b<<','<<c
          <<"],\"incoming\":["<<a<<','<<d<<"],\"evaluation\":";metric(m);
        std::cout<<",\"state\":";state(e.current);std::cout<<"}\n";
        e.current.remove(d);require(same(e.current,partial),"manual last rollback failed");++finals;
      }
      e.remove_first(a);e.end(b,c);require(same(e.current,baseline),"outer rollback failed");
      for(int d:controls) {
        auto m=e.evaluate(b,c,a,d);require(same(e.current,baseline),"convenience rollback failed");
        std::cout<<"{\"event\":\"convenience\",\"outgoing\":["<<b<<','<<c
          <<"],\"incoming\":["<<a<<','<<d<<"],\"metrics\":";metric(m);std::cout<<"}\n";
      }++n;
    }
    require(file.eof(),"damaged cases");int rejected=0;
    auto reject=[&](auto operation) {
      const ws::Counts before=e.current;int rb=e.removed_b,rc=e.removed_c,fa=e.first_a;
      try {operation();} catch(const std::runtime_error&) {
        ++rejected;require(same(e.current,before) && rb==e.removed_b && rc==e.removed_c && fa==e.first_a,
                          "rejected operation mutated state");return;
      }throw std::runtime_error("invalid operation accepted");
    };
    b=1142;c=1871;a=145;int d=146;while(e.initial_chosen[d])++d;
    reject([&]{e.add_first(a);});reject([&]{e.support();});reject([&]{e.completions(a);});
    reject([&]{e.evaluate_last(d);});reject([&]{e.remove_first(a);});reject([&]{e.end(b,c);});
    reject([&]{e.begin(-1,c);});reject([&]{e.begin(b,vc::NB);});reject([&]{e.begin(c,b);});
    reject([&]{e.begin(b,b);});reject([&]{e.begin(a,c);});
    reject([&]{e.evaluate(b,c,a,a);});reject([&]{e.evaluate(b,c,d,a);});
    reject([&]{e.evaluate(b,c,-1,d);});reject([&]{e.evaluate(b,c,a,vc::NB);});
    reject([&]{e.evaluate(b,c,b,c);});
    e.begin(b,c);reject([&]{e.begin(b,c);});reject([&]{e.support();});
    reject([&]{e.add_first(b);});reject([&]{e.add_first(-1);});
    e.add_first(a);const ws::Counts partial=e.current;
    reject([&]{e.add_first(d);});reject([&]{e.completions(d);});
    reject([&]{e.evaluate_last(a);});reject([&]{e.evaluate_last(-1);});
    reject([&]{e.evaluate_last(vc::NB);});reject([&]{e.evaluate_last(c);});
    reject([&]{e.remove_first(d);});reject([&]{e.end(b,c);});
    require(same(e.current,partial),"partial rejection rollback");
    e.remove_first(a);reject([&]{e.end(c,b);});e.end(b,c);
    require(same(e.current,baseline),"final restoration");require(rejected==29,"rejection count");
    std::cout<<"{\"event\":\"finished\",\"partials\":"<<n<<",\"final_controls\":"<<finals
      <<",\"invalid_operations_rejected\":"<<rejected<<",\"rollback_passed\":true,\"optimizer_launches\":0}\n";
  } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 3;}
}
