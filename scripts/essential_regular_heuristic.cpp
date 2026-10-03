// Document:    Private-Triple-Guided Regular Cover Heuristic
// Version:     v1.2.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      d58e6194964213f7867b03a0e5f42a068d5c9a8d6a87c768800a7c6257ec044a
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

// Heuristic only. Preserve 64 distinct blocks and degree20 at each point.
// An unsupported block-point incidence has no private triple containing it.
// Trade one/two exclusive points between blocks or cycle three to eight points.
// Objective weights cycle between holes, unsupported incidences and pair
// deficits. A hard ceiling of ten holes applies only to this local campaign.
// Heavy triple overlap is a soft preference, not an asserted safe reduction.

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

struct Block { unsigned mask; std::array<int, 10> triples, pairs; };
struct Score { int holes, unsupported, pairs, heavy; };
std::vector<Block> blocks;
std::vector<unsigned> triple_masks;
std::array<int, 65536> rank_by_mask;
int triple_rank[16][16][16], pair_rank[16][16];

void universe() {
    rank_by_mask.fill(-1);
    int tid = 0, pid = 0;
    for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b) {
        pair_rank[a][b] = pid++;
        for (int c = b + 1; c < 16; ++c) {
            triple_rank[a][b][c] = tid++;
            triple_masks.push_back((1u << a) | (1u << b) | (1u << c));
        }
    }
    for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
    for (int c = b + 1; c < 16; ++c) for (int d = c + 1; d < 16; ++d)
    for (int e = d + 1; e < 16; ++e) {
        std::array<int, 5> v{a, b, c, d, e};
        Block block{};
        for (int x : v) block.mask |= 1u << x;
        int t = 0, p = 0;
        for (int i = 0; i < 5; ++i) for (int j = i + 1; j < 5; ++j) {
            block.pairs[p++] = pair_rank[v[i]][v[j]];
            for (int k = j + 1; k < 5; ++k)
                block.triples[t++] = triple_rank[v[i]][v[j]][v[k]];
        }
        rank_by_mask[block.mask] = static_cast<int>(blocks.size());
        blocks.push_back(block);
    }
    if (blocks.size() != 4368 || tid != 560 || pid != 120)
        throw std::runtime_error("bad universe");
}

struct State {
    std::array<int, 64> ids{};
    std::array<int, 560> coverage{};
    std::array<int, 120> pair_counts{};
    std::array<bool, 4368> selected{};
    explicit State(const std::array<int, 64>& initial) : ids(initial) {
        for (int id : ids) {
            if (id < 0 || id >= 4368 || selected[id])
                throw std::runtime_error("bad or duplicate block");
            selected[id] = true;
            for (int t : blocks[id].triples) ++coverage[t];
            for (int p : blocks[id].pairs) ++pair_counts[p];
        }
    }
    void remove(int id) {
        selected[id] = false;
        for (int t : blocks[id].triples) --coverage[t];
        for (int p : blocks[id].pairs) --pair_counts[p];
    }
    void insert(int id) {
        selected[id] = true;
        for (int t : blocks[id].triples) ++coverage[t];
        for (int p : blocks[id].pairs) ++pair_counts[p];
    }
    unsigned unsupported_mask(int slot) const {
        int id = ids[slot];
        unsigned supported = 0;
        for (int t : blocks[id].triples) if (coverage[t] == 1) supported |= triple_masks[t];
        return blocks[id].mask & ~supported;
    }
    Score score() const {
        Score score{0, 0, 0, 0};
        int six = 0, seven = 0;
        for (int n : coverage) {
            score.holes += n == 0; six += n == 6; seven += n == 7;
            score.heavy += 8 * std::max(0, n - 7);
        }
        score.heavy += std::max(0, 3 * six + 4 * seven - 16);
        for (int n : pair_counts) score.pairs += std::max(0, 5 - n);
        for (int slot = 0; slot < 64; ++slot)
            score.unsupported += __builtin_popcount(unsupported_mask(slot));
        return score;
    }
    void audit() const {
        State rebuilt(ids);
        if (rebuilt.coverage != coverage || rebuilt.pair_counts != pair_counts ||
            rebuilt.selected != selected) throw std::runtime_error("incremental state mismatch");
        std::array<int, 16> degree{};
        for (int id : ids) for (int x = 0; x < 16; ++x)
            if (blocks[id].mask & (1u << x)) ++degree[x];
        if (std::any_of(degree.begin(), degree.end(), [](int n) { return n != 20; }))
            throw std::runtime_error("degree20 invariant violated");
    }
};

int main(int argc, char** argv) {
    if (argc != 5) {
        std::cerr << "usage: essential_regular_heuristic SEED_FILE RNG_SEED SECONDS PREFIX\n";
        return 2;
    }
    universe();
    std::ifstream input(argv[1]);
    if (!input) throw std::runtime_error("cannot open seed");
    std::vector<int> parsed;
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream stream(line);
        int x, size = 0; unsigned mask = 0;
        while (stream >> x) {
            if (x < 1 || x > 16 || (mask & (1u << (x - 1))))
                throw std::runtime_error("invalid point label");
            mask |= 1u << (x - 1); ++size;
        }
        if (!stream.eof()) throw std::runtime_error("damaged label token");
        if (size != 5 || rank_by_mask[mask] < 0) throw std::runtime_error("invalid block size");
        parsed.push_back(rank_by_mask[mask]);
    }
    if (parsed.size() != 64) throw std::runtime_error("seed needs64 blocks");
    std::array<int, 64> initial;
    std::copy(parsed.begin(), parsed.end(), initial.begin());
    State state(initial); state.audit();
    Score current = state.score();
    if (current.holes > 10) throw std::runtime_error("seed exceeds10 holes");
    const std::uint64_t seed = std::stoull(argv[2]);
    std::mt19937_64 random(seed);
    const double budget = std::stod(argv[3]);
    if (!(budget > 0) || !std::isfinite(budget)) throw std::runtime_error("bad budget");
    const std::string prefix = argv[4];
    auto start = std::chrono::steady_clock::now();
    auto elapsed = [&]() {
        return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    };
    auto choose = [&](unsigned mask) {
        if (!mask) return 0u;
        int n = static_cast<int>(random() % __builtin_popcount(mask));
        while (n--) mask &= mask - 1;
        return mask & (~mask + 1);
    };
    auto dominates = [](Score a, Score b) {
        return a.holes <= b.holes && a.unsupported <= b.unsupported && a.pairs <= b.pairs;
    };
    std::vector<std::pair<Score, std::array<int, 64>>> frontier;
    std::vector<std::array<int, 64>> reservoir;
    std::array<int, 11> best_heavy;
    best_heavy.fill(10000);
    std::uint64_t proposals = 0, applied = 0, accepted = 0, restarts = 0;
    std::array<std::uint64_t, 9> applied_by_size{}, accepted_by_size{};
    std::array<bool, 9> cycle_control{}, rollback_control{};
    int reservoir_insertions = 0, reservoir_restarts = 0, long_cycle_rollback_audits = 0;
    int snapshots = 0;
    std::set<std::vector<int>> diversity_keys;
    std::array<int, 11> diversity_counts{};
    auto save_state = [&](const std::string& path) {
        auto ordered = state.ids;
        std::sort(ordered.begin(), ordered.end());
        std::ofstream out(path);
        if (!out) throw std::runtime_error("cannot save snapshot");
        for (int id : ordered) {
            bool first = true;
            for (int x = 0; x < 16; ++x) if (blocks[id].mask & (1u << x)) {
                out << (first ? "" : " ") << x + 1; first = false;
            }
            out << '\n';
        }
    };
    auto record = [&](Score score) {
        if (score.unsupported == 0 && score.pairs == 0 && score.holes <= 10) {
            auto ordered = state.ids;
            std::sort(ordered.begin(), ordered.end());
            auto distance = [](const auto& a, const auto& b) {
                int common = 0, i = 0, j = 0;
                while (i < 64 && j < 64) {
                    if (a[i] == b[j]) { ++common; ++i; ++j; }
                    else if (a[i] < b[j]) ++i;
                    else ++j;
                }
                return 64 - common;
            };
            int nearest = 64;
            for (const auto& entry : reservoir) nearest = std::min(nearest, distance(ordered, entry));
            if (nearest >= 4) {
                if (reservoir.size() < 64) {
                    reservoir.push_back(ordered); ++reservoir_insertions;
                } else {
                    int closest = 65, replace = -1;
                    for (int i = 0; i < 64; ++i) for (int j = i + 1; j < 64; ++j) {
                        int gap = distance(reservoir[i], reservoir[j]);
                        if (gap < closest) { closest = gap; replace = j; }
                    }
                    if (nearest > closest) { reservoir[replace] = ordered; ++reservoir_insertions; }
                }
            }
            if (score.heavy < best_heavy[score.holes]) {
                best_heavy[score.holes] = score.heavy;
                state.audit();
                std::string path = prefix + "-heavy-e" + std::to_string(score.heavy) +
                    "-h" + std::to_string(score.holes) + "-u0-p0.txt";
                save_state(path);
                std::cout << "{\"event\":\"heavy_improvement\",\"holes\":" << score.holes
                          << ",\"heavy_excess\":" << score.heavy << ",\"proposals\":" << proposals
                          << ",\"seconds\":" << elapsed() << ",\"path\":\"" << path
                          << "\"}\n" << std::flush;
            }
        }
        if (score.unsupported == 0 && score.pairs == 0 && score.holes <= 8 &&
            diversity_counts[score.holes] < 16) {
            // Each component is invariant under all point and block relabelings.
            // Different keys therefore guarantee nonisomorphic saved near-covers.
            std::array<int, 65> triples_hist{}, pairs_hist{};
            std::array<int, 11> private_hist{};
            std::array<int, 16> missing_degree{};
            for (int t = 0; t < 560; ++t) {
                ++triples_hist[state.coverage[t]];
                if (!state.coverage[t]) for (int x = 0; x < 16; ++x)
                    if (triple_masks[t] & (1u << x)) ++missing_degree[x];
            }
            for (int n : state.pair_counts) ++pairs_hist[n];
            for (int id : state.ids) {
                int private_count = 0;
                for (int t : blocks[id].triples) private_count += state.coverage[t] == 1;
                ++private_hist[private_count];
            }
            std::sort(missing_degree.begin(), missing_degree.end());
            std::vector<int> key;
            key.insert(key.end(), triples_hist.begin(), triples_hist.end());
            key.insert(key.end(), pairs_hist.begin(), pairs_hist.end());
            key.insert(key.end(), private_hist.begin(), private_hist.end());
            key.insert(key.end(), missing_degree.begin(), missing_degree.end());
            if (diversity_keys.insert(key).second) {
                state.audit();
                int variant = diversity_counts[score.holes]++;
                std::string path = prefix + "-variant-" + std::to_string(variant) +
                    "-h" + std::to_string(score.holes) + "-u0-p0.txt";
                save_state(path);
                std::cout << "{\"event\":\"essential_variant\",\"holes\":" << score.holes
                          << ",\"variant\":" << variant << ",\"proposals\":" << proposals
                          << ",\"seconds\":" << elapsed() << ",\"path\":\"" << path
                          << "\"}\n" << std::flush;
            }
        }
        for (const auto& entry : frontier) if (dominates(entry.first, score)) return;
        state.audit();
        frontier.erase(std::remove_if(frontier.begin(), frontier.end(), [&](const auto& entry) {
            return dominates(score, entry.first);
        }), frontier.end());
        frontier.emplace_back(score, state.ids);
        std::string path = prefix + "-h" + std::to_string(score.holes) + "-u" +
                           std::to_string(score.unsupported) + "-p" +
                           std::to_string(score.pairs) + ".txt";
        save_state(path);
        ++snapshots;
        std::cout << "{\"event\":\"frontier\",\"holes\":" << score.holes
                  << ",\"unsupported\":" << score.unsupported << ",\"pair_deficit\":"
                  << score.pairs << ",\"proposals\":" << proposals << ",\"seconds\":"
                  << elapsed() << ",\"path\":\"" << path << "\"}\n" << std::flush;
    };
    record(current);
    while (elapsed() < budget && current.holes > 0) {
        ++proposals;
        if (proposals % 2'000'000 == 0) {
            if (!reservoir.empty() && random() % 4 != 0) {
                state = State(reservoir[random() % reservoir.size()]); ++reservoir_restarts;
            } else state = State(frontier[random() % frontier.size()].second);
            current = state.score(); ++restarts;
        }
        int slots[8] = {static_cast<int>(random() % 64), -1, -1};
        int mode = static_cast<int>(random() % 100), changed = 2;
        unsigned masks[8]{};
        if (mode >= 85 && mode < 90) {
            changed = 4 + static_cast<int>(random() % 5);
            std::array<unsigned, 8> original{}, sent{};
            for (int k = 0; k < changed; ++k) {
                bool duplicate;
                do {
                    slots[k] = static_cast<int>(random() % 64); duplicate = false;
                    for (int j = 0; j < k; ++j) duplicate |= slots[k] == slots[j];
                } while (duplicate);
                original[k] = blocks[state.ids[slots[k]]].mask;
            }
            bool possible = true;
            for (int k = 0; k < changed; ++k) {
                sent[k] = choose(original[k] & ~original[(k + changed - 1) % changed]);
                possible &= sent[k] != 0;
            }
            if (!possible) continue;
            for (int k = 0; k < changed; ++k)
                masks[k] = original[k] ^ sent[k] ^ sent[(k + 1) % changed];
        } else {
        unsigned outgoing = 0, incoming = 0;
        if (mode < 40 && current.unsupported > 0) {
            std::vector<int> unsupported_slots;
            for (int i = 0; i < 64; ++i) if (state.unsupported_mask(i)) unsupported_slots.push_back(i);
            slots[0] = unsupported_slots[random() % unsupported_slots.size()];
            outgoing = choose(state.unsupported_mask(slots[0]));
        } else if (mode < 80) {
            std::vector<int> holes;
            for (int t = 0; t < 560; ++t) if (!state.coverage[t]) holes.push_back(t);
            unsigned hole = triple_masks[holes[random() % holes.size()]];
            std::vector<int> carriers;
            for (int i = 0; i < 64; ++i)
                if (__builtin_popcount(blocks[state.ids[i]].mask & hole) == 2) carriers.push_back(i);
            if (carriers.empty()) continue;
            slots[0] = carriers[random() % carriers.size()];
            unsigned mask = blocks[state.ids[slots[0]]].mask;
            incoming = hole & ~mask; outgoing = choose(mask & ~hole);
        }
        slots[1] = static_cast<int>(random() % 63);
        if (slots[1] >= slots[0]) ++slots[1];
        unsigned a = blocks[state.ids[slots[0]]].mask;
        unsigned b = blocks[state.ids[slots[1]]].mask;
        if (outgoing && ((b & outgoing) || (incoming && !(b & incoming)))) continue;
        if (!outgoing) outgoing = choose(a & ~b);
        if (!incoming) incoming = choose(b & ~a);
        if (!outgoing || !incoming) continue;
        masks[0] = a ^ outgoing ^ incoming; masks[1] = b ^ outgoing ^ incoming;
        if (mode >= 95) {
            unsigned more_out = choose((a & ~b) & ~outgoing);
            unsigned more_in = choose((b & ~a) & ~incoming);
            if (!more_out || !more_in) continue;
            masks[0] ^= more_out ^ more_in; masks[1] ^= more_out ^ more_in;
        } else if (mode >= 90) {
            do { slots[2] = static_cast<int>(random() % 64); }
            while (slots[2] == slots[0] || slots[2] == slots[1]);
            unsigned c = blocks[state.ids[slots[2]]].mask;
            unsigned third = choose(c & ~b);
            if (!third || (c & outgoing)) continue;
            // a sends outgoing to c, b sends incoming to a, c sends third to b.
            masks[1] = b ^ incoming ^ third; masks[2] = c ^ third ^ outgoing; changed = 3;
        }
        }
        int old_ids[8], new_ids[8]; bool valid = true;
        for (int k = 0; k < changed; ++k) {
            old_ids[k] = state.ids[slots[k]]; new_ids[k] = rank_by_mask[masks[k]];
            if (new_ids[k] < 0 || state.selected[new_ids[k]]) valid = false;
            for (int j = 0; j < k; ++j) if (new_ids[j] == new_ids[k]) valid = false;
        }
        if (!valid) continue;
        bool control = changed >= 4 && !cycle_control[changed];
        std::string before_path;
        if (control) {
            state.audit();
            before_path = prefix + "-cycle" + std::to_string(changed) + "-before-h" +
                std::to_string(current.holes) + "-u" + std::to_string(current.unsupported) +
                "-p" + std::to_string(current.pairs) + ".txt";
            save_state(before_path);
        }
        for (int k = 0; k < changed; ++k) state.remove(old_ids[k]);
        for (int k = 0; k < changed; ++k) {
            state.ids[slots[k]] = new_ids[k]; state.insert(new_ids[k]);
        }
        ++applied; ++applied_by_size[changed];
        Score next = state.score();
        if (control) {
            state.audit(); cycle_control[changed] = true;
            std::string path = prefix + "-cycle" + std::to_string(changed) + "-after-h" +
                std::to_string(next.holes) + "-u" + std::to_string(next.unsupported) +
                "-p" + std::to_string(next.pairs) + ".txt";
            save_state(path);
            std::cout << "{\"event\":\"move_control\",\"changed\":" << changed
                      << ",\"holes\":" << next.holes << ",\"unsupported\":" << next.unsupported
                      << ",\"pair_deficit\":" << next.pairs << ",\"path\":\"" << path
                      << "\",\"before_path\":\"" << before_path << "\"}\n" << std::flush;
        }
        static const int hole_weights[6] = {4, 3, 5, 4, 6, 3};
        static const int essential_weights[6] = {2, 5, 4, 8, 2, 10};
        static const int heavy_weights[6] = {0, 2, 4, 6, 10, 16};
        int phase = static_cast<int>((proposals / 1'000'000) % 6);
        auto energy = [&](Score score) {
            return hole_weights[phase] * score.holes + essential_weights[phase] * score.unsupported
                   + 6 * score.pairs + heavy_weights[phase] * score.heavy;
        };
        double cooling = static_cast<double>(proposals % 1'000'000) / 1'000'000;
        double temperature = 0.1 + 2.0 * std::pow(1.0 - cooling, 3);
        int delta = energy(next) - energy(current);
        bool accept = next.holes == 0 || (next.holes <= 10 && (delta <= 0 ||
            std::generate_canonical<double, 53>(random) < std::exp(-delta / temperature)));
        if (accept) { current = next; ++accepted; ++accepted_by_size[changed]; record(current); }
        else {
            for (int k = 0; k < changed; ++k) state.remove(new_ids[k]);
            for (int k = 0; k < changed; ++k) {
                state.ids[slots[k]] = old_ids[k]; state.insert(old_ids[k]);
            }
            if (changed >= 4 && !rollback_control[changed]) {
                state.audit(); rollback_control[changed] = true; ++long_cycle_rollback_audits;
            }
        }
        if (proposals % 100'000 == 0) state.audit();
    }
    state.audit();
    std::string final_path = prefix + "-final-h" + std::to_string(current.holes) +
        "-u" + std::to_string(current.unsupported) + "-p" + std::to_string(current.pairs) + ".txt";
    save_state(final_path);
    std::cout << "{\"event\":\"finish\",\"seed\":" << seed << ",\"budget_seconds\":"
              << budget << ",\"seconds\":" << elapsed() << ",\"proposals\":" << proposals
              << ",\"applied\":" << applied << ",\"accepted\":" << accepted
              << ",\"restarts\":" << restarts << ",\"snapshots\":" << snapshots
              << ",\"reservoir_size\":" << reservoir.size()
              << ",\"reservoir_insertions\":" << reservoir_insertions
              << ",\"reservoir_restarts\":" << reservoir_restarts
              << ",\"long_cycle_rollback_audits\":" << long_cycle_rollback_audits
              << ",\"final_path\":\"" << final_path << "\",\"applied_by_size\":[";
    for (int k = 0; k < 9; ++k) { if (k) std::cout << ','; std::cout << applied_by_size[k]; }
    std::cout << "],\"accepted_by_size\":[";
    for (int k = 0; k < 9; ++k) { if (k) std::cout << ','; std::cout << accepted_by_size[k]; }
    std::cout << ']'
              << ",\"essential_variants\":" << diversity_keys.size()
              << ",\"frontier\":[";
    for (std::size_t i = 0; i < frontier.size(); ++i) {
        const Score s = frontier[i].first;
        if (i) std::cout << ',';
        std::cout << '[' << s.holes << ',' << s.unsupported << ',' << s.pairs << ']';
    }
    std::cout << "],\"status\":\"" << (current.holes ? "INCONCLUSIVE" : "COVER_FOUND")
              << "\"}\n" << std::flush;
}
