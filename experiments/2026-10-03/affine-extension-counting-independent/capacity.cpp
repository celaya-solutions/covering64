// Document:   Bounded Affine Extension Capacity Enumeration
// Version:    v1.0.0
// Author:     Celaya Solutions
// Contact:    hello@celayasolutions.com
// Date:       2026-10-03
// SHA256:     bd3dab24df966e1d1a00404936d3888f083db78a3f634da68d6d2fb0f72c999e
// Chain:      n/a
// Tx:         [not anchored]
// License:    All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using Mask = std::uint64_t;
std::array<std::array<Mask, 12>, 20> incidence;

int capacity(Mask selected, int extra) {
    std::array<int, 220> remaining{};
    std::size_t position = 0;
    int base = 0;
    for (const auto& line : incidence) {
        std::array<int, 12> weights{};
        for (std::size_t p = 0; p < 12; ++p) {
            weights[p] = std::popcount(line[p] & selected);
        }
        auto largest = std::max_element(weights.begin(), weights.end());
        base += *largest;
        std::iter_swap(largest, weights.begin());
        for (std::size_t p = 1; p < 12; ++p) remaining[position++] = weights[p];
    }
    if (extra > 0) {
        std::partial_sort(remaining.begin(), remaining.begin() + extra,
                          remaining.end(), std::greater<int>());
        for (int i = 0; i < extra; ++i) base += remaining[i];
    }
    return base;
}

int number(const char* text, int low, int high) {
    std::size_t consumed = 0;
    int value = std::stoi(text, &consumed);
    if (consumed != std::string(text).size() || value < low || value > high) {
        throw std::runtime_error("invalid argument");
    }
    return value;
}

int main(int argc, char** argv) {
    try {
        if (argc < 3) throw std::runtime_error("input and mode required");
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("missing input");
        for (auto& line : incidence) for (auto& mask : line) {
            if (!(input >> mask) || mask >= (Mask{1} << 48) || std::popcount(mask) != 6) {
                throw std::runtime_error("invalid incidence mask");
            }
        }
        std::string trailing;
        if (input >> trailing) throw std::runtime_error("extra input");
        if (std::string(argv[2]) == "samples") {
            if (argc != 3) throw std::runtime_error("unexpected arguments");
            Mask mask;
            int extra;
            while (std::cin >> mask) {
                if (!(std::cin >> extra) || mask >= (Mask{1} << 48) || extra < 0 || extra > 220) {
                    throw std::runtime_error("invalid sample");
                }
                std::cout << capacity(mask, extra) << '\n';
            }
            if (!std::cin.eof()) throw std::runtime_error("malformed sample");
        } else if (std::string(argv[2]) == "enumerate") {
            if (argc != 7) throw std::runtime_error("removed, extra, fixed, limit required");
            int removed = number(argv[3], 1, 24);
            int extra = number(argv[4], 0, 220);
            int fixed = number(argv[5], -1, 47);
            std::size_t consumed = 0;
            Mask limit = std::stoull(argv[6], &consumed);
            if (consumed != std::string(argv[6]).size() || argv[6][0] == '-') {
                throw std::runtime_error("invalid limit");
            }
            std::vector<int> vertices;
            for (int i = 0; i < 48; ++i) if (i != fixed) vertices.push_back(i);
            int choose = removed - (fixed >= 0);
            Mask initial = fixed >= 0 ? Mask{1} << fixed : 0;
            std::map<int, Mask> histogram;
            Mask count = 0, survivors = 0, first_survivor = 0;
            std::function<void(int, int, Mask)> visit = [&](int start, int left, Mask mask) {
                if (limit && count == limit) return;
                if (!left) {
                    int bound = capacity(mask, extra);
                    ++histogram[bound];
                    ++count;
                    if (bound >= 10 * removed) {
                        if (!survivors) first_survivor = mask;
                        ++survivors;
                    }
                    return;
                }
                for (int p = start; p <= static_cast<int>(vertices.size()) - left; ++p) {
                    visit(p + 1, left - 1, mask | (Mask{1} << vertices[p]));
                    if (limit && count == limit) return;
                }
            };
            visit(0, choose, initial);
            std::cout << "{\"removed\":" << removed << ",\"extra\":" << extra
                      << ",\"fixed_circle_zero_based\":" << fixed << ",\"limit\":" << limit
                      << ",\"deletion_sets\":" << count << ",\"survivors\":" << survivors
                      << ",\"first_survivor_mask\":" << first_survivor << ",\"histogram\":{";
            bool first = true;
            for (auto [bound, quantity] : histogram) {
                if (!first) std::cout << ',';
                first = false;
                std::cout << '"' << bound << "\":" << quantity;
            }
            std::cout << "}}\n";
        } else throw std::runtime_error("unknown mode");
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
