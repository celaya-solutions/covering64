# Document:    Neutral Observation Recorder Adapter
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2c99b3b08c922b58f68ce5fc7b9e55c56c764afb71130a4241419f704d1a1ade
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Keep original strict validation intact and check a separate capped neutral sample."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINALS = {
    "one": HERE.parent / "weak-pair-swap-scan/run.py",
    "two": HERE.parent / "weak-pair-two-swap-scan-v2/run.py",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Recorder:
    def __init__(self, kind):
        require(kind in ORIGINALS, "unknown shell")
        self.kind = kind
        spec = importlib.util.spec_from_file_location("neutral_original_" + kind, ORIGINALS[kind])
        self.original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.original)

    def __getattr__(self, name):
        return getattr(self.original, name)

    def validate(self, prefix, stdout, rc, stderr, elapsed, initial, cores, control_limit=None):
        audit = self.original.validate(
            prefix, stdout, rc, stderr, elapsed, initial, cores, control_limit
        )
        final = audit["final"]
        meta = json.loads(Path(str(prefix) + "-neutral-meta.json").read_text())
        rows = json.loads(Path(str(prefix) + "-neutral.json").read_text())
        require(isinstance(meta, dict) and isinstance(rows, list), "neutral document types")
        require(
            set(meta) == {"neutral_seen", "retained", "cap", "capped", "complete", "rank"},
            "neutral metadata fields",
        )
        require(
            all(
                type(meta[key]) is int and meta[key] >= 0
                for key in ("neutral_seen", "retained", "cap")
            ),
            "neutral counters",
        )
        require(
            meta["cap"] == 64 and meta["retained"] == len(rows) == min(64, meta["neutral_seen"]),
            "neutral cap accounting",
        )
        require(
            type(meta["complete"]) is bool and meta["complete"] == final["complete"],
            "neutral completion flag",
        )
        require(
            type(meta["capped"]) is bool and meta["capped"] == (meta["neutral_seen"] > 64),
            "neutral truncation flag",
        )
        baseline = [initial["metrics"]["holes"], initial["metrics"]["D2max"]]
        require(
            isinstance(meta["rank"], list)
            and len(meta["rank"]) == 2
            and all(type(v) is int and v >= 0 for v in meta["rank"]),
            "neutral rank type",
        )
        require(meta["rank"] == baseline, "neutral baseline rank")
        require(
            meta["neutral_seen"] + final["strictly_improving_neighbors"] <= final["legal"],
            "neutral count exceeds legal non-improving records",
        )
        original = set(initial["ids"])
        selected = sorted(original)
        absent = [i for i in range(4368) if i not in original]
        checked = []
        for row in rows:
            require(isinstance(row, dict), "neutral row object")
            outgoing, incoming = row["outgoing"], row["incoming"]
            if self.kind == "one":
                require(type(outgoing) is type(incoming) is int, "neutral one-swap IDs")
                require(outgoing in original and incoming in absent, "neutral one-swap membership")
                ordinal = selected.index(outgoing) * 4304 + absent.index(incoming) + 1
                require(ordinal <= final["evaluated"], "neutral past evaluated prefix")
                ids = sorted((original - {outgoing}) | {incoming})
            else:
                ordinal, outer = self.original.exchange_position(original, outgoing, incoming)
                require(
                    ordinal <= final["last_evaluated_ordinal"] and outer <= final["outer_started"],
                    "neutral past evaluated prefix",
                )
                require(
                    type(row["shell_ordinal"]) is int and row["shell_ordinal"] == ordinal,
                    "neutral shell ordinal",
                )
                ids = sorted((original - set(outgoing)) | set(incoming))
            require(
                type(row["neutral_ordinal"]) is int and row["neutral_ordinal"] == ordinal,
                "neutral ordinal mismatch",
            )
            require(
                type(row["neutral_index"]) is int and 1 <= row["neutral_index"] <= meta["retained"],
                "neutral traversal index",
            )
            require(
                isinstance(row["ids"], list)
                and all(type(i) is int for i in row["ids"])
                and row["ids"] == ids,
                "neutral full-family IDs",
            )
            actual = self.original.inspect_family(ids, cores)
            require(
                json.dumps(actual["metrics"], sort_keys=True)
                == json.dumps(row["metrics"], sort_keys=True)
                and self.original.legal(actual["metrics"]),
                "neutral metrics or legality",
            )
            require(
                [actual["metrics"]["holes"], actual["metrics"]["D2max"]] == baseline,
                "candidate is not neutral",
            )
            actual.update(
                {
                    "outgoing": outgoing,
                    "incoming": incoming,
                    "ids": ids,
                    "neutral_index": row["neutral_index"],
                    "neutral_ordinal": ordinal,
                }
            )
            if self.kind == "two":
                actual["shell_ordinal"] = ordinal
            else:
                actual["ordinal"] = ordinal
            checked.append(actual)
        tuples = [tuple(row["ids"]) for row in checked]
        require(tuples == sorted(set(tuples)), "neutral family order or duplicate")
        traversal = sorted(checked, key=lambda row: row["neutral_index"])
        require(
            [row["neutral_index"] for row in traversal] == list(range(1, len(rows) + 1)),
            "neutral index coverage",
        )
        require(
            all(
                a["neutral_ordinal"] < b["neutral_ordinal"]
                for a, b in zip(traversal, traversal[1:])
            ),
            "neutral traversal order",
        )
        require(
            not {row["sha256"] for row in checked}
            & {row["sha256"] for row in audit["audited_families"]},
            "strict-neutral alias",
        )
        audit["audited_families"].extend(checked)
        audit.update(
            {
                "neutral_families": checked,
                "neutral_metadata": meta,
                "strict_validator_reused_without_changes": True,
                "neutral_scope": "First at most64 neutral families in deterministic traversal, "
                "then sorted by full-family IDs; not globally smallest64.",
            }
        )
        return audit
