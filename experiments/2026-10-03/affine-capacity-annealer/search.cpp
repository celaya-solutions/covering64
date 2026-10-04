// Document:    Constructive Affine Circle Deletion Capacity Search
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      76e98a3327d44c45b9ceab328f70cdb0067c883c2fa600cde55bf7e986f01e49
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Mask = std::uint64_t;
using Clock = std::chrono::steady_clock;
std::array<std::array<Mask, 12>, 20> incidence;

int capacity(Mask deleted, int extra) {
    std::array<int, 7> residual{};
    int total = 0;
    for (const auto& line : incidence) {
        int best = 0;
        for (auto mask : line) {
            int value = std::popcount(mask & deleted);
            ++residual[value];
            best = std::max(best, value);
        }
        total += best;
        --residual[best];
    }
    for (int value = 6; value >= 0 && extra; --value) {
        int take = std::min(extra, residual[value]);
        total += take * value;
        extra -= take;
    }
    if (extra) throw std::runtime_error("too many extra extensions");
    return total;
}

struct State {
    Mask mask = 1;
    std::vector<int> chosen{0};
    std::vector<int> other;
};

State initialize(int removed, std::mt19937_64& generator) {
    std::vector<int> available;
    for (int i = 1; i < 48; ++i) available.push_back(i);
    std::shuffle(available.begin(), available.end(), generator);
    State state;
    for (int i = 0; i < 47; ++i) {
        if (i < removed - 1) {
            state.chosen.push_back(available[i]);
            state.mask |= Mask{1} << available[i];
        } else state.other.push_back(available[i]);
    }
    return state;
}

void check(const State& state, int removed) {
    if (state.chosen.size() != static_cast<std::size_t>(removed)
        || state.other.size() != static_cast<std::size_t>(48 - removed)
        || state.chosen[0] != 0 || std::popcount(state.mask) != removed) {
        throw std::runtime_error("malformed state");
    }
    Mask chosen = 0, other = 0;
    for (int i : state.chosen) {
        if (i < 0 || i >= 48 || (chosen & (Mask{1} << i))) throw std::runtime_error("chosen duplicate");
        chosen |= Mask{1} << i;
    }
    for (int i : state.other) {
        if (i < 0 || i >= 48 || (other & (Mask{1} << i))) throw std::runtime_error("other duplicate");
        other |= Mask{1} << i;
    }
    if (chosen != state.mask || (chosen & other) || (chosen | other) != (Mask{1} << 48) - 1) {
        throw std::runtime_error("state partition failed");
    }
}

void exchange(State& state, std::size_t selected, std::size_t replacement) {
    if (!selected || selected >= state.chosen.size() || replacement >= state.other.size()) {
        throw std::runtime_error("invalid exchange");
    }
    state.mask ^= (Mask{1} << state.chosen[selected]) | (Mask{1} << state.other[replacement]);
    std::swap(state.chosen[selected], state.other[replacement]);
}

Mask integer(const char* text) {
    std::size_t consumed;
    Mask number = std::stoull(text, &consumed);
    if (consumed != std::string(text).size() || text[0] == '-') throw std::runtime_error("invalid integer");
    return number;
}

void selftest(Mask seed) {
    std::mt19937_64 generator(seed);
    int swaps = 0, rollbacks = 0, damage = 0;
    for (int removed = 9; removed <= 24; ++removed) {
        State state = initialize(removed, generator);
        check(state, removed);
        for (int i = 0; i < 1000; ++i) {
            State original = state;
            int baseline = capacity(state.mask, removed - 4);
            std::size_t a = 1 + generator() % (removed - 1);
            std::size_t b = generator() % (48 - removed);
            Mask expected = state.mask ^ (Mask{1} << state.chosen[a]) ^ (Mask{1} << state.other[b]);
            exchange(state, a, b);
            check(state, removed);
            if (state.mask != expected) throw std::runtime_error("swap mismatch");
            ++swaps;
            exchange(state, a, b);
            check(state, removed);
            if (state.mask != original.mask || state.chosen != original.chosen
                || state.other != original.other || capacity(state.mask, removed - 4) != baseline) {
                throw std::runtime_error("rollback mismatch");
            }
            ++rollbacks;
            exchange(state, a, b);
        }
        State broken = state;
        broken.chosen[1] = 0;
        try { check(broken, removed); } catch (const std::exception&) { ++damage; }
        broken = state;
        broken.mask ^= 1;
        try { check(broken, removed); } catch (const std::exception&) { ++damage; }
        broken = state;
        broken.other[0] = broken.chosen[1];
        try { check(broken, removed); } catch (const std::exception&) { ++damage; }
    }
    if (swaps != 16000 || rollbacks != 16000 || damage != 48) throw std::runtime_error("control count");
    std::cout << "{\"swaps\":" << swaps << ",\"rollbacks\":" << rollbacks
              << ",\"damaged_states_rejected\":" << damage << "}\n";
}

void run(int removed, Mask seed, double budget) {
    std::mt19937_64 generator(seed);
    State state = initialize(removed, generator);
    check(state, removed);
    int current = capacity(state.mask, removed - 4);
    int best = current;
    Mask best_mask = state.mask, iterations = 0, accepted = 0, rejected = 0, restarts = 0;
    std::vector<std::pair<Mask, int>> survivors;
    auto record = [&](Mask mask, int value) {
        if (value > best) { best = value; best_mask = mask; }
        if (value < 10 * removed || survivors.size() == 8) return;
        for (auto [seen, score] : survivors) {
            (void)score;
            if (std::popcount(seen ^ mask) < 4) return;
        }
        survivors.emplace_back(mask, value);
    };
    record(state.mask, current);
    auto started = Clock::now();
    while (std::chrono::duration<double>(Clock::now() - started).count() < budget
           && survivors.size() < 8) {
        if (iterations && iterations % 50000 == 0) {
            state = initialize(removed, generator);
            current = capacity(state.mask, removed - 4);
            record(state.mask, current);
            ++restarts;
        }
        std::size_t a = 1 + generator() % (removed - 1);
        std::size_t b = generator() % (48 - removed);
        exchange(state, a, b);
        int proposed = capacity(state.mask, removed - 4);
        record(state.mask, proposed);
        double phase = static_cast<double>(iterations % 50000) / 50000;
        double temperature = 0.15 + 3.5 * (1 - phase) * (1 - phase);
        double uniform = std::generate_canonical<double, 53>(generator);
        if (proposed >= current || uniform < std::exp((proposed - current) / temperature)) {
            current = proposed;
            ++accepted;
        } else {
            exchange(state, a, b);
            ++rejected;
        }
        ++iterations;
        if (iterations % 1024 == 0) check(state, removed);
    }
    check(state, removed);
    if (capacity(best_mask, removed - 4) != best) throw std::runtime_error("best score mismatch");
    double elapsed = std::chrono::duration<double>(Clock::now() - started).count();
    std::cout << "{\"removed\":" << removed << ",\"seed\":" << seed
              << ",\"requested_seconds\":" << budget << ",\"elapsed_seconds\":" << elapsed
              << ",\"iterations\":" << iterations << ",\"accepted\":" << accepted
              << ",\"rejected\":" << rejected << ",\"restarts\":" << restarts
              << ",\"best_capacity\":" << best << ",\"required_capacity\":" << 10 * removed
              << ",\"best_mask\":" << best_mask << ",\"survivors\":[";
    for (std::size_t i = 0; i < survivors.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << "{\"mask\":" << survivors[i].first << ",\"capacity\":" << survivors[i].second << '}';
    }
    std::cout << "]}\n";
}

int main(int argc, char** argv) {
    try {
        if (argc < 3) throw std::runtime_error("input and mode required");
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("missing input");
        for (auto& row : incidence) for (auto& mask : row) {
            if (!(input >> mask) || mask >= (Mask{1} << 48) || std::popcount(mask) != 6) {
                throw std::runtime_error("invalid incidence mask");
            }
        }
        std::string trailing;
        if (input >> trailing) throw std::runtime_error("extra input");
        std::string mode = argv[2];
        if (mode == "samples" && argc == 3) {
            Mask mask;
            int extra;
            while (std::cin >> mask) {
                if (!(std::cin >> extra) || mask >= (Mask{1} << 48) || extra < 0 || extra > 220) {
                    throw std::runtime_error("invalid query");
                }
                std::cout << capacity(mask, extra) << '\n';
            }
            if (!std::cin.eof()) throw std::runtime_error("malformed query");
        } else if (mode == "selftest" && argc == 4) selftest(integer(argv[3]));
        else if (mode == "run" && argc == 6) {
            Mask removed = integer(argv[3]), seed = integer(argv[4]);
            std::size_t consumed;
            double seconds = std::stod(argv[5], &consumed);
            if (removed < 9 || removed > 24 || !std::isfinite(seconds) || seconds <= 0 || seconds > 10
                || consumed != std::string(argv[5]).size()) throw std::runtime_error("invalid run");
            run(static_cast<int>(removed), seed, seconds);
        } else throw std::runtime_error("invalid mode or argument count");
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
