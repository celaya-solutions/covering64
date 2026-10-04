# Document:    Structural Features of the Complete First-Link LP Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3037b54f88cdaebcae9926778cc14bac903a79e5116a0c8613b2f25d2c0288d7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import gzip
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCREEN = REPO / "experiments/scratch/four-seven-link-lp-full"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def features(case, edges):
    def group(point):
        return (point - 1) // 4

    def hub(point):
        return point % 4 == 0

    adjacent = (
        {frozenset(e) for e in ((0, 1), (1, 2), (2, 3), (0, 3))}
        if case == "cycle"
        else {frozenset((0, 1)), frozenset((2, 3))}
    )

    def relation(a, b):
        if group(a) == group(b):
            return "own"
        return "neighbor" if frozenset((group(a), group(b))) in adjacent else "nonneighbor"

    leaves = [b if a == 4 else a for a, b in edges if 4 in (a, b)]
    require(len(leaves) == 2, "hub leaf count")
    answer = dict(
        hub_hub=sum(hub(a) and hub(b) for a, b in edges),
        own_group_edge=sum(group(a) == group(b) for a, b in edges),
        own_hub_hub_leaves=sum(hub(p) for p in leaves),
        own_hub_neighbor_leaves=sum(relation(4, p) == "neighbor" for p in leaves),
        own_hub_leaf_same_group=int(group(leaves[0]) == group(leaves[1])),
    )
    for kind, rel in itertools.product(("hh", "ah", "aa"), ("own", "neighbor", "nonneighbor")):
        answer[f"{kind}_{rel}"] = sum(
            ("hh" if hub(a) and hub(b) else "ah" if hub(a) or hub(b) else "aa") == kind
            and relation(a, b) == rel
            for a, b in edges
        )
    require(
        sum(
            answer[f"{kind}_{rel}"]
            for kind, rel in itertools.product(
                ("hh", "ah", "aa"), ("own", "neighbor", "nonneighbor")
            )
        )
        == 7,
        "edge partition",
    )
    require(
        2 * answer["hub_hub"] + sum(answer[f"ah_{r}"] for r in ("own", "neighbor", "nonneighbor"))
        == 5,
        "hub degree incidence identity",
    )
    return answer


def matches(feature, terms):
    return all(
        feature[key] <= value if op == "<=" else feature[key] >= value for key, op, value in terms
    )


def pure_exclusion_rules(rows):
    keys = [key for key in rows[0]["features"] if key not in ("hh_own", "aa_own")]
    terms = []
    for key in keys:
        values = sorted({r["features"][key] for r in rows})
        if len(values) > 1:
            terms.extend((key, "<=", value) for value in values[:-1])
            terms.extend((key, ">=", value) for value in values[1:])
    candidates = []
    for length in (1, 2):
        for condition in itertools.combinations(terms, length):
            if len({t[0] for t in condition}) != length:
                continue
            selected = [r for r in rows if matches(r["features"], condition)]
            if len(selected) >= 3 and all(r["excluded"] for r in selected):
                candidates.append(
                    dict(
                        terms=condition,
                        ids=[r["id"] for r in selected],
                        orbit_count=len(selected),
                        labeled_count=sum(r["orbit_size"] for r in selected),
                    )
                )
    candidates.sort(key=lambda c: (-c["orbit_count"], len(c["terms"]), c["terms"]))
    # A short descriptive cover, not a fitted predictor or a claim of necessity.
    selected_rules = []
    covered = set()
    for _ in range(6):
        available = sorted(
            candidates, key=lambda c: (-len(set(c["ids"]) - covered), len(c["terms"]), c["terms"])
        )
        if not available or len(set(available[0]["ids"]) - covered) < 3:
            break
        rule = available[0]
        selected_rules.append(rule)
        covered.update(rule["ids"])
        candidates.remove(rule)
    return selected_rules


def main():
    metadata = json.loads((HERE / "result.json").read_text())
    screen_path = SCREEN / "results.json.gz"
    screen_rows = json.loads(gzip.decompress(screen_path.read_bytes()))
    screen = {r["id"]: r for r in screen_rows}
    require(len(screen) == len(screen_rows) == 258, "complete screen required")
    orbit_certificates = json.loads(gzip.decompress((HERE / "relabelings.json.gz").read_bytes()))
    representatives = {
        r["id"]: (case["case"], r) for case in metadata["cases"] for r in case["representatives"]
    }
    require(set(screen) == set(representatives), "representative coverage mismatch")
    all_features = {
        identifier: features(case, rep["edges"])
        for identifier, (case, rep) in representatives.items()
    }
    invariant_count = 0
    for case_certificate in orbit_certificates:
        for orbit in case_certificate["orbits"]:
            for item in orbit["maps"]:
                require(
                    features(case_certificate["case"], item["edges"]) == all_features[orbit["id"]],
                    "feature is not orbit invariant",
                )
                invariant_count += 1
    rows = []
    for identifier, (case, rep) in representatives.items():
        result = screen[identifier]
        excluded = result["proves_infeasible"]
        require(
            type(excluded) is bool and result["feasibility_lp"]["status"] == (2 if excluded else 0),
            "unexpected screen outcome",
        )
        rows.append(
            dict(
                id=identifier,
                case=case,
                excluded=excluded,
                orbit_size=rep["orbit_size"],
                edges=rep["edges"],
                features=all_features[identifier],
            )
        )
    case_results = []
    for case in ("cycle", "matching"):
        case_rows = [r for r in rows if r["case"] == case]
        bins = collections.defaultdict(lambda: collections.Counter())
        for row in case_rows:
            f = row["features"]
            key = (f["own_hub_hub_leaves"], f["hub_hub"], f["own_group_edge"])
            bins[key]["excluded" if row["excluded"] else "numerically_feasible"] += 1
        singles = []
        for key in case_rows[0]["features"]:
            for value in sorted({r["features"][key] for r in case_rows}):
                selected = [r for r in case_rows if r["features"][key] == value]
                if all(r["excluded"] for r in selected):
                    singles.append(dict(feature=key, value=value, ids=[r["id"] for r in selected]))
        feasible = sorted(
            (r for r in case_rows if not r["excluded"]), key=lambda r: (r["orbit_size"], r["id"])
        )
        signature_bins = collections.defaultdict(list)
        for row in case_rows:
            signature_bins[tuple(row["features"].values())].append(row)
        mixed_signatures = [
            [dict(id=r["id"], excluded=r["excluded"]) for r in bucket]
            for bucket in signature_bins.values()
            if len({r["excluded"] for r in bucket}) > 1
        ]
        case_results.append(
            dict(
                case=case,
                excluded=sum(r["excluded"] for r in case_rows),
                numerically_feasible=len(feasible),
                excluded_labeled=sum(r["orbit_size"] for r in case_rows if r["excluded"]),
                bins=[
                    dict(own_hub_hub_leaves=k[0], hub_hub=k[1], own_group_edge=k[2], **v)
                    for k, v in sorted(bins.items())
                ],
                single_value_exclusions=singles,
                short_exclusion_rules=pure_exclusion_rules(case_rows),
                distinct_feature_signatures=len(signature_bins),
                mixed_outcome_feature_signatures=mixed_signatures,
                small_orbit_cp_options=feasible[:5],
            )
        )
    audit_path = HERE.parent / "four-seven-link-lp-independent/full-v1.1.0-final-audit.json"
    require(audit_path.exists(), "missing independent certificate audit")
    audit = json.loads(audit_path.read_text())
    require(
        audit["complete_selected_coverage"] is True
        and audit["records"] == 258
        and audit["expected_records"] == 258
        and audit["excluded"] == 100,
        "incomplete certificate audit",
    )
    require(audit["results_sha256"] == sha(screen_path), "certificate audit input mismatch")
    result = dict(
        source_sha256=sha(Path(__file__)),
        screen_sha256=sha(screen_path),
        representatives_sha256=sha(HERE / "result.json"),
        orbit_archive_sha256=sha(HERE / "relabelings.json.gz"),
        certificate_audit_sha256=sha(audit_path),
        certificate_audit_path=str(audit_path.relative_to(REPO)),
        all_mapped_features_checked=invariant_count,
        cases=case_results,
        rows=rows,
        scope="Feature bins exhaust the independently verified label orbits. Fully excluded "
        "bins inherit the checked finite certificate exclusion. Numeric LP feasibility "
        "does not supply an exact fractional witness or an integer covering. "
        "CP suggestions are a search-order choice, not success predictions.",
    )
    (HERE / "lp-feature-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    for case in case_results:
        print(
            json.dumps(
                {
                    k: v
                    for k, v in case.items()
                    if k
                    in (
                        "case",
                        "excluded",
                        "numerically_feasible",
                        "excluded_labeled",
                        "short_exclusion_rules",
                    )
                }
            )
        )


if __name__ == "__main__":
    main()
