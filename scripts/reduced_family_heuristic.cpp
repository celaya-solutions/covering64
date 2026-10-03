// Document:    Joint Reduced Multiplicity-Seven Family Heuristic
// Version:     v1.2.1
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      5f368df446b7bf7c47bdad1f3a126342561278c7878949f622513e7ea47b03f1
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

// Bounded construction heuristic only. Family moves preserve local degree4
// and missing matching containment in G; outside moves preserve degrees6,7^12.
// Raw holes are counted exactly. Optional soft penalties guide, never forbid,
// intermediate states violating necessary full-cover conditions.

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Mask = unsigned;
using Family = std::array<Mask, 13>;
using Outside = std::array<Mask, 18>;
using Mapping = std::array<int, 13>;
struct Embedding { int kind; Mapping mapping; };
using HoleKey = std::array<Mask, 6>;
std::array<Family, 3> templates;
std::vector<Mapping> pg_automorphisms;
std::array<std::map<HoleKey, std::vector<Mapping>>, 2> reverse_trades;
std::array<std::vector<std::vector<Mask>>, 3> hole_targets;
const std::array<Mapping, 2> nearest_pg{{
    {0,1,2,3,5,4,8,6,7,11,9,10,12},
    {0,1,2,3,5,4,8,6,7,10,11,9,12}
}};
const std::array<std::pair<int, int>, 7> graph{{{0,1},{0,2},{3,4},{5,6},{7,8},{9,10},{11,12}}};
std::array<std::vector<int>, 8192> triples;
std::array<int, 8192> triple_rank;
std::vector<Mask> triple_masks;
std::vector<Mask> graph_masks;
std::mt19937_64 rng;

Family map_family(const Family& source, const Mapping& mapping);

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

void universe() {
    triple_rank.fill(-1);
    for (int a = 0; a < 13; ++a) for (int b = a + 1; b < 13; ++b)
        for (int c = b + 1; c < 13; ++c) {
            Mask mask = (1u << a) | (1u << b) | (1u << c);
            triple_rank[mask] = static_cast<int>(triple_masks.size());
            triple_masks.push_back(mask);
        }
    for (Mask mask = 0; mask < 8192; ++mask) {
        int size = __builtin_popcount(mask);
        if (size != 4 && size != 5) continue;
        for (int t = 0; t < 286; ++t)
            if ((mask & triple_masks[t]) == triple_masks[t]) triples[mask].push_back(t);
    }
    for (auto [a,b] : graph) graph_masks.push_back((1u << a) | (1u << b));
}

std::vector<Mask> read_masks(const std::string& path, int size, int points) {
    std::ifstream input(path);
    require(static_cast<bool>(input), "cannot open input");
    std::vector<Mask> masks;
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream row(line);
        Mask mask = 0; int point, count = 0;
        while (row >> point) {
            require(point >= 1 && point <= points && !(mask & (1u << (point - 1))),
                    "malformed point label");
            mask |= 1u << (point - 1); ++count;
        }
        require(row.eof() && count == size, "damaged block row");
        masks.push_back(mask);
    }
    require(std::set<Mask>(masks.begin(), masks.end()).size() == masks.size(), "duplicate block");
    return masks;
}

std::vector<Mask> family_holes(const Family& family, bool contained) {
    std::array<int, 13> degrees{};
    int pairs[13][13]{};
    require(std::set<Mask>(family.begin(), family.end()).size() == 13, "duplicate family block");
    for (Mask block : family) {
        require(block < 8192 && __builtin_popcount(block) == 4, "malformed family block");
        for (int a = 0; a < 13; ++a) if (block & (1u << a)) {
            ++degrees[a];
            for (int b = a + 1; b < 13; ++b) if (block & (1u << b)) ++pairs[a][b];
        }
    }
    require(std::all_of(degrees.begin(), degrees.end(), [](int x) { return x == 4; }),
            "family degree invariant failed");
    std::vector<Mask> holes; Mask used = 0;
    for (int a = 0; a < 13; ++a) for (int b = a + 1; b < 13; ++b) if (!pairs[a][b]) {
        Mask hole = (1u << a) | (1u << b);
        require(!(used & hole), "family holes not a matching"); used |= hole;
        if (contained) require(std::find(graph_masks.begin(), graph_masks.end(), hole) != graph_masks.end(),
                               "family hole outside G");
        holes.push_back(hole);
    }
    require(holes.size() == 0 || holes.size() == 4 || holes.size() == 6, "unknown template class");
    return holes;
}

struct State {
    std::array<Family, 3> families;
    std::array<Embedding, 3> embeddings;
    Outside outside;
    std::array<int, 286> counts{}, missing{}, position{};
    std::array<bool, 8192> selected{};
    int holes = 286;

    State(const std::array<Family, 3>& fs, const Outside& os,
          const std::array<Embedding, 3>& es) : families(fs), embeddings(es), outside(os) {
        std::iota(missing.begin(), missing.end(), 0);
        std::iota(position.begin(), position.end(), 0);
        for (const Family& family : families) for (Mask block : family) add(block);
        for (Mask block : outside) {
            require(block < 8192 && __builtin_popcount(block) == 5 && !selected[block],
                    "invalid or duplicate outside block");
            selected[block] = true; add(block);
        }
    }
    void add(Mask block) {
        for (int t : triples[block]) if (counts[t]++ == 0) {
            int at = position[t], moved = missing[--holes];
            missing[at] = moved; position[moved] = at; position[t] = -1;
        }
    }
    void remove(Mask block) {
        for (int t : triples[block]) if (--counts[t] == 0) {
            position[t] = holes; missing[holes++] = t;
        }
    }
    void replace_family(int slot, const Family& next, const Embedding& embedding) {
        for (Mask block : families[slot]) remove(block);
        families[slot] = next;
        embeddings[slot] = embedding;
        for (Mask block : families[slot]) add(block);
    }
    void swap_blocks(int a, int b, Mask x, Mask y) {
        selected[outside[a]] = selected[outside[b]] = false;
        remove(outside[a]); remove(outside[b]);
        outside[a] = x; outside[b] = y;
        selected[x] = selected[y] = true; add(x); add(y);
    }
    void audit() const {
        State rebuilt(families, outside, embeddings);
        require(rebuilt.counts == counts && rebuilt.selected == selected && rebuilt.holes == holes,
                "incremental coverage mismatch");
        for (int t = 0; t < 286; ++t) {
            require(counts[t] >= 0, "negative coverage");
            if (!counts[t]) require(position[t] >= 0 && position[t] < holes && missing[position[t]] == t,
                                     "missing-triple index mismatch");
            else require(position[t] == -1, "covered triple remains in missing index");
        }
        for (int slot = 0; slot < 3; ++slot) {
            family_holes(families[slot], true);
            const auto& embedding = embeddings[slot];
            require(embedding.kind >= 0 && embedding.kind < 3, "invalid template kind");
            auto sorted = embedding.mapping; std::sort(sorted.begin(), sorted.end());
            for (int p = 0; p < 13; ++p) require(sorted[p] == p, "embedding is not bijective");
            require(map_family(templates[embedding.kind], embedding.mapping) == families[slot],
                    "family embedding mismatch");
        }
        std::array<int, 13> degrees{};
        for (Mask block : outside) for (int p = 0; p < 13; ++p) if (block & (1u << p)) ++degrees[p];
        for (int p = 0; p < 13; ++p) require(degrees[p] == (p == 0 ? 6 : 7), "outside degree mismatch");
    }
};

Mask choose(Mask mask) {
    if (!mask) return 0;
    int n = static_cast<int>(rng() % __builtin_popcount(mask));
    while (n--) mask &= mask - 1;
    return mask & (~mask + 1);
}

struct Swap { int a, b; Mask x, y, old_x, old_y; };
bool propose_swap(const State& state, Swap& move, bool targeted) {
    move.a = static_cast<int>(rng() % 18);
    Mask outgoing = 0, incoming = 0;
    if (targeted && state.holes) {
        Mask hole = triple_masks[state.missing[rng() % state.holes]];
        std::array<int, 18> carriers{}; int count = 0;
        for (int i = 0; i < 18; ++i) if (__builtin_popcount(state.outside[i] & hole) == 2)
            carriers[count++] = i;
        if (!count) return false;
        move.a = carriers[rng() % count];
        incoming = hole & ~state.outside[move.a];
        outgoing = choose(state.outside[move.a] & ~hole);
    }
    move.b = static_cast<int>(rng() % 17); if (move.b >= move.a) ++move.b;
    move.old_x = state.outside[move.a]; move.old_y = state.outside[move.b];
    if (outgoing && ((move.old_y & outgoing) || !(move.old_y & incoming))) return false;
    if (!outgoing) outgoing = choose(move.old_x & ~move.old_y);
    if (!incoming) incoming = choose(move.old_y & ~move.old_x);
    if (!outgoing || !incoming) return false;
    move.x = move.old_x ^ outgoing ^ incoming; move.y = move.old_y ^ outgoing ^ incoming;
    return move.x != move.y && !state.selected[move.x] && !state.selected[move.y];
}

Family map_family(const Family& source, const Mapping& mapping) {
    Family result{};
    for (int i = 0; i < 13; ++i) for (int p = 0; p < 13; ++p)
        if (source[i] & (1u << p)) result[i] |= 1u << mapping[p];
    std::sort(result.begin(), result.end());
    return result;
}

Mapping compose(const Mapping& outer, const Mapping& inner) {
    Mapping result{};
    for (int p = 0; p < 13; ++p) result[p] = outer[inner[p]];
    return result;
}

Mapping inverse(const Mapping& mapping) {
    Mapping result{};
    for (int p = 0; p < 13; ++p) result[mapping[p]] = p;
    return result;
}

std::vector<Mapping> isomorphisms(const Family& source, const Family& target, bool all) {
    std::array<std::array<int, 13>, 13> source_pairs{}, target_pairs{};
    auto pairs = [](const Family& family, auto& counts) {
        for (Mask block : family) for (int p = 0; p < 13; ++p) if (block & (1u << p))
            for (int q = 0; q < 13; ++q) if (block & (1u << q)) ++counts[p][q];
    };
    pairs(source, source_pairs); pairs(target, target_pairs);
    auto source_signatures = source_pairs, target_signatures = target_pairs;
    for (auto& signature : source_signatures) std::sort(signature.begin(), signature.end());
    for (auto& signature : target_signatures) std::sort(signature.begin(), signature.end());
    std::array<bool, 8192> contained{};
    for (Mask block : target) {
        Mask subset = block;
        do { contained[subset] = true; subset = (subset - 1) & block; } while (subset);
    }
    contained[0] = true;
    Mapping mapping; mapping.fill(-1);
    std::vector<Mapping> result;
    std::function<bool(int, Mask)> visit = [&](int mapped, Mask used) {
        if (mapped == 13) {
            require(map_family(source, mapping) == target, "isomorphism leaf mismatch");
            result.push_back(mapping); return !all;
        }
        int point = -1; std::vector<int> choices;
        for (int p = 0; p < 13; ++p) if (mapping[p] < 0) {
            std::vector<int> candidates;
            for (int q = 0; q < 13; ++q) if (!(used & (1u << q)) &&
                    source_signatures[p] == target_signatures[q]) {
                bool valid = true;
                for (int r = 0; r < 13 && valid; ++r) if (mapping[r] >= 0)
                    valid = source_pairs[p][r] == target_pairs[q][mapping[r]];
                if (!valid) continue;
                for (Mask block : source) if (block & (1u << p)) {
                    Mask partial = 1u << q;
                    for (int r = 0; r < 13; ++r) if ((block & (1u << r)) && mapping[r] >= 0)
                        partial |= 1u << mapping[r];
                    if (!contained[partial]) { valid = false; break; }
                }
                if (valid) candidates.push_back(q);
            }
            if (candidates.empty()) return false;
            if (point < 0 || candidates.size() < choices.size()) {
                point = p; choices = std::move(candidates);
            }
        }
        for (int q : choices) {
            mapping[point] = q;
            if (visit(mapped + 1, used | (1u << q))) return true;
            mapping[point] = -1;
        }
        return false;
    };
    visit(0, 0); return result;
}

HoleKey hole_key(const std::vector<Mask>& holes) {
    HoleKey result{}; std::copy(holes.begin(), holes.end(), result.begin());
    std::sort(result.begin(), result.end()); return result;
}

void prepare_trades() {
    for (int kind = 0; kind < 3; ++kind) {
        auto holes = family_holes(templates[kind], false);
        for (int subset = 0; subset < 128; ++subset) if (__builtin_popcount(static_cast<unsigned>(subset)) ==
                                                        static_cast<int>(holes.size())) {
            Mask used = 0; bool valid = true; std::vector<Mask> edges;
            for (int i = 0; i < 7; ++i) if (subset & (1 << i)) {
                if (used & graph_masks[i]) valid = false;
                used |= graph_masks[i]; edges.push_back(graph_masks[i]);
            }
            if (valid) hole_targets[kind].push_back(edges);
        }
    }
    pg_automorphisms = isomorphisms(templates[0], templates[0], true);
    require(pg_automorphisms.size() == 5616, "wrong PG automorphism count");
    for (int kind = 1; kind < 3; ++kind) {
        auto near = map_family(templates[0], nearest_pg[kind - 1]);
        int shared = 0;
        for (Mask block : near) shared += std::binary_search(templates[kind].begin(), templates[kind].end(), block);
        require(shared == (kind == 1 ? 9 : 7), "saved PG trade map mismatch");
        Mapping back = inverse(nearest_pg[kind - 1]);
        for (const Mapping& automorphism : pg_automorphisms) {
            Mapping embedding = compose(automorphism, back);
            auto holes = family_holes(map_family(templates[kind], embedding), false);
            reverse_trades[kind - 1][hole_key(holes)].push_back(embedding);
        }
    }
}

std::vector<int> members(Mask mask) {
    std::vector<int> result;
    for (int p = 0; p < 13; ++p) if (mask & (1u << p)) result.push_back(p);
    return result;
}

Family resample(int kind, Embedding& embedding) {
    auto holes = family_holes(templates[kind], false);
    auto target = hole_targets[kind][rng() % hole_targets[kind].size()];
    std::shuffle(target.begin(), target.end(), rng);
    Mapping mapping; mapping.fill(-1);
    Mask source_used = 0, target_used = 0;
    for (std::size_t i = 0; i < holes.size(); ++i) {
        auto a = members(holes[i]), b = members(target[i]);
        if (rng() & 1) std::swap(b[0], b[1]);
        mapping[a[0]] = b[0]; mapping[a[1]] = b[1];
        source_used |= holes[i]; target_used |= target[i];
    }
    auto a = members(8191u & ~source_used), b = members(8191u & ~target_used);
    std::shuffle(b.begin(), b.end(), rng);
    for (std::size_t i = 0; i < a.size(); ++i) mapping[a[i]] = b[i];
    embedding = {kind, mapping};
    return map_family(templates[kind], mapping);
}

bool permute_family(const Family& source, Family& result, Mapping& mapping) {
    auto holes = family_holes(source, true);
    std::iota(mapping.begin(), mapping.end(), 0);
    if (holes.size() >= 2 && rng() % 3 == 0) {
        int a = static_cast<int>(rng() % holes.size()), b;
        do { b = static_cast<int>(rng() % holes.size()); } while (b == a);
        auto x = members(holes[a]), y = members(holes[b]);
        if (rng() & 1) std::swap(y[0], y[1]);
        std::swap(mapping[x[0]], mapping[y[0]]); std::swap(mapping[x[1]], mapping[y[1]]);
    } else {
        int a = static_cast<int>(rng() % 13), b = static_cast<int>(rng() % 12);
        if (b >= a) ++b; std::swap(mapping[a], mapping[b]);
    }
    for (Mask hole : holes) {
        auto x = members(hole); Mask image = (1u << mapping[x[0]]) | (1u << mapping[x[1]]);
        if (std::find(graph_masks.begin(), graph_masks.end(), image) == graph_masks.end()) return false;
    }
    result = map_family(source, mapping);
    return result != source;
}

bool trade_family(const Embedding& current, Family& result, Embedding& next) {
    if (current.kind) {
        next = {0, compose(current.mapping, nearest_pg[current.kind - 1])};
    } else {
        // Look up all PG automorphisms whose trade holes map into G. This keeps
        // rare compatible trades accessible without rejection-sampling all5616.
        Mapping back = inverse(current.mapping), selected{};
        std::size_t total = 0; int selected_kind = -1;
        for (int kind = 1; kind < 3; ++kind) for (const auto& target : hole_targets[kind]) {
            std::vector<Mask> preimage;
            for (Mask edge : target) {
                auto points = members(edge);
                preimage.push_back((1u << back[points[0]]) | (1u << back[points[1]]));
            }
            auto found = reverse_trades[kind - 1].find(hole_key(preimage));
            if (found == reverse_trades[kind - 1].end()) continue;
            const auto& embeddings = found->second;
            total += embeddings.size();
            if (rng() % total < embeddings.size()) {
                selected = embeddings[rng() % embeddings.size()]; selected_kind = kind;
            }
        }
        if (selected_kind < 0) return false;
        next = {selected_kind, compose(current.mapping, selected)};
    }
    result = map_family(templates[next.kind], next.mapping);
    return true;
}

using Signature = std::array<Mask, 57>;
Signature signature(const State& state) {
    Signature result{}; int at = 0;
    for (int slot = 0; slot < 3; ++slot) for (Mask block : state.families[slot])
        result[at++] = (block << 3) | (1u << slot);
    for (Mask block : state.outside) result[at++] = block << 3;
    std::sort(result.begin(), result.end()); return result;
}

int distance(const Signature& a, const Signature& b) {
    int shared = 0; std::size_t x = 0, y = 0;
    while (x < a.size() && y < b.size()) {
        if (a[x] < b[y]) ++x;
        else if (b[y] < a[x]) ++y;
        else { ++shared; ++x; ++y; }
    }
    return 57 - shared;
}

std::array<int, 13> pair_row_bounds(const State& state) {
    std::array<bool, 286> covered{};
    for (const Family& family : state.families) for (Mask block : family)
        for (int t : triples[block]) covered[t] = true;
    int needed[13][13]{};
    for (int t = 0; t < 286; ++t) if (!covered[t]) {
        Mask mask = triple_masks[t]; int a = __builtin_ctz(mask); mask &= mask - 1;
        int b = __builtin_ctz(mask); mask &= mask - 1; int c = __builtin_ctz(mask);
        ++needed[a][b]; ++needed[a][c]; ++needed[b][c];
    }
    std::array<int, 13> result{};
    for (int a = 0; a < 13; ++a) for (int b = a + 1; b < 13; ++b) {
        int lower = (needed[a][b] + 2) / 3;
        result[a] += lower; result[b] += lower;
    }
    return result;
}

int row_overflow(const std::array<int, 13>& rows) {
    int result = 0;
    for (int p = 0; p < 13; ++p) result += std::max(0, rows[p] - (p == 0 ? 24 : 28));
    return result;
}

struct Profile {
    int n6 = 0, n7 = 1, above7 = 0, excess = 0, maximum = 7;
    bool disjoint_five = false, forbidden_five = false;
    int overflow() const { return std::max(0, 3 * n6 + 4 * n7 - 16); }
    int penalty() const { return overflow() + 5 * excess + static_cast<int>(forbidden_five); }
    bool qualifies() const { return penalty() == 0; }
};

Profile profile(const State& state) {
    Profile result; std::vector<Mask> heavy;
    for (int t = 0; t < 286; ++t) {
        int count = state.counts[t];
        result.n6 += count == 6; result.n7 += count == 7; result.above7 += count > 7;
        result.excess += std::max(0, count - 7); result.maximum = std::max(result.maximum, count);
        if (count >= 6) heavy.push_back(triple_masks[t]);
    }
    // The fixed heavy triple123 is disjoint from every outside triple. Thus
    // four disjoint heavy outside triples give five disjoint heavy triples.
    for (std::size_t a = 0; a < heavy.size(); ++a)
        for (std::size_t b = a + 1; b < heavy.size(); ++b) if (!(heavy[a] & heavy[b]))
            for (std::size_t c = b + 1; c < heavy.size(); ++c) if (!((heavy[a] | heavy[b]) & heavy[c]))
                for (std::size_t d = c + 1; d < heavy.size(); ++d)
                    if (!((heavy[a] | heavy[b] | heavy[c]) & heavy[d])) {
                        result.disjoint_five = true;
                        // The audited five-heavy exclusion needs at least two
                        // sevenfold triples. One is the fixed triple123.
                        if (state.counts[triple_rank[heavy[a]]] >= 7 ||
                            state.counts[triple_rank[heavy[b]]] >= 7 ||
                            state.counts[triple_rank[heavy[c]]] >= 7 ||
                            state.counts[triple_rank[heavy[d]]] >= 7) {
                            result.forbidden_five = true; return result;
                        }
                    }
    return result;
}

struct Evaluation {
    Profile heavy;
    int family_overflow;
    double score;
    bool qualifies() const { return heavy.qualifies() && family_overflow == 0; }
};

Evaluation evaluate(const State& state, double heavy_weight, double family_weight, int known_rows = -1) {
    Profile heavy = profile(state);
    int rows = known_rows < 0 ? row_overflow(pair_row_bounds(state)) : known_rows;
    return {heavy, rows, state.holes + heavy_weight * heavy.penalty() + family_weight * rows};
}

void log_evaluation(const Evaluation& value) {
    std::cout << ",\"score\":" << value.score << ",\"n6\":" << value.heavy.n6
              << ",\"n7\":" << value.heavy.n7 << ",\"triples_above7\":" << value.heavy.above7
              << ",\"max_triple_multiplicity\":" << value.heavy.maximum
              << ",\"heavy_count_overflow\":" << value.heavy.overflow()
              << ",\"disjoint_five_heavy\":" << (value.heavy.disjoint_five ? "true" : "false")
              << ",\"forbidden_five_heavy\":" << (value.heavy.forbidden_five ? "true" : "false")
              << ",\"heavy_penalty\":" << value.heavy.penalty()
              << ",\"passes_heavy_filters\":" << (value.heavy.qualifies() ? "true" : "false")
              << ",\"passes_scored_filters\":" << (value.qualifies() ? "true" : "false");
}

void log_hub_diagnostics(const State& state) {
    std::vector<Mask> blocks;
    for (Mask edge : graph_masks) blocks.push_back((edge << 3) | 7u);
    for (Mask block : signature(state)) blocks.push_back(block);
    std::vector<Mask> sevenfold{7u};
    for (int t = 0; t < 286; ++t) if (state.counts[t] == 7) sevenfold.push_back(triple_masks[t] << 3);
    std::array<int, 16> hubs{}; int invalid = 0;
    for (Mask triple : sevenfold) {
        std::array<int, 16> degrees{};
        for (Mask block : blocks) if ((block & triple) == triple)
            for (int p = 0; p < 16; ++p) if ((block & ~triple) & (1u << p)) ++degrees[p];
        int hub = -1; bool valid = true;
        for (int p = 0; p < 16; ++p) if (!(triple & (1u << p))) {
            if (degrees[p] == 2 && hub < 0) hub = p;
            else if (degrees[p] != 1) valid = false;
        }
        if (valid && hub >= 0) ++hubs[hub]; else ++invalid;
    }
    int repeated = 0;
    for (int n : hubs) repeated += std::max(0, n - 1);
    std::cout << ",\"mu7_hub_diagnostics\":{\"invalid_link_graphs\":" << invalid
              << ",\"repeated_hubs\":" << repeated << ",\"hub_counts_by_point\":[";
    for (int p = 0; p < 16; ++p) std::cout << (p ? "," : "") << hubs[p];
    std::cout << "]}";
}

void log_pair_row_bounds(const State& state) {
    auto lower = pair_row_bounds(state); int overflow = 0;
    std::cout << ",\"family_pair_row_bounds\":[";
    for (int p = 0; p < 13; ++p) {
        std::cout << (p ? "," : "") << lower[p];
        overflow += std::max(0, lower[p] - (p == 0 ? 24 : 28));
    }
    std::cout << "],\"family_pair_row_overflow\":" << overflow;
}

int main(int argc, char** argv) {
    require(argc >= 8 && argc <= 10,
            "usage: reduced_family_heuristic SEED PG R4 R6 RNG SECONDS PREFIX [HEAVY_WEIGHT [FAMILY_WEIGHT]]");
    universe();
    std::array<Family, 3> families{}; std::array<int, 3> sizes{};
    for (int i = 0; i < 3; ++i) {
        auto data = read_masks(argv[i + 2], 4, 13);
        require(data.size() == 13, "template needs13 blocks");
        std::copy(data.begin(), data.end(), templates[i].begin());
        std::sort(templates[i].begin(), templates[i].end());
        require(family_holes(templates[i], false).size() == static_cast<std::size_t>(i == 0 ? 0 : i == 1 ? 4 : 6),
                "wrong template class");
    }
    auto data = read_masks(argv[1], 5, 16); require(data.size() == 64, "seed needs64 blocks");
    Outside outside{}; int outside_size = 0; std::set<Mask> heavy;
    for (Mask block : data) {
        Mask anchors = block & 7u;
        if (!anchors) { require(outside_size < 18, "too many outside blocks"); outside[outside_size++] = block >> 3; }
        else if (__builtin_popcount(anchors) == 1) {
            int slot = __builtin_ctz(anchors); require(sizes[slot] < 13, "too many local blocks");
            families[slot][sizes[slot]++] = block >> 3;
        } else { require(anchors == 7, "two-anchor block"); heavy.insert(block >> 3); }
    }
    require(outside_size == 18 && sizes == std::array<int,3>{13,13,13}, "wrong seed split");
    require(heavy == std::set<Mask>(graph_masks.begin(), graph_masks.end()), "wrong normalized seven blocks");
    for (Family& family : families) std::sort(family.begin(), family.end());
    prepare_trades();
    std::array<Embedding, 3> embeddings;
    for (int slot = 0; slot < 3; ++slot) {
        std::size_t count = family_holes(families[slot], true).size();
        int kind = count == 0 ? 0 : count == 4 ? 1 : 2;
        auto maps = isomorphisms(templates[kind], families[slot], false);
        require(!maps.empty(), "seed family does not match its template");
        embeddings[slot] = {kind, maps.front()};
    }
    State state(families, outside, embeddings); state.audit(); State best = state;
    std::uint64_t seed = std::stoull(argv[5]); rng.seed(seed);
    double budget = std::stod(argv[6]); require(budget > 0 && std::isfinite(budget), "bad budget");
    double heavy_weight = argc >= 9 ? std::stod(argv[8]) : 0;
    double family_weight = argc >= 10 ? std::stod(argv[9]) : 0;
    require(std::isfinite(heavy_weight) && heavy_weight >= 0 &&
            std::isfinite(family_weight) && family_weight >= 0, "bad penalty weight");
    Evaluation evaluation = evaluate(state, heavy_weight, family_weight), best_evaluation = evaluation;
    State score_best = state;
    int best_heavy_holes = evaluation.heavy.qualifies() ? state.holes : 287;
    int best_qualifying_holes = evaluation.qualifies() ? state.holes : 287;
    std::string prefix = argv[7];
    auto start = std::chrono::steady_clock::now();
    auto elapsed = [&]() { return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count(); };
    std::uint64_t proposals = 0, repair_proposals = 0, repair_accepted = 0, restarts = 0;
    std::array<std::uint64_t, 4> applied{}, accepted{};
    std::array<std::uint64_t, 2> trades{};
    std::array<bool, 4> controls{}, rollbacks{};
    struct Entry { State state; Signature blocks; double score; };
    std::vector<Entry> reservoir{{state, signature(state), evaluation.score}};
    std::array<int, 287> diverse_saved{};
    int diversity_count = 0;
    double next_progress = 45;
    int serial = 0, improvements = 0, rollback_audits = 0;
    std::string best_path, best_heavy_path, best_qualifying_path, best_score_path;
    auto save = [&](const State& current, const std::string& role, int mode) {
        current.audit();
        std::vector<std::vector<int>> blocks;
        for (int i = 0; i < 7; ++i) blocks.push_back({1,2,3});
        for (int i = 0; i < 7; ++i) for (int p : members(graph_masks[i])) blocks[i].push_back(p + 4);
        for (int anchor = 0; anchor < 3; ++anchor) for (Mask block : current.families[anchor]) {
            std::vector<int> row{anchor + 1}; for (int p : members(block)) row.push_back(p + 4); blocks.push_back(row);
        }
        for (Mask block : current.outside) {
            std::vector<int> row; for (int p : members(block)) row.push_back(p + 4); blocks.push_back(row);
        }
        std::sort(blocks.begin(), blocks.end());
        std::string path = prefix + "-" + role + "-" + std::to_string(serial++) + "-h" + std::to_string(current.holes) + ".txt";
        std::ofstream output(path); require(static_cast<bool>(output), "cannot save snapshot");
        for (const auto& row : blocks) for (std::size_t i = 0; i < row.size(); ++i) output << row[i] << (i + 1 == row.size() ? '\n' : ' ');
        output.close();
        std::cout << "{\"event\":\"snapshot\",\"role\":\"" << role << "\",\"mode\":" << mode
                  << ",\"holes\":" << current.holes << ",\"proposals\":" << proposals
                  << ",\"seconds\":" << elapsed() << ",\"path\":\"" << path << "\"";
        log_pair_row_bounds(current);
        log_evaluation(evaluate(current, heavy_weight, family_weight));
        log_hub_diagnostics(current);
        std::cout << "}\n" << std::flush;
        return path;
    };
    best_path = save(state, "initial", -1);
    best_score_path = best_path;
    if (evaluation.heavy.qualifies()) best_heavy_path = best_path;
    if (evaluation.qualifies()) best_qualifying_path = best_path;
    while (elapsed() < budget && best.holes > 0) {
        if (elapsed() >= next_progress) {
            std::cout << "{\"event\":\"progress\",\"seconds\":" << elapsed()
                      << ",\"proposals\":" << proposals << ",\"best_holes\":" << best.holes
                      << ",\"current_holes\":" << state.holes << ",\"diverse_saved\":" << diversity_count
                      << ",\"best_score\":" << best_evaluation.score
                      << ",\"best_heavy_qualifying_holes\":" << (best_heavy_holes < 287 ? best_heavy_holes : -1)
                      << ",\"best_qualifying_holes\":" << (best_qualifying_holes < 287 ? best_qualifying_holes : -1)
                      << ",\"reservoir_size\":" << reservoir.size() << ",\"restarts\":" << restarts
                      << ",\"applied_by_mode\":[" << applied[0] << ',' << applied[1] << ',' << applied[2]
                      << ',' << applied[3] << "],\"accepted_by_mode\":[" << accepted[0] << ',' << accepted[1]
                      << ',' << accepted[2] << ',' << accepted[3] << ']';
            log_pair_row_bounds(state);
            log_evaluation(evaluation);
            log_hub_diagnostics(state);
            std::cout << "}\n" << std::flush;
            next_progress += 45;
        }
        ++proposals;
        if (proposals % 1'000'000 == 0) {
            state = (rng() & 1) ? score_best : reservoir[rng() % reservoir.size()].state;
            evaluation = evaluate(state, heavy_weight, family_weight);
            ++restarts;
        }
        int roll = static_cast<int>(rng() % 100), mode = roll < 65 ? 0 : roll < 85 ? 1 : roll < 90 ? 2 : 3;
        int slot = static_cast<int>(rng() % 3);
        Swap swap{}; Family next{}, previous = state.families[slot];
        Embedding next_embedding = state.embeddings[slot]; Mapping permutation{};
        if (mode == 0 && !propose_swap(state, swap, rng() % 5 != 0)) continue;
        if (mode == 1) {
            if (!permute_family(previous, next, permutation)) continue;
            next_embedding.mapping = compose(permutation, next_embedding.mapping);
        }
        if (mode == 2) next = resample(static_cast<int>(rng() % 3), next_embedding);
        if (mode == 3 && !trade_family(state.embeddings[slot], next, next_embedding)) continue;
        bool control = !controls[mode];
        if (control) save(state, "control_before", mode);
        State backup = state;
        Evaluation before_evaluation = evaluation;
        if (mode == 0) state.swap_blocks(swap.a, swap.b, swap.x, swap.y);
        else state.replace_family(slot, next, next_embedding);
        if (mode == 3) {
            int kind = std::max(backup.embeddings[slot].kind, next_embedding.kind);
            ++trades[kind - 1];
        }
        if (mode >= 2) for (int trial = 0; trial < 64 && state.holes; ++trial) {
            ++repair_proposals; Swap repair{};
            if (!propose_swap(state, repair, true)) continue;
            int before = state.holes;
            state.swap_blocks(repair.a, repair.b, repair.x, repair.y);
            if (state.holes <= before) ++repair_accepted;
            else state.swap_blocks(repair.a, repair.b, repair.old_x, repair.old_y);
        }
        ++applied[mode];
        if (control) { save(state, "control_after", mode); controls[mode] = true; }
        evaluation = evaluate(state, heavy_weight, family_weight,
                              mode == 0 ? before_evaluation.family_overflow : -1);
        double cooling = static_cast<double>(proposals % 200'000) / 200'000;
        double temperature = 0.15 + 3.5 * std::pow(1.0 - cooling, 2);
        double delta = evaluation.score - before_evaluation.score;
        bool keep = state.holes == 0 || delta <= 0 ||
                    std::generate_canonical<double, 53>(rng) < std::exp(-delta / temperature);
        // Preserve every new candidate record even when annealing rejects it.
        bool raw_improved = state.holes < best.holes;
        bool heavy_improved = evaluation.heavy.qualifies() && state.holes < best_heavy_holes;
        bool qualified_improved = evaluation.qualifies() && state.holes < best_qualifying_holes;
        bool score_improved = evaluation.score < best_evaluation.score;
        if (raw_improved || heavy_improved || qualified_improved || score_improved) {
            std::string role = raw_improved ? "improvement" : qualified_improved ? "qualifying_improvement" :
                               heavy_improved ? "heavy_qualifying_improvement" : "score_improvement";
            std::string path = save(state, role, mode);
            if (raw_improved) { best = state; ++improvements; best_path = path; }
            if (heavy_improved) { best_heavy_holes = state.holes; best_heavy_path = path; }
            if (qualified_improved) { best_qualifying_holes = state.holes; best_qualifying_path = path; }
            if (score_improved) { score_best = state; best_evaluation = evaluation; best_score_path = path; }
        }
        if (keep) {
            ++accepted[mode];
            if (score_improved) {
                reservoir.erase(std::remove_if(reservoir.begin(), reservoir.end(), [&](const Entry& entry) {
                    return entry.score > best_evaluation.score + 1;
                }), reservoir.end());
                if (reservoir.size() == 32) reservoir.erase(reservoir.begin());
                reservoir.push_back({state, signature(state), evaluation.score});
            } else if (evaluation.score <= best_evaluation.score + 1 && diverse_saved[state.holes] < 8) {
                Signature blocks = signature(state);
                bool different = std::all_of(reservoir.begin(), reservoir.end(), [&](const Entry& entry) {
                    return distance(blocks, entry.blocks) >= 4;
                });
                if (different) {
                    if (reservoir.size() == 32) reservoir.erase(reservoir.begin());
                    reservoir.push_back({state, blocks, evaluation.score});
                    ++diverse_saved[state.holes]; ++diversity_count;
                    save(state, "diverse", mode);
                }
            }
        } else {
            state = backup; evaluation = before_evaluation;
            if (!rollbacks[mode]) { state.audit(); rollbacks[mode] = true; ++rollback_audits; }
        }
        if (proposals % 100'000 == 0) state.audit();
    }
    state.audit(); best.audit(); save(state, "final", -1);
    std::cout << "{\"event\":\"finish\",\"seed\":" << seed << ",\"budget_seconds\":" << budget
              << ",\"seconds\":" << elapsed() << ",\"proposals\":" << proposals
              << ",\"best_holes\":" << best.holes << ",\"best_path\":\"" << best_path
              << "\",\"best_score\":" << best_evaluation.score << ",\"best_score_path\":\"" << best_score_path
              << "\",\"best_heavy_qualifying_holes\":" << (best_heavy_holes < 287 ? best_heavy_holes : -1)
              << ",\"best_heavy_qualifying_path\":\"" << best_heavy_path
              << "\",\"best_qualifying_holes\":" << (best_qualifying_holes < 287 ? best_qualifying_holes : -1)
              << ",\"best_qualifying_path\":\"" << best_qualifying_path
              << "\",\"heavy_penalty_weight\":" << heavy_weight << ",\"family_penalty_weight\":" << family_weight
              << ",\"improvements\":" << improvements << ",\"restarts\":" << restarts
              << ",\"repair_proposals\":" << repair_proposals << ",\"repair_accepted\":" << repair_accepted
              << ",\"rollback_audits\":" << rollback_audits << ",\"pg_automorphisms\":" << pg_automorphisms.size()
              << ",\"diverse_saved\":" << diversity_count << ",\"reservoir_size\":" << reservoir.size()
              << ",\"trades_by_size\":[" << trades[0] << ',' << trades[1] << "],\"applied_by_mode\":["
              << applied[0] << ',' << applied[1] << ',' << applied[2] << ',' << applied[3]
              << "],\"accepted_by_mode\":[" << accepted[0] << ',' << accepted[1] << ',' << accepted[2]
              << ',' << accepted[3] << "],\"status\":\""
              << (best.holes ? "INCONCLUSIVE" : "COVER_FOUND") << "\"}\n" << std::flush;
}
