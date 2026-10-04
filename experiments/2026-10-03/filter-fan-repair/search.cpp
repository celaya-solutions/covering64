// Document:    Unrestricted Filter-and-Fan Covering Repair Prototype
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      d6a1873ef3caf35f8a41a0d005967814bbf1cf7a4b64cc415ffb21dfeaafc881
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <bitset>
#include <charconv>
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
#include <tuple>
#include <vector>

namespace {
constexpr int NB = 4368, NT = 560, SIZE = 64;
using Clock = std::chrono::steady_clock;
using Weights = std::array<int, NT>;
struct Block { unsigned mask; std::array<int, 10> triples; };
std::vector<Block> blocks;
std::vector<unsigned> triples;
std::array<std::vector<int>, NT> containing;
std::array<int, 65536> bymask, tripleid;
volatile std::sig_atomic_t stopped = 0;
void interrupt(int) { stopped = 1; }
void require(bool value, const std::string &why) {
    if (!value) throw std::runtime_error(why);
}
uint64_t integer(const std::string &s) {
    uint64_t n = 0;
    auto p = std::from_chars(s.data(), s.data() + s.size(), n);
    require(p.ec == std::errc{} && p.ptr == s.data() + s.size(), "invalid integer");
    return n;
}
void universe() {
    bymask.fill(-1); tripleid.fill(-1);
    for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
    for (int c = b + 1; c < 16; ++c) {
        unsigned m = (1u << a) | (1u << b) | (1u << c);
        tripleid[m] = static_cast<int>(triples.size()); triples.push_back(m);
    }
    for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
    for (int c = b + 1; c < 16; ++c) for (int d = c + 1; d < 16; ++d)
    for (int e = d + 1; e < 16; ++e) {
        Block block{};
        block.mask = (1u << a) | (1u << b) | (1u << c) | (1u << d) | (1u << e);
        int j = 0, id = static_cast<int>(blocks.size());
        for (int t = 0; t < NT; ++t)
            if ((triples[t] & block.mask) == triples[t]) {
                block.triples[j++] = t; containing[t].push_back(id);
            }
        require(j == 10, "block triple count");
        bymask[block.mask] = id; blocks.push_back(block);
    }
    require(blocks.size() == NB && triples.size() == NT, "universe dimensions");
    for (const auto &row : containing) require(row.size() == 78, "triple incidence");
}
struct Move { int slot, old, incoming; };
struct State {
    std::array<int, SIZE> ids{};
    std::array<int, NT> counts{};
    std::bitset<NB> selected;
    int deficit = NT;
    explicit State(const std::array<int, SIZE> &start) : ids(start) {
        for (int id : ids) {
            require(id >= 0 && id < NB && !selected[id], "invalid or duplicate block ID");
            selected[id] = true;
            for (int t : blocks[id].triples) if (counts[t]++ == 0) --deficit;
        }
    }
    void audit() const {
        State recount(ids);
        require(counts == recount.counts && selected == recount.selected &&
                deficit == recount.deficit, "incremental state differs from recount");
    }
    int energy(const Weights &weights) const {
        int score = 0;
        for (int t = 0; t < NT; ++t) if (!counts[t]) score += weights[t];
        return score;
    }
    void apply(Move move) {
        require(move.slot >= 0 && move.slot < SIZE && move.incoming >= 0 &&
                move.incoming < NB, "move range");
        require(ids[move.slot] == move.old && !selected[move.incoming],
                "stale outgoing block or duplicate incoming block");
        selected[move.old] = false; selected[move.incoming] = true;
        ids[move.slot] = move.incoming;
        for (int t : blocks[move.old].triples) if (--counts[t] == 0) ++deficit;
        for (int t : blocks[move.incoming].triples) if (counts[t]++ == 0) --deficit;
    }
    bool same(const State &other) const {
        return ids == other.ids && counts == other.counts &&
               selected == other.selected && deficit == other.deficit;
    }
};
std::array<int, SIZE> read_seed(const std::string &path) {
    std::ifstream stream(path); require(bool(stream), "cannot read seed");
    std::vector<int> ids; std::string line;
    while (std::getline(stream, line)) {
        line = line.substr(0, line.find('#'));
        std::istringstream row(line); std::string word; unsigned mask = 0; int n = 0;
        while (row >> word) {
            auto point = integer(word);
            require(point >= 1 && point <= 16, "point label range");
            unsigned bit = 1u << (point - 1);
            require(!(mask & bit), "duplicate point"); mask |= bit; ++n;
        }
        if (!n) continue;
        require(n == 5 && bymask[mask] >= 0, "block size"); ids.push_back(bymask[mask]);
    }
    require(ids.size() == SIZE, "seed needs exactly 64 blocks");
    std::sort(ids.begin(), ids.end());
    require(std::adjacent_find(ids.begin(), ids.end()) == ids.end(), "duplicate seed block");
    std::array<int, SIZE> result{}; std::copy(ids.begin(), ids.end(), result.begin());
    return result;
}
void save_blocks(const std::string &path, const State &state) {
    auto ids = state.ids; std::sort(ids.begin(), ids.end());
    std::ofstream stream(path); require(bool(stream), "cannot open block output");
    for (int id : ids) {
        bool first = true;
        for (int p = 0; p < 16; ++p) if (blocks[id].mask & (1u << p)) {
            if (!first) stream << ' ';
            stream << p + 1; first = false;
        }
        stream << '\n';
    }
    require(bool(stream), "cannot write blocks");
}
std::pair<int, int> delta(const State &state, Move move, const Weights &weights) {
    int raw = 0, weighted = 0;
    for (int t : blocks[move.old].triples)
        if (state.counts[t] == 1 &&
            (triples[t] & blocks[move.incoming].mask) != triples[t]) {
            ++raw; weighted += weights[t];
        }
    for (int t : blocks[move.incoming].triples)
        if (state.counts[t] == 0) { --raw; weighted -= weights[t]; }
    return {raw, weighted};
}
template<class T> void array_json(std::ostream &out, const T &values) {
    out << '['; bool first = true;
    for (auto value : values) { if (!first) out << ','; out << value; first = false; }
    out << ']';
}
void trace(std::ostream &out, const State &start, const std::vector<Move> &moves,
           const Weights &weights, const std::string &kind) {
    State state = start;
    out << "{\"kind\":\"" << kind << "\",\"start_ids\":"; array_json(out, start.ids);
    out << ",\"weights\":"; array_json(out, weights); out << ",\"moves\":[";
    bool first = true;
    for (Move move : moves) {
        if (!first) out << ',';
        first = false;
        int before = state.deficit, score = state.energy(weights);
        state.apply(move); state.audit();
        out << "{\"slot\":" << move.slot << ",\"old\":" << move.old
            << ",\"incoming\":" << move.incoming << ",\"before\":" << before
            << ",\"after\":" << state.deficit << ",\"energy_before\":" << score
            << ",\"energy_after\":" << state.energy(weights) << '}';
    }
    out << "],\"end_ids\":"; array_json(out, state.ids);
    out << ",\"end_counts\":"; array_json(out, state.counts);
    out << ",\"deficit\":" << state.deficit;
    for (auto it = moves.rbegin(); it != moves.rend(); ++it) {
        state.apply({it->slot, it->incoming, it->old}); state.audit();
    }
    require(state.same(start), "full-prefix rollback failed");
    out << ",\"rollback_exact\":true}\n";
    require(bool(out), "cannot write trace");
}
struct Node {
    State state;
    std::vector<Move> path;
    std::bitset<NT> frontier;
    int score, history = 0;
    uint64_t tie = 0;
    Node(const State &s, const Weights &weights) : state(s), score(s.energy(weights)) {}
};
struct Choice {
    Move move;
    int score, deficit, history, frontier_hits;
    uint64_t tie;
    auto rank() const { return std::make_tuple(score, deficit, history, -frontier_hits, tie); }
};
struct Stats { uint64_t proposals = 0, retained = 0, trees = 0; int depth = 0; };
bool expired(Clock::time_point deadline) { return stopped || Clock::now() >= deadline; }
std::vector<Choice> fan(const Node &node, const Weights &weights, int count,
                        std::mt19937_64 &rng, Clock::time_point deadline, Stats &stats) {
    std::bitset<NB * SIZE> seen;
    std::vector<Choice> best;
    for (int t = 0; t < NT; ++t) if (!node.state.counts[t])
    for (int incoming : containing[t]) {
        if (node.state.selected[incoming]) continue;
        for (int slot = 0; slot < SIZE; ++slot) {
            int code = slot * NB + incoming;
            if (seen[code]) continue;
            seen[code] = true;
            if ((++stats.proposals & 127u) == 0 && expired(deadline)) return best;
            Move move{slot, node.state.ids[slot], incoming};
            auto change = delta(node.state, move, weights);
            int history = node.history, frontier_hits = 0;
            for (Move previous : node.path)
                history += int(previous.old == incoming) + int(previous.slot == slot);
            for (int u : blocks[incoming].triples)
                frontier_hits += int(node.frontier[u] && !node.state.counts[u]);
            Choice candidate{move, node.score + change.second,
                             node.state.deficit + change.first, history, frontier_hits, rng()};
            if (static_cast<int>(best.size()) < count || candidate.rank() < best.back().rank()) {
                best.push_back(candidate);
                std::sort(best.begin(), best.end(), [](const Choice &a, const Choice &b) {
                    return a.rank() < b.rank();
                });
                if (static_cast<int>(best.size()) > count) best.pop_back();
            }
        }
    }
    return best;
}
Node search_tree(const State &root, const Weights &weights, int width, int branching,
                 int depth, std::mt19937_64 &rng, Clock::time_point deadline, Stats &stats,
                 std::ostream &traces) {
    std::vector<Node> beam{Node(root, weights)};
    Node best(root, weights), explored(root, weights);
    for (int level = 1; level <= depth && !expired(deadline); ++level) {
        std::vector<Node> children;
        for (const auto &parent : beam) {
            auto choices = fan(parent, weights, branching, rng, deadline, stats);
            for (const auto &choice : choices) {
                Node child = parent;
                child.state.apply(choice.move); child.state.audit();
                child.path.push_back(choice.move); child.score = choice.score;
                child.history = choice.history; child.tie = choice.tie;
                require(child.state.deficit == choice.deficit &&
                        child.state.energy(weights) == child.score, "delta mismatch");
                child.frontier.reset();
                for (int t = 0; t < NT; ++t)
                    if (parent.state.counts[t] > 0 && child.state.counts[t] == 0)
                        child.frontier[t] = true;
                if (child.state.deficit < best.state.deficit) best = child;
                if (explored.path.empty() || child.state.deficit < explored.state.deficit)
                    explored = child;
                children.push_back(std::move(child));
            }
            if (expired(deadline)) break;
        }
        stats.depth = std::max(stats.depth, level);
        if (best.state.deficit < root.deficit || children.empty()) break;
        std::sort(children.begin(), children.end(), [](const Node &a, const Node &b) {
            return std::make_tuple(a.score, a.state.deficit, a.history, a.tie) <
                   std::make_tuple(b.score, b.state.deficit, b.history, b.tie);
        });
        std::set<std::array<int, SIZE>> distinct;
        beam.clear();
        for (auto &child : children) {
            auto key = child.state.ids; std::sort(key.begin(), key.end());
            if (!distinct.insert(key).second) continue;
            beam.push_back(std::move(child)); ++stats.retained;
            if (static_cast<int>(beam.size()) == width) break;
        }
    }
    ++stats.trees;
    trace(traces, root, best.path.empty() ? explored.path : best.path, weights,
          best.path.empty() ? "explored" : "improvement");
    return best;
}
int self_test(const State &start, const std::string &prefix) {
    std::ofstream traces(prefix + "-traces.jsonl"); require(bool(traces), "trace output");
    std::mt19937_64 rng(2026100360); Weights weights;
    for (int &weight : weights) weight = 1 + static_cast<int>(rng() % 11);
    int checked = 0, damaged = 0;
    for (int chain = 0; chain < 80; ++chain) {
        State state = start; std::vector<Move> moves;
        for (int length = 0; length < 12; ++length) {
            int incoming;
            do { incoming = static_cast<int>(rng() % NB); } while (state.selected[incoming]);
            int slot = static_cast<int>(rng() % SIZE);
            Move move{slot, state.ids[slot], incoming};
            auto change = delta(state, move, weights);
            int old_deficit = state.deficit, old_energy = state.energy(weights);
            state.apply(move); state.audit();
            require(state.deficit == old_deficit + change.first &&
                    state.energy(weights) == old_energy + change.second, "self-test delta");
            moves.push_back(move); ++checked;
            trace(traces, start, moves, weights, "prefix-control");
        }
    }
    int absent = 0; while (start.selected[absent]) ++absent;
    for (Move move : std::vector<Move>{{-1, start.ids[0], absent}, {64, start.ids[0], absent},
            {0, start.ids[0], NB}, {0, start.ids[0], -1}, {0, start.ids[1], absent},
            {0, start.ids[0], start.ids[1]}}) {
        State state = start; bool rejected = false;
        try { state.apply(move); } catch (const std::runtime_error &) { rejected = true; }
        require(rejected && state.same(start), "invalid move mutated state"); ++damaged;
    }
    for (int kind = 0; kind < 4; ++kind) {
        State state = start;
        if (kind == 0) ++state.counts[0];
        if (kind == 1) state.selected.flip(0);
        if (kind == 2) ++state.deficit;
        if (kind == 3) state.ids[0] = state.ids[1];
        bool rejected = false;
        try { state.audit(); } catch (const std::runtime_error &) { rejected = true; }
        require(rejected, "damaged state accepted"); ++damaged;
    }
    std::cout << "{\"passed\":true,\"random_moves\":" << checked
              << ",\"prefix_rollback_controls\":" << checked
              << ",\"damaged_controls\":" << damaged << "}\n";
    return 0;
}
} // namespace
int main(int argc, char **argv) {
    try {
        require(argc >= 4, "usage: search --self-test START PREFIX | START SEED SECONDS MODE PREFIX [WIDTH FAN DEPTH]");
        universe();
        if (std::string(argv[1]) == "--self-test") {
            require(argc == 4, "self-test argument count");
            return self_test(State(read_seed(argv[2])), argv[3]);
        }
        require(argc == 6 || argc == 9, "search argument count");
        State current(read_seed(argv[1])); current.audit();
        uint64_t seed = integer(argv[2]); std::mt19937_64 rng(seed);
        std::string seconds_arg = argv[3]; size_t parsed = 0;
        double seconds = std::stod(seconds_arg, &parsed);
        require(parsed == seconds_arg.size() && std::isfinite(seconds) && seconds > 0 &&
                seconds <= 3600, "invalid wall-clock budget");
        std::string mode = argv[4], prefix = argv[5];
        require(mode == "beam" || mode == "greedy", "unknown mode");
        int width = 12, branching = 6, depth = 12;
        if (argc == 9) {
            auto w = integer(argv[6]), f = integer(argv[7]), d = integer(argv[8]);
            require(w >= 1 && w <= 64 && f >= 1 && f <= 64 && d >= 1 && d <= 64,
                    "tree parameter range");
            width = static_cast<int>(w); branching = static_cast<int>(f); depth = static_cast<int>(d);
        }
        if (mode == "greedy") { width = 1; branching = 1; depth = 1; }
        Weights weights; weights.fill(1); Stats stats;
        std::ofstream traces(prefix + "-traces.jsonl"); require(bool(traces), "trace output");
        save_blocks(prefix + "-best.txt", current);
        std::signal(SIGINT, interrupt); std::signal(SIGTERM, interrupt);
        auto began = Clock::now();
        auto deadline = began + std::chrono::duration_cast<Clock::duration>(
            std::chrono::duration<double>(seconds));
        std::cout << "{\"seed\":" << seed << ",\"seconds\":" << seconds
                  << ",\"mode\":\"" << mode << "\",\"width\":" << width
                  << ",\"fan\":" << branching << ",\"depth\":" << depth
                  << ",\"start_deficit\":" << current.deficit << "}" << std::endl;
        State best = current;
        while (best.deficit > 0 && !expired(deadline)) {
            if (mode == "greedy") {
                Node root(current, weights);
                auto choice = fan(root, weights, 1, rng, deadline, stats);
                if (!choice.empty()) {
                    trace(traces, current, {choice[0].move}, weights, "greedy-component");
                    current.apply(choice[0].move); current.audit();
                }
                ++stats.trees; stats.depth = 1;
            } else {
                Node result = search_tree(current, weights, width, branching, depth, rng,
                                          deadline, stats, traces);
                if (!result.path.empty()) current = result.state;
            }
            if (current.deficit < best.deficit) {
                best = current; save_blocks(prefix + "-best.txt", best);
                std::cout << "{\"event\":\"best\",\"deficit\":" << best.deficit
                          << ",\"tree\":" << stats.trees << "}" << std::endl;
            }
            // Weight updates are outside the tree, so scores within every tree use fixed weights.
            for (int t = 0; t < NT; ++t) if (!current.counts[t]) ++weights[t];
            if (stats.trees % 64 == 0)
                for (int &weight : weights) weight = 1 + (weight - 1) * 3 / 4;
        }
        best.audit();
        std::cout << "{\"event\":\"final\",\"best_deficit\":" << best.deficit
                  << ",\"trees\":" << stats.trees << ",\"proposals\":" << stats.proposals
                  << ",\"retained\":" << stats.retained << ",\"max_depth\":" << stats.depth
                  << ",\"elapsed\":" << std::chrono::duration<double>(Clock::now() - began).count()
                  << ",\"interrupted\":" << (stopped ? "true" : "false") << "}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n'; return 2;
    }
}
