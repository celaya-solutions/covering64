# Document:    Prepare Optional Fourteen-Cut Native Guidance
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      02d1efb162b01838d514ee2ea69ebd85b451f613015ecdd990c385b6a17008db
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "scripts/four_seven_template_cut_heuristic.cpp"
TARGET = ROOT / "scripts/four_seven_template_multicut_heuristic.cpp"
BUNDLE = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
GATE = HERE.parent / "cut-bundle-independent/audit.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not TARGET.exists() and not (HERE / "preparation.json").exists()
    assert sha(SOURCE) == "08efce024da6d66001beb1eb10bd45b865df99b29f22c6dc01d1199fc06c1b38"
    assert sha(BUNDLE) == "67b98dc2d53d9427ea38e08fbcee13f52844e0043c96abbd2fedac5ecf1fb534"
    gate = json.loads(GATE.read_text())
    assert gate["passed"]
    bundle = json.loads(BUNDLE.read_text())
    assert bundle["cut_count"] == 14 and len(bundle["heavy_blocks"]) == 276
    assert all(c["denominator"] == 1000 for c in bundle["cuts"])
    source = SOURCE.read_text()

    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old[:80]
        source = source.replace(old, new)

    rhs = ", ".join(str(c["rhs"]) for c in bundle["cuts"])
    data = []
    for i, block in enumerate(bundle["heavy_blocks"]):
        mask = sum(1 << (p - 1) for p in block)
        values = ", ".join(str(c["coefficients"][i]) for c in bundle["cuts"])
        data.append(f"    {{{mask}u, {{{{{values}}}}}}}")
    new_constants = (
        "static int cut_weight = 1;\n"
        "static constexpr size_t HEAVY_CUT_COUNT = 14;\n"
        "using CutValues = std::array<int64_t, HEAVY_CUT_COUNT>;\n"
        f"static constexpr CutValues HEAVY_CUT_RHS = {{{{{rhs}}}}};\n"
        "static constexpr int64_t HEAVY_CUT_DENOMINATOR = 1000;\n"
        f'static constexpr const char* HEAVY_CUT_SHA256 = "{sha(BUNDLE)}";\n'
        "static constexpr std::array<std::pair<Mask, CutValues>, 276> HEAVY_CUT_DATA = {{\n"
        + ",\n".join(data)
        + "\n}};\n"
        "static std::array<CutValues, 65536> heavy_cut_coefficients{};\n"
        "static std::array<bool, 65536> heavy_cut_known{};\n"
        "static std::array<std::vector<CutValues>, 4> template_cut_sums;\n"
        "static int64_t cut_violation(const CutValues& lhs) {\n"
        "    int64_t maximum = 0;\n"
        "    for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i)\n"
        "        maximum = std::max(maximum, HEAVY_CUT_RHS[i] - lhs[i]);\n"
        "    return maximum;\n}\n"
        "static int cut_penalty(const CutValues& lhs) {\n"
        "    return cut_guide_enabled ? cut_weight * static_cast<int>(\n"
        "        (cut_violation(lhs) + HEAVY_CUT_DENOMINATOR - 1) / "
        "HEAVY_CUT_DENOMINATOR) : 0;\n}\n"
        "static void write_cut_values(std::ostream& output, const CutValues& values) {\n"
        "    output << '[';\n"
        '    for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i) output << (i ? "," : "") << values[i];\n'
        "    output << ']';\n}\n\n"
    )
    start = source.index("static constexpr int64_t HEAVY_CUT_RHS")
    end = source.index("static Mask anchor_mask", start)
    source = source[:start] + new_constants + source[end:]
    replace(
        """    for (int64_t deficit : {-1, 0, 1, 999, 1000, 1001}) {
        int expected_penalty = cut_guide_enabled ?
            static_cast<int>((std::max<int64_t>(0, deficit) + 999) / 1000) : 0;
        require(cut_penalty(HEAVY_CUT_RHS - deficit) == expected_penalty, "cut ceiling control");
    }""",
        """    for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i) {
        for (int64_t deficit : {-1, 0, 1, 999, 1000, 1001}) {
            CutValues trial = HEAVY_CUT_RHS;
            trial[i] -= deficit;
            int expected_penalty = cut_guide_enabled ? cut_weight *
                static_cast<int>((std::max<int64_t>(0, deficit) + 999) / 1000) : 0;
            require(cut_penalty(trial) == expected_penalty, "cut ceiling control");
        }
    }""",
    )
    replace("            int64_t sum = 0;", "            CutValues sum{};")
    replace(
        "                sum += heavy_cut_coefficients[block];",
        "                for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i)\n"
        "                    sum[i] += heavy_cut_coefficients[block][i];",
    )
    replace("    int64_t cut_lhs = 0;", "    CutValues cut_lhs{};")
    replace(
        "            cut_lhs += template_cut_sums[group][template_ids[group]];",
        "            for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i)\n"
        "                cut_lhs[i] += template_cut_sums[group][template_ids[group]][i];",
    )
    replace(
        "        int64_t rebuilt_cut = 0;\n"
        "        for (Mask block : fixed) rebuilt_cut += heavy_cut_coefficients[block];",
        "        CutValues rebuilt_cut{};\n"
        "        for (Mask block : fixed) for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i)\n"
        "            rebuilt_cut[i] += heavy_cut_coefficients[block][i];",
    )
    replace(
        """    int64_t projected_cut_lhs(const Plan& plan) const {
        if (plan.mode != 3) return cut_lhs;
        return cut_lhs - template_cut_sums[plan.group][plan.previous_template] +
               template_cut_sums[plan.group][plan.next_template];
    }""",
        """    CutValues projected_cut_lhs(const Plan& plan) const {
        CutValues result = cut_lhs;
        if (plan.mode == 3) for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i)
            result[i] += template_cut_sums[plan.group][plan.next_template][i] -
                         template_cut_sums[plan.group][plan.previous_template][i];
        return result;
    }""",
    )
    replace(
        "        int64_t predicted_cut = projected_cut_lhs(plan);",
        "        CutValues predicted_cut = projected_cut_lhs(plan);",
    )
    replace(
        '           << ",\\"cut_lhs\\":" << state.cut_lhs << ",\\"cut_rhs\\":" << HEAVY_CUT_RHS',
        """           << ",\\\"cut_weight\\\":" << cut_weight
           << ",\\\"cut_count\\\":" << HEAVY_CUT_COUNT
           << ",\\\"cut_lhs\\\":";
    write_cut_values(output, state.cut_lhs);
    output << ",\\\"cut_rhs\\\":";
    write_cut_values(output, HEAVY_CUT_RHS);
    CutValues violations{};
    for (size_t i = 0; i < HEAVY_CUT_COUNT; ++i)
        violations[i] = std::max<int64_t>(0, HEAVY_CUT_RHS[i] - state.cut_lhs[i]);
    output << ",\\\"cut_violations\\\":";
    write_cut_values(output, violations);
    output""",
    )
    replace("        require(argc >= 6 && argc <= 8,", "        require(argc >= 6 && argc <= 10,")
    replace(
        '"usage: CATALOG START SEED SECONDS PREFIX [--cut-guide] "',
        '"usage: CATALOG START SEED SECONDS PREFIX [--cut-guide] [--cut-weight 1..1000] "',
    )
    replace(
        "        std::string control_mode;",
        "        std::string control_mode;\n        bool weight_seen = false;",
    )
    replace(
        "                cut_guide_enabled = true;\n            } else {",
        """                cut_guide_enabled = true;
            } else if (argument == "--cut-weight") {
                require(!weight_seen && index + 1 < argc, "duplicate or missing cut weight");
                uint64_t parsed_weight = unsigned_argument(argv[++index]);
                require(parsed_weight >= 1 && parsed_weight <= 1000, "cut weight must be1..1000");
                cut_weight = static_cast<int>(parsed_weight);
                weight_seen = true;
            } else {""",
    )
    replace(
        """                for (size_t index = 0; index < template_cut_sums[group].size(); ++index)
                    std::cout << (index ? "," : "") << template_cut_sums[group][index];""",
        """                for (size_t index = 0; index < template_cut_sums[group].size(); ++index)
                {
                    if (index) std::cout << ',';
                    write_cut_values(std::cout, template_cut_sums[group][index]);
                }""",
    )
    replace(
        '                  << ",\\"lookahead_weight\\":" << LOOKAHEAD_WEIGHT << "}" << std::endl;',
        """                  << ",\\\"lookahead_weight\\\":" << LOOKAHEAD_WEIGHT
                  << ",\\\"cut_enabled\\\":" << (cut_guide_enabled ? "true" : "false")
                  << ",\\\"cut_weight\\\":" << cut_weight
                  << ",\\\"cut_sha256\\\":\\\"" << HEAVY_CUT_SHA256 << "\\\"}" << std::endl;""",
    )
    header, body = source.split("\n\n", 1)
    header = header.replace(
        "Optional Exact Heavy-Cut Guided Template Covering Heuristic",
        "Optional Fourteen-Cut Guided Template Covering Heuristic",
    )
    header = header.replace("v1.3.0", "v1.4.0").replace("2026-10-03", "2026-10-04")
    header = "\n".join(
        "// SHA256:      " + hashlib.sha256(body.encode()).hexdigest()
        if line.startswith("// SHA256:")
        else line
        for line in header.splitlines()
    )
    TARGET.write_text(header + "\n\n" + body)
    receipt = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha(SOURCE),
        "target": str(TARGET.relative_to(ROOT)),
        "target_sha256": sha(TARGET),
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "bundle_sha256": sha(BUNDLE),
        "bundle_gate_sha256": sha(GATE),
        "preparer_sha256": sha(Path(__file__)),
        "cuts": 14,
        "heavy_blocks": 276,
        "default_enabled": False,
        "default_weight": 1,
        "maximum_weight": 1000,
        "guide": "weight * max_i ceil(max(0, rhs_i - lhs_i) / 1000)",
        "search_launched": False,
    }
    (HERE / "preparation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
