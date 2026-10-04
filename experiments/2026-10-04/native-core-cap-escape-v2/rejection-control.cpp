// Document:    Frozen Native Core-Cap Rejection State-Preservation Controls
// Version:     v1.1.0
// Author:      Celaya Solutions
// Contact:     hello@celayasolutions.com
// Date:        2026-10-04
// SHA256:      07f1b4a54720ba495a0085e26871cd792850697c5bfd162c0d7c6112b188a025
// Chain:       n/a
// Tx:          [not anchored]
// License:     All Rights Reserved / Celaya Solutions
#define NATIVE_CORE_NO_MAIN
#include "search.cpp"

int main() {
  try {
    universe();
    initialize_cores();
    unsigned checked = 0;
    for (int c = 0; c < 3; ++c) {
      std::vector<int> ids(CORE_IDS[c].begin(), CORE_IDS[c].begin() + 55);
      for (int id = 0; ids.size() < 64; ++id)
        if (!core_member[0][id] && !core_member[1][id] && !core_member[2][id]) ids.push_back(id);
      State state(ids);
      auto heavy = heavy_ids(state);
      auto counts = core_counts(state);
      audit_state(state, heavy);
      audit_core_state(state, counts);
      int slot = 55, old = state.ids[slot], next = CORE_IDS[c][55];
      if (state.selected[next] || counts[c] != 55 || core_member[c][old])
        throw std::runtime_error("Malformed boundary control");
      const auto before = state;
      const auto heavy_before = heavy;
      const auto counts_before = counts;
      auto proposed = proposed_core_counts(counts, old, next);
      bool moved = false;
      if (core_caps_pass(proposed)) {
        moved = true;
        state.move(slot, next);
        update_heavy(heavy, state, old, next);
        counts = proposed;
      }
      if (moved || proposed[c] != 56 || state.ids != before.ids || state.count != before.count ||
          state.weight != before.weight || state.selected != before.selected ||
          state.deficit != before.deficit || heavy != heavy_before || counts != counts_before)
        throw std::runtime_error("Core rejection changed state");
      audit_state(state, heavy);
      audit_core_state(state, counts);
      ++checked;
    }
    std::cout << "{\"passed\":true,\"pre_mutation_rejections\":" << checked
              << ",\"entire_state_unchanged\":true,\"optimizer_calls\":0}" << std::endl;
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}
