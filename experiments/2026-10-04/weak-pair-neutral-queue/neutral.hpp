// Document:    Capped Neutral Observation Recorder
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      2af002eb04ee055cf87e1fe917e2504aad1fb14be8ad8da0360c00a1d36fb999
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#pragma once
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <initializer_list>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace nq {
constexpr std::size_t CAP=64;
inline std::vector<int> family(const std::vector<int>& center,
    std::initializer_list<int> outgoing,std::initializer_list<int> incoming) {
  auto ids=center;
  for(int b:outgoing) {
    auto it=std::find(ids.begin(),ids.end(),b);
    if(it==ids.end()) throw std::logic_error("neutral removal absent");
    ids.erase(it);
  }
  ids.insert(ids.end(),incoming.begin(),incoming.end());
  std::sort(ids.begin(),ids.end());
  if(ids.size()!=64 || std::adjacent_find(ids.begin(),ids.end())!=ids.end())
    throw std::logic_error("malformed neutral family");
  return ids;
}
template<class Tie> struct Sample {
  struct Item {std::vector<int> ids;Tie tie;std::uint64_t traversal,ordinal;};
  std::uint64_t seen=0;
  std::vector<Item> kept;
  void keep(std::vector<int> ids,const Tie& tie,std::uint64_t ordinal) {
    if(kept.size()>=CAP || seen!=kept.size()+1)
      throw std::logic_error("neutral retention accounting");
    kept.push_back({std::move(ids),tie,seen,ordinal});
  }
};
template<class Tie,class Emit> void write(const std::string& prefix,Sample<Tie>& sample,
    std::pair<int,int> rank,bool complete,Emit emit) {
  if(sample.kept.size()!=std::min<std::uint64_t>(sample.seen,CAP))
    throw std::logic_error("neutral cap accounting");
  std::sort(sample.kept.begin(),sample.kept.end(),
            [](const auto& a,const auto& b){return a.ids<b.ids;});
  for(std::size_t i=1;i<sample.kept.size();++i)
    if(sample.kept[i-1].ids==sample.kept[i].ids)
      throw std::logic_error("duplicate neutral family");
  std::ofstream out(prefix+"-neutral.json");
  if(!out) throw std::runtime_error("cannot write neutral sample");
  out<<"[\n";
  for(std::size_t i=0;i<sample.kept.size();++i) {
    const auto& item=sample.kept[i];if(i) out<<",\n";
    out<<"{";emit(out,item.tie);
    out<<",\"neutral_index\":"<<item.traversal<<",\"neutral_ordinal\":"<<item.ordinal
       <<",\"ids\":[";
    for(std::size_t j=0;j<item.ids.size();++j) out<<(j?",":"")<<item.ids[j];
    out<<"]}";
  }
  out<<"\n]\n";out.close();if(!out) throw std::runtime_error("neutral sample write failed");
  std::ofstream meta(prefix+"-neutral-meta.json");
  if(!meta) throw std::runtime_error("cannot write neutral metadata");
  meta<<"{\"neutral_seen\":"<<sample.seen<<",\"retained\":"<<sample.kept.size()
      <<",\"cap\":64,\"capped\":"<<(sample.seen>CAP?"true":"false")
      <<",\"complete\":"<<(complete?"true":"false")
      <<",\"rank\":["<<rank.first<<","<<rank.second<<"]}\n";
  meta.close();if(!meta) throw std::runtime_error("neutral metadata write failed");
}
} // namespace nq
