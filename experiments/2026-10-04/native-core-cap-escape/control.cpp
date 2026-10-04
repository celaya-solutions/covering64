// Document:    Native Core-Cap Deterministic Transition Controls
// Version:     v1.0.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      662c4e1ec71081337b7c7477d0e5cce5531cc59686be30322a5b30950d9c8632
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#include <numeric>
#define NATIVE_CORE_NO_MAIN
#include "search.cpp"

void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}

bool independent_member(int core, int id) {
  return std::find(CORE_IDS[core].begin(), CORE_IDS[core].end(), id) != CORE_IDS[core].end();
}

CoreCounts independent_core_counts(const State& state) {
  CoreCounts counts{};
  for (int id : state.ids) for (int c = 0; c < 3; ++c)
    counts[c] += independent_member(c, id);
  return counts;
}

bool oracle(const State& state) {
  std::vector<int> ids;
  for (int t = 0; t < 560; ++t) if (state.count[t] >= 6) ids.push_back(t);
  int n = int(ids.size());
  for (int a = 0; a < n; ++a) for (int b = a + 1; b < n; ++b)
  for (int c = b + 1; c < n; ++c) for (int d = c + 1; d < n; ++d)
  for (int e = d + 1; e < n; ++e) {
    std::array<int, 16> hits{};
    int seven = 0;
    for (int j : {a, b, c, d, e}) {
      int id = ids[j];
      seven += state.count[id] >= 7;
      for (int p = 0; p < 16; ++p) if (triples[id] & (1u << p)) ++hits[p];
    }
    if (seven >= 2 && *std::max_element(hits.begin(), hits.end()) <= 1) return true;
  }
  return false;
}

void independent_recount(const State& state, const std::vector<int>& heavy,
                         const CoreCounts& cores) {
  std::array<int, 560> counts{};
  std::array<bool, 4368> selected{};
  for (int id : state.ids) {
    require(!selected[id], "Duplicate selected block");
    selected[id] = true;
    for (int t = 0; t < 560; ++t)
      if ((triples[t] & blocks[id].mask) == triples[t]) ++counts[t];
  }
  int deficit = 0;
  std::vector<int> expected;
  for (int t = 0; t < 560; ++t) {
    deficit += counts[t] == 0;
    if (counts[t] >= 6) expected.push_back(t);
  }
  auto actual = heavy;
  std::sort(actual.begin(), actual.end());
  require(counts == state.count && selected == state.selected && deficit == state.deficit,
          "Independent state recount mismatch");
  require(actual == expected, "Independent heavy set recount mismatch");
  require(cores == independent_core_counts(state), "Independent core recount mismatch");
  require(core_caps_pass(cores), "Accepted state violates cap");
}

State boundary_state(int core, int count) {
  std::vector<int> ids(CORE_IDS[core].begin(), CORE_IDS[core].begin() + count);
  for (int id = 0; ids.size() < 64; ++id)
    if (!independent_member(core, id)) ids.push_back(id);
  return State(ids);
}

template <class F> void expect_rejection(F operation) {
  bool rejected = false;
  try { operation(); } catch (const std::runtime_error&) { rejected = true; }
  require(rejected, "Damaged control was accepted");
}

int main(int argc, char** argv) {
  try {
    require(argc == 5, "Expected hint, profile obstruction, core obstruction, output path");
    universe();
    initialize_cores();
    State hint(read_blocks(argv[1]));
    const auto hint_heavy = heavy_ids(hint);
    const auto hint_cores = core_counts(hint);
    require(hint.deficit == 10 && hint_cores == CoreCounts{1, 8, 55}, "Wrong hint");
    audit_eligible_state(hint, hint_heavy, hint_cores);
    record_eligible(argv[4], hint, hint_heavy, hint_cores);
    unsigned boundaries = 0, transitions = 0, cap_rejects = 0;
    for (int c = 0; c < 3; ++c) for (int amount : {54, 55, 56}) {
      State state = boundary_state(c, amount);
      auto counts = core_counts(state);
      require(counts[c] == amount && counts == independent_core_counts(state), "Boundary recount");
      CoreCounts isolated{};
      isolated[c] = amount;
      require(core_caps_pass(isolated) == (amount <= 55), "Boundary predicate");
      ++boundaries;
      if (amount == 56) continue;
      for (int out = 0; out < 2; ++out) for (int in = 0; in < 2; ++in) {
        int slot = -1, next = -1;
        for (int i = 0; i < 64; ++i)
          if (int(independent_member(c, state.ids[i])) == out) { slot = i; break; }
        for (int id = 0; id < 4368; ++id)
          if (!state.selected[id] && int(independent_member(c, id)) == in) { next = id; break; }
        require(slot >= 0 && next >= 0, "Missing transition class");
        auto proposed = proposed_core_counts(counts, state.ids[slot], next);
        State moved = state;
        moved.move(slot, next);
        require(proposed == independent_core_counts(moved), "Transition delta mismatch");
        require(proposed[c] == amount - out + in, "Wrong membership transition");
        if (!core_caps_pass(proposed)) ++cap_rejects;
        ++transitions;
      }
    }
    std::array<std::vector<int>, 8> patterns;
    for (int id = 0; id < 4368; ++id) {
      int pattern = 0;
      for (int c = 0; c < 3; ++c) pattern += (1 << c) * int(independent_member(c, id));
      patterns[pattern].push_back(id);
    }
    unsigned joint_transitions = 0;
    for (int a = 0; a < 8; ++a) for (int b = 0; b < 8; ++b) {
      if (patterns[a].empty() || patterns[b].empty()) continue;
      if (a == b && patterns[a].size() < 2) continue;
      int old = patterns[a][0], next = patterns[b][a == b ? 1 : 0];
      std::vector<int> ids{old};
      for (int id = 0; ids.size() < 64; ++id) if (id != old && id != next) ids.push_back(id);
      State before(ids), after(ids);
      auto proposed = proposed_core_counts(core_counts(before), old, next);
      after.move(0, next);
      require(proposed == independent_core_counts(after), "Joint membership delta mismatch");
      ++joint_transitions;
    }
    require(joint_transitions == 35, "Incomplete joint membership transitions");
    State profile_bad(read_blocks(argv[2])), core_bad(read_blocks(argv[3]));
    require(core_caps_pass(core_counts(profile_bad)), "Profile control must pass core caps");
    require(forbidden_profile(heavy_ids(profile_bad), profile_bad), "Expected profile control");
    require(core_counts(core_bad)[2] == 60, "Expected core-60 control");
    expect_rejection([&] { audit_eligible_state(profile_bad, heavy_ids(profile_bad), core_counts(profile_bad)); });
    expect_rejection([&] { audit_eligible_state(core_bad, heavy_ids(core_bad), core_counts(core_bad)); });
    expect_rejection([&] { record_eligible(argv[4], profile_bad, heavy_ids(profile_bad), core_counts(profile_bad)); });
    expect_rejection([&] { record_eligible(argv[4], core_bad, heavy_ids(core_bad), core_counts(core_bad)); });
    const std::string snapshot_prefix = std::string(argv[4]) + "-snapshots";
    save_final_snapshots(snapshot_prefix, profile_bad.ids, hint.ids);
    require(read_blocks(snapshot_prefix + "-final-current.txt") == profile_bad.ids,
            "Diagnostic current state was filtered away");
    require(read_blocks(snapshot_prefix + "-final-best.txt") == hint.ids,
            "Final best snapshot changed");
    auto corrupt_counts = hint_cores;
    --corrupt_counts[0];
    expect_rejection([&] { audit_core_state(hint, corrupt_counts); });
    State duplicate = hint;
    duplicate.ids[1] = duplicate.ids[0];
    expect_rejection([&] { audit_eligible_state(duplicate, heavy_ids(duplicate), core_counts(duplicate)); });
    std::mt19937_64 control_rng(2026104200);
    unsigned profiles = 0, positive_profiles = 0;
    for (int trial = 0; trial < 4000; ++trial) {
      State state({});
      if (trial < 2000) {
        std::array<int, 16> points{};
        std::iota(points.begin(), points.end(), 0);
        std::shuffle(points.begin(), points.end(), control_rng);
        for (int i = 0; i < 5; ++i) {
          unsigned mask = (1u << points[3*i]) | (1u << points[3*i+1]) | (1u << points[3*i+2]);
          auto at = std::find(triples.begin(), triples.end(), mask);
          state.count[at - triples.begin()] = 6 + int(control_rng() % 3);
        }
      }
      int extra = int(control_rng() % 9);
      for (int i = 0; i < extra; ++i) state.count[control_rng() % 560] = 6 + int(control_rng() % 4);
      auto heavy = heavy_ids(state);
      std::shuffle(heavy.begin(), heavy.end(), control_rng);
      bool expected = oracle(state);
      require(forbidden_profile(heavy, state) == expected, "Global profile oracle mismatch");
      ++profiles;
      positive_profiles += expected;
    }
    // This explicit regression has four sevenfold and one sixfold disjoint triple.
    State regression({});
    for (int i = 0; i < 5; ++i) {
      unsigned mask = (1u << (3*i)) | (1u << (3*i+1)) | (1u << (3*i+2));
      regression.count[std::find(triples.begin(), triples.end(), mask) - triples.begin()] = i == 4 ? 6 : 7;
    }
    require(oracle(regression) && forbidden_profile(heavy_ids(regression), regression), "Sixfold regression");
    State state = hint;
    auto heavy = hint_heavy;
    auto cores = hint_cores;
    unsigned moves = 0, rollbacks = 0, restarts = 0, untouched_rejections = 0;
    for (int trial = 0; trial < 5000; ++trial) {
      if (trial % 500 == 0) {
        state = hint; heavy = hint_heavy; cores = hint_cores;
        audit_eligible_state(state, heavy, cores);
        ++restarts;
      }
      int slot = int(control_rng() % 64), old = state.ids[slot], next = int(control_rng() % 4368);
      if (state.selected[next]) continue;
      auto proposed = proposed_core_counts(cores, old, next);
      const auto before = state;
      const auto heavy_before = heavy;
      const auto cores_before = cores;
      if (!core_caps_pass(proposed)) {
        require(state.ids == before.ids && state.count == before.count &&
                state.selected == before.selected && state.deficit == before.deficit &&
                heavy == heavy_before && cores == cores_before, "Core rejection touched state");
        ++untouched_rejections;
        continue;
      }
      state.move(slot, next);
      update_heavy(heavy, state, old, next);
      if (control_rng() % 2) {
        state.move(slot, old);
        update_heavy(heavy, state, old, next);
        require(state.ids == before.ids && state.count == before.count &&
                state.selected == before.selected && state.deficit == before.deficit &&
                cores == cores_before, "Energy rollback touched state");
        ++rollbacks;
      } else {
        cores = proposed;
      }
      independent_recount(state, heavy, cores);
      ++moves;
    }
    require(read_blocks(argv[4]) == read_blocks(argv[1]), "Rejected record overwrote legal output");
    require(cap_rejects >= 3 && positive_profiles > 0, "Controls lack positive cases");
    std::cout << "{\"boundaries\":" << boundaries << ",\"membership_transitions\":" << transitions
              << ",\"joint_membership_transitions\":" << joint_transitions
              << ",\"boundary_cap_rejections\":" << cap_rejects << ",\"synthetic_profiles\":" << profiles
              << ",\"positive_profiles\":" << positive_profiles << ",\"moves\":" << moves
              << ",\"rollbacks\":" << rollbacks << ",\"restarts\":" << restarts
              << ",\"untouched_core_rejections\":" << untouched_rejections
              << ",\"record_rejection_controls\":4,\"damaged_state_controls\":2}" << std::endl;
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}
