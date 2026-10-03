// Document:    Independent Direct Local Family Enumeration
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      5661309b31ddd1dfd4a2cc05b3710edd709424b3907d9f2348c18cf3dfbc9bba
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

// Enumerates nine blocks after fixing the four blocks through a hole-free point.
// No determinant filter, no positive-matching enumeration, and no graph library.
// Only the 26 hole-pattern representatives are reduced by group permutations.
// Output contains every labelled completion, allowing independent class checks.

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>
#include <vector>

using Pattern = std::array<int, 6>;
using Block = std::array<int, 4>;
using Solution = std::array<int, 9>;

struct TimeLimit {};

struct Search {
    std::array<std::array<int, 12>, 12> pair_id{};
    std::vector<std::array<int, 2>> pairs;
    std::vector<Block> blocks;
    std::vector<std::array<int, 6>> block_pairs;
    std::array<std::vector<int>, 66> containing;
    std::array<int, 66> counts{};
    std::array<bool, 66> holes{};
    std::array<int, 12> degrees{};
    std::array<int, 12> excess{};
    std::array<int, 12> hole_degree{};
    std::array<bool, 495> selected{};
    Solution chosen{};
    std::set<Solution> solutions;
    std::uint64_t nodes = 0;
    std::chrono::steady_clock::time_point deadline;

    Search(const Pattern& pattern, std::chrono::steady_clock::time_point end)
        : deadline(end) {
        for (int a = 0; a < 12; ++a) {
            for (int b = a + 1; b < 12; ++b) {
                int index = static_cast<int>(pairs.size());
                pair_id[a][b] = pair_id[b][a] = index;
                pairs.push_back({a, b});
                counts[index] = (a / 3 == b / 3);
            }
        }
        std::array<int, 4> used{};
        int index = 0;
        for (int a = 0; a < 4; ++a) {
            for (int b = a + 1; b < 4; ++b, ++index) {
                for (int k = 0; k < pattern[index]; ++k) {
                    int p = 3 * a + used[a]++;
                    int q = 3 * b + used[b]++;
                    holes[pair_id[p][q]] = true;
                    hole_degree[p] = hole_degree[q] = 1;
                }
            }
        }
        for (int a = 0; a < 12; ++a)
            for (int b = a + 1; b < 12; ++b)
                for (int c = b + 1; c < 12; ++c)
                    for (int d = c + 1; d < 12; ++d) {
                        Block block{a, b, c, d};
                        std::array<int, 6> edge_ids{};
                        bool permitted = true;
                        int i = 0;
                        for (int j = 0; j < 4; ++j)
                            for (int k = j + 1; k < 4; ++k) {
                                int edge = pair_id[block[j]][block[k]];
                                edge_ids[i++] = edge;
                                if (holes[edge]) permitted = false;
                            }
                        if (!permitted) continue;
                        int block_id = static_cast<int>(blocks.size());
                        blocks.push_back(block);
                        block_pairs.push_back(edge_ids);
                        for (int edge : edge_ids) containing[edge].push_back(block_id);
                    }
    }

    bool valid(int block_id) const {
        if (selected[block_id]) return false;
        for (int point : blocks[block_id]) if (degrees[point] == 3) return false;
        std::array<int, 12> extra{};
        for (int edge : block_pairs[block_id]) {
            if (counts[edge] == 2) return false;
            if (counts[edge] == 1) {
                auto [a, b] = pairs[edge];
                if (++extra[a] + excess[a] > hole_degree[a]) return false;
                if (++extra[b] + excess[b] > hole_degree[b]) return false;
            }
        }
        return true;
    }

    void walk(int depth) {
        ++nodes;
        if ((nodes & 4095) == 0 && std::chrono::steady_clock::now() >= deadline)
            throw TimeLimit{};
        if (depth == 9) {
            for (int edge = 0; edge < 66; ++edge)
                if (!holes[edge] && counts[edge] == 0) return;
            for (int point = 0; point < 12; ++point)
                if (degrees[point] != 3 || excess[point] != hole_degree[point])
                    throw std::runtime_error("invalid completed family");
            Solution solution = chosen;
            std::sort(solution.begin(), solution.end());
            solutions.insert(solution);
            return;
        }
        std::vector<bool> viable(blocks.size());
        for (int i = 0; i < static_cast<int>(blocks.size()); ++i) viable[i] = valid(i);
        int best_edge = -1;
        std::size_t best_size = std::numeric_limits<std::size_t>::max();
        std::vector<int> best_options;
        for (int edge = 0; edge < 66; ++edge) {
            if (holes[edge] || counts[edge]) continue;
            std::vector<int> options;
            for (int block_id : containing[edge])
                if (viable[block_id]) options.push_back(block_id);
            if (options.empty()) return;
            if (options.size() < best_size) {
                best_size = options.size();
                best_edge = edge;
                best_options = std::move(options);
                if (best_size == 1) break;
            }
        }
        if (best_edge < 0) return;
        for (int block_id : best_options) {
            chosen[depth] = block_id;
            selected[block_id] = true;
            for (int point : blocks[block_id]) ++degrees[point];
            for (int edge : block_pairs[block_id]) {
                if (++counts[edge] == 2) {
                    auto [a, b] = pairs[edge];
                    ++excess[a]; ++excess[b];
                }
            }
            walk(depth + 1);
            for (int edge : block_pairs[block_id]) {
                if (counts[edge]-- == 2) {
                    auto [a, b] = pairs[edge];
                    --excess[a]; --excess[b];
                }
            }
            for (int point : blocks[block_id]) --degrees[point];
            selected[block_id] = false;
        }
    }
};

std::set<Pattern> patterns() {
    std::array<std::array<int, 4>, 4> edge_id{};
    std::array<std::array<int, 2>, 6> edge{};
    int index = 0;
    for (int a = 0; a < 4; ++a)
        for (int b = a + 1; b < 4; ++b) {
            edge[index] = {a, b};
            edge_id[a][b] = edge_id[b][a] = index++;
        }
    std::set<Pattern> result;
    for (int code = 0; code < 4096; ++code) {
        Pattern value{};
        std::array<int, 4> degree{};
        int remainder = code;
        for (int i = 0; i < 6; ++i) {
            value[i] = remainder % 4; remainder /= 4;
            degree[edge[i][0]] += value[i];
            degree[edge[i][1]] += value[i];
        }
        if (*std::max_element(degree.begin(), degree.end()) > 3) continue;
        Pattern smallest = value;
        std::array<int, 4> permutation{0, 1, 2, 3};
        do {
            Pattern image{};
            for (int i = 0; i < 6; ++i)
                image[edge_id[permutation[edge[i][0]]][permutation[edge[i][1]]]] = value[i];
            smallest = std::min(smallest, image);
        } while (std::next_permutation(permutation.begin(), permutation.end()));
        result.insert(smallest);
    }
    return result;
}

int main(int argc, char** argv) {
    double seconds = argc > 1 ? std::atof(argv[1]) : 60.0;
    auto started = std::chrono::steady_clock::now();
    auto deadline = started + std::chrono::milliseconds(static_cast<int>(1000 * seconds));
    std::uint64_t total_nodes = 0;
    bool complete = true, first = true;
    std::cout << "{\"schema\":1,\"patterns\":[";
    for (const auto& pattern : patterns()) {
        Search search(pattern, deadline);
        bool pattern_complete = true;
        try { search.walk(0); }
        catch (const TimeLimit&) { complete = pattern_complete = false; }
        total_nodes += search.nodes;
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"pattern\":[";
        for (int i = 0; i < 6; ++i) std::cout << (i ? "," : "") << pattern[i];
        std::cout << "],\"complete\":" << (pattern_complete ? "true" : "false")
                  << ",\"nodes\":" << search.nodes << ",\"families\":[";
        bool first_family = true;
        for (const auto& solution : search.solutions) {
            if (!first_family) std::cout << ',';
            first_family = false;
            std::cout << '[';
            for (int g = 0; g < 4; ++g)
                std::cout << (g ? "," : "") << '[' << 3*g+1 << ',' << 3*g+2
                          << ',' << 3*g+3 << ",13]";
            for (int block_id : solution) {
                std::cout << ",[";
                for (int i = 0; i < 4; ++i)
                    std::cout << (i ? "," : "") << search.blocks[block_id][i]+1;
                std::cout << ']';
            }
            std::cout << ']';
        }
        std::cout << "]}" << std::flush;
        if (!complete) break;
    }
    double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    std::cout << "],\"complete\":" << (complete ? "true" : "false")
              << ",\"nodes\":" << total_nodes << ",\"seconds\":" << elapsed << "}\n";
}
