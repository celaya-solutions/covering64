// Document:    Three-Deletion Coverage Upper-Bound Screen
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      9293186b16dce0924977221f748871fa255712c75f78b0d26536593b63260b25
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Block = std::array<int, 5>;
using Cover = std::array<int, 10>;

template<class K> void print_hist(const std::map<K, long long>& histogram) {
  std::cout << "{";
  bool first = true;
  for (const auto& [key, value] : histogram) {
    if (!first) std::cout << ",";
    first = false;
    std::cout << "\"" << key << "\":" << value;
  }
  std::cout << "}";
}

int main(int argc, char** argv) {
  if (argc != 5) throw std::runtime_error("input expected_holes target_holes output.tsv");
  const auto started = std::chrono::steady_clock::now();
  const int expected_holes = std::stoi(argv[2]), target = std::stoi(argv[3]);
  if (target < 0 || target != expected_holes - 1) throw std::runtime_error("strict target");
  std::vector<Block> blocks;
  std::vector<Cover> covers;
  std::array<std::vector<int>, 560> containing;
  int triple_id[17][17][17] = {};
  int triple_count = 0;
  for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b) for (int c=b+1;c<=16;++c)
    triple_id[a][b][c] = triple_count++;
  for (int a=1;a<=16;++a) for (int b=a+1;b<=16;++b) for (int c=b+1;c<=16;++c)
    for (int d=c+1;d<=16;++d) for (int e=d+1;e<=16;++e) blocks.push_back({a,b,c,d,e});
  for (int id=0;id<4368;++id) {
    Cover coverage{}; int index=0;
    for (int a=0;a<5;++a) for (int b=a+1;b<5;++b) for (int c=b+1;c<5;++c) {
      int t=triple_id[blocks[id][a]][blocks[id][b]][blocks[id][c]];
      coverage[index++]=t; containing[t].push_back(id);
    }
    covers.push_back(coverage);
  }
  if (blocks.size()!=4368 || triple_count!=560) throw std::runtime_error("universe");
  for (const auto& carriers : containing) if (carriers.size()!=78) throw std::runtime_error("carrier size");
  std::ifstream input(argv[1]);
  if (!input) throw std::runtime_error("input missing");
  std::vector<int> selected;
  std::array<bool, 4368> chosen{};
  std::array<int, 560> multiplicity{};
  std::string line;
  while (std::getline(input,line)) {
    std::istringstream row(line); Block b{}; std::string extra;
    for (int& p : b) if (!(row>>p)) throw std::runtime_error("short block");
    if (row>>extra) throw std::runtime_error("long block");
    if (b[0]<1 || b[4]>16 || std::adjacent_find(b.begin(),b.end(),std::greater_equal<int>())!=b.end())
      throw std::runtime_error("labels/order");
    auto found=std::lower_bound(blocks.begin(),blocks.end(),b);
    if (found==blocks.end() || *found!=b) throw std::runtime_error("unknown block");
    int id=static_cast<int>(found-blocks.begin());
    if (chosen[id] || (!selected.empty() && selected.back()>=id)) throw std::runtime_error("duplicate/order");
    selected.push_back(id); chosen[id]=true;
    for (int t : covers[id]) ++multiplicity[t];
  }
  if (selected.size()!=64) throw std::runtime_error("need64");
  std::array<int, 4368> carrier_counts{};
  int initial_holes=0;
  for (int t=0;t<560;++t) if (!multiplicity[t]) {
    ++initial_holes;
    for (int id : containing[t]) ++carrier_counts[id];
  }
  if (initial_holes!=expected_holes) throw std::runtime_error("initial holes mismatch");
  std::vector<int> eligible;
  for (int id=0;id<4368;++id) if (!chosen[id]) eligible.push_back(id);
  if (eligible.size()!=4304) throw std::runtime_error("eligible size");
  std::ofstream output(argv[4]);
  if (!output) throw std::runtime_error("output missing");
  output << "delete0\tdelete1\tdelete2\tuncovered\tdemand\ttop0\ttop1\ttop2\tupper\texcluded\tadder_floor\tadders_meeting_floor\n";
  long long processed=0,excluded=0,candidate_evaluations=0,carrier_updates=0;
  std::map<int,long long> uncovered_hist,slack_hist,pool_hist;
  bool exhausted=true;
  for (int i=0;i<62;++i) for (int j=i+1;j<63;++j) for (int k=j+1;k<64;++k) {
    double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    if (elapsed>=29.0) {exhausted=false;goto finished;}
    std::array<int,3> deleted{selected[i],selected[j],selected[k]};
    std::vector<int> newly_uncovered;
    for (int id : deleted) for (int t : covers[id]) if (--multiplicity[t]==0) {
      newly_uncovered.push_back(t);
      for (int candidate : containing[t]) {++carrier_counts[candidate];++carrier_updates;}
    }
    int missing=initial_holes+static_cast<int>(newly_uncovered.size());
    int demand=missing-target;
    std::array<int,3> top{};
    std::array<int,11> count_hist{};
    for (int id : eligible) {
      const int value=carrier_counts[id];
      if (value<0 || value>10) throw std::runtime_error("carrier count bounds");
      ++count_hist[value];++candidate_evaluations;
      if (value>top[0]) {top[2]=top[1];top[1]=top[0];top[0]=value;}
      else if (value>top[1]) {top[2]=top[1];top[1]=value;}
      else if (value>top[2]) top[2]=value;
    }
    int upper=top[0]+top[1]+top[2];
    bool impossible=upper<demand;
    int floor=std::max(0,demand-top[0]-top[1]),pool=0;
    for (int value=floor;value<=10;++value) pool+=count_hist[value];
    ++processed;++uncovered_hist[missing];++slack_hist[upper-demand];
    if (impossible) ++excluded; else ++pool_hist[pool];
    output << deleted[0] << '\t' << deleted[1] << '\t' << deleted[2] << '\t' << missing << '\t'
           << demand << '\t' << top[0] << '\t' << top[1] << '\t' << top[2] << '\t' << upper << '\t'
           << impossible << '\t' << floor << '\t' << pool << '\n';
    for (int t : newly_uncovered) for (int candidate : containing[t]) --carrier_counts[candidate];
    for (int id : deleted) for (int t : covers[id]) ++multiplicity[t];
  }
finished:
  output.close();
  const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
  const bool complete=exhausted && processed==41664;
  std::cout << "{\"completed\":" << (complete?"true":"false")
    << ",\"deletions_processed\":" << processed << ",\"deletions_total\":41664"
    << ",\"initial_holes\":" << initial_holes << ",\"target_holes\":" << target
    << ",\"eligible_adders\":4304,\"excluded_deletions\":" << excluded
    << ",\"surviving_deletions\":" << processed-excluded
    << ",\"candidate_count_evaluations\":" << candidate_evaluations
    << ",\"carrier_increment_updates\":" << carrier_updates
    << ",\"elapsed_seconds\":" << elapsed << ",\"uncovered_histogram\":";
  print_hist(uncovered_hist); std::cout << ",\"upper_minus_demand_histogram\":";print_hist(slack_hist);
  std::cout << ",\"survivor_necessary_pool_size_histogram\":";print_hist(pool_hist);
  std::cout << ",\"replacement_tuples_examined\":0,\"optimizer_calls\":0}\n";
  return complete?0:2;
}
