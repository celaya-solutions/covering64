// Document:    Independent Synthetic Neutral Recorder Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      44a11b29d73f2ae3d0ee9fa42141bceb4f51c9140641ed49cac4200aa6c314b3
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include "../weak-pair-neutral-queue/neutral.hpp"
#include <iostream>
#include <numeric>

struct Tie { int outgoing, incoming; };
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  std::vector<int> center(64);
  std::iota(center.begin(), center.end(), 0);
  auto emit = [](std::ostream& out, const Tie& tie) {
    out << "\"outgoing\":" << tie.outgoing
        << ",\"incoming\":" << tie.incoming;
  };
  int rejected = 0;
  auto rejects = [&rejected](auto fn) {
    try { fn(); } catch (const std::logic_error&) { ++rejected; return; }
    throw std::logic_error("damaged control accepted");
  };
  for (int count : {0, 1, 64, 65, 70}) {
    nq::Sample<Tie> sample;
    for (int i = 0; i < count; ++i) {
      ++sample.seen;
      if (sample.kept.size() < nq::CAP)
        sample.keep(nq::family(center, {0}, {1000-i}), {0, 1000-i}, 3*i+2);
    }
    nq::write(std::string(argv[1])+"/count-"+std::to_string(count), sample,
              {12, 26}, count != 65, emit);
  }
  rejects([&] { (void)nq::family(center, {64}, {100}); });
  rejects([&] { (void)nq::family(center, {0}, {1}); });
  rejects([&] { (void)nq::family(center, {0}, {100, 101}); });
  rejects([&] { (void)nq::family(center, {0, 0}, {100, 101}); });
  rejects([&] {
    nq::Sample<Tie> sample;
    sample.keep(nq::family(center, {0}, {100}), {0, 100}, 1);
  });
  rejects([&] {
    nq::Sample<Tie> sample;
    sample.seen=65;
    sample.kept.resize(64);
    sample.keep(nq::family(center, {0}, {100}), {0, 100}, 1);
  });
  rejects([&] {
    nq::Sample<Tie> sample;
    sample.seen=2;
    sample.kept.push_back({center, {0, 100}, 1, 1});
    sample.kept.push_back({center, {0, 100}, 2, 2});
    nq::write(std::string(argv[1])+"/duplicates", sample, {12, 26}, true, emit);
  });
  rejects([&] {
    nq::Sample<Tie> sample;
    sample.seen=1;
    nq::write(std::string(argv[1])+"/missing", sample, {12, 26}, true, emit);
  });
  auto ids=nq::family(center, {63, 0}, {101, 100});
  if (ids.size()!=64 || ids.front()!=1 || ids[61]!=62 || ids[62]!=100 || ids[63]!=101)
    throw std::logic_error("two-swap family reconstruction");
  std::cout << "{\"damaged_controls_rejected\":" << rejected
            << ",\"positive_counts\":[0,1,64,65,70],\"two_swap_reconstruction\":true}\n";
}
