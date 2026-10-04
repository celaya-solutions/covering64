// Document:    Capped Neutral Recorder Unit Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      933fa24ab45d44e168dd145724f30dfc43deaffc1efa45453d57ffd657c6f4c9
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include "neutral.hpp"
#include <iostream>
struct Tie {int index;};
int main(int argc,char** argv) {
  try {
    if(argc!=2) throw std::runtime_error("output prefix required");
    nq::Sample<Tie> sample;
    for(int i=1;i<=100;++i) {
      ++sample.seen;
      if(sample.kept.size()<nq::CAP) {
        std::vector<int> ids;for(int b=0;b<63;++b) ids.push_back(b);
        ids.push_back(1000-i);sample.keep(ids,Tie{i},i*2);
      }
    }
    nq::write(argv[1],sample,{12,26},true,[](std::ostream& out,const Tie& t) {
      out<<"\"synthetic_control\":"<<t.index;
    });
    std::vector<int> base;for(int i=0;i<64;++i) base.push_back(i);
    auto valid=nq::family(base,{0},{64});
    if(valid.size()!=64 || valid.front()!=1 || valid.back()!=64) throw std::logic_error("family control");
    int rejected=0;
    try {nq::family(base,{0},{1});}catch(const std::logic_error&){++rejected;}
    try {nq::family(base,{0,1},{64});}catch(const std::logic_error&){++rejected;}
    try {nq::family(base,{100},{64});}catch(const std::logic_error&){++rejected;}
    if(rejected!=3) throw std::logic_error("damage controls");
    std::cout<<"{\"passed\":true,\"synthetic_seen\":100,\"retained\":64,\"rejected\":3,"
               "\"search_launches\":0}\n";
    return 0;
  }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 2;}
}
