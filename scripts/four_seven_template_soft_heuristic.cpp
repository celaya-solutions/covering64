// Document:    Soft-Score Complete Heavy Template Covering Heuristic
// Version:     v1.1.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      21893db894c5a5753e8010311b40b281d3b42bcfcb0e0ebdbedb5ca3e58fd95c
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
#include <numeric>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Mask = unsigned;
using Clock = std::chrono::steady_clock;
using Template = std::array<Mask, 7>;
static std::array<std::vector<Template>, 4> catalogs;
static std::array<std::array<std::vector<int>, 65536>, 4> edge_templates;
static std::string catalog_case;
static Mask anchor_mask(int group) { return 7u << (4 * group); }
static bool ordinary(Mask block) {
    if (block >= 65536 || __builtin_popcount(block) != 5) return false;
    for (int group = 0; group < 4; ++group)
        if (__builtin_popcount(block & anchor_mask(group)) > 1) return false;
    return true;
}
static std::array<std::array<int, 10>, 65536> block_triples{};
static std::array<int, 65536> triple_id{};
static std::array<int, 65536> pair_id{};
static std::array<std::array<int, 10>, 65536> block_pairs{};
static std::array<int, 120> pair_targets{};
static std::array<bool, 560> heavy_triple{};
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
    pair_id.fill(-1);
    int pair_index = 0;
    for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
        pair_id[(1u << a) | (1u << b)] = pair_index++;
    require(pair_index == 120, "wrong pair universe");
    int index = 0;
    for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
        for (int c = b + 1; c < 16; ++c) {
            Mask mask = (1u << a) | (1u << b) | (1u << c);
            triple_id[mask] = index;
            triple_masks[index++] = mask;
        }
    require(index == 560, "wrong triple universe");
    for (int group = 0; group < 4; ++group) heavy_triple[triple_id[anchor_mask(group)]] = true;
    for (Mask mask = 0; mask < 65536; ++mask) if (__builtin_popcount(mask) == 5) {
        auto labels = points(mask);
        int count = 0;
        for (int a = 0; a < 5; ++a) for (int b = a + 1; b < 5; ++b)
            for (int c = b + 1; c < 5; ++c)
                block_triples[mask][count++] = triple_id[(1u << labels[a]) |
                    (1u << labels[b]) | (1u << labels[c])];
        require(count == 10, "wrong block incidence count");
        int pair_count = 0;
        for (int a = 0; a < 5; ++a) for (int b = a + 1; b < 5; ++b)
            block_pairs[mask][pair_count++] = pair_id[(1u << labels[a]) | (1u << labels[b])];
        require(pair_count == 10, "wrong block pair count");
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

static void read_catalog(const std::string& path) {
    std::ifstream input(path);
    require(static_cast<bool>(input), "cannot open catalog");
    std::string marker;
    std::array<int, 4> sizes{};
    require(static_cast<bool>(input >> marker >> catalog_case >> sizes[0] >> sizes[1] >> sizes[2] >> sizes[3]),
            "malformed catalog header");
    require(marker == "C64T1" && (catalog_case == "matching" || catalog_case == "cycle"),
            "unsupported catalog format or case");
    int expected = catalog_case == "matching" ? 12042 : 25020;
    for (int group = 0; group < 4; ++group) {
        require(sizes[group] == expected, "wrong catalog count");
        std::set<Template> unique;
        for (int index = 0; index < sizes[group]; ++index) {
            int group_label, template_label;
            require(static_cast<bool>(input >> group_label >> template_label) &&
                    group_label == group + 1 && template_label == index + 1, "catalog index mismatch");
            Template row{};
            std::array<int, 16> degrees{};
            std::set<Mask> edges;
            for (int edge = 0; edge < 7; ++edge) {
                int a, b;
                require(static_cast<bool>(input >> a >> b) && 1 <= a && a < b && b <= 16,
                        "malformed template edge");
                Mask outside = (1u << (a - 1)) | (1u << (b - 1));
                require(!(outside & anchor_mask(group)) && edges.insert(outside).second,
                        "invalid or duplicate template edge");
                row[edge] = anchor_mask(group) | outside;
                ++degrees[a - 1]; ++degrees[b - 1];
            }
            for (int point = 0; point < 16; ++point)
                require(degrees[point] == ((anchor_mask(group) & (1u << point)) ? 0 :
                        point == 4 * group + 3 ? 2 : 1), "template outside degree mismatch");
            auto sorted = row;
            std::sort(sorted.begin(), sorted.end());
            require(unique.insert(sorted).second, "duplicate template");
            catalogs[group].push_back(row);
            for (Mask edge : edges) edge_templates[group][edge].push_back(index);
        }
    }
    input >> std::ws;
    require(input.eof(), "extra catalog token");
}

static void initialize_pair_targets() {
    pair_targets.fill(5);
    auto set = [&](int a, int b, int value) { pair_targets[pair_id[(1u << a) | (1u << b)]] = value; };
    for (int group = 0; group < 4; ++group) {
        for (int a = 0; a < 3; ++a) for (int b = a + 1; b < 3; ++b)
            set(4 * group + a, 4 * group + b, 7);
        for (int a = 0; a < 3; ++a) set(4 * group + a, 4 * group + 3, 6);
    }
    if (catalog_case == "matching") { set(3, 7, 7); set(11, 15, 7); }
    else { set(3, 7, 6); set(7, 11, 6); set(11, 15, 6); set(3, 15, 6); }
    require(std::accumulate(pair_targets.begin(), pair_targets.end(), 0) == 640, "pair target total");
}

struct Plan {
    int mode = 0;
    std::vector<int> slots;
    std::vector<Mask> before, after;
    int group = -1, previous_template = -1, next_template = -1;
};

struct State {
    std::vector<Mask> fixed;
    std::array<Mask, 36> free{};
    std::array<int, 4> template_ids{};
    std::array<int, 560> counts{};
    std::array<int, 120> pairs{};
    std::array<unsigned char, 65536> selected{};
    std::vector<int> missing;
    std::array<int, 560> missing_position{};

    explicit State(const std::vector<Mask>& all) {
        std::array<std::vector<Mask>, 4> heavy;
        int movable = 0;
        for (Mask block : all) {
            require(!selected[block], "duplicate state block");
            selected[block] = 1;
            int group = -1;
            for (int g = 0; g < 4; ++g)
                if ((block & anchor_mask(g)) == anchor_mask(g)) group = g;
            if (group >= 0) heavy[group].push_back(block);
            else {
                require(ordinary(block) && movable < 36, "invalid ordinary block or count");
                free[movable++] = block;
            }
            for (int triple : block_triples[block]) ++counts[triple];
            for (int pair : block_pairs[block]) ++pairs[pair];
        }
        require(movable == 36, "exactly36 ordinary blocks required");
        for (int group = 0; group < 4; ++group) {
            require(heavy[group].size() == 7, "each heavy group needs7 blocks");
            std::sort(heavy[group].begin(), heavy[group].end());
            int found = -1;
            for (int index = 0; index < static_cast<int>(catalogs[group].size()); ++index) {
                auto row = catalogs[group][index];
                std::sort(row.begin(), row.end());
                if (std::equal(row.begin(), row.end(), heavy[group].begin())) found = index;
            }
            require(found >= 0, "seed heavy group absent from catalog");
            template_ids[group] = found;
            const auto& row = catalogs[group][found];
            fixed.insert(fixed.end(), row.begin(), row.end());
        }
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
        std::array<int, 16> degrees{}, ordinary_degrees{};
        std::array<int, 560> rebuilt{};
        std::array<int, 120> rebuilt_pairs{};
        std::set<Mask> unique;
        require(fixed.size() == 28, "wrong heavy block count");
        for (Mask block : all()) {
            require(__builtin_popcount(block) == 5 && selected[block], "malformed selected block");
            require(unique.insert(block).second, "duplicate selected block");
            for (int point : points(block)) ++degrees[point];
            for (int triple : block_triples[block]) ++rebuilt[triple];
            for (int pair : block_pairs[block]) ++rebuilt_pairs[pair];
        }
        require(unique.size() == 64 && rebuilt == counts, "incremental triple count drift");
        require(rebuilt_pairs == pairs, "incremental pair count drift");
        require(std::count(selected.begin(), selected.end(), 1) == 64, "selected flags drift");
        for (Mask block : free) {
            require(ordinary(block), "forbidden ordinary block");
            for (int point : points(block)) ++ordinary_degrees[point];
        }
        for (int point = 0; point < 16; ++point) {
            require(degrees[point] == 20, "degree20 drift");
            require(ordinary_degrees[point] == (point % 4 == 3 ? 15 : 10), "ordinary degree drift");
        }
        for (int group = 0; group < 4; ++group) {
            require(template_ids[group] >= 0 && template_ids[group] < static_cast<int>(catalogs[group].size()),
                    "invalid template index");
            require(std::equal(catalogs[group][template_ids[group]].begin(),
                               catalogs[group][template_ids[group]].end(), fixed.begin() + 7 * group),
                    "heavy group changed outside catalog");
        }
        int holes = 0;
        for (int triple = 0; triple < 560; ++triple) {
            for (int group = 0; group < 4; ++group)
                if (__builtin_popcount(triple_masks[triple] & anchor_mask(group)) >= 2)
                    require(counts[triple] > 0, "anchor-pair triple uncovered");
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
        if (plan.mode == 3) {
            if (plan.group < 0 || plan.group >= 4 || plan.slots.size() != 7 ||
                plan.previous_template != template_ids[plan.group] || plan.next_template < 0 ||
                plan.next_template >= static_cast<int>(catalogs[plan.group].size())) return false;
            if (!std::equal(plan.after.begin(), plan.after.end(),
                            catalogs[plan.group][plan.next_template].begin())) return false;
        } else if (plan.mode < 0 || plan.mode > 2 || plan.group != -1) return false;
        std::array<int, 16> change{};
        for (size_t index = 0; index < plan.slots.size(); ++index) {
            int slot = plan.slots[index];
            if (plan.mode == 3) {
                if (slot != 7 * plan.group + static_cast<int>(index) || fixed[slot] != plan.before[index])
                    return false;
            } else if (slot < 0 || slot >= 36 || free[slot] != plan.before[index] ||
                       !ordinary(plan.after[index])) return false;
            Mask block = plan.after[index];
            if (block >= 65536 || __builtin_popcount(block) != 5) return false;
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
    int pair_defect() const {
        int result = 0;
        for (int pair = 0; pair < 120; ++pair) result += std::abs(pairs[pair] - pair_targets[pair]);
        return result;
    }
    int overcoverage() const {
        int result = 0;
        for (int triple = 0; triple < 560; ++triple)
            if (!heavy_triple[triple]) result += std::max(0, counts[triple] - 2);
        return result;
    }
    int score() const { return 5 * static_cast<int>(missing.size()) + pair_defect() + 5 * overcoverage(); }
    std::array<int, 120> pair_changes(const Plan& plan) const {
        std::array<int, 120> result{};
        for (Mask block : plan.before) for (int pair : block_pairs[block]) --result[pair];
        for (Mask block : plan.after) for (int pair : block_pairs[block]) ++result[pair];
        return result;
    }
    int score_delta(const Plan& plan) const {
        auto change = changes(plan);
        auto pair_change = pair_changes(plan);
        int result = 0;
        for (int triple = 0; triple < 560; ++triple) {
            result += 5 * ((counts[triple] + change[triple] == 0) - (counts[triple] == 0));
            if (!heavy_triple[triple]) result += 5 * (std::max(0, counts[triple] + change[triple] - 2) -
                                                    std::max(0, counts[triple] - 2));
        }
        for (int pair = 0; pair < 120; ++pair)
            result += std::abs(pairs[pair] + pair_change[pair] - pair_targets[pair]) -
                      std::abs(pairs[pair] - pair_targets[pair]);
        return result;
    }
    void apply(const Plan& plan) {
        require(legal(plan), "illegal move reached mutation");
        int predicted_score = score() + score_delta(plan);
        int predicted_holes = static_cast<int>(missing.size()) + delta(plan);
        auto pair_change = pair_changes(plan);
        auto change = changes(plan);
        for (Mask block : plan.before) selected[block] = 0;
        for (size_t index = 0; index < plan.slots.size(); ++index) {
            if (plan.mode == 3) fixed[plan.slots[index]] = plan.after[index];
            else free[plan.slots[index]] = plan.after[index];
            selected[plan.after[index]] = 1;
        }
        if (plan.mode == 3) template_ids[plan.group] = plan.next_template;
        for (int pair = 0; pair < 120; ++pair) {
            pairs[pair] += pair_change[pair];
            require(pairs[pair] >= 0, "negative pair count");
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
        require(score() == predicted_score && static_cast<int>(missing.size()) == predicted_holes,
                "predicted score or hole delta failed");
    }
};

static Plan propose(const State& state, int mode) {
    Plan plan;
    plan.mode = mode;
    if (mode == 0) {
        if (state.missing.empty()) return plan;
        Mask target = triple_masks[state.missing[random_int(static_cast<int>(state.missing.size()))]];
        std::vector<int> close;
        for (int slot = 0; slot < 36; ++slot)
            if (__builtin_popcount(state.free[slot] & target) == 2) close.push_back(slot);
        if (close.empty()) return plan;
        int first = close[random_int(static_cast<int>(close.size()))];
        Mask incoming = target & ~state.free[first];
        Mask outgoing = random_bit(state.free[first] & ~target);
        std::vector<int> donors;
        for (int slot = 0; slot < 36; ++slot)
            if ((state.free[slot] & incoming) && !(state.free[slot] & outgoing)) donors.push_back(slot);
        if (donors.empty()) return plan;
        int second = donors[random_int(static_cast<int>(donors.size()))];
        plan.slots = {first, second};
        plan.before = {state.free[first], state.free[second]};
        plan.after = {(state.free[first] ^ outgoing) | incoming,
                      (state.free[second] ^ incoming) | outgoing};
    } else if (mode == 1) {
        int first = random_int(36), second = random_int(35);
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
    } else if (mode == 2) {
        int size = 3 + random_int(4);
        while (static_cast<int>(plan.slots.size()) < size) {
            int slot = random_int(36);
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
    if (mode == 3) {
        int group = random_int(4), next = random_int(static_cast<int>(catalogs[group].size()));
        if (!state.missing.empty() && random_int(2) == 0) {
            Mask target = triple_masks[state.missing[random_int(static_cast<int>(state.missing.size()))]];
            std::vector<int> useful;
            for (int g = 0; g < 4; ++g) if (__builtin_popcount(target & anchor_mask(g)) == 1 &&
                    !edge_templates[g][target & ~anchor_mask(g)].empty()) useful.push_back(g);
            if (!useful.empty()) {
                group = useful[random_int(static_cast<int>(useful.size()))];
                const auto& options = edge_templates[group][target & ~anchor_mask(group)];
                next = options[random_int(static_cast<int>(options.size()))];
            }
        }
        plan.group = group;
        plan.previous_template = state.template_ids[group];
        plan.next_template = next;
        for (int index = 0; index < 7; ++index) {
            plan.slots.push_back(7 * group + index);
            plan.before.push_back(state.fixed[7 * group + index]);
            plan.after.push_back(catalogs[group][next][index]);
        }
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
                      const std::string& role, int before_holes, int before_score,
                      int after_holes, int after_score) {
    std::cout << "{\"event\":\"operation\",\"role\":\"" << role << "\",\"mode\":"
              << plan.mode << ",\"before\":\"" << before << "\",\"after\":\"" << after
              << "\",\"removed\":";
    mask_json(plan.before);
    std::cout << ",\"added\":";
    mask_json(plan.after);
    std::cout << ",\"template_group\":" << plan.group + 1
              << ",\"template_before\":" << plan.previous_template + 1
              << ",\"template_after\":" << plan.next_template + 1
              << ",\"holes_before\":" << before_holes << ",\"score_before\":" << before_score
              << ",\"holes_after\":" << after_holes << ",\"score_after\":" << after_score
              << "}" << std::endl;
}

int main(int argc, char** argv) {
    try {
        require(argc == 6 || (argc == 7 && std::string(argv[6]) == "--controls-only"),
                "usage: CATALOG START SEED SECONDS PREFIX [--controls-only]");
        uint64_t seed = unsigned_argument(argv[3]);
        size_t consumed = 0;
        double seconds = std::stod(argv[4], &consumed);
        require(consumed == std::string(argv[4]).size() && std::isfinite(seconds) && seconds > 0,
                "positive finite budget required");
        std::string prefix = argv[5];
        rng.seed(seed);
        initialize_tables();
        std::signal(SIGTERM, stop);
        std::signal(SIGINT, stop);
        read_catalog(argv[1]);
        initialize_pair_targets();
        State initial(read_blocks(argv[2]));
        save(initial, prefix + "-initial.txt");
        std::cout << "{\"event\":\"start\",\"seed\":" << seed << ",\"seconds\":" << seconds
                  << ",\"workers\":1,\"catalog\":\"" << catalog_case << "\""
                  << ",\"initial_holes\":" << initial.missing.size() << ",\"initial_score\":" << initial.score()
                  << ",\"initial_pair_l1\":" << initial.pair_defect()
                  << ",\"initial_nonheavy_excess\":" << initial.overcoverage() << "}" << std::endl;
        if (initial.missing.empty()) {
            save(initial, prefix + "-best.txt");
            save(initial, prefix + "-raw-best.txt");
            save(initial, prefix + "-score-best.txt");
            std::cout << "{\"event\":\"finished\",\"best_holes\":0,\"proposals\":0,"
                         "\"seconds\":0,\"reason\":\"initial_cover\",\"best_score\":"
                      << initial.score() << ",\"best_raw_score\":" << initial.score()
                      << ",\"best_score_holes\":0}" << std::endl;
            return 0;
        }
        for (int mode = 0; mode < 4; ++mode) {
            State state = initial;
            Plan plan;
            for (int attempt = 0; attempt < 200000; ++attempt) {
                plan = propose(state, mode);
                if (state.legal(plan)) break;
            }
            require(state.legal(plan), "could not exercise a move control");
            int before_holes = static_cast<int>(state.missing.size()), before_score = state.score();
            auto before_pairs = state.pairs;
            auto before_counts = state.counts;
            auto before_free = state.free;
            auto before_selected = state.selected;
            auto before_fixed = state.fixed;
            auto before_templates = state.template_ids;
            std::string before = prefix + "-control" + std::to_string(mode) + "-before.txt";
            std::string after = prefix + "-control" + std::to_string(mode) + "-after.txt";
            save(state, before);
            state.apply(plan);
            save(state, after);
            operation(plan, before, after, "forced_apply", before_holes, before_score,
                      static_cast<int>(state.missing.size()), state.score());
            if (state.missing.empty()) {
                save(state, prefix + "-best.txt");
                save(state, prefix + "-raw-best.txt");
                save(state, prefix + "-score-best.txt");
                std::cout << "{\"event\":\"finished\",\"best_holes\":0,\"reason\":\"control_cover\","
                             "\"best_score\":" << state.score() << ",\"best_raw_score\":" << state.score()
                          << ",\"best_score_holes\":0}" << std::endl;
                return 0;
            }
            Plan rollback{mode, plan.slots, plan.after, plan.before,
                          plan.group, plan.next_template, plan.previous_template};
            state.apply(rollback);
            state.audit();
            require(state.pairs == before_pairs && state.score() == before_score &&
                    state.counts == before_counts && state.free == before_free &&
                    state.selected == before_selected && state.fixed == before_fixed &&
                    state.template_ids == before_templates, "rollback failed");
            save(state, prefix + "-control" + std::to_string(mode) + "-rollback.txt");
            Plan damaged = plan;
            damaged.after[1] = damaged.after[0];
            require(!state.legal(damaged), "duplicate move accepted");
            require(state.pairs == before_pairs && state.score() == before_score &&
                    state.counts == before_counts && state.free == before_free &&
                    state.selected == before_selected && state.fixed == before_fixed &&
                    state.template_ids == before_templates, "rejected move mutated state");
        }
        if (argc == 7) {
            std::cout << "{\"event\":\"controls_passed\",\"modes\":4,\"rollbacks\":4,"
                         "\"duplicate_rejections\":4}" << std::endl;
            return 0;
        }
        State state = initial;
        State raw_best_state = state, score_best_state = state;
        int best = static_cast<int>(state.missing.size()), best_raw_score = state.score();
        int best_score = state.score(), best_score_holes = best;
        std::array<uint64_t, 4> attempted{}, accepted{};
        uint64_t proposals = 0, restarts = 0, sampled = 0;
        auto began = Clock::now();
        auto elapsed = [&]() { return std::chrono::duration<double>(Clock::now() - began).count(); };
        auto record_best = [&]() {
            int holes = static_cast<int>(state.missing.size()), score = state.score();
            bool raw_improves = holes < best || (holes == best && score < best_raw_score);
            bool score_improves = score < best_score || (score == best_score && holes < best_score_holes);
            if (raw_improves) {
                best = holes; best_raw_score = score; raw_best_state = state;
                save(state, prefix + "-best.txt");
                save(state, prefix + "-raw-best.txt");
                save(state, prefix + "-raw-h" + std::to_string(holes) + "-s" + std::to_string(score) + ".txt");
            }
            if (score_improves) {
                best_score = score; best_score_holes = holes; score_best_state = state;
                save(state, prefix + "-score-best.txt");
                save(state, prefix + "-score-s" + std::to_string(score) + "-h" + std::to_string(holes) + ".txt");
            }
            if (raw_improves || score_improves)
                std::cout << "{\"event\":\"improvement\",\"holes\":" << holes
                          << ",\"score\":" << score << ",\"pair_l1\":" << state.pair_defect()
                          << ",\"nonheavy_excess\":" << state.overcoverage()
                          << ",\"best_holes\":" << best << ",\"best_score\":" << best_score
                          << ",\"raw_improved\":" << (raw_improves ? "true" : "false")
                          << ",\"score_improved\":" << (score_improves ? "true" : "false")
                          << ",\"proposals\":" << proposals << ",\"seconds\":" << elapsed() << "}" << std::endl;
        };
        save(state, prefix + "-raw-best.txt");
        save(state, prefix + "-score-best.txt");
        save(state, prefix + "-best.txt");
        while (!stop_requested && elapsed() < seconds && best > 0) {
            int draw = random_int(100), mode = draw < 35 ? 0 : draw < 60 ? 1 : draw < 75 ? 2 : 3;
            ++proposals;
            ++attempted[mode];
            Plan plan = propose(state, mode);
            if (state.legal(plan)) {
                int hole_change = state.delta(plan), change = state.score_delta(plan);
                double phase = static_cast<double>(proposals % 100000) / 100000;
                double temperature = 5 * (0.07 + 0.93 * std::pow(1 - phase, 3));
                bool take = static_cast<int>(state.missing.size()) + hole_change == 0 ||
                            change <= 0 || std::generate_canonical<double, 53>(rng) <
                                               std::exp(-change / temperature);
                if (take) {
                    bool sample = sampled < 12 && proposals % 5000 == 0;
                    std::string before = prefix + "-sample" + std::to_string(sampled) + "-before.txt";
                    std::string after = prefix + "-sample" + std::to_string(sampled) + "-after.txt";
                    int before_holes = static_cast<int>(state.missing.size()), before_score = state.score();
                    if (sample) save(state, before);
                    state.apply(plan);
                    ++accepted[mode];
                    if (sample) {
                        save(state, after);
                        operation(plan, before, after, "accepted_sample", before_holes, before_score,
                                  static_cast<int>(state.missing.size()), state.score());
                        ++sampled;
                    }
                    record_best();
                }
            }
            if (proposals % 100000 == 0) state.audit();
            if (proposals % 500000 == 0 && best > 0) {
                state = restarts % 3 == 2 ? initial : score_best_state;
                for (int step = 0; step < 50 && best > 0; ++step) {
                    Plan perturb = propose(state, 1 + random_int(3));
                    if (state.legal(perturb)) state.apply(perturb);
                    record_best();
                }
                state.audit();
                ++restarts;
            }
        }
        state.audit();
        raw_best_state.audit(); score_best_state.audit();
        require(static_cast<int>(raw_best_state.missing.size()) == best && raw_best_state.score() == best_raw_score &&
                score_best_state.score() == best_score &&
                static_cast<int>(score_best_state.missing.size()) == best_score_holes, "best-record drift");
        std::cout << "{\"event\":\"" << (stop_requested ? "interrupted" : "finished")
                  << "\",\"best_holes\":" << best << ",\"best_raw_score\":" << best_raw_score
                  << ",\"best_score\":" << best_score << ",\"best_score_holes\":" << best_score_holes
                  << ",\"proposals\":" << proposals
                  << ",\"seconds\":" << elapsed() << ",\"restarts\":" << restarts
                  << ",\"sampled_operations\":" << sampled << ",\"attempted\":["
                  << attempted[0] << ',' << attempted[1] << ',' << attempted[2] << ',' << attempted[3]
                  << "],\"accepted\":[" << accepted[0] << ',' << accepted[1] << ',' << accepted[2] << ',' << accepted[3]
                  << "]}" << std::endl;
        return best == 0 ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
