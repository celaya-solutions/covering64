// Document:    Anchor-Pair Lookahead Complete Heavy Template Covering Heuristic
// Version:     v1.2.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      024a50427709e3caaab594ec2681bff9b7b5444916b737f0f890bb08a5f1024e
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
#include <unordered_map>

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
static std::array<Mask, 120> pair_masks{};
static std::array<std::array<int, 3>, 560> triple_pairs{};
static std::array<bool, 120> forced_pair{};
static std::array<int, 120> pair_excess_budget{};
struct OrdinaryData {
    Mask block;
    std::array<int, 10> pairs, triples;
    std::array<std::array<int, 3>, 10> pair_triples;
};
static std::vector<OrdinaryData> ordinary_data;
struct Lookahead {
    int unsupported = 0, admissible = 0, heavy_excess = 0;
    bool operator==(const Lookahead& other) const {
        return unsupported == other.unsupported && admissible == other.admissible &&
               heavy_excess == other.heavy_excess;
    }
};
static std::unordered_map<uint64_t, Lookahead> lookahead_cache;
static uint64_t lookahead_hits = 0, lookahead_misses = 0, lookahead_clears = 0;
static constexpr int LOOKAHEAD_WEIGHT = 100;
static constexpr size_t LOOKAHEAD_CACHE_LIMIT = 100000;
static size_t lookahead_cache_limit = LOOKAHEAD_CACHE_LIMIT;
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
        {
            Mask mask = (1u << a) | (1u << b);
            pair_masks[pair_index] = mask;
            pair_id[mask] = pair_index++;
        }
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
        if (ordinary(mask)) {
            OrdinaryData item{mask, block_pairs[mask], block_triples[mask], {}};
            for (int j = 0; j < 10; ++j) {
                int n = 0;
                for (int point : labels) if (!(pair_masks[item.pairs[j]] & (1u << point)))
                    item.pair_triples[j][n++] = triple_id[pair_masks[item.pairs[j]] | (1u << point)];
                require(n == 3, "ordinary pair link size");
            }
            ordinary_data.push_back(item);
        }
    }
    require(ordinary_data.size() == 1200, "ordinary universe size");
    for (int t = 0; t < 560; ++t) {
        auto labels = points(triple_masks[t]);
        triple_pairs[t] = {pair_id[(1u << labels[0]) | (1u << labels[1])],
                          pair_id[(1u << labels[0]) | (1u << labels[2])],
                          pair_id[(1u << labels[1]) | (1u << labels[2])]};
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
    for (int p = 0; p < 120; ++p) {
        auto labels = points(pair_masks[p]);
        forced_pair[p] = labels[0] % 4 != 3 || labels[1] % 4 != 3;
        pair_excess_budget[p] = 3 * pair_targets[p] - 14;
    }
}

static Lookahead evaluate_lookahead(const std::array<int, 4>& ids,
                                    std::vector<Mask>* allowed = nullptr,
                                    std::vector<int>* unsupported = nullptr) {
    std::array<int, 560> heavy_counts{}, supports{};
    std::array<int, 120> excess{};
    for (int group = 0; group < 4; ++group)
        for (Mask block : catalogs[group][ids[group]])
            for (int t : block_triples[block]) ++heavy_counts[t];
    for (int t = 0; t < 560; ++t) if (heavy_counts[t] > 1)
        for (int p : triple_pairs[t]) excess[p] += heavy_counts[t] - 1;
    Lookahead result;
    for (int p = 0; p < 120; ++p) if (forced_pair[p])
        result.heavy_excess += std::max(0, excess[p] - pair_excess_budget[p]);
    if (result.heavy_excess == 0) for (const auto& item : ordinary_data) {
        bool viable = true;
        for (int j = 0; j < 10 && viable; ++j) {
            int p = item.pairs[j];
            if (!forced_pair[p]) continue;
            int increment = 0;
            for (int t : item.pair_triples[j]) increment += heavy_counts[t] >= 1;
            if (excess[p] + increment > pair_excess_budget[p]) viable = false;
        }
        if (viable) {
            ++result.admissible;
            if (allowed) allowed->push_back(item.block);
            for (int t : item.triples) ++supports[t];
        }
    }
    for (int t = 0; t < 560; ++t) if (heavy_counts[t] == 0 && supports[t] == 0) {
        ++result.unsupported;
        if (unsupported) unsupported->push_back(t);
    }
    return result;
}

static Lookahead cached_lookahead(const std::array<int, 4>& ids) {
    uint64_t key = 0;
    for (int group = 0; group < 4; ++group) {
        require(ids[group] >= 0 && ids[group] < 65536, "template cache key range");
        key |= static_cast<uint64_t>(ids[group]) << (16 * group);
    }
    auto found = lookahead_cache.find(key);
    if (found != lookahead_cache.end()) { ++lookahead_hits; return found->second; }
    ++lookahead_misses;
    Lookahead result = evaluate_lookahead(ids);
    if (lookahead_cache.size() >= lookahead_cache_limit) { lookahead_cache.clear(); ++lookahead_clears; }
    lookahead_cache.emplace(key, result);
    return result;
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
    Lookahead lookahead;
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
        lookahead = cached_lookahead(template_ids);
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
        require(lookahead == evaluate_lookahead(template_ids), "lookahead cache drift");
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
    int base_score() const { return 5 * static_cast<int>(missing.size()) + pair_defect() + 5 * overcoverage(); }
    int score() const { return base_score() + LOOKAHEAD_WEIGHT * lookahead.unsupported; }
    Lookahead projected_lookahead(const Plan& plan) const {
        if (plan.mode != 3) return lookahead;
        auto next = template_ids;
        next[plan.group] = plan.next_template;
        return cached_lookahead(next);
    }
    std::array<int, 120> pair_changes(const Plan& plan) const {
        std::array<int, 120> result{};
        for (Mask block : plan.before) for (int pair : block_pairs[block]) --result[pair];
        for (Mask block : plan.after) for (int pair : block_pairs[block]) ++result[pair];
        return result;
    }
    int score_delta(const Plan& plan) const {
        auto change = changes(plan);
        auto pair_change = pair_changes(plan);
        int result = LOOKAHEAD_WEIGHT * (projected_lookahead(plan).unsupported - lookahead.unsupported);
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
        if (plan.mode == 3) {
            template_ids[plan.group] = plan.next_template;
            lookahead = cached_lookahead(template_ids);
        }
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

static bool accept_score_move(int projected_holes, int score_delta, double temperature) {
    return projected_holes == 0 || score_delta <= 0 ||
           std::generate_canonical<double, 53>(rng) < std::exp(-score_delta / temperature);
}

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

static void lookahead_json(const State& state, std::ostream& output) {
    std::vector<Mask> allowed;
    std::vector<int> unsupported;
    Lookahead actual = evaluate_lookahead(state.template_ids, &allowed, &unsupported);
    require(actual == state.lookahead, "lookahead detail disagreement");
    std::vector<std::vector<int>> allowed_labels;
    for (Mask block : allowed) {
        auto labels = points(block);
        for (int& point : labels) ++point;
        allowed_labels.push_back(labels);
    }
    std::sort(allowed_labels.begin(), allowed_labels.end());
    output << "{\"event\":\"lookahead\",\"weight\":" << LOOKAHEAD_WEIGHT
           << ",\"holes\":" << state.missing.size() << ",\"base_score\":" << state.base_score()
           << ",\"score\":" << state.score() << ",\"unsupported_count\":" << actual.unsupported
           << ",\"admissible_count\":" << actual.admissible << ",\"heavy_excess\":" << actual.heavy_excess
           << ",\"cache_hits\":" << lookahead_hits << ",\"cache_misses\":" << lookahead_misses
           << ",\"cache_clears\":" << lookahead_clears
           << ",\"template_ids_1based\":[";
    for (int group = 0; group < 4; ++group) output << (group ? "," : "") << state.template_ids[group] + 1;
    output << "],\"unsupported_triples\":[";
    for (size_t i = 0; i < unsupported.size(); ++i) {
        if (i) output << ',';
        auto labels = points(triple_masks[unsupported[i]]);
        output << '[' << labels[0] + 1 << ',' << labels[1] + 1 << ',' << labels[2] + 1 << ']';
    }
    output << "],\"admissible_blocks\":[";
    for (size_t i = 0; i < allowed_labels.size(); ++i) {
        if (i) output << ',';
        output << '[';
        for (int j = 0; j < 5; ++j) output << (j ? "," : "") << allowed_labels[i][j];
        output << ']';
    }
    output << "]}";
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
    std::ofstream details(path + ".lookahead.json");
    require(static_cast<bool>(details), "cannot write lookahead details");
    lookahead_json(state, details);
    details << '\n';
    require(static_cast<bool>(details), "lookahead detail write failed");
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
        require(argc == 6 || (argc == 7 && (std::string(argv[6]) == "--controls-only" ||
                                                  std::string(argv[6]) == "--lookahead-only" ||
                                                  std::string(argv[6]) == "--cache-control")),
                "usage: CATALOG START SEED SECONDS PREFIX [--controls-only|--lookahead-only|--cache-control]");
        uint64_t seed = unsigned_argument(argv[3]);
        size_t consumed = 0;
        double seconds = std::stod(argv[4], &consumed);
        require(consumed == std::string(argv[4]).size() && std::isfinite(seconds) && seconds > 0,
                "positive finite budget required");
        std::string prefix = argv[5];
        rng.seed(seed);
        require(accept_score_move(0, 1000000, 0.001), "zero-hole score override failed");
        initialize_tables();
        std::signal(SIGTERM, stop);
        std::signal(SIGINT, stop);
        read_catalog(argv[1]);
        initialize_pair_targets();
        State initial(read_blocks(argv[2]));
        if (argc == 7 && std::string(argv[6]) == "--cache-control") {
            lookahead_cache_limit = 2;
            lookahead_cache.clear();
            uint64_t before_clears = lookahead_clears;
            auto a = initial.template_ids, b = a, c = a;
            require(catalogs[0].size() >= 3, "cache control needs three templates");
            b[0] = (a[0] + 1) % catalogs[0].size();
            c[0] = (a[0] + 2) % catalogs[0].size();
            Lookahead first = cached_lookahead(a);
            require(cached_lookahead(a) == first, "cache repeated-read control failed");
            require(cached_lookahead(b) == evaluate_lookahead(b), "second cache fixture failed");
            require(cached_lookahead(c) == evaluate_lookahead(c), "third cache fixture failed");
            require(lookahead_clears == before_clears + 1 && lookahead_cache.size() == 1,
                    "cache eviction branch control failed");
            require(cached_lookahead(a) == first && cached_lookahead(a) == initial.lookahead,
                    "cache refill after eviction failed");
            lookahead_cache_limit = LOOKAHEAD_CACHE_LIMIT;
            lookahead_cache.clear();
            require(cached_lookahead(a) == initial.lookahead, "cache reset failed");
            std::cout << "{\"event\":\"cache_control\",\"passed\":true,\"test_limit\":2,"
                         "\"production_limit\":" << lookahead_cache_limit
                      << ",\"production_eviction_branch_count\":" << lookahead_clears - before_clears
                      << ",\"hits\":" << lookahead_hits << ",\"misses\":" << lookahead_misses
                      << "}" << std::endl;
            return 0;
        }
        if (argc == 7 && std::string(argv[6]) == "--lookahead-only") {
            require(cached_lookahead(initial.template_ids) == initial.lookahead &&
                    cached_lookahead(initial.template_ids) == initial.lookahead,
                    "same-process repeated cache query failed");
            lookahead_json(initial, std::cout);
            std::cout << std::endl;
            return 0;
        }
        save(initial, prefix + "-initial.txt");
        std::cout << "{\"event\":\"start\",\"seed\":" << seed << ",\"seconds\":" << seconds
                  << ",\"workers\":1,\"catalog\":\"" << catalog_case << "\""
                  << ",\"initial_holes\":" << initial.missing.size() << ",\"initial_score\":" << initial.score()
                  << ",\"initial_pair_l1\":" << initial.pair_defect()
                  << ",\"initial_nonheavy_excess\":" << initial.overcoverage()
                  << ",\"initial_unsupported\":" << initial.lookahead.unsupported
                  << ",\"initial_admissible\":" << initial.lookahead.admissible
                  << ",\"lookahead_weight\":" << LOOKAHEAD_WEIGHT << "}" << std::endl;
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
            auto before_lookahead = state.lookahead;
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
            require(state.lookahead == before_lookahead && state.pairs == before_pairs && state.score() == before_score &&
                    state.counts == before_counts && state.free == before_free &&
                    state.selected == before_selected && state.fixed == before_fixed &&
                    state.template_ids == before_templates, "rollback failed");
            save(state, prefix + "-control" + std::to_string(mode) + "-rollback.txt");
            Plan damaged = plan;
            damaged.after[1] = damaged.after[0];
            require(!state.legal(damaged), "duplicate move accepted");
            require(state.lookahead == before_lookahead && state.pairs == before_pairs && state.score() == before_score &&
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
                          << ",\"unsupported\":" << state.lookahead.unsupported
                          << ",\"admissible\":" << state.lookahead.admissible
                          << ",\"base_score\":" << state.base_score()
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
                bool take = accept_score_move(static_cast<int>(state.missing.size()) + hole_change,
                                              change, temperature);
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
                  << ",\"raw_best_unsupported\":" << raw_best_state.lookahead.unsupported
                  << ",\"score_best_unsupported\":" << score_best_state.lookahead.unsupported
                  << ",\"lookahead_hits\":" << lookahead_hits
                  << ",\"lookahead_misses\":" << lookahead_misses
                  << ",\"lookahead_clears\":" << lookahead_clears
                  << ",\"lookahead_cache_size\":" << lookahead_cache.size()
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
