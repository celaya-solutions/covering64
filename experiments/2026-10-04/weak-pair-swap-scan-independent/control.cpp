// Document:    Independent Weak-Pair Native Fixed Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      12bc8a00dc4fdeb1b9a4c152df8b7b63b8dd859bee5588cbd18ce31f816fb734
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include "../weak-pair-swap-scan/scan.hpp"
#include <fstream>
#include <iostream>
#include <memory>

static void require(bool ok,const char* why) { if(!ok) throw std::runtime_error(why); }
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
static void universe(const ws::Universe& u) {
  std::cout<<"{\"event\":\"universe\",\"columns\":[";
  for(int b=0;b<vc::NB;++b) {
    if(b)std::cout<<',';std::cout<<'[';array(u.points[b]);std::cout<<',';
    array(u.pair_members[b]);std::cout<<',';array(u.members[b]);std::cout<<',';
    array(u.quad_members[b]);std::cout<<']';
  }std::cout<<"],\"pair_rows\":[";
  for(int p=0;p<ws::NP;++p) {
    if(p)std::cout<<',';std::cout<<'[';array(u.pair_triples[p]);std::cout<<',';
    array(u.pair_quads[p]);std::cout<<']';
  }std::cout<<"]}\n";
}
int main(int argc,char** argv) {
  try {
    require(argc==3,"usage: control BASE CASES");
    auto u=std::make_unique<ws::Universe>();
    universe(*u);
    auto ids=u->read(argv[1]);
    ws::SwapEngine e(*u,ids);const ws::Counts original=e.current;
    std::cout<<"{\"event\":\"initial\",\"state\":";state(e.current);std::cout<<"}\n";
    std::ifstream input(argv[2]);require(bool(input),"missing cases");
    int out,in,n=0;
    while(input>>out>>in) {
      auto affected=e.affected(out,in);auto m=e.evaluate(out,in);
      require(same(e.current,original),"evaluate rollback mismatch");
      e.current.remove(out);e.current.add(in);
      std::cout<<"{\"event\":\"trial\",\"out\":"<<out<<",\"in\":"<<in
        <<",\"evaluation\":";metric(m);std::cout<<",\"affected\":";array(affected);
      std::cout<<",\"state\":";state(e.current);std::cout<<"}\n";
      e.current.remove(in);e.current.add(out);
      require(same(e.current,original),"manual rollback mismatch");++n;
    }
    require(input.eof(),"damaged cases");
    int absent=0;while(e.initial_chosen[absent])++absent;
    int rejected=0;
    auto reject=[&](auto operation) {
      try {operation();} catch(const std::runtime_error&) {
        ++rejected;require(same(e.current,original),"rejection mutated state");return;
      }throw std::runtime_error("invalid operation accepted");
    };
    reject([&]{e.evaluate(-1,absent);});reject([&]{e.evaluate(vc::NB,absent);});
    reject([&]{e.evaluate(ids[0],-1);});reject([&]{e.evaluate(ids[0],vc::NB);});
    reject([&]{e.evaluate(absent,ids[0]);});reject([&]{e.evaluate(ids[0],ids[1]);});
    reject([&]{e.current.add(ids[0]);});reject([&]{e.current.add(-1);});
    reject([&]{e.current.add(vc::NB);});reject([&]{e.current.remove(absent);});
    reject([&]{e.current.remove(-1);});reject([&]{e.current.remove(vc::NB);});
    require(rejected==12,"rejection count");
    ws::Metrics legal;legal.cardinality=64;legal.minimum_pair_count=5;
    require(legal.legal(),"legal metadata rejected");
    int predicate_rejections=0;
    for(int field=0;field<5;++field) {
      auto bad=legal;
      if(field==0)bad.cardinality=63;if(field==1)bad.minimum_pair_count=4;
      if(field==2)bad.d3=1;if(field==3)bad.d4=1;if(field==4)bad.core_overlaps[2]=56;
      require(!bad.legal(),"illegal metadata accepted");++predicate_rejections;
    }
    auto a=legal,b=legal;a.holes=11;a.d2max=999;b.holes=12;b.d2max=0;
    require(a.rank()<b.rank(),"holes do not rank first");
    b=a;b.d2sum=9999;require(a.rank()==b.rank(),"full-row sum affected rank");
    std::cout<<"{\"event\":\"finished\",\"trials\":"<<n
      <<",\"invalid_operations_rejected\":"<<rejected
      <<",\"predicate_rejections\":"<<predicate_rejections<<",\"rank_controls\":2"
      <<",\"rollback_passed\":true,\"optimizer_launches\":0}\n";
  } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 3;}
}
