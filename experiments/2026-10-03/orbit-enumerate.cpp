// Document:    Exhaustive four-orbit union control
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      [pending]
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include <cstdio>
#include <cstdint>
#include <vector>
#include <fstream>
#include <charconv>
#include <string>
int main(int argc,char**argv){
 if(argc!=2)return 2;
 std::ifstream in(argv[1]); if(!in)return 2;
 std::vector<uint64_t> a; std::string token;
 while(in>>token){
  uint64_t x=0;
  auto parsed=std::from_chars(token.data(),token.data()+token.size(),x);
  if(parsed.ec!=std::errc{} || parsed.ptr!=token.data()+token.size() || x>=(1ULL<<35))return 3;
  a.push_back(x); if(a.size()>273)return 3;
 }
 if(!in.eof())return 3;
 if(a.size()!=273)return 3;
 uint64_t all=(1ULL<<35)-1, checks=0; int best=0;
 for(int i=0;i<273;i++)for(int j=i+1;j<273;j++)
 for(int k=j+1;k<273;k++){
  uint64_t abc=a[i]|a[j]|a[k];
  for(int l=k+1;l<273;l++){
   checks++;int c=__builtin_popcountll(abc|a[l]);
   if(c>best){best=c; printf("best %d orbits %d %d %d %d\n",best,i,j,k,l);fflush(stdout);}
   if((abc|a[l])==all){printf("FOUND\n");return 0;}
  }
 }
 printf("EXHAUSTED combinations=%llu best_triple_orbits=%d/35 scope=translation_invariant_four_orbits_only\n",(unsigned long long)checks,best);
 return 1;
}
