// Document:    Optional Exact Heavy-Cut Guided Template Covering Heuristic
// Version:     v1.3.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      32dee9ed7a7677caf267ce3c59e020d2243a29db0eee60c286a24eaba21c9df7
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
#include <utility>

using Mask = unsigned;
using Clock = std::chrono::steady_clock;
using Template = std::array<Mask, 7>;
static std::array<std::vector<Template>, 4> catalogs;
static std::array<std::array<std::vector<int>, 65536>, 4> edge_templates;
static std::string catalog_case;
static bool cut_guide_enabled = false;
static constexpr int64_t HEAVY_CUT_RHS = 108686;
static constexpr int64_t HEAVY_CUT_DENOMINATOR = 1000;
static constexpr const char* HEAVY_CUT_SHA256 = "9b946f1dbb41f49495a2303b1cac8b2de8a68e0e2eca2aa455dab02f5c5872c1";
static constexpr std::array<std::pair<Mask, int64_t>, 276> HEAVY_CUT_DATA = {{
    {31u, 3593},
    {47u, 2857},
    {79u, 2543},
    {143u, -1370},
    {271u, 2800},
    {527u, 2453},
    {1039u, 3022},
    {2063u, 199},
    {4111u, -3474},
    {8207u, -6073},
    {16399u, -3673},
    {32783u, 45},
    {151u, 8167},
    {279u, 8999},
    {535u, 9125},
    {1047u, 9335},
    {2071u, 8277},
    {4119u, 6639},
    {8215u, 5513},
    {16407u, 6475},
    {32791u, 7780},
    {167u, 7827},
    {295u, 7974},
    {551u, 8982},
    {1063u, 9391},
    {2087u, 8245},
    {4135u, 5506},
    {8231u, 5334},
    {16423u, 7111},
    {32807u, 7501},
    {199u, 7460},
    {327u, 8744},
    {583u, 7923},
    {1095u, 9356},
    {2119u, 7812},
    {4167u, 6866},
    {8263u, 5227},
    {16455u, 5034},
    {32839u, 8098},
    {391u, 6832},
    {647u, 7154},
    {1159u, 8559},
    {2183u, 4796},
    {4231u, 3840},
    {8327u, 3363},
    {16519u, 2993},
    {32903u, 4088},
    {2311u, 6305},
    {4359u, 5527},
    {8455u, 3270},
    {16647u, 5434},
    {33031u, 5516},
    {2567u, 6442},
    {4615u, 5626},
    {8711u, 3586},
    {16903u, 5661},
    {33287u, 5163},
    {3079u, 7781},
    {5127u, 8081},
    {9223u, 5716},
    {17415u, 8211},
    {33799u, 6758},
    {6151u, 3960},
    {10247u, 3924},
    {18439u, 1763},
    {34823u, 5067},
    {36871u, 2053},
    {40967u, 3720},
    {49159u, 3830},
    {121u, 9421},
    {1801u, 9700},
    {28681u, -812},
    {241u, 4525},
    {369u, 6942},
    {625u, 6983},
    {1137u, 5433},
    {2161u, 7798},
    {4209u, 9191},
    {8305u, 9433},
    {16497u, 8943},
    {32881u, 8425},
    {1809u, 6331},
    {28689u, 6214},
    {1825u, 6366},
    {28705u, 5524},
    {1857u, 6265},
    {28737u, 5505},
    {1921u, 7688},
    {28801u, 2432},
    {3841u, 3314},
    {5889u, 10075},
    {9985u, 7348},
    {18177u, 10479},
    {34561u, 7256},
    {28929u, 5514},
    {29185u, 6086},
    {29697u, 6374},
    {30721u, 3153},
    {61441u, -1268},
    {122u, 8778},
    {1802u, 8799},
    {28682u, 1272},
    {242u, 4171},
    {370u, 5852},
    {626u, 7648},
    {1138u, 5865},
    {2162u, 7877},
    {4210u, 7722},
    {8306u, 9820},
    {16498u, 8346},
    {32882u, 8505},
    {1810u, 5618},
    {28690u, 6235},
    {1826u, 6012},
    {28706u, 5426},
    {1858u, 5511},
    {28738u, 4801},
    {1922u, 6469},
    {28802u, 3209},
    {3842u, 2203},
    {5890u, 10117},
    {9986u, 7532},
    {18178u, 10272},
    {34562u, 5885},
    {28930u, 7886},
    {29186u, 5761},
    {29698u, 7072},
    {30722u, 3400},
    {61442u, -1144},
    {124u, 8384},
    {1804u, 8770},
    {28684u, 1772},
    {244u, 3786},
    {372u, 7139},
    {628u, 5499},
    {1140u, 5662},
    {2164u, 8627},
    {4212u, 8724},
    {8308u, 9619},
    {16500u, 7537},
    {32884u, 7923},
    {1812u, 5350},
    {28692u, 6388},
    {1828u, 5161},
    {28708u, 5321},
    {1860u, 5771},
    {28740u, 5391},
    {1924u, 6834},
    {28804u, 3203},
    {3844u, 1113},
    {5892u, 9724},
    {9988u, 7758},
    {18180u, 10615},
    {34564u, 6670},
    {28932u, 5227},
    {29188u, 8786},
    {29700u, 7322},
    {30724u, 3180},
    {61444u, -903},
    {248u, 1540},
    {376u, 2621},
    {632u, 2336},
    {1144u, 2295},
    {2168u, 5055},
    {4216u, 7954},
    {8312u, 9234},
    {16504u, 7605},
    {32888u, 5502},
    {1816u, 2195},
    {28696u, 8292},
    {1832u, 3168},
    {28712u, 7131},
    {1864u, 3293},
    {28744u, 7232},
    {1928u, 5442},
    {28808u, 3516},
    {3848u, 1197},
    {5896u, 7788},
    {9992u, 8199},
    {18184u, 8296},
    {34568u, 5866},
    {28936u, 6698},
    {29192u, 7321},
    {29704u, 6722},
    {30728u, 4363},
    {61448u, -247},
    {496u, -790},
    {752u, -1250},
    {1264u, -2749},
    {2288u, 1850},
    {4336u, 3101},
    {8432u, 4054},
    {16624u, 3789},
    {33008u, 2503},
    {2416u, 2762},
    {4464u, 5579},
    {8560u, 8590},
    {16752u, 5433},
    {33136u, 4063},
    {2672u, 4135},
    {4720u, 5593},
    {8816u, 8492},
    {17008u, 5593},
    {33392u, 2430},
    {3184u, 4232},
    {5232u, 3521},
    {9328u, 5900},
    {17520u, 3203},
    {33904u, 4190},
    {6256u, 5292},
    {10352u, 7108},
    {18544u, 4793},
    {34928u, 5776},
    {36976u, 5935},
    {41072u, 7881},
    {49264u, 5833},
    {1936u, 1308},
    {28816u, 7419},
    {3856u, -1029},
    {5904u, 5690},
    {10000u, 6366},
    {18192u, 6249},
    {34576u, 3856},
    {28944u, 10272},
    {29200u, 10764},
    {29712u, 7639},
    {30736u, 6795},
    {61456u, 2742},
    {1952u, 1736},
    {28832u, 6398},
    {3872u, -806},
    {5920u, 7977},
    {10016u, 6918},
    {18208u, 5633},
    {34592u, 3943},
    {28960u, 10015},
    {29216u, 10041},
    {29728u, 7600},
    {30752u, 4732},
    {61472u, 1682},
    {1984u, 1585},
    {28864u, 6747},
    {3904u, -902},
    {5952u, 5082},
    {10048u, 6966},
    {18240u, 8201},
    {34624u, 3784},
    {28992u, 9495},
    {29248u, 10533},
    {29760u, 7267},
    {30784u, 5784},
    {61504u, 833},
    {3968u, -1267},
    {6016u, 5898},
    {10112u, 5882},
    {18304u, 6048},
    {34688u, 5737},
    {29056u, 5927},
    {29312u, 6050},
    {29824u, 6053},
    {30848u, 4497},
    {61568u, -1505},
    {7936u, 3408},
    {12032u, 2080},
    {20224u, 5522},
    {36608u, 1124},
    {38656u, 10404},
    {42752u, 7517},
    {50944u, 8950},
    {30976u, 9253},
    {61696u, 3718},
    {31232u, 8477},
    {61952u, 5304},
    {31744u, 7264},
    {62464u, 2557},
    {63488u, 303}
}};
static std::array<int64_t, 65536> heavy_cut_coefficients{};
static std::array<bool, 65536> heavy_cut_known{};
static std::array<std::vector<int64_t>, 4> template_cut_sums;
static int64_t cut_violation(int64_t lhs) { return std::max<int64_t>(0, HEAVY_CUT_RHS - lhs); }
static int cut_penalty(int64_t lhs) {
    return cut_guide_enabled ? static_cast<int>((cut_violation(lhs) + HEAVY_CUT_DENOMINATOR - 1) /
                                               HEAVY_CUT_DENOMINATOR) : 0;
}

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


static void initialize_heavy_cut() {
    for (int64_t deficit : {-1, 0, 1, 999, 1000, 1001}) {
        int expected_penalty = cut_guide_enabled ?
            static_cast<int>((std::max<int64_t>(0, deficit) + 999) / 1000) : 0;
        require(cut_penalty(HEAVY_CUT_RHS - deficit) == expected_penalty, "cut ceiling control");
    }
    for (const auto& item : HEAVY_CUT_DATA) {
        require(item.first < 65536 && __builtin_popcount(item.first) == 5 &&
                !heavy_cut_known[item.first], "invalid or duplicate heavy-cut block");
        heavy_cut_known[item.first] = true;
        heavy_cut_coefficients[item.first] = item.second;
    }
    int expected = 0;
    for (Mask block = 0; block < 65536; ++block) if (__builtin_popcount(block) == 5) {
        int anchors = 0;
        bool legal = true;
        for (int group = 0; group < 4; ++group) {
            int count = __builtin_popcount(block & anchor_mask(group));
            anchors += count == 3;
            legal = legal && count != 2;
        }
        bool candidate = legal && anchors == 1;
        require(heavy_cut_known[block] == candidate, "incomplete heavy-cut universe");
        expected += candidate;
    }
    require(expected == 276, "heavy-cut candidate count");
    for (int group = 0; group < 4; ++group) {
        for (const auto& row : catalogs[group]) {
            int64_t sum = 0;
            for (Mask block : row) {
                require(heavy_cut_known[block], "catalog outside heavy-cut family");
                sum += heavy_cut_coefficients[block];
            }
            template_cut_sums[group].push_back(sum);
        }
    }
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
    int64_t cut_lhs = 0;
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
        for (int group = 0; group < 4; ++group)
            cut_lhs += template_cut_sums[group][template_ids[group]];
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
        int64_t rebuilt_cut = 0;
        for (Mask block : fixed) rebuilt_cut += heavy_cut_coefficients[block];
        require(cut_lhs == rebuilt_cut, "incremental heavy-cut drift");
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
    int score() const { return base_score() + LOOKAHEAD_WEIGHT * lookahead.unsupported + cut_penalty(cut_lhs); }
    int64_t projected_cut_lhs(const Plan& plan) const {
        if (plan.mode != 3) return cut_lhs;
        return cut_lhs - template_cut_sums[plan.group][plan.previous_template] +
               template_cut_sums[plan.group][plan.next_template];
    }
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
        int result = LOOKAHEAD_WEIGHT * (projected_lookahead(plan).unsupported - lookahead.unsupported) +
                     cut_penalty(projected_cut_lhs(plan)) - cut_penalty(cut_lhs);
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
        int64_t predicted_cut = projected_cut_lhs(plan);
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
        cut_lhs = predicted_cut;
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
           << ",\"cut_enabled\":" << (cut_guide_enabled ? "true" : "false")
           << ",\"cut_lhs\":" << state.cut_lhs << ",\"cut_rhs\":" << HEAVY_CUT_RHS
           << ",\"cut_violation\":" << cut_violation(state.cut_lhs)
           << ",\"cut_denominator\":" << HEAVY_CUT_DENOMINATOR
           << ",\"cut_penalty\":" << cut_penalty(state.cut_lhs)
           << ",\"cut_sha256\":\"" << HEAVY_CUT_SHA256 << "\""
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
        require(argc >= 6 && argc <= 8,
                "usage: CATALOG START SEED SECONDS PREFIX [--cut-guide] "
                "[--controls-only|--lookahead-only|--cache-control|--cut-catalog]");
        std::string control_mode;
        for (int index = 6; index < argc; ++index) {
            std::string argument = argv[index];
            if (argument == "--cut-guide") {
                require(!cut_guide_enabled, "duplicate cut flag");
                cut_guide_enabled = true;
            } else {
                require(control_mode.empty() && (argument == "--controls-only" ||
                        argument == "--lookahead-only" || argument == "--cache-control" ||
                        argument == "--cut-catalog"),
                        "invalid or duplicate control flag");
                control_mode = argument;
            }
        }
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
        initialize_heavy_cut();
        initialize_pair_targets();
        if (control_mode == "--cut-catalog") {
            std::cout << "{\"event\":\"cut_catalog\",\"case\":\"" << catalog_case
                      << "\",\"cut_sha256\":\"" << HEAVY_CUT_SHA256 << "\",\"groups\":[";
            for (int group = 0; group < 4; ++group) {
                if (group) std::cout << ',';
                std::cout << '[';
                for (size_t index = 0; index < template_cut_sums[group].size(); ++index)
                    std::cout << (index ? "," : "") << template_cut_sums[group][index];
                std::cout << ']';
            }
            std::cout << "]}" << std::endl;
            return 0;
        }
        State initial(read_blocks(argv[2]));
        if (control_mode == "--cache-control") {
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
        if (control_mode == "--lookahead-only") {
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
            auto before_cut = state.cut_lhs;
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
            require(state.cut_lhs == before_cut && state.lookahead == before_lookahead && state.pairs == before_pairs && state.score() == before_score &&
                    state.counts == before_counts && state.free == before_free &&
                    state.selected == before_selected && state.fixed == before_fixed &&
                    state.template_ids == before_templates, "rollback failed");
            save(state, prefix + "-control" + std::to_string(mode) + "-rollback.txt");
            Plan damaged = plan;
            damaged.after[1] = damaged.after[0];
            require(!state.legal(damaged), "duplicate move accepted");
            require(state.cut_lhs == before_cut && state.lookahead == before_lookahead && state.pairs == before_pairs && state.score() == before_score &&
                    state.counts == before_counts && state.free == before_free &&
                    state.selected == before_selected && state.fixed == before_fixed &&
                    state.template_ids == before_templates, "rejected move mutated state");
        }
        if (control_mode == "--controls-only") {
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
