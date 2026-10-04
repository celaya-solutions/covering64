// Document:    Declared-Partition Core Transport Enumeration
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      ec121e5bde5ff49905cc465a231e18a150d720fe83026de1f54f9e450fd26374
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <cassert>
#include <iostream>
#include <set>
#include <vector>

using Block = std::array<int, 5>;
using Triple = std::array<int, 3>;

int main() {
    std::array<Block, 60> core{};
    std::array<Block, 64> candidate{};
    std::array<Triple, 5> source{}, target{};
    int core_count, candidate_count;
    assert(std::cin >> core_count >> candidate_count);
    assert(core_count == 60 && candidate_count == 64);
    std::array<bool, 65536> present{};
    auto read_blocks = [&](auto &blocks) {
        std::set<Block> seen;
        for (auto &block : blocks) {
            for (auto &p : block) {
                assert(std::cin >> p);
                assert(1 <= p && p <= 16);
                --p;
            }
            assert(std::is_sorted(block.begin(), block.end()));
            assert(std::adjacent_find(block.begin(), block.end()) == block.end());
            assert(seen.insert(block).second);
        }
    };
    read_blocks(core);
    read_blocks(candidate);
    for (const auto &block : candidate) {
        int mask = 0;
        for (int p : block) mask |= 1 << p;
        present[mask] = true;
    }
    auto read_partition = [&](auto &triples) {
        int used = 0;
        for (auto &triple : triples) {
            for (auto &p : triple) {
                assert(std::cin >> p);
                assert(1 <= p && p <= 16 && !(used & (1 << (p - 1))));
                used |= 1 << (p - 1);
                --p;
            }
            assert(std::is_sorted(triple.begin(), triple.end()));
        }
        for (int p = 0; p < 16; ++p) if (!(used & (1 << p))) return p;
        assert(false);
        return -1;
    };
    int source_hub = read_partition(source), target_hub = read_partition(target);
    std::string extra;
    assert(!(std::cin >> extra));
    std::array<std::vector<Triple>, 5> orientations;
    for (int g = 0; g < 5; ++g) {
        auto triple = target[g];
        do { orientations[g].push_back(triple); }
        while (std::next_permutation(triple.begin(), triple.end()));
        assert(orientations[g].size() == 6);
    }
    std::array<int, 5> groups{0, 1, 2, 3, 4};
    std::array<int, 16> mapping{}, best{};
    std::array<long long, 61> histogram{};
    int best_overlap = -1;
    long long checked = 0, ties = 0;
    do {
        for (int code = 0; code < 7776; ++code) {
            int digits = code;
            mapping[source_hub] = target_hub;
            for (int g = 0; g < 5; ++g) {
                const auto &image = orientations[groups[g]][digits % 6];
                digits /= 6;
                for (int k = 0; k < 3; ++k) mapping[source[g][k]] = image[k];
            }
            int overlap = 0;
            for (const auto &block : core) {
                const int mask = (1 << mapping[block[0]]) | (1 << mapping[block[1]]) |
                                 (1 << mapping[block[2]]) | (1 << mapping[block[3]]) |
                                 (1 << mapping[block[4]]);
                overlap += present[mask];
            }
            ++checked;
            ++histogram[overlap];
            if (overlap > best_overlap) {
                best_overlap = overlap;
                best = mapping;
                ties = 1;
            } else if (overlap == best_overlap) {
                ++ties;
                if (best < mapping) best = mapping;
            }
        }
    } while (std::next_permutation(groups.begin(), groups.end()));
    assert(checked == 933120);
    std::cout << "{\"label_maps_checked\":" << checked
              << ",\"best_overlap\":" << best_overlap
              << ",\"best_overlap_map_count\":" << ties << ",\"map_images\":[";
    for (int p = 0; p < 16; ++p) {
        if (p) std::cout << ',';
        std::cout << best[p] + 1;
    }
    std::cout << "],\"overlap_histogram\":[";
    for (int i = 0; i <= 60; ++i) {
        if (i) std::cout << ',';
        std::cout << histogram[i];
    }
    std::cout << "]}\n";
}
