// Document:    Heavy Profile Guided Covering Search
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      1043813199b639121138d71ec02e209bce8378eeaf95d3b7ef0715562bf1af1a
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
// A construction heuristic. Exhausted budgets do not prove nonexistence.
#define main existing_heuristic_main
#include "heuristic_search.cpp"
#undef main

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

int main(int argc, char** argv) {
  try {
    universe();
    if (argc == 3 && std::string(argv[1]) == "--profile") {
      State state(read_blocks(argv[2]));
      if (state.ids.size() != 64) throw std::runtime_error("Expected exactly64 blocks");
      std::cout << "{\"missing\":" << state.deficit << ",\"forbidden\":"
                << (forbidden_profile(heavy_ids(state), state) ? "true" : "false") << "}\n";
      return 0;
    }
    if (argc != 5) throw std::runtime_error("usage: START SEED SECONDS OUTPUT_PREFIX");
    auto initial = read_blocks(argv[1]);
    if (initial.size() != 64) throw std::runtime_error("Expected exactly64 blocks");
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
    uint64_t iterations = 0, restarts = 0;
    int best = 561;
    std::vector<int> best_ids = initial;
    double last_progress = 0;
    std::cout << "{\"event\":\"start\",\"seed\":" << seed
              << ",\"budget\":" << budget << "}" << std::endl;
    while (elapsed() < budget && !stopped) {
      State state(restarts % 3 == 0 || best == 561 ? initial : best_ids);
      auto heavy = heavy_ids(state);
      bool forbidden = forbidden_profile(heavy, state);
      // Both the initial state and all accepted states are eligible for records.
      for (uint64_t step = 0; step < 1500000; ++step, ++iterations) {
        if (!forbidden && state.deficit < best) {
          audit_state(state, heavy);
          best = state.deficit;
          best_ids = state.ids;
          save(prefix + "-h" + std::to_string(best) + ".txt", best_ids);
          std::cout << "{\"event\":\"improvement\",\"missing\":" << best
                    << ",\"seconds\":" << elapsed() << ",\"iteration\":"
                    << iterations << "}" << std::endl;
          if (best == 0) return 0;
        }
        if ((step & 4095) == 0) {
          audit_state(state, heavy);
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
        int before = state.deficit;
        state.move(slot, next);
        update_heavy(heavy, state, old, next);
        bool proposed_forbidden = forbidden_profile(heavy, state);
        double phase = double(step) / 1500000;
        double temperature = 0.06 + (0.7 + 0.1 * (restarts % 4)) * std::pow(1 - phase, 3);
        double delta = state.deficit - before + 8.0 * (int(proposed_forbidden) - int(forbidden));
        if (delta <= 0 || std::generate_canonical<double, 53>(rng) < std::exp(-delta / temperature)) {
          forbidden = proposed_forbidden;
        } else {
          state.move(slot, old);
          update_heavy(heavy, state, old, next);
        }
      }
      // Retain a possible improvement reached by the last allowed move.
      if (!forbidden && state.deficit < best) {
        audit_state(state, heavy);
        best = state.deficit;
        best_ids = state.ids;
        save(prefix + "-h" + std::to_string(best) + ".txt", best_ids);
        std::cout << "{\"event\":\"improvement\",\"missing\":" << best
                  << ",\"seconds\":" << elapsed() << "}" << std::endl;
        if (best == 0) return 0;
      }
      ++restarts;
    }
    std::cout << "{\"event\":\"" << (stopped ? "interrupted" : "finished")
              << "\",\"best\":" << best << ",\"iterations\":" << iterations
              << ",\"seconds\":" << elapsed() << "}" << std::endl;
    return 1;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}
