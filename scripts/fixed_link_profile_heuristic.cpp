// Document:    Fixed-Link Degree-Profile-Preserving Covering Heuristic
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      a2369d59fb0ead8ab131b18eb9c0aec30901d54f93a516bb9cc11762a3620af0
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <csignal>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Mask = unsigned;
using Clock = std::chrono::steady_clock;
static std::array<std::array<int, 10>, 65536> block_triples{};
static std::array<int, 65536> triple_id{};
static std::array<Mask, 560> triple_masks{};
static std::mt19937_64 rng;
static volatile std::sig_atomic_t stop_requested = 0;

static void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}
static int random_int(int upper) {
    require(upper > 0, "empty random range");
    return std::uniform_int_distribution<int>(0, upper - 1)(rng);
}
static uint64_t unsigned_argument(const std::string& value) {
    require(!value.empty() && value.find_first_not_of("0123456789") == std::string::npos,
            "unsigned integer argument required");
    size_t consumed = 0;
    uint64_t result = std::stoull(value, &consumed);
    require(consumed == value.size(), "invalid integer argument");
    return result;
}
static void stop(int) { stop_requested = 1; }
static std::vector<int> points(Mask mask) {
    std::vector<int> result;
    for (int point = 0; point < 16; ++point) if (mask & (1u << point)) result.push_back(point);
    return result;
}
static Mask random_bit(Mask mask) {
    auto present = points(mask);
    return 1u << present[random_int(static_cast<int>(present.size()))];
}
static void initialize_tables() {
    triple_id.fill(-1);
    int index = 0;
    for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
        for (int c = b + 1; c < 16; ++c) {
            Mask mask = (1u << a) | (1u << b) | (1u << c);
            triple_id[mask] = index;
            triple_masks[index++] = mask;
        }
    require(index == 560, "wrong triple universe");
    for (Mask mask = 0; mask < 65536; ++mask) if (__builtin_popcount(mask) == 5) {
        auto labels = points(mask);
        int count = 0;
        for (int a = 0; a < 5; ++a) for (int b = a + 1; b < 5; ++b)
            for (int c = b + 1; c < 5; ++c)
                block_triples[mask][count++] = triple_id[(1u << labels[a]) |
                    (1u << labels[b]) | (1u << labels[c])];
        require(count == 10, "wrong block incidence count");
    }
}
static std::vector<Mask> read_blocks(const std::string& path) {
    std::ifstream input(path);
    require(static_cast<bool>(input), "cannot open seed");
    std::vector<Mask> blocks;
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream stream(line);
        stream >> std::ws;
        if (stream.eof()) continue;
        Mask mask = 0;
        for (int count = 0; count < 5; ++count) {
            int point;
            require(static_cast<bool>(stream >> point), "five integer labels required");
            require(point >= 1 && point <= 16, "label outside1..16");
            Mask bit = 1u << (point - 1);
            require(!(mask & bit), "repeated label");
            mask |= bit;
        }
        stream >> std::ws;
        require(stream.eof(), "extra seed token");
        blocks.push_back(mask);
    }
    require(blocks.size() == 64 && std::set<Mask>(blocks.begin(), blocks.end()).size() == 64,
            "seed must contain64 distinct blocks");
    return blocks;
}

struct Plan {
    int mode = 0;
    std::vector<int> slots;
    std::vector<Mask> before, after;
};

struct State {
    int anchor, high;
    std::vector<Mask> fixed;
    std::array<Mask, 45> free{};
    std::array<int, 560> counts{};
    std::array<unsigned char, 65536> selected{};
    std::vector<int> missing;
    std::array<int, 560> missing_position{};

    State(const std::vector<Mask>& all, int anchor_point, int high_point)
        : anchor(anchor_point), high(high_point) {
        int movable = 0;
        for (Mask block : all) {
            require(!selected[block], "duplicate state block");
            selected[block] = 1;
            if (block & (1u << anchor)) fixed.push_back(block);
            else {
                require(movable < 45, "too many mutable blocks");
                free[movable++] = block;
            }
            for (int triple : block_triples[block]) ++counts[triple];
        }
        require(fixed.size() == 19 && movable == 45, "fixed link must contain19 blocks");
        missing_position.fill(-1);
        for (int triple = 0; triple < 560; ++triple) if (counts[triple] == 0) {
            missing_position[triple] = static_cast<int>(missing.size());
            missing.push_back(triple);
        }
        audit();
    }
    std::vector<Mask> all() const {
        auto result = fixed;
        result.insert(result.end(), free.begin(), free.end());
        return result;
    }
    void audit() const {
        std::array<int, 16> degrees{};
        std::array<int, 560> rebuilt{};
        std::set<Mask> unique;
        for (Mask block : all()) {
            require(__builtin_popcount(block) == 5 && selected[block], "malformed selected block");
            require(unique.insert(block).second, "duplicate selected block");
            for (int point : points(block)) ++degrees[point];
            for (int triple : block_triples[block]) ++rebuilt[triple];
        }
        require(unique.size() == 64 && rebuilt == counts, "incremental triple count drift");
        require(std::count(selected.begin(), selected.end(), 1) == 64, "selected flags drift");
        for (int point = 0; point < 16; ++point)
            require(degrees[point] == (point == anchor ? 19 : point == high ? 21 : 20),
                    "degree profile drift");
        for (Mask block : free) require(!(block & (1u << anchor)), "anchor entered mutable block");
        for (Mask block : fixed) require(block & (1u << anchor), "invalid immutable link");
        int holes = 0;
        for (int triple = 0; triple < 560; ++triple) {
            if (triple_masks[triple] & (1u << anchor))
                require(counts[triple] > 0, "frozen link misses a triple");
            if (counts[triple] == 0) {
                ++holes;
                require(missing_position[triple] >= 0 &&
                        missing_position[triple] < static_cast<int>(missing.size()) &&
                        missing[missing_position[triple]] == triple, "missing index drift");
            } else require(missing_position[triple] == -1, "covered triple in missing index");
        }
        require(holes == static_cast<int>(missing.size()), "wrong deficit");
    }
    bool legal(const Plan& plan) const {
        if (plan.slots.size() < 2 || plan.slots.size() != plan.before.size() ||
            plan.before.size() != plan.after.size()) return false;
        std::set<int> slots(plan.slots.begin(), plan.slots.end());
        if (slots.size() != plan.slots.size()) return false;
        std::set<Mask> old(plan.before.begin(), plan.before.end());
        std::set<Mask> fresh(plan.after.begin(), plan.after.end());
        if (fresh.size() != plan.after.size() || fresh == old) return false;
        std::array<int, 16> change{};
        for (size_t index = 0; index < plan.slots.size(); ++index) {
            int slot = plan.slots[index];
            if (slot < 0 || slot >= 45 || free[slot] != plan.before[index]) return false;
            Mask block = plan.after[index];
            if (block >= 65536 || __builtin_popcount(block) != 5 || (block & (1u << anchor))) return false;
            if (selected[block] && !old.count(block)) return false;
            for (int point : points(plan.before[index])) --change[point];
            for (int point : points(block)) ++change[point];
        }
        return std::all_of(change.begin(), change.end(), [](int value) { return value == 0; });
    }
    std::array<int, 560> changes(const Plan& plan) const {
        std::array<int, 560> result{};
        for (Mask block : plan.before) for (int triple : block_triples[block]) --result[triple];
        for (Mask block : plan.after) for (int triple : block_triples[block]) ++result[triple];
        return result;
    }
    int delta(const Plan& plan) const {
        auto change = changes(plan);
        int result = 0;
        for (int triple = 0; triple < 560; ++triple)
            result += (counts[triple] + change[triple] == 0) - (counts[triple] == 0);
        return result;
    }
    void apply(const Plan& plan) {
        require(legal(plan), "illegal move reached mutation");
        auto change = changes(plan);
        for (Mask block : plan.before) selected[block] = 0;
        for (size_t index = 0; index < plan.slots.size(); ++index) {
            free[plan.slots[index]] = plan.after[index];
            selected[plan.after[index]] = 1;
        }
        for (int triple = 0; triple < 560; ++triple) if (change[triple]) {
            int previous = counts[triple];
            counts[triple] += change[triple];
            require(counts[triple] >= 0, "negative triple count");
            if (previous == 0 && counts[triple] != 0) {
                int position = missing_position[triple];
                int last = missing.back();
                missing[position] = last;
                missing_position[last] = position;
                missing.pop_back();
                missing_position[triple] = -1;
            } else if (previous != 0 && counts[triple] == 0) {
                missing_position[triple] = static_cast<int>(missing.size());
                missing.push_back(triple);
            }
        }
    }
};

static Plan propose(const State& state, int mode) {
    Plan plan;
    plan.mode = mode;
    if (mode == 0) {
        if (state.missing.empty()) return plan;
        Mask target = triple_masks[state.missing[random_int(static_cast<int>(state.missing.size()))]];
        std::vector<int> close;
        for (int slot = 0; slot < 45; ++slot)
            if (__builtin_popcount(state.free[slot] & target) == 2) close.push_back(slot);
        if (close.empty()) return plan;
        int first = close[random_int(static_cast<int>(close.size()))];
        Mask incoming = target & ~state.free[first];
        Mask outgoing = random_bit(state.free[first] & ~target);
        std::vector<int> donors;
        for (int slot = 0; slot < 45; ++slot)
            if ((state.free[slot] & incoming) && !(state.free[slot] & outgoing)) donors.push_back(slot);
        if (donors.empty()) return plan;
        int second = donors[random_int(static_cast<int>(donors.size()))];
        plan.slots = {first, second};
        plan.before = {state.free[first], state.free[second]};
        plan.after = {(state.free[first] ^ outgoing) | incoming,
                      (state.free[second] ^ incoming) | outgoing};
    } else if (mode == 1) {
        int first = random_int(45), second = random_int(44);
        if (second >= first) ++second;
        Mask common = state.free[first] & state.free[second];
        auto distinct = points(state.free[first] ^ state.free[second]);
        std::shuffle(distinct.begin(), distinct.end(), rng);
        Mask a = common, b = common;
        for (size_t index = 0; index < distinct.size(); ++index)
            (index < distinct.size() / 2 ? a : b) |= 1u << distinct[index];
        plan.slots = {first, second};
        plan.before = {state.free[first], state.free[second]};
        plan.after = {a, b};
    } else {
        int size = 3 + random_int(4);
        while (static_cast<int>(plan.slots.size()) < size) {
            int slot = random_int(45);
            if (std::find(plan.slots.begin(), plan.slots.end(), slot) == plan.slots.end())
                plan.slots.push_back(slot);
        }
        std::vector<Mask> outgoing;
        for (int slot : plan.slots) plan.before.push_back(state.free[slot]);
        for (int index = 0; index < size; ++index) {
            Mask choice = plan.before[index] & ~plan.before[(index + 1) % size];
            if (!choice) return Plan{};
            outgoing.push_back(random_bit(choice));
        }
        for (int index = 0; index < size; ++index)
            plan.after.push_back((plan.before[index] ^ outgoing[index]) |
                                 outgoing[(index + size - 1) % size]);
    }
    return plan;
}

static void save(const State& state, const std::string& path) {
    state.audit();
    std::vector<std::vector<int>> blocks;
    for (Mask block : state.all()) {
        auto labels = points(block);
        for (int& point : labels) ++point;
        blocks.push_back(labels);
    }
    std::sort(blocks.begin(), blocks.end());
    std::ofstream output(path);
    require(static_cast<bool>(output), "cannot write snapshot");
    for (const auto& block : blocks) {
        for (int index = 0; index < 5; ++index) output << (index ? " " : "") << block[index];
        output << '\n';
    }
    require(static_cast<bool>(output), "snapshot write failed");
}
static void mask_json(const std::vector<Mask>& masks) {
    std::cout << '[';
    for (size_t index = 0; index < masks.size(); ++index) {
        if (index) std::cout << ',';
        std::cout << '[';
        auto labels = points(masks[index]);
        for (size_t position = 0; position < labels.size(); ++position)
            std::cout << (position ? "," : "") << labels[position] + 1;
        std::cout << ']';
    }
    std::cout << ']';
}
static void operation(const Plan& plan, const std::string& before, const std::string& after,
                      const std::string& role) {
    std::cout << "{\"event\":\"operation\",\"role\":\"" << role << "\",\"mode\":"
              << plan.mode << ",\"before\":\"" << before << "\",\"after\":\"" << after
              << "\",\"removed\":";
    mask_json(plan.before);
    std::cout << ",\"added\":";
    mask_json(plan.after);
    std::cout << "}" << std::endl;
}

int main(int argc, char** argv) {
    try {
        require(argc == 7 || (argc == 8 && std::string(argv[7]) == "--controls-only"),
                "usage: START ANCHOR HIGH_POINT SEED SECONDS PREFIX [--controls-only]");
        uint64_t anchor_label = unsigned_argument(argv[2]), high_label = unsigned_argument(argv[3]);
        require(anchor_label >= 1 && anchor_label <= 16 && high_label >= 1 && high_label <= 16 &&
                anchor_label != high_label,
                "distinct1-based anchor and high point required");
        int anchor = static_cast<int>(anchor_label) - 1, high = static_cast<int>(high_label) - 1;
        uint64_t seed = unsigned_argument(argv[4]);
        size_t consumed = 0;
        double seconds = std::stod(argv[5], &consumed);
        require(consumed == std::string(argv[5]).size() && std::isfinite(seconds) && seconds > 0,
                "positive finite budget required");
        std::string prefix = argv[6];
        rng.seed(seed);
        initialize_tables();
        std::signal(SIGTERM, stop);
        std::signal(SIGINT, stop);
        State initial(read_blocks(argv[1]), anchor, high);
        auto fixed_identity = initial.fixed;
        std::sort(fixed_identity.begin(), fixed_identity.end());
        save(initial, prefix + "-initial.txt");
        std::cout << "{\"event\":\"start\",\"seed\":" << seed << ",\"seconds\":" << seconds
                  << ",\"workers\":1,\"anchor\":" << anchor + 1 << ",\"high_point\":" << high + 1
                  << ",\"initial_holes\":" << initial.missing.size() << "}" << std::endl;
        if (initial.missing.empty()) {
            save(initial, prefix + "-best.txt");
            std::cout << "{\"event\":\"finished\",\"best_holes\":0,\"proposals\":0,"
                         "\"seconds\":0,\"reason\":\"initial_cover\"}" << std::endl;
            return 0;
        }
        for (int mode = 0; mode < 3; ++mode) {
            State state = initial;
            Plan plan;
            for (int attempt = 0; attempt < 200000; ++attempt) {
                plan = propose(state, mode);
                if (state.legal(plan)) break;
            }
            require(state.legal(plan), "could not exercise a move control");
            auto before_counts = state.counts;
            auto before_free = state.free;
            auto before_selected = state.selected;
            std::string before = prefix + "-control" + std::to_string(mode) + "-before.txt";
            std::string after = prefix + "-control" + std::to_string(mode) + "-after.txt";
            save(state, before);
            state.apply(plan);
            save(state, after);
            operation(plan, before, after, "forced_apply");
            Plan rollback{mode, plan.slots, plan.after, plan.before};
            state.apply(rollback);
            state.audit();
            require(state.counts == before_counts && state.free == before_free &&
                    state.selected == before_selected, "rollback failed");
            save(state, prefix + "-control" + std::to_string(mode) + "-rollback.txt");
            Plan damaged = plan;
            damaged.after[1] = damaged.after[0];
            require(!state.legal(damaged), "duplicate move accepted");
            require(state.counts == before_counts && state.free == before_free &&
                    state.selected == before_selected, "rejected move mutated state");
        }
        if (argc == 8) {
            std::cout << "{\"event\":\"controls_passed\",\"modes\":3,\"rollbacks\":3,"
                         "\"duplicate_rejections\":3}" << std::endl;
            return 0;
        }
        State state = initial;
        auto best_free = state.free;
        int best = static_cast<int>(state.missing.size());
        std::array<uint64_t, 3> attempted{}, accepted{};
        uint64_t proposals = 0, restarts = 0, sampled = 0;
        auto began = Clock::now();
        auto elapsed = [&]() { return std::chrono::duration<double>(Clock::now() - began).count(); };
        auto record_best = [&]() {
            if (static_cast<int>(state.missing.size()) >= best) return;
            best = static_cast<int>(state.missing.size());
            best_free = state.free;
            save(state, prefix + "-best.txt");
            save(state, prefix + "-h" + std::to_string(best) + ".txt");
            std::cout << "{\"event\":\"improvement\",\"holes\":" << best
                      << ",\"proposals\":" << proposals << ",\"seconds\":" << elapsed()
                      << "}" << std::endl;
        };
        save(state, prefix + "-best.txt");
        while (!stop_requested && elapsed() < seconds && best > 0) {
            int draw = random_int(100), mode = draw < 45 ? 0 : draw < 80 ? 1 : 2;
            ++proposals;
            ++attempted[mode];
            Plan plan = propose(state, mode);
            if (state.legal(plan)) {
                int change = state.delta(plan);
                double phase = static_cast<double>(proposals % 100000) / 100000;
                double temperature = 0.07 + 0.93 * std::pow(1 - phase, 3);
                bool take = change <= 0 || std::generate_canonical<double, 53>(rng) <
                                               std::exp(-change / temperature);
                if (take) {
                    bool sample = sampled < 12 && proposals % 5000 == 0;
                    std::string before = prefix + "-sample" + std::to_string(sampled) + "-before.txt";
                    std::string after = prefix + "-sample" + std::to_string(sampled) + "-after.txt";
                    if (sample) save(state, before);
                    state.apply(plan);
                    ++accepted[mode];
                    if (sample) {
                        save(state, after);
                        operation(plan, before, after, "accepted_sample");
                        ++sampled;
                    }
                    record_best();
                }
            }
            if (proposals % 100000 == 0) state.audit();
            if (proposals % 500000 == 0 && best > 0) {
                std::vector<Mask> restart = initial.fixed;
                const auto& chosen = restarts % 3 == 2 ? initial.free : best_free;
                restart.insert(restart.end(), chosen.begin(), chosen.end());
                state = State(restart, anchor, high);
                for (int step = 0; step < 50 && best > 0; ++step) {
                    Plan perturb = propose(state, 1 + random_int(2));
                    if (state.legal(perturb)) state.apply(perturb);
                    record_best();
                }
                state.audit();
                ++restarts;
            }
        }
        state.audit();
        auto final_fixed = state.fixed;
        std::sort(final_fixed.begin(), final_fixed.end());
        require(final_fixed == fixed_identity, "fixed link changed");
        std::cout << "{\"event\":\"" << (stop_requested ? "interrupted" : "finished")
                  << "\",\"best_holes\":" << best << ",\"proposals\":" << proposals
                  << ",\"seconds\":" << elapsed() << ",\"restarts\":" << restarts
                  << ",\"sampled_operations\":" << sampled << ",\"attempted\":["
                  << attempted[0] << ',' << attempted[1] << ',' << attempted[2]
                  << "],\"accepted\":[" << accepted[0] << ',' << accepted[1] << ',' << accepted[2]
                  << "]}" << std::endl;
        return best == 0 ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
