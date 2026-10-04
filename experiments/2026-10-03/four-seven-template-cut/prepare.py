# Document:    Audited Heavy-Cut Native Variant Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      86435c962090fba2c5679f24aae698538d04a96dc00c8c463578cb811dcca056
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "scripts/four_seven_template_lookahead_heuristic.cpp"
TARGET = ROOT / "scripts/four_seven_template_cut_heuristic.cpp"
CUT = HERE.parent / "lookahead-parametric-cut/cut.json"
GATE = HERE.parent / "lookahead-cut-independent/audit.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cut = json.loads(CUT.read_text())
    gate = json.loads(GATE.read_text())
    assert gate["passed"] and gate["sha256"]["cut"] == sha(CUT)
    assert sha(SOURCE) == "e9584eb88bb4bb744b7a2d83af26d1f3f3cf23c5efeeb42a1d94438582c4da35"
    text = SOURCE.read_text()

    def replace(old, new):
        nonlocal text
        assert text.count(old) == 1, old[:100]
        text = text.replace(old, new)

    replace(
        "Anchor-Pair Lookahead Complete Heavy Template Covering Heuristic",
        "Optional Exact Heavy-Cut Guided Template Covering Heuristic",
    )
    replace("// Version:     v1.2.0", "// Version:     v1.3.0")
    replace("#include <unordered_map>", "#include <unordered_map>\n#include <utility>")
    entries = ",\n".join(
        "    {" + str(sum(1 << (p - 1) for p in b)) + "u, " + str(c) + "}"
        for b, c in zip(cut["heavy_blocks"], cut["coefficients"], strict=True)
    )
    data = """
static bool cut_guide_enabled = false;
static constexpr int64_t HEAVY_CUT_RHS = 108686;
static constexpr int64_t HEAVY_CUT_DENOMINATOR = 1000;
static constexpr const char* HEAVY_CUT_SHA256 = "__CUT_HASH__";
static constexpr std::array<std::pair<Mask, int64_t>, 276> HEAVY_CUT_DATA = {{
CUT_ENTRIES
}};
static std::array<int64_t, 65536> heavy_cut_coefficients{};
static std::array<bool, 65536> heavy_cut_known{};
static std::array<std::vector<int64_t>, 4> template_cut_sums;
static int64_t cut_violation(int64_t lhs) { return std::max<int64_t>(0, HEAVY_CUT_RHS - lhs); }
static int cut_penalty(int64_t lhs) {
    return cut_guide_enabled ? static_cast<int>((cut_violation(lhs) + HEAVY_CUT_DENOMINATOR - 1) /
                                               HEAVY_CUT_DENOMINATOR) : 0;
}
""".replace("__CUT_HASH__", sha(CUT)).replace("CUT_ENTRIES", entries)
    replace("static std::string catalog_case;", "static std::string catalog_case;" + data)
    initializer = """
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

"""
    replace(
        "static void initialize_pair_targets() {",
        initializer + "static void initialize_pair_targets() {",
    )
    replace("    Lookahead lookahead;", "    Lookahead lookahead;\n    int64_t cut_lhs = 0;")
    replace(
        "        lookahead = cached_lookahead(template_ids);\n        audit();",
        "        lookahead = cached_lookahead(template_ids);\n"
        "        for (int group = 0; group < 4; ++group)\n"
        "            cut_lhs += template_cut_sums[group][template_ids[group]];\n        audit();",
    )
    replace(
        '        require(fixed.size() == 28, "wrong heavy block count");',
        '        require(fixed.size() == 28, "wrong heavy block count");\n'
        "        int64_t rebuilt_cut = 0;\n"
        "        for (Mask block : fixed) rebuilt_cut += heavy_cut_coefficients[block];\n"
        '        require(cut_lhs == rebuilt_cut, "incremental heavy-cut drift");',
    )
    replace(
        "    int score() const { return base_score() + LOOKAHEAD_WEIGHT * lookahead.unsupported; }",
        "    int score() const { return base_score() + LOOKAHEAD_WEIGHT * lookahead.unsupported"
        " + cut_penalty(cut_lhs); }\n"
        "    int64_t projected_cut_lhs(const Plan& plan) const {\n"
        "        if (plan.mode != 3) return cut_lhs;\n"
        "        return cut_lhs - template_cut_sums[plan.group][plan.previous_template] +\n"
        "               template_cut_sums[plan.group][plan.next_template];\n    }",
    )
    replace(
        "        int result = LOOKAHEAD_WEIGHT * (projected_lookahead(plan).unsupported"
        " - lookahead.unsupported);",
        "        int result = LOOKAHEAD_WEIGHT * (projected_lookahead(plan).unsupported"
        " - lookahead.unsupported) +\n"
        "                     cut_penalty(projected_cut_lhs(plan)) - cut_penalty(cut_lhs);",
    )
    replace(
        "        int predicted_score = score() + score_delta(plan);",
        "        int predicted_score = score() + score_delta(plan);\n"
        "        int64_t predicted_cut = projected_cut_lhs(plan);",
    )
    replace(
        "        for (int pair = 0; pair < 120; ++pair) {\n"
        "            pairs[pair] += pair_change[pair];",
        "        cut_lhs = predicted_cut;\n"
        "        for (int pair = 0; pair < 120; ++pair) {\n"
        "            pairs[pair] += pair_change[pair];",
    )
    replace(
        '           << ",\\"cache_clears\\":" << lookahead_clears',
        '           << ",\\"cut_enabled\\":" << (cut_guide_enabled ? "true" : "false")\n'
        '           << ",\\"cut_lhs\\":" << state.cut_lhs << ",\\"cut_rhs\\":" << HEAVY_CUT_RHS\n'
        '           << ",\\"cut_violation\\":" << cut_violation(state.cut_lhs)\n'
        '           << ",\\"cut_denominator\\":" << HEAVY_CUT_DENOMINATOR\n'
        '           << ",\\"cut_penalty\\":" << cut_penalty(state.cut_lhs)\n'
        '           << ",\\"cut_sha256\\":\\"" << HEAVY_CUT_SHA256 << "\\""\n'
        '           << ",\\"cache_clears\\":" << lookahead_clears',
    )
    start = text.index("        require(argc == 6 ||")
    end = text.index("        uint64_t seed =", start)
    text = (
        text[:start]
        + """        require(argc >= 6 && argc <= 8,
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
"""
        + text[end:]
    )
    replace(
        "        read_catalog(argv[1]);\n        initialize_pair_targets();",
        "        read_catalog(argv[1]);\n        initialize_heavy_cut();\n"
        "        initialize_pair_targets();",
    )
    replace(
        "        State initial(read_blocks(argv[2]));",
        """        if (control_mode == "--cut-catalog") {
            std::cout << "{\\"event\\":\\"cut_catalog\\",\\"case\\":\\"" << catalog_case
                      << "\\",\\"cut_sha256\\":\\"" << HEAVY_CUT_SHA256 << "\\",\\"groups\\":[";
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
        State initial(read_blocks(argv[2]));""",
    )
    replace(
        '        if (argc == 7 && std::string(argv[6]) == "--cache-control") {',
        '        if (control_mode == "--cache-control") {',
    )
    replace(
        '        if (argc == 7 && std::string(argv[6]) == "--lookahead-only") {',
        '        if (control_mode == "--lookahead-only") {',
    )
    replace("        if (argc == 7) {", '        if (control_mode == "--controls-only") {')
    replace(
        "            auto before_lookahead = state.lookahead;",
        "            auto before_lookahead = state.lookahead;\n"
        "            auto before_cut = state.cut_lhs;",
    )
    text = text.replace(
        "require(state.lookahead == before_lookahead && state.pairs == before_pairs",
        "require(state.cut_lhs == before_cut && state.lookahead == before_lookahead"
        " && state.pairs == before_pairs",
    )
    lines = text.splitlines()
    lines[5] = "// SHA256:      " + hashlib.sha256(text.split("\n\n", 1)[1].encode()).hexdigest()
    TARGET.write_text("\n".join(lines) + "\n")
    result = {
        "version": "v1.3.0",
        "source_sha256": sha(SOURCE),
        "cut_sha256": sha(CUT),
        "cut_gate_sha256": sha(GATE),
        "preparer_sha256": sha(Path(__file__)),
        "target": str(TARGET.relative_to(ROOT)),
        "target_sha256": sha(TARGET),
        "default_cut_enabled": False,
        "cut_flag": "--cut-guide",
        "cut_penalty": "ceil(max(0,108686-heavy_sum)/1000)",
        "hard_rejections_added": False,
        "search_launched": False,
    }
    (HERE / "preparation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
