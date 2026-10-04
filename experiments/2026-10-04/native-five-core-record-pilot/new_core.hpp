// Document:    Named Common62 Core Record Qualification
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      fc8e8678e5a3dd8e4427ffa5f47b217474f6787cce0a17510fd1e026c6ca80ff
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#pragma once
#include <array>
#include <utility>
namespace escape_core {
constexpr std::array<int,62> ids = {46,123,155,222,357,407,437,535,545,633,676,713,740,980,1020,1082,1230,1247,1347,1391,1429,1459,1511,1659,1789,1962,2028,2057,2140,2161,2218,2285,2306,2402,2432,2660,2687,2764,2869,2960,3036,3053,3135,3227,3313,3374,3437,3502,3527,3556,3578,3606,3615,3665,3759,3870,3936,4040,4063,4158,4201,4277};
constexpr std::array<int,5> thresholds = {55,55,55,55,56};
inline bool eligible(int cardinality,const std::array<int,5>& overlaps) {
  if(cardinality!=64) return false;
  for(int i=0;i<5;++i) if(overlaps[i]>thresholds[i]) return false;
  return true;
}
inline bool weak_eligible(int cardinality,const std::array<int,5>& overlaps,
    int holes,int minimum_pair_count,int d3,int d4) {
  return eligible(cardinality,overlaps) && holes<=11 && minimum_pair_count>=5 && d3==0 && d4==0;
}
inline bool weak_rank_improves(int holes,int d2,bool present,int best_holes,int best_d2) {
  return !present || std::pair{holes,d2}<std::pair{best_holes,best_d2};
}
} // namespace escape_core
