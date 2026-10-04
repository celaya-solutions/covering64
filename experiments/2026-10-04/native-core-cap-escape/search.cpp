// Document:    Native Three-Core-Cap Heavy Profile Escape Search
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      948c23dbe7f675c66e4eb2df86cf90381195955765d195cc0511549c4099774f
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
// A construction heuristic. Exhausted budgets do not prove nonexistence.
#define main existing_heuristic_main
#include "heuristic_search.cpp"
#undef main
#include "cores.hpp"

bool forbidden_dfs(const std::vector<int>& heavy, const State& state,
                   int start, int chosen, int seven, unsigned used) {
  if (chosen == 5) return seven >= 2;
  if (int(heavy.size()) - start < 5 - chosen) return false;
  for (int j = start; j < int(heavy.size()); ++j) {
    int t = heavy[j];
    if (!(used & triples[t]) && forbidden_dfs(heavy, state, j + 1, chosen + 1,
          seven + (state.count[t] >= 7), used | triples[t])) return true;
  }
  return false;
}

std::vector<int> heavy_ids(const State& state) {
  std::vector<int> result;
  for (int t = 0; t < 560; ++t) if (state.count[t] >= 6) result.push_back(t);
  return result;
}

bool forbidden_profile(const std::vector<int>& heavy, const State& state) {
  if (heavy.size() < 5) return false;
  int seven = 0;
  for (int t : heavy) seven += state.count[t] >= 7;
  return seven >= 2 && forbidden_dfs(heavy, state, 0, 0, 0, 0);
}

void update_heavy(std::vector<int>& heavy, const State& state, int a, int b) {
  for (int id : {a, b}) for (int t : blocks[id].triples) {
    auto at = std::find(heavy.begin(), heavy.end(), t);
    if (state.count[t] >= 6 && at == heavy.end()) heavy.push_back(t);
    else if (state.count[t] < 6 && at != heavy.end()) heavy.erase(at);
  }
}

void audit_state(const State& state, const std::vector<int>& heavy) {
  State fresh(state.ids);
  if (fresh.count != state.count || fresh.deficit != state.deficit ||
      fresh.selected != state.selected) throw std::runtime_error("State recount failed");
  auto sorted = heavy;
  std::sort(sorted.begin(), sorted.end());
  if (sorted != heavy_ids(state)) throw std::runtime_error("Heavy index recount failed");
}


using CoreCounts = std::array<int, 3>;
std::array<std::array<bool, 4368>, 3> core_member{};

void initialize_cores() {
  for (int c = 0; c < 3; ++c) {
    core_member[c].fill(false);
    for (int id : CORE_IDS[c]) {
      if (id < 0 || id >= 4368 || core_member[c][id])
        throw std::runtime_error("Malformed core table");
      core_member[c][id] = true;
    }
  }
}

CoreCounts core_counts(const State& state) {
  CoreCounts counts{};
  for (int id : state.ids) for (int c = 0; c < 3; ++c)
    counts[c] += int(core_member[c][id]);
  return counts;
}

bool core_caps_pass(const CoreCounts& counts) {
  return std::all_of(counts.begin(), counts.end(), [](int count) {
    return count >= 0 && count <= CORE_CAP;
  });
}

CoreCounts proposed_core_counts(const CoreCounts& counts, int old, int next) {
  auto result = counts;
  for (int c = 0; c < 3; ++c)
    result[c] += int(core_member[c][next]) - int(core_member[c][old]);
  return result;
}

void audit_core_state(const State& state, const CoreCounts& counts) {
  if (state.ids.size() != 64 ||
      std::count(state.selected.begin(), state.selected.end(), true) != 64 ||
      core_counts(state) != counts || !core_caps_pass(counts))
    throw std::runtime_error("Core count or cap recount failed");
}

void audit_eligible_state(const State& state, const std::vector<int>& heavy,
                          const CoreCounts& counts) {
  audit_state(state, heavy);
  audit_core_state(state, counts);
  if (forbidden_profile(heavy, state))
    throw std::runtime_error("Forbidden profile cannot initialize, restart or record");
}

void record_eligible(const std::string& path, const State& state,
                     const std::vector<int>& heavy, const CoreCounts& counts) {
  audit_eligible_state(state, heavy, counts);
  save(path, state.ids);
}

void save_final_snapshots(const std::string& prefix, const std::vector<int>& current_ids,
                          const std::vector<int>& best_ids) {
  State current(current_ids), best(best_ids);
  audit_state(current, heavy_ids(current));
  audit_core_state(current, core_counts(current));
  record_eligible(prefix + "-final-best.txt", best, heavy_ids(best), core_counts(best));
  save(prefix + "-final-current.txt", current_ids);
}

void print_cores(const CoreCounts& counts) {
  std::cout << '[' << counts[0] << ',' << counts[1] << ',' << counts[2] << ']';
}

#ifndef NATIVE_CORE_NO_MAIN

int main(int argc, char** argv) {
  try {
    universe();
    initialize_cores();
    if (argc == 2 && std::string(argv[1]) == "--dump-cores") {
      std::cout << "{\"cap\":" << CORE_CAP << ",\"block_masks\":[";
      for (int i = 0; i < 4368; ++i) {
        if (i) std::cout << ',';
        std::cout << blocks[i].mask;
      }
      std::cout << "],\"triple_masks\":[";
      for (int i = 0; i < 560; ++i) {
        if (i) std::cout << ',';
        std::cout << triples[i];
      }
      std::cout << "],\"membership\":[";
      for (int i = 0; i < 4368; ++i) {
        if (i) std::cout << ',';
        std::cout << (int(core_member[0][i]) + 2 * int(core_member[1][i])
                      + 4 * int(core_member[2][i]));
      }
      std::cout << "]}\n";
      return 0;
    }
    if (argc == 3 && std::string(argv[1]) == "--profile") {
      State state(read_blocks(argv[2]));
      if (state.ids.size() != 64) throw std::runtime_error("Expected exactly64 blocks");
      std::cout << "{\"missing\":" << state.deficit << ",\"forbidden\":"
                << (forbidden_profile(heavy_ids(state), state) ? "true" : "false")
                << ",\"core_overlaps\":";
      auto counts = core_counts(state);
      print_cores(counts);
      std::cout << ",\"caps_pass\":" << (core_caps_pass(counts) ? "true" : "false")
                << "}\n";
      return 0;
    }
    if (argc != 5) throw std::runtime_error("usage: START SEED SECONDS OUTPUT_PREFIX");
    auto initial = read_blocks(argv[1]);
    if (initial.size() != 64) throw std::runtime_error("Expected exactly64 blocks");
    State initial_state(initial);
    audit_eligible_state(initial_state, heavy_ids(initial_state), core_counts(initial_state));
    uint64_t seed = std::stoull(argv[2]);
    double budget = std::stod(argv[3]);
    if (!std::isfinite(budget) || budget <= 0) throw std::runtime_error("Invalid budget");
    std::string prefix = argv[4];
    rng.seed(seed);
    std::signal(SIGTERM, stop_search);
    std::signal(SIGINT, stop_search);
    auto start = std::chrono::steady_clock::now();
    auto elapsed = [&] { return std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count(); };
    uint64_t iterations = 0, restarts = 0, core_rejections = 0;
    int best = 561;
    std::vector<int> best_ids = initial, final_ids = initial;
    double last_progress = 0;
    std::cout << "{\"event\":\"start\",\"seed\":" << seed
              << ",\"budget\":" << budget << "}" << std::endl;
    while (elapsed() < budget && !stopped) {
      State state(restarts % 3 == 0 || best == 561 ? initial : best_ids);
      auto heavy = heavy_ids(state);
      auto cores = core_counts(state);
      audit_eligible_state(state, heavy, cores);
      bool forbidden = forbidden_profile(heavy, state);
      // Core caps are hard; the unchanged profile predicate controls record eligibility.
      for (uint64_t step = 0; step < 1500000; ++step, ++iterations) {
        if (!forbidden && state.deficit < best) {
          audit_eligible_state(state, heavy, cores);
          best = state.deficit;
          best_ids = state.ids;
          record_eligible(prefix + "-h" + std::to_string(best) + ".txt", state, heavy, cores);
          std::cout << "{\"event\":\"improvement\",\"missing\":" << best
                    << ",\"seconds\":" << elapsed() << ",\"iteration\":"
                    << iterations << "}" << std::endl;
          if (best == 0) {
            save_final_snapshots(prefix, state.ids, best_ids);
            return 0;
          }
        }
        if ((step & 4095) == 0) {
          audit_state(state, heavy);
          audit_core_state(state, cores);
          if (elapsed() >= budget || stopped) break;
          if (elapsed() - last_progress >= 30) {
            last_progress = elapsed();
            std::cout << "{\"event\":\"progress\",\"best\":" << best
                      << ",\"missing\":" << state.deficit << ",\"seconds\":"
                      << last_progress << ",\"iterations\":" << iterations
                      << ",\"restarts\":" << restarts << "}" << std::endl;
          }
        }
        int slot = randint(64), old = state.ids[slot], next = -1;
        if (randint(8) == 0 && state.deficit > 0) {
          int target;
          do target = randint(560); while (state.count[target] != 0);
          next = containing[target][randint(int(containing[target].size()))];
        } else {
          int remove, add;
          do remove = randint(16); while (!(blocks[old].mask & (1u << remove)));
          do add = randint(16); while (blocks[old].mask & (1u << add));
          next = bymask[blocks[old].mask ^ (1u << remove) ^ (1u << add)];
        }
        if (state.selected[next]) continue;
        auto proposed_cores = proposed_core_counts(cores, old, next);
        if (!core_caps_pass(proposed_cores)) {
          ++core_rejections;
          continue;
        }
        int before = state.deficit;
        state.move(slot, next);
        update_heavy(heavy, state, old, next);
        bool proposed_forbidden = forbidden_profile(heavy, state);
        double phase = double(step) / 1500000;
        double temperature = 0.06 + (0.7 + 0.1 * (restarts % 4)) * std::pow(1 - phase, 3);
        double delta = state.deficit - before + 8.0 * (int(proposed_forbidden) - int(forbidden));
        if (delta <= 0 || std::generate_canonical<double, 53>(rng) < std::exp(-delta / temperature)) {
          forbidden = proposed_forbidden;
          cores = proposed_cores;
        } else {
          state.move(slot, old);
          update_heavy(heavy, state, old, next);
        }
      }
      // Retain a possible improvement reached by the last allowed move.
      if (!forbidden && state.deficit < best) {
        audit_eligible_state(state, heavy, cores);
        best = state.deficit;
        best_ids = state.ids;
        record_eligible(prefix + "-h" + std::to_string(best) + ".txt", state, heavy, cores);
        std::cout << "{\"event\":\"improvement\",\"missing\":" << best
                  << ",\"seconds\":" << elapsed() << "}" << std::endl;
        if (best == 0) {
          save_final_snapshots(prefix, state.ids, best_ids);
          return 0;
        }
      }
      audit_state(state, heavy);
      audit_core_state(state, cores);
      final_ids = state.ids;
      ++restarts;
    }
    save_final_snapshots(prefix, final_ids, best_ids);
    State best_state(best_ids);
    std::cout << "{\"event\":\"" << (stopped ? "interrupted" : "finished")
              << "\",\"best\":" << best << ",\"iterations\":" << iterations
              << ",\"seconds\":" << elapsed()
              << ",\"core_rejections\":" << core_rejections << ",\"best_core_overlaps\":";
    print_cores(core_counts(best_state));
    std::cout << ",\"final_core_overlaps\":";
    print_cores(core_counts(State(final_ids)));
    std::cout << ",\"final_profile_forbidden\":"
              << (forbidden_profile(heavy_ids(State(final_ids)), State(final_ids)) ? "true" : "false")
              << "}" << std::endl;
    return 1;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}

#endif
