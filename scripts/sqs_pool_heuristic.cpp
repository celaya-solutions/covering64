// Document:    Strict SQS Extension Pool Hole Minimizer
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-03
// SHA256:      2eafc58031b1e1c744928dd328b6999d8203234d04c60f4a5808b29f38338b83
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions

#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cmath>
#include <csignal>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
struct Block { unsigned mask; std::array<int, 10> triples; };
std::vector<Block> blocks;
std::vector<unsigned> triples;
std::array<int, 65536> block_id{}, triple_id{};
std::vector<int> allowed;
std::array<bool, 4368> is_allowed{};
std::array<std::vector<int>, 560> carriers;
volatile std::sig_atomic_t stopped = 0;
void stop(int) { stopped = 1; }
void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
void build_universe() {
  block_id.fill(-1); triple_id.fill(-1);
  for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
    for (int c = b + 1; c < 16; ++c) {
      unsigned mask = (1u << a) | (1u << b) | (1u << c);
      triple_id[mask] = int(triples.size()); triples.push_back(mask);
    }
  for (int a = 0; a < 16; ++a) for (int b = a + 1; b < 16; ++b)
    for (int c = b + 1; c < 16; ++c) for (int d = c + 1; d < 16; ++d)
      for (int e = d + 1; e < 16; ++e) {
        unsigned mask = (1u << a) | (1u << b) | (1u << c) | (1u << d) | (1u << e);
        Block block{mask, {}}; int count = 0;
        for (int t = 0; t < 560; ++t)
          if ((triples[t] & mask) == triples[t]) block.triples[count++] = t;
        require(count == 10, "bad universe block");
        block_id[mask] = int(blocks.size()); blocks.push_back(block);
      }
  require(blocks.size() == 4368 && triples.size() == 560, "bad universe");
}
std::vector<int> read_blocks(const fs::path& path, std::size_t expected, bool pool_member) {
  std::ifstream input(path); require(bool(input), "cannot read block file");
  std::vector<int> result; std::string line;
  while (std::getline(input, line)) {
    std::istringstream row(line); std::string token;
    unsigned mask = 0; int previous = 0, size = 0;
    while (row >> token) {
      int point = 0;
      auto parsed = std::from_chars(token.data(), token.data() + token.size(), point);
      require(parsed.ec == std::errc{} && parsed.ptr == token.data() + token.size(), "bad token");
      require(point > previous && point <= 16, "points must increase within 1..16");
      mask |= 1u << (point - 1); previous = point; ++size;
    }
    require(size == 5 && block_id[mask] >= 0, "block must have five points");
    int id = block_id[mask];
    require(result.empty() || id > result.back(), "block IDs must increase without duplicates");
    require(!pool_member || is_allowed[id], "start block outside pool");
    result.push_back(id);
  }
  require(input.eof() && result.size() == expected, "wrong block count or read failure");
  return result;
}
void load_pool(const fs::path& path) {
  allowed = read_blocks(path, 1744, false);
  for (int id : allowed) {
    is_allowed[id] = true;
    for (int t : blocks[id].triples) carriers[t].push_back(id);
  }
  for (const auto& support : carriers) require(!support.empty(), "pool misses a triple");
}
std::ofstream output_file(const fs::path& path) {
  require(!fs::exists(path), "refusing to overwrite artifact");
  std::ofstream output(path); require(bool(output), "cannot create output");
  return output;
}
void save_blocks(const fs::path& path, std::vector<int> ids) {
  std::sort(ids.begin(), ids.end()); auto output = output_file(path);
  for (int id : ids) {
    bool first = true;
    for (int p = 0; p < 16; ++p) if (blocks[id].mask & (1u << p)) {
      if (!first) output << ' ';
      output << p + 1; first = false;
    }
    output << '\n';
  }
  output.flush(); require(bool(output), "cannot save blocks");
}
template <typename Values> void array_json(std::ostream& output, const Values& values) {
  output << '['; bool first = true;
  for (const auto& value : values) {
    if (!first) output << ',';
    output << value; first = false;
  }
  output << ']';
}
struct State {
  std::vector<int> ids;
  std::array<int, 560> count{};
  std::array<bool, 4368> selected{};
  int holes = 560;
  explicit State(std::vector<int> initial) : ids(std::move(initial)) {
    require(ids.size() == 64, "state needs64 blocks");
    for (int id : ids) {
      require(id >= 0 && id < 4368 && is_allowed[id] && !selected[id], "invalid state ID");
      selected[id] = true;
      for (int t : blocks[id].triples) if (count[t]++ == 0) --holes;
    }
  }
  int delta(int slot, int added) const {
    require(slot >= 0 && slot < 64 && added >= 0 && added < 4368 &&
            is_allowed[added] && !selected[added], "invalid replacement");
    int change = 0, old = ids[slot];
    for (int t : blocks[old].triples)
      if (count[t] == 1 && (triples[t] & blocks[added].mask) != triples[t]) ++change;
    for (int t : blocks[added].triples) if (count[t] == 0) --change;
    return change;
  }
  void apply(int slot, int added) {
    int expected = holes + delta(slot, added), old = ids[slot];
    selected[old] = false; selected[added] = true; ids[slot] = added;
    for (int t : blocks[old].triples) if (--count[t] == 0) ++holes;
    for (int t : blocks[added].triples) if (count[t]++ == 0) --holes;
    require(holes == expected, "replacement delta disagrees with updated counts");
  }
  void audit() const {
    // Rebuild using direct triple-mask containment, not incremental move code.
    std::array<int, 560> actual{}; std::array<bool, 4368> membership{};
    for (int id : ids) {
      require(id >= 0 && id < 4368 && is_allowed[id] && !membership[id], "audit membership failure");
      membership[id] = true;
      for (int t = 0; t < 560; ++t)
        if ((triples[t] & blocks[id].mask) == triples[t]) ++actual[t];
    }
    require(ids.size() == 64 && actual == count && membership == selected &&
            std::count(actual.begin(), actual.end(), 0) == holes, "full recount disagrees");
  }
};
void prepare(const fs::path& directory) {
  require(!fs::exists(directory), "prepare directory exists"); fs::create_directory(directory);
  std::array<int, 560> counts{}; std::array<bool, 4368> chosen{}; std::vector<int> initial;
  int holes = 560; auto trace = output_file(directory / "greedy-trace.csv");
  trace << "step,global_id,gain,holes\n";
  for (int step = 0; step < 64; ++step) {
    int best = -1, gain = -1;
    for (int id : allowed) if (!chosen[id]) {
      int current = 0; for (int t : blocks[id].triples) current += counts[t] == 0;
      if (current > gain) { gain = current; best = id; }
    }
    require(best >= 0, "greedy failed"); chosen[best] = true; initial.push_back(best);
    for (int t : blocks[best].triples) if (counts[t]++ == 0) --holes;
    trace << step + 1 << ',' << best << ',' << gain << ',' << holes << '\n';
  }
  trace.flush(); require(bool(trace), "cannot save greedy trace");
  std::sort(initial.begin(), initial.end()); save_blocks(directory / "initial64.txt", initial);
  State state(initial); state.audit(); require(state.holes == holes, "greedy count mismatch");
  auto deltas = output_file(directory / "initial-deltas.csv");
  deltas << "slot,removed_global_id,added_global_id,delta,holes_after\n"; int delta_rows = 0;
  for (int slot = 0; slot < 64; ++slot) for (int added : allowed) if (!state.selected[added]) {
    int change = state.delta(slot, added);
    deltas << slot << ',' << state.ids[slot] << ',' << added << ',' << change << ','
           << state.holes + change << '\n'; ++delta_rows;
  }
  deltas.flush(); require(bool(deltas) && delta_rows == 107520, "bad initial delta export");
  auto controls = output_file(directory / "move-controls.jsonl");
  int accepted = 0, checkpoints = 0;
  for (int step = 0; step < 96; ++step) {
    int slot = (step * 17) % 64, offset = (step * 73 + 11) % 1744;
    while (state.selected[allowed[offset]]) offset = (offset + 1) % 1744;
    int added = allowed[offset];
    const char* action = step % 3 == 0 ? "accepted" : step % 3 == 1 ? "rejected" : "rollback";
    if (step % 3 == 2 && state.delta(slot, added) <= 0) {
      bool found = false;
      for (int s = 0; s < 64 && !found; ++s) for (int id : allowed)
        if (!state.selected[id] && state.delta(s, id) > 0) {
          slot = s; added = id; found = true; break;
        }
      require(found, "positive-delta rollback control unavailable");
    }
    State before = state; int old = state.ids[slot], change = state.delta(slot, added);
    int tentative_holes = state.holes + change;
    if (step % 3 == 0) { state.apply(slot, added); ++accepted; }
    if (step % 3 == 2) {
      state.apply(slot, added); state.audit(); require(state.holes == tentative_holes, "tentative mismatch");
      state.apply(slot, old);
    }
    if (step % 3 != 0)
      require(state.ids == before.ids && state.count == before.count &&
              state.selected == before.selected && state.holes == before.holes, "rollback/reject changed state");
    bool periodic = step % 3 == 0 && accepted % 4 == 0;
    if (periodic) { state.audit(); ++checkpoints; }
    controls << "{\"step\":" << step << ",\"action\":\"" << action << "\",\"slot\":" << slot
             << ",\"removed_global_id\":" << old << ",\"added_global_id\":" << added
             << ",\"delta\":" << change << ",\"holes_before\":" << before.holes
             << ",\"tentative_holes\":" << tentative_holes << ",\"holes_after\":" << state.holes
             << ",\"accepted_total\":" << accepted << ",\"periodic_audit\":" << (periodic ? "true" : "false")
             << ",\"selected_ids\":"; array_json(controls, state.ids);
    controls << ",\"cached_counts\":"; array_json(controls, state.count); controls << "}\n";
  }
  controls.flush(); require(bool(controls), "cannot save move controls"); state.audit();
  auto report = output_file(directory / "preparation.json");
  report << "{\"prepared\":true,\"optimization_runs\":0,\"initial_holes\":" << holes
         << ",\"initial_delta_rows\":" << delta_rows << ",\"control_proposals\":96,\"accepted_controls\":"
         << accepted << ",\"accepted_count_checkpoints\":" << checkpoints << "}\n";
  report.flush(); require(bool(report), "cannot save preparation report");
  std::cout << "{\"prepared\":true,\"initial_holes\":" << holes << ",\"initial_delta_rows\":" << delta_rows << "}\n";
}
void run(const fs::path& start, uint64_t seed, double seconds, const fs::path& directory) {
  State state(read_blocks(start, 64, true)); state.audit();
  require(!fs::exists(directory), "run directory exists"); fs::create_directory(directory);
  auto events = output_file(directory / "events.jsonl");
  std::mt19937_64 rng(seed); auto random = [&](int n) { return int(rng() % unsigned(n)); };
  auto started = std::chrono::steady_clock::now();
  auto elapsed = [&] { return std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count(); };
  uint64_t proposals = 0, accepted = 0, rejected = 0, selected_skips = 0, audits = 1;
  int best = state.holes; save_blocks(directory / ("best-" + std::to_string(best) + ".txt"), state.ids);
  auto best_event = [&] {
    events << "{\"event\":\"best\",\"holes\":" << best << ",\"proposals\":" << proposals
           << ",\"accepted\":" << accepted << ",\"seconds\":" << elapsed() << "}\n"; events.flush();
  };
  best_event();
  while (!stopped && state.holes > 0 && elapsed() < seconds) {
    int slot = random(64), added;
    if (random(2) == 0) {
      std::array<int, 560> missing{}; int size = 0;
      for (int t = 0; t < 560; ++t) if (state.count[t] == 0) missing[size++] = t;
      const auto& support = carriers[missing[random(size)]];
      added = support[random(int(support.size()))];
    } else added = allowed[random(1744)];
    ++proposals;
    if (state.selected[added]) { ++selected_skips; continue; }
    int change = state.delta(slot, added);
    double phase = double(proposals % 250000) / 250000.0;
    double temperature = 0.05 + 0.75 * std::pow(1.0 - phase, 3);
    bool accept = change <= 0 || std::generate_canonical<double, 53>(rng) < std::exp(-change / temperature);
    if (!accept) { ++rejected; continue; }
    state.apply(slot, added); ++accepted;
    if (accepted % 4096 == 0) {
      state.audit(); ++audits;
      events << "{\"event\":\"recount\",\"accepted\":" << accepted << ",\"holes\":" << state.holes
             << ",\"proposals\":" << proposals << "}\n"; events.flush();
    }
    if (state.holes < best) {
      state.audit(); ++audits; best = state.holes;
      save_blocks(directory / ("best-" + std::to_string(best) + ".txt"), state.ids); best_event();
    }
  }
  state.audit(); ++audits;
  save_blocks(directory / "final64.txt", state.ids);
  require(proposals == accepted + rejected + selected_skips, "proposal accounting mismatch");
  auto report = output_file(directory / "result.json");
  report << "{\"seed\":" << seed << ",\"budget_seconds\":" << seconds << ",\"elapsed_seconds\":" << elapsed()
         << ",\"best_holes\":" << best << ",\"final_holes\":" << state.holes << ",\"proposals\":" << proposals
         << ",\"accepted\":" << accepted << ",\"rejected\":" << rejected << ",\"selected_skips\":" << selected_skips
         << ",\"full_recounts\":" << audits << ",\"interrupted\":" << (stopped ? "true" : "false")
         << ",\"global_lower_bound_claim\":false}\n";
  report.flush(); events.flush(); require(bool(report) && bool(events), "cannot save final report");
  std::cout << "{\"finished\":true,\"best_holes\":" << best << ",\"proposals\":" << proposals << "}\n";
}
int main(int argc, char** argv) {
  try {
    require(argc >= 3, "usage: sqs_pool_heuristic prepare POOL OUT | validate POOL START | run POOL START SEED SECONDS OUT");
    std::string mode = argv[1];
    require((mode == "prepare" && argc == 4) || (mode == "validate" && argc == 4) ||
            (mode == "run" && argc == 7), "bad mode or argument count");
    build_universe(); load_pool(argv[2]);
    if (mode == "prepare") prepare(argv[3]);
    else if (mode == "validate") {
      State state(read_blocks(argv[3], 64, true)); state.audit();
      std::cout << "{\"well_formed\":true,\"blocks\":64,\"holes\":" << state.holes << "}\n";
    } else {
      uint64_t seed = 0; std::string token = argv[4];
      auto parsed = std::from_chars(token.data(), token.data() + token.size(), seed);
      require(parsed.ec == std::errc{} && parsed.ptr == token.data() + token.size(), "bad seed");
      std::size_t end = 0; double seconds = std::stod(argv[5], &end);
      require(end == std::string(argv[5]).size() && std::isfinite(seconds) && seconds > 0, "bad duration");
      std::signal(SIGINT, stop); std::signal(SIGTERM, stop);
      run(argv[3], seed, seconds, argv[6]);
    }
    return 0;
  } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 2; }
}
