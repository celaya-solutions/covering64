# Document:    Independent Clebsch Checker Damage Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      368c8c426803be92e550ee935a8bdf4b329ea567354c8ae49d44ea8839810906
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Producer-to-archive checks and mathematical damage controls; no solver calls."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def load(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load("check_independent_clebsch")
producer = load("independent_clebsch_search")
profiles = load("independent_clebsch_profiles")


@pytest.fixture(scope="module")
def archive(tmp_path_factory):
    directory = tmp_path_factory.mktemp("clebsch-audit")
    universe, model, variables, graph = producer.build_model()
    target = directory / "model.pbtxt"
    model.export_to_file(str(target))
    assert len(universe.blocks) == len(variables) == 4368
    return checker.parse_pbtxt(target.read_text()), graph


def test_full_matrix_and_independent_graph(archive):
    document, graph = archive
    report = checker.audit_document(document, graph=graph)
    assert report["constraints"] == 697
    assert report["nonzero_coefficients"] == 113568
    assert not report["solver_invoked"]
    _, edges, paths = producer.geometry()
    assert (edges, paths) == checker.reference_geometry()


@pytest.mark.parametrize("damage", [
    "omitted_variable", "variable_order", "nonboolean", "omitted_row", "extra_row",
    "missing_coefficient", "wrong_coefficient", "wrong_pair", "wrong_triple",
    "duplicate_index", "negative_index", "extra_enforcement", "objective",
])
def test_damaged_matrix_rejected(archive, damage):
    original, _ = archive
    document = copy.deepcopy(original)
    constraints = document["constraints"]
    row = constraints[17]["linear"][0]
    if damage == "omitted_variable":
        document["variables"].pop()
    elif damage == "variable_order":
        document["variables"][0], document["variables"][1] = (
            document["variables"][1], document["variables"][0]
        )
    elif damage == "nonboolean":
        document["variables"][0]["domain"] = [0, 2]
    elif damage == "omitted_row":
        constraints.pop()
    elif damage == "extra_row":
        constraints.append(copy.deepcopy(constraints[0]))
    elif damage == "missing_coefficient":
        row["coeffs"].pop()
    elif damage == "wrong_coefficient":
        row["coeffs"][0] = 2
    elif damage == "wrong_pair":
        row["domain"] = [5, 6]
    elif damage == "wrong_triple":
        constraints[137]["linear"][0]["domain"] = [0, 2]
    elif damage == "duplicate_index":
        row["vars"][1] = row["vars"][0]
    elif damage == "negative_index":
        row["vars"][0] = -1
    elif damage == "extra_enforcement":
        constraints[0]["enforcement_literal"] = [0]
    else:
        document["objective"] = [{"vars": [0], "coeffs": [1]}]
    with pytest.raises(ValueError):
        checker.audit_document(document)


@pytest.mark.parametrize("damage", ["edge", "duplicate", "words", "boolean", "order"])
def test_damaged_graph_rejected(archive, damage):
    _, original = archive
    graph = copy.deepcopy(original)
    if damage == "edge":
        graph["edges"][0] = (1, 2)
    elif damage == "duplicate":
        graph["edges"][1] = graph["edges"][0]
    elif damage == "words":
        graph["words"][0] = 1
    elif damage == "boolean":
        graph["edges"][0] = (True, graph["edges"][0][1])
    else:
        graph["edges"].reverse()
    with pytest.raises(ValueError):
        checker.check_graph(graph)


@pytest.mark.parametrize("seed", [0, 1, 2, 17, 20261003])
def test_constructed_profile_has_independent_pair_loads(seed):
    profile = profiles.make_profile(seed)
    assert len(checker.check_profile(profile)) == 80
    assert profiles.make_profile(seed) == profile


def test_fixed_profile_matrix(tmp_path):
    profile = profiles.make_profile(0)
    _, model, _, graph = producer.build_model(profile)
    path = tmp_path / "fixed.pbtxt"
    model.export_to_file(str(path))
    report = checker.audit_model(path.read_text(), graph=graph, profile=profile)
    assert report["fixed_excess_profile"]
    with pytest.raises(ValueError):
        checker.audit_model(path.read_text(), graph=graph)


def test_clebsch_cut_bounds():
    edges, _ = checker.reference_geometry()
    summary = checker.balanced_cut_summary(edges)
    assert summary["necessary_bounds_pass"]
    assert summary["cut_histograms"][8] == {
        16: 70, 18: 1440, 20: 1560, 22: 1920, 24: 600, 26: 640, 28: 200, 32: 5,
    }


def test_bipartite_degree_five_excess_fails_cut_bound():
    edges = {(left + 1, 9 + (left + offset) % 8) for left in range(8) for offset in range(5)}
    summary = checker.balanced_cut_summary(edges)
    assert summary["maximum_cut_8_8"] == 40
    assert not summary["necessary_bounds_pass"]


def test_block_internal_triple_identity():
    from math import comb

    for size in range(6):
        internal = comb(size, 3) + comb(5 - size, 3)
        assert 2 * internal == 20 - 3 * size * (5 - size)


@pytest.mark.parametrize("damage", ["omitted", "duplicate", "nonpath", "load", "label"])
def test_damaged_profile_rejected(damage):
    profile = profiles.make_profile(0)
    if damage == "omitted":
        profile.pop()
    elif damage == "duplicate":
        profile[-1] = profile[0]
    elif damage == "nonpath":
        profile[-1] = (1, 2, 3)
        profile.sort()
    elif damage == "load":
        _, paths = checker.reference_geometry()
        profile[-1] = min(paths - set(profile))
        profile.sort()
    else:
        profile[0] = (0, *profile[0][1:])
    with pytest.raises(ValueError):
        checker.check_profile(profile)


@pytest.mark.parametrize("damage", ["all_duplicates", "extra_duplicate", "unsorted", "boolean"])
def test_producer_rejects_malformed_profile(damage):
    profile = profiles.make_profile(0)
    if damage == "all_duplicates":
        profile = [profile[0]] * 80
    elif damage == "extra_duplicate":
        profile.append(profile[0])
    elif damage == "unsorted":
        profile[0] = tuple(reversed(profile[0]))
    else:
        profile[0] = (True, *profile[0][1:])
    with pytest.raises(ValueError):
        producer.build_model(profile)


def test_profile_orbit_certificate_replay():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/2026-10-03/independent-geometry/profile-orbits/certificate.json"
    record = json.loads(path.read_text())
    seeds = {str(orbit["seed"]): profiles.make_profile(orbit["seed"])
             for orbit in record["body"]["orbits"]}
    report = checker.audit_profile_certificate(record, seeds)
    assert report["seed_maps_checked"]
    assert report["orbit_size_histogram"] == {16: 4, 80: 12}


@pytest.mark.parametrize("damage", ["member", "map", "profile", "action"])
def test_profile_orbit_damage_rejected_after_rehash(damage):
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/2026-10-03/independent-geometry/profile-orbits/certificate.json"
    record = json.loads(path.read_text())
    body = record["body"]
    if damage == "member":
        body["orbits"][0]["member_bits"].pop()
    elif damage == "map":
        body["profiles"][0]["action_to_representative"] = (
            body["profiles"][0]["action_to_representative"] + 1
        ) % 80
    elif damage == "profile":
        body["profiles"][0]["sha256"] = "0" * 64
    else:
        permutation = body["actions"][0]["permutation"]
        permutation[0], permutation[1] = permutation[1], permutation[0]
    canonical = (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode()
    record["SHA256"] = hashlib.sha256(canonical).hexdigest()
    with pytest.raises(ValueError):
        checker.audit_profile_certificate(record)


@pytest.mark.parametrize("source", [
    "variables {", "variables { domain: [0,", "variables { domain: [0 1] }",
    "variables { domain: [0, 1] } !", "variables { domain: [0, 1.5] }", "}",
])
def test_malformed_pbtxt_fails_closed(source):
    with pytest.raises(ValueError):
        checker.parse_pbtxt(source)
