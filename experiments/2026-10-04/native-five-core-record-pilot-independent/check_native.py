# Document:    Independent Five Core Native Record Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2b9b2e2e97ac33d28a2df37dd38df6175771710f247200ed81068864177e0d10
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compile a zero-step recorder diagnostic; never execute a production binary."""

import hashlib
import itertools
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "native-five-core-record-pilot"
BASE = HERE.parent / "native-variable-partial-start"
RAW = ROOT / "experiments/scratch/native-five-core-independent-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: i for i, block in enumerate(BLOCKS)}
PAIRS = list(itertools.combinations(range(1, 17), 2))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(blocks):
    return "".join(" ".join(map(str, b)) + "\n" for b in sorted(blocks))


def parse(path):
    blocks = [tuple(map(int, row.split())) for row in path.read_text().splitlines()]
    assert blocks == sorted(set(blocks)) and all(b in RANK for b in blocks)
    return blocks


def recount(blocks, cores):
    pairs = Counter(p for b in blocks for p in itertools.combinations(b, 2))
    triples = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    quads = Counter(q for b in blocks for q in itertools.combinations(b, 4))
    d2 = d3 = d4 = 0
    for pair in PAIRS:
        other = [p for p in range(1, 17) if p not in pair]
        loads = sorted(triples[tuple(sorted((*pair, p)))] for p in other)
        d2 += max(0, 12 - 3 * pairs[pair] + loads[-1] + loads[-2])
        d3 += sum(max(0, 13 - 3 * pairs[pair] + triples[tuple(sorted((*pair, p)))]) for p in other)
        d4 += sum(
            max(0, 12 - 3 * pairs[pair] + 2 * quads[tuple(sorted((*pair, *q)))])
            for q in itertools.combinations(other, 2)
        )
    ids = {RANK[b] for b in blocks}
    return {
        "metrics": {
            "cardinality": len(blocks),
            "holes": 560 - len(triples),
            "core_overlaps": [len(ids & set(c)) for c in cores],
        },
        "minimum_pair_count": min(pairs[p] for p in PAIRS),
        "D2max": d2,
        "D3": d3,
        "D4": d4,
    }


def main():
    assert len(sys.argv) == 2, "pass the independently received frozen manifest SHA256"
    manifest_path = PRODUCER / "manifest.json"
    assert sha(manifest_path) == sys.argv[1]
    manifest = json.loads(manifest_path.read_text())
    for group in ("source_files", "input_files", "raw_files"):
        for path, digest in manifest[group].items():
            assert sha(ROOT / path) == digest
    assert not RAW.exists() and not (HERE / "native-checks.json").exists()
    RAW.mkdir()
    old = json.loads((BASE / "manifest.json").read_text())
    certificate_path = HERE.parent / "h11-d25-common-core-cap/certificate.json"
    assert (
        sha(certificate_path) == "1006dc7a15b515c075311da4ef8f074d92da60d10ed9fe3b12db23c77dc687ad"
    )
    certificate = json.loads(certificate_path.read_text())
    cores = old["core_rows"] + [certificate["core_ids"]]
    assert manifest["core_rows"] == cores
    for name in ("kernel.hpp", "cores.hpp"):
        assert (PRODUCER / name).read_bytes() == (BASE / name).read_bytes()
    assert (PRODUCER / "scan.hpp").read_bytes() == (
        HERE.parent / "weak-pair-two-swap-scan-v2/scan.hpp"
    ).read_bytes()
    source = (PRODUCER / "search.cpp").read_text()
    base_source = (BASE / "search.cpp").read_text()
    start, stop = "  while(!interrupted", '  state.audit();u.write(prefix+"-final-current.txt"'
    assert (
        source[source.index(start) : source.index(stop)]
        == base_source[base_source.index(start) : base_source.index(stop)]
    )
    for name in ("kernel.hpp", "cores.hpp", "scan.hpp", "new_core.hpp"):
        shutil.copyfile(PRODUCER / name, RAW / name)
    parent = next(
        row
        for row in manifest["initial_partials"]
        if row["sha256"] == "f621e945358cc9e51c53995ee9a4a6161a0124778984fa410a87227984a28a7a"
    )
    parent_blocks = parse(ROOT / parent["path"])
    relabeled = sorted(tuple(sorted(p % 16 + 1 for p in block)) for block in parent_blocks)
    bad_path = BASE / "seed-2026104801/search-final-admissible64.txt"
    bad = parse(bad_path)
    historical_path = BASE / "seed-2026104802/search-record-5-admissible64.txt"
    assert (
        sha(historical_path) == "439d5153ba2f2063c8dedb20ce71f9381dfecdca087e4fa9f9f0dd3808f4d22f"
    )
    historical = parse(historical_path)
    extra = next(b for b in BLOCKS if b not in set(relabeled))
    fixtures = {
        "bad_h9": bad,
        "historical_h11_d27": historical,
        "weak_h11_relabel_control": relabeled,
        "historical_worse_d2_again": historical,
        "weak_same_rank_again": relabeled,
        "partial63": relabeled[:-1],
        "partial65": sorted(relabeled + [extra]),
    }
    fixture_paths = {}
    expected = {}
    for name, blocks in fixtures.items():
        path = RAW / (name + ".txt")
        path.write_text(canonical(blocks))
        fixture_paths[name] = path
        expected[name] = recount(blocks, cores)
    assert expected["bad_h9"]["metrics"]["holes"] == 9
    assert expected["bad_h9"]["minimum_pair_count"] == 4
    assert expected["bad_h9"]["D3"] == 104 and expected["bad_h9"]["D4"] == 96
    assert expected["weak_h11_relabel_control"]["metrics"]["holes"] == 11
    assert expected["weak_h11_relabel_control"]["minimum_pair_count"] == 5
    assert expected["historical_h11_d27"]["D2max"] == 27
    assert expected["weak_h11_relabel_control"]["D2max"] == 25
    assert (
        expected["weak_h11_relabel_control"]["D3"]
        == expected["weak_h11_relabel_control"]["D4"]
        == 0
    )
    injection = r"""
  auto before_ids=state.ids();auto before_weights=state.weight;auto before_rng=rng;
  int cap_cases=0,weak_cases=0,rank_cases=0;
  for(int card: {63,64,65}) for(int mask=0;mask<32;++mask) {
    auto overlap=escape_core::thresholds;
    for(int j=0;j<5;++j) if(mask&(1<<j)) ++overlap[j];
    if(escape_core::eligible(card,overlap)!=(card==64 && mask==0))
      throw std::logic_error("synthetic cap truth table");
    ++cap_cases;
  }
  for(int card: {63,64,65}) for(int bad: {0,1}) for(int h: {0,9,11,12})
    for(int minimum: {4,5}) for(int d3: {0,1}) for(int d4: {0,1}) {
      auto overlap=escape_core::thresholds;overlap[4]+=bad;
      bool want=card==64 && !bad && h<=11 && minimum>=5 && d3==0 && d4==0;
      if(escape_core::weak_eligible(card,overlap,h,minimum,d3,d4)!=want)
        throw std::logic_error("synthetic weak truth table");
      ++weak_cases;
    }
  for(int h: {0,10,11,12}) for(int d2: {0,25,27}) for(bool present: {false,true})
    for(int old_h: {0,10,11,12}) for(int old_d2: {0,25,27}) {
      bool want=!present || h<old_h || (h==old_h && d2<old_d2);
      if(escape_core::weak_rank_improves(h,d2,present,old_h,old_d2)!=want)
        throw std::logic_error("synthetic rank truth table");
      ++rank_cases;
    }
  std::cout<<"{\"event\":\"independent_header\",\"thresholds\":[";
  for(int i=0;i<5;++i) std::cout<<(i?",":"")<<escape_core::thresholds[i];
  std::cout<<"],\"ids\":[";
  for(std::size_t i=0;i<escape_core::ids.size();++i) std::cout<<(i?",":"")<<escape_core::ids[i];
  std::cout<<"],\"cap_cases\":"<<cap_cases<<",\"weak_cases\":"<<weak_cases
    <<",\"rank_cases\":"<<rank_cases<<"}\n";
  auto control=[&](const char* name,const char* path) {
    vc::SearchState value(u,u.read(path));value.audit();
    ws::Counts counts(u,value.ids());auto profile=ws::full_metrics(counts);
    std::cout<<"{\"event\":\"independent_profile\",\"name\":\""<<name<<"\",\"metrics\":";
    emit(metrics(value));
    std::cout<<",\"minimum_pair_count\":"<<profile.minimum_pair_count
      <<",\"D2max\":"<<profile.d2max<<",\"D3\":"<<profile.d3
      <<",\"D4\":"<<profile.d4<<"}\n";
    consider(value);
  };
"""
    for name, path in fixture_paths.items():
        injection += f"  control({json.dumps(name)},{json.dumps(str(path))});\n"
    injection += """  if(state.ids()!=before_ids || state.weight!=before_weights || rng!=before_rng)
    throw std::logic_error("record observation mutated live state or RNG");
"""
    anchor = "  consider(state); // Initial records do not count as search mutations."
    assert source.count(anchor) == 1
    diagnostic = RAW / "recorder-diagnostic.cpp"
    diagnostic.write_text(source.replace(anchor, anchor + "\n" + injection))
    compiler = Path(shutil.which("clang++"))
    binary = RAW / "recorder-diagnostic"
    command = [
        str(compiler),
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-DVC_CONTROL_STEPS=0",
        str(diagnostic),
        "-o",
        str(binary),
    ]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (RAW / "compiler-stderr.txt").write_text(compiled.stderr)
    assert compiled.returncode == 0, compiled.stderr
    output_prefix = RAW / "record"
    args = [
        str(binary),
        str(ROOT / manifest["incumbent_path"]),
        str(ROOT / parent["path"]),
        "2026105601",
        "300",
        str(output_prefix),
    ]
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    (RAW / "stdout.jsonl").write_text(result.stdout)
    (RAW / "stderr.txt").write_text(result.stderr)
    assert result.returncode == 1 and not result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    header = next(e for e in events if e["event"] == "independent_header")
    assert header["thresholds"] == [55, 55, 55, 55, 56] and header["ids"] == cores[4]
    assert header["cap_cases"] == 96 and header["weak_cases"] == 192
    assert header["rank_cases"] == 288
    profiles = [e for e in events if e["event"] == "independent_profile"]
    assert len(profiles) == 7
    for row in profiles:
        assert {k: v for k, v in row.items() if k not in ("event", "name")} == expected[row["name"]]
    records = [e for e in events if e["event"] == "record"]
    assert [e["role"] for e in records] == [
        "complete",
        "raw64",
        "raw64",
        "admissible64",
        "weak64",
        "weak64",
    ]
    assert all(e["step"] == e["mutations"] == 0 for e in records)
    assert records[2]["metrics"]["holes"] == records[3]["metrics"]["holes"] == 9
    assert [e["weak_D2max"] for e in records if e["role"] == "weak64"] == [27, 25]
    assert records[-1]["metrics"]["holes"] == 11
    final = events[-1]
    assert final["iterations"] == final["mutations"] == final["weight_updates"] == 0
    assert final["raw64"]["holes"] == final["admissible64"]["holes"] == 9
    assert final["weak64"]["holes"] == 11 and final["complete"]["cardinality"] == 65
    assert final["weak_D2max"] == 25
    for event in records:
        path = Path(str(output_prefix) + f"-record-{event['serial']}-{event['role']}.txt")
        assert recount(parse(path), cores)["metrics"] == event["metrics"]
    receipt = {
        "passed": True,
        "manifest_sha256": sha(manifest_path),
        "audit_source_sha256": sha(Path(__file__)),
        "driver_sha256": sha(PRODUCER / "search.cpp"),
        "kernel_headers_unchanged": True,
        "live_loop_exactly_unchanged": True,
        "compiled_header": header,
        "real_family_profiles": profiles,
        "record_roles": [e["role"] for e in records],
        "bad_H9_does_not_suppress_weak_H11": True,
        "equal_hole_lower_D2_replaces_weak_record": True,
        "worse_D2_or_identical_rank_does_not_replace": True,
        "mixed_cardinality_records_rejected": [63, 65],
        "live_state_weights_rng_unchanged": True,
        "compiler_path": str(compiler),
        "compiler_sha256": sha(compiler),
        "compile_command": command,
        "diagnostic_command": args,
        "diagnostic_source_sha256": sha(diagnostic),
        "diagnostic_binary_sha256": sha(binary),
        "production_native_launches": 0,
        "native_advance_calls": 0,
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.iterdir()) if p.is_file()
        },
        "scope": (
            "Named-image five caps; lexicographic (H,D2max) weak bucket with H<=11; "
            "relabeled H11 is a diagnostic control, not a discovery."
        ),
    }
    target = HERE / "native-checks.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps({"passed": True, "receipt_sha256": sha(target), "production_native_launches": 0})
    )


if __name__ == "__main__":
    main()
