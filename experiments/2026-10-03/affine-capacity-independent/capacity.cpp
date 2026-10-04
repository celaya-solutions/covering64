// Document:    Independent Affine Extension Incidence Capacity Enumerator
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      [pending]
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

std::array<std::array<uint64_t, 12>, 20> masks;

int capacity(uint64_t deleted, int extra) {
    std::array<int, 7> residual{};
    int total = 0;
    for (const auto& line : masks) {
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
    if (extra) throw std::runtime_error("too many extensions");
    return total;
}

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("input file and mode required");
        std::ifstream input(argv[1]);
        for (auto& line : masks) for (auto& mask : line) {
            if (!(input >> mask) || mask >= (uint64_t{1} << 48)
                || std::popcount(mask) != 6) throw std::runtime_error("invalid mask");
        }
        std::string trailing;
        if (input >> trailing) throw std::runtime_error("trailing data");
        if (std::string(argv[2]) == "samples") {
            uint64_t deleted; int extra;
            while (std::cin >> deleted >> extra) {
                if (deleted >= (uint64_t{1} << 48) || extra < 0 || extra > 220)
                    throw std::runtime_error("invalid query");
                std::cout << capacity(deleted, extra) << '\n';
            }
        } else if (std::string(argv[2]) == "all-five") {
            std::array<uint64_t, 127> histogram{};
            uint64_t count = 0;
            for (int a = 0; a < 44; ++a)
            for (int b = a + 1; b < 45; ++b)
            for (int c = b + 1; c < 46; ++c)
            for (int d = c + 1; d < 47; ++d)
            for (int e = d + 1; e < 48; ++e) {
                uint64_t deleted = (uint64_t{1} << a) | (uint64_t{1} << b)
                    | (uint64_t{1} << c) | (uint64_t{1} << d) | (uint64_t{1} << e);
                ++histogram[capacity(deleted, 1)];
                ++count;
            }
            std::cout << "{\"deletion_sets\":" << count << ",\"histogram\":{";
            bool first = true;
            for (int value = 0; value < 127; ++value) if (histogram[value]) {
                if (!first) std::cout << ',';
                first = false;
                std::cout << '\"' << value << "\":" << histogram[value];
            }
            std::cout << "}}\n";
        } else throw std::runtime_error("unknown mode");
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
