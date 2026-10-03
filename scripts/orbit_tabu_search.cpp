// Document:    Small Semiregular Orbit Tabu Search for 64-Block Covers
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      128d644d545a8849ea564ae622a9501e488a8e11339bf94d26207c6bc42dac60
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

// Heuristic only: a timeout or failure to find a cover is inconclusive.
// C4/V4 acts on four disjoint 4-point classes; C8/V8 on two 8-point classes.
// Every nonidentity permutation has only even cycles, so odd-sized subsets
// have no stabilizer. All 3-subset and 5-subset orbits have full group size.
// The code explicitly audits these orbit sizes and independently recounts
// the coverage of every saved candidate over all 560 original triples.

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using Block = std::array<int, 5>;
using Triple = std::array<int, 3>;

struct Orbit {
    std::vector<int> blocks;
    std::vector<int> triples;
};

int main(int argc, char** argv) {
    if (argc != 5) {
        std::cerr << "usage: orbit_tabu_search C4|C8|V4|V8 seed seconds output-prefix\n";
        return 2;
    }
    const std::string family = argv[1];
    if (family != "C4" && family != "C8" && family != "V4" && family != "V8")
        throw std::runtime_error("unknown family");
    const int order = family[1] - '0';
    const bool cyclic = family[0] == 'C';
    const std::uint64_t seed = std::stoull(argv[2]);
    const double seconds = std::stod(argv[3]);
    const std::string prefix = argv[4];
    if (seconds <= 0) throw std::runtime_error("nonpositive budget");
    std::mt19937_64 random(seed);
    auto transform = [&](int point, int h) {
        int offset = point % order;
        return point - offset + (cyclic ? (offset + h) % order : (offset ^ h));
    };
    std::vector<Triple> triples;
    std::map<Triple, int> triple_rank;
    for (int a = 0; a < 16; ++a)
        for (int b = a + 1; b < 16; ++b)
            for (int c = b + 1; c < 16; ++c) {
                Triple t{a, b, c};
                triple_rank[t] = static_cast<int>(triples.size());
                triples.push_back(t);
            }
    std::vector<Block> blocks;
    std::map<Block, int> block_rank;
    for (int a = 0; a < 16; ++a)
        for (int b = a + 1; b < 16; ++b)
            for (int c = b + 1; c < 16; ++c)
                for (int d = c + 1; d < 16; ++d)
                    for (int e = d + 1; e < 16; ++e) {
                        Block block{a, b, c, d, e};
                        block_rank[block] = static_cast<int>(blocks.size());
                        blocks.push_back(block);
                    }
    if (triples.size() != 560 || blocks.size() != 4368)
        throw std::runtime_error("bad universe");
    std::map<int, int> triple_reps;
    std::vector<int> triple_orbit(560, -1);
    for (int tid = 0; tid < 560; ++tid) {
        std::set<int> images;
        for (int h = 0; h < order; ++h) {
            Triple t = triples[tid];
            for (int& x : t) x = transform(x, h);
            std::sort(t.begin(), t.end());
            images.insert(triple_rank.at(t));
        }
        if (images.size() != static_cast<std::size_t>(order))
            throw std::runtime_error("short triple orbit");
        int rep = *images.begin();
        if (!triple_reps.count(rep))
            triple_reps[rep] = static_cast<int>(triple_reps.size());
        triple_orbit[tid] = triple_reps.at(rep);
    }
    std::vector<Orbit> orbits;
    std::set<int> visited;
    for (int bid = 0; bid < 4368; ++bid) {
        if (visited.count(bid)) continue;
        std::set<int> images;
        for (int h = 0; h < order; ++h) {
            Block block = blocks[bid];
            for (int& x : block) x = transform(x, h);
            std::sort(block.begin(), block.end());
            images.insert(block_rank.at(block));
        }
        if (images.size() != static_cast<std::size_t>(order))
            throw std::runtime_error("short block orbit");
        visited.insert(images.begin(), images.end());
        std::set<int> support;
        for (int id : images) {
            const Block& b = blocks[id];
            for (int i = 0; i < 5; ++i)
                for (int j = i + 1; j < 5; ++j)
                    for (int k = j + 1; k < 5; ++k)
                        support.insert(triple_orbit[triple_rank.at({b[i], b[j], b[k]})]);
        }
        orbits.push_back({std::vector<int>(images.begin(), images.end()),
                          std::vector<int>(support.begin(), support.end())});
    }
    const int n = static_cast<int>(orbits.size());
    const int nt = static_cast<int>(triple_reps.size());
    const int selected_count = 64 / order;
    if (n * order != 4368 || nt * order != 560)
        throw std::runtime_error("orbit partition is incomplete");
    std::cout << "{\"event\":\"start\",\"family\":\"" << family
              << "\",\"seed\":" << seed << ",\"seconds_budget\":" << seconds
              << ",\"block_orbits\":" << n << ",\"triple_orbits\":" << nt
              << ",\"selected_orbits\":" << selected_count << "}\n" << std::flush;
    std::vector<int> counts(nt), weights(nt, 1), selected(selected_count), used(n), tabu(n);
    const auto start = std::chrono::steady_clock::now();
    auto elapsed = [&]() {
        return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    };
    int best_holes = 561;
    long long iterations = 0, moves = 0, restarts = 0;
    auto save = [&](int hole_orbits) {
        std::vector<int> full;
        for (int oid : selected)
            full.insert(full.end(), orbits[oid].blocks.begin(), orbits[oid].blocks.end());
        std::sort(full.begin(), full.end());
        if (full.size() != 64 || std::set<int>(full.begin(), full.end()).size() != 64)
            throw std::runtime_error("duplicate or malformed full candidate");
        std::set<Triple> covered;
        for (int bid : full) {
            const Block& b = blocks[bid];
            for (int i = 0; i < 5; ++i)
                for (int j = i + 1; j < 5; ++j)
                    for (int k = j + 1; k < 5; ++k)
                        covered.insert({b[i], b[j], b[k]});
        }
        int holes = 560 - static_cast<int>(covered.size());
        if (holes != hole_orbits * order) throw std::runtime_error("score mismatch");
        if (holes >= best_holes) return;
        best_holes = holes;
        const std::string path = prefix + "-deficit-" + std::to_string(holes) + ".txt";
        std::ofstream out(path);
        if (!out) throw std::runtime_error("cannot write witness");
        for (int bid : full) {
            const Block& b = blocks[bid];
            for (int i = 0; i < 5; ++i) out << (i ? " " : "") << b[i] + 1;
            out << '\n';
        }
        std::cout << "{\"event\":\"best\",\"family\":\"" << family
                  << "\",\"deficit\":" << holes << ",\"iterations\":" << iterations
                  << ",\"seconds\":" << elapsed() << ",\"path\":\"" << path
                  << "\"}\n" << std::flush;
    };
    while (elapsed() < seconds && best_holes > 0) {
        ++restarts;
        std::fill(counts.begin(), counts.end(), 0);
        std::fill(weights.begin(), weights.end(), 1);
        std::fill(used.begin(), used.end(), 0);
        std::fill(tabu.begin(), tabu.end(), 0);
        // Randomized greedy seeds: choose randomly among the best five gains.
        for (int slot = 0; slot < selected_count; ++slot) {
            std::vector<std::pair<int, int>> gains;
            for (int oid = 0; oid < n; ++oid) {
                if (used[oid]) continue;
                int gain = 0;
                for (int t : orbits[oid].triples) gain += counts[t] == 0;
                gains.emplace_back(gain, oid);
            }
            std::shuffle(gains.begin(), gains.end(), random);
            std::stable_sort(gains.begin(), gains.end(), [](auto a, auto b) {
                return a.first > b.first;
            });
            int oid = gains[random() % std::min<std::size_t>(5, gains.size())].second;
            selected[slot] = oid;
            used[oid] = 1;
            for (int t : orbits[oid].triples) ++counts[t];
        }
        auto holes = [&]() { return static_cast<int>(std::count(counts.begin(), counts.end(), 0)); };
        save(holes());
        for (int local = 1; local <= 3000 && best_holes > 0; ++local) {
            if ((local & 15) == 0 && elapsed() >= seconds) break;
            ++iterations;
            int best_score = std::numeric_limits<int>::max();
            int best_slot = -1, best_add = -1, ties = 0;
            int current_score = 0;
            for (int t = 0; t < nt; ++t) if (!counts[t]) current_score += weights[t];
            for (int slot = 0; slot < selected_count; ++slot) {
                int remove = selected[slot], remove_score = current_score;
                for (int t : orbits[remove].triples) {
                    --counts[t];
                    if (!counts[t]) remove_score += weights[t];
                }
                int removed_holes = holes();
                for (int add = 0; add < n; ++add) {
                    if (used[add]) continue;
                    int score = remove_score, candidate_holes = removed_holes;
                    for (int t : orbits[add].triples)
                        if (!counts[t]) { score -= weights[t]; --candidate_holes; }
                    if (tabu[add] > local && candidate_holes * order >= best_holes) continue;
                    if (score < best_score) {
                        best_score = score; best_slot = slot; best_add = add; ties = 1;
                    } else if (score == best_score && random() % ++ties == 0) {
                        best_slot = slot; best_add = add;
                    }
                }
                for (int t : orbits[remove].triples) ++counts[t];
            }
            if (best_slot < 0) break;
            int remove = selected[best_slot];
            used[remove] = 0;
            tabu[remove] = local + 7 + static_cast<int>(random() % 15);
            for (int t : orbits[remove].triples) --counts[t];
            selected[best_slot] = best_add;
            used[best_add] = 1;
            for (int t : orbits[best_add].triples) ++counts[t];
            ++moves;
            if (holes() * order < best_holes) save(holes());
            if (local % 20 == 0)
                for (int t = 0; t < nt; ++t) if (!counts[t]) ++weights[t];
        }
    }
    std::cout << "{\"event\":\"finish\",\"family\":\"" << family
              << "\",\"seed\":" << seed << ",\"best_deficit\":" << best_holes
              << ",\"iterations\":" << iterations << ",\"moves\":" << moves
              << ",\"restarts\":" << restarts << ",\"seconds\":" << elapsed()
              << ",\"status\":\"" << (best_holes == 0 ? "COVER_FOUND" : "INCONCLUSIVE")
              << "\"}\n" << std::flush;
}
