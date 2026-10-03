// Document:    Independent Modular Check of the Two-Spoke Gram Obstruction
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      f1b1e3a7f396289787ed11be9bae62348d8493fcc0161f621085b0d65411ee50
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
// Enumerate every simple positive excess graph F with degrees equal to
// H=P3+mK2, disjoint from H. Reject each Gram matrix 3I+J+F-H by a modular
// nonsquare determinant. A real incidence matrix A requires det(AA^T)=det(A)^2.

#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>

constexpr int N = 13;
using Matrix = std::array<std::array<int, N>, N>;
Matrix negative{}, positive{};
std::array<int, N> remaining{};
std::vector<int> primes;
std::uint64_t cases = 0, unresolved = 0;
std::map<int, std::uint64_t> witnesses;

int power(int value, int exponent, int modulus) {
    int result = 1;
    while (exponent) {
        if (exponent & 1) result = result * value % modulus;
        value = value * value % modulus;
        exponent >>= 1;
    }
    return result;
}

int determinant(Matrix matrix, int modulus) {
    for (auto &row : matrix)
        for (int &entry : row) entry = (entry % modulus + modulus) % modulus;
    int result = 1;
    for (int column = 0; column < N; ++column) {
        int pivot = column;
        while (pivot < N && matrix[pivot][column] == 0) ++pivot;
        if (pivot == N) return 0;
        if (pivot != column) {
            std::swap(matrix[pivot], matrix[column]);
            result = (modulus - result) % modulus;
        }
        const int entry = matrix[column][column];
        result = result * entry % modulus;
        const int inverse = power(entry, modulus - 2, modulus);
        for (int row = column + 1; row < N; ++row) {
            const int factor = matrix[row][column] * inverse % modulus;
            for (int c = column; c < N; ++c)
                matrix[row][c] = (matrix[row][c] - factor * matrix[column][c]
                                  % modulus + modulus) % modulus;
        }
    }
    return result;
}

int nonsquare_witness(const Matrix &matrix) {
    for (int prime : primes) {
        const int residue = determinant(matrix, prime);
        if (residue != 0 && power(residue, (prime - 1) / 2, prime) == prime - 1)
            return prime;
    }
    return 0;
}

void inspect_graph() {
    ++cases;
    Matrix gram{};
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            gram[i][j] = i == j ? 4 : 1 + positive[i][j] - negative[i][j];
    const int witness = nonsquare_witness(gram);
    if (witness) ++witnesses[witness];
    else ++unresolved;
}

void enumerate_graphs() {
    int vertex = N - 1;
    while (vertex >= 0 && remaining[vertex] == 0) --vertex;
    if (vertex < 0) {
        inspect_graph();
        return;
    }
    // Every nonhub has degree one. An unfinished hub with no other active
    // vertex cannot be completed. Pair the largest active nonhub first.
    if (vertex == 0) return;
    if (remaining[vertex] != 1) throw std::runtime_error("bad degree state");
    for (int other = 0; other < vertex; ++other) {
        if (remaining[other] == 0 || negative[vertex][other]) continue;
        --remaining[vertex]; --remaining[other];
        positive[vertex][other] = positive[other][vertex] = 1;
        enumerate_graphs();
        positive[vertex][other] = positive[other][vertex] = 0;
        ++remaining[vertex]; ++remaining[other];
    }
}

void controls() {
    Matrix plane{}, diagonal{}, nonsquare{};
    for (int i = 0; i < N; ++i) {
        diagonal[i][i] = 1;
        nonsquare[i][i] = i == 0 ? 2 : 1;
        for (int j = 0; j < N; ++j) plane[i][j] = i == j ? 4 : 1;
    }
    if (nonsquare_witness(plane) || nonsquare_witness(diagonal)
        || !nonsquare_witness(nonsquare)) throw std::runtime_error("determinant control");
    // A nonsymmetric integer A gives an independent collection of valid Gram
    // matrices. Every row and column has four ones here.
    Matrix incidence{}, gram{};
    for (int i = 0; i < N; ++i)
        for (int k : {0, 1, 3, 6}) incidence[i][(i + k) % N] = 1;
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            for (int k = 0; k < N; ++k) gram[i][j] += incidence[i][k] * incidence[j][k];
    if (nonsquare_witness(gram)) throw std::runtime_error("Gram control rejected");
    // Exercise pivot swapping; the transposition matrix has determinant -1.
    std::swap(diagonal[0], diagonal[1]);
    for (int prime : primes)
        if (determinant(diagonal, prime) != prime - 1)
            throw std::runtime_error("pivot sign control");
}

int main() {
    for (int candidate = 3; candidate <= 1009; candidate += 2) {
        bool prime = true;
        for (int divisor = 2; divisor * divisor <= candidate; ++divisor)
            if (candidate % divisor == 0) { prime = false; break; }
        if (prime) primes.push_back(candidate);
    }
    controls();
    std::uint64_t total = 0, failures = 0;
    std::cout << "{\"controls_passed\":5,\"cases\":[";
    for (int matching_edges = 0; matching_edges <= 5; ++matching_edges) {
        negative = {}; positive = {}; remaining = {};
        const auto edge = [](int a, int b) {
            negative[a][b] = negative[b][a] = 1;
            ++remaining[a]; ++remaining[b];
        };
        edge(0, 1); edge(0, 2);
        for (int e = 0; e < matching_edges; ++e) edge(3 + 2 * e, 4 + 2 * e);
        cases = unresolved = 0; witnesses.clear();
        enumerate_graphs();
        if (matching_edges) std::cout << ',';
        std::cout << "{\"matching_edges\":" << matching_edges
                  << ",\"graphs\":" << cases << ",\"unresolved\":" << unresolved
                  << ",\"first_nonsquare_modulus_counts\":{";
        bool first = true;
        for (const auto &[prime, count] : witnesses) {
            if (!first) std::cout << ',';
            std::cout << '\"' << prime << "\":" << count;
            first = false;
        }
        std::cout << "}}";
        total += cases; failures += unresolved;
    }
    std::cout << "],\"total_graphs\":" << total << ",\"unresolved\":" << failures << "}\n";
    return failures == 0 ? 0 : 1;
}
