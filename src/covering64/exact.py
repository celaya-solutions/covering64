"""Unrestricted covering feasibility and a proof-ready Boolean encoding.

CP-SAT is useful for construction and bounded exploration. Its INFEASIBLE
status is not an independently checked nonexistence certificate. For that
purpose, export CNF, run a proof-producing SAT solver, and check its proof
against the unchanged CNF using a separate checker.
"""

from __future__ import annotations

import hashlib
import math
import platform
from pathlib import Path
from typing import Iterable

from .core import Universe, verify_cover


def _check_target(universe: Universe, target: int) -> None:
    if isinstance(target, bool) or not isinstance(target, int):
        raise ValueError("target must be an integer")
    if not 0 <= target <= len(universe.blocks):
        raise ValueError(f"target must be between 0 and {len(universe.blocks)}")


def _hint_indices(
    universe: Universe, hint: Iterable[Iterable[int]] | None
) -> set[int] | None:
    """Validate a partial or complete incumbent without assuming coverage."""
    if hint is None:
        return None
    block_index = {block: index for index, block in enumerate(universe.blocks)}
    indices: set[int] = set()
    for block in hint:
        raw = tuple(block)
        if any(isinstance(point, bool) or not isinstance(point, int) for point in raw):
            raise ValueError("hint block labels must be integers")
        canonical = tuple(sorted(raw))
        if canonical not in block_index:
            raise ValueError(f"hint contains an invalid block: {raw}")
        index = block_index[canonical]
        if index in indices:
            raise ValueError(f"hint contains a duplicate block: {canonical}")
        indices.add(index)
    return indices


def solve_exact(
    universe: Universe,
    target: int,
    seconds: float = 30,
    seed: int = 0,
    workers: int = 1,
    hint: Iterable[Iterable[int]] | None = None,
    fix_first_block: bool = False,
) -> dict:
    """Search all blocks for a cover consisting of exactly ``target`` blocks.

    ``hint`` is a distinct family of valid blocks and need not cover the
    universe. It is a suggestion to the solver, never a restriction. With
    ``fix_first_block=True`` the lexicographically first block is selected.
    This preserves existence: every nonempty cover can be relabeled by a
    point permutation to contain that block. The default applies no such
    normalization. Multiple workers may make otherwise seeded runs vary.
    """
    _check_target(universe, target)
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be finite and positive")
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError("workers must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**31 - 1:
        raise ValueError("seed must be an integer between 0 and 2**31 - 1")
    hint_indices = _hint_indices(universe, hint)

    import ortools
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"block_{i + 1}") for i in range(len(universe.blocks))]
    for containing in universe.containing:
        model.add_bool_or([selected[index] for index in containing])
    model.add(sum(selected) == target)
    if fix_first_block:
        model.add(selected[0] == 1)
    if hint_indices is not None:
        for index, variable in enumerate(selected):
            model.add_hint(variable, int(index in hint_indices))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed
    solver.parameters.num_search_workers = workers
    status = solver.solve(model)
    report = {
        "method": "cp-sat",
        "status": solver.status_name(status),
        "parameters": {"v": universe.v, "k": universe.k, "t": universe.t},
        "target": target,
        "settings": {
            "seconds": seconds,
            "seed": seed,
            "workers": workers,
            "fix_first_block": fix_first_block,
            "hint_blocks": None if hint_indices is None else len(hint_indices),
            "cardinality": "exactly target distinct blocks",
        },
        "block_variables": len(selected),
        "coverage_constraints": len(universe.containing),
        "wall_time_seconds": solver.wall_time,
        "branches": solver.num_branches,
        "conflicts": solver.num_conflicts,
        "response_stats": solver.response_stats(),
        "solver_version": ortools.__version__,
        "python_version": platform.python_version(),
        "proof_generated": False,
        "proof_note": "CP-SAT status alone is not an independently checked UNSAT certificate.",
        "witness": None,
        "verification": None,
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        witness = [
            block for block, variable in zip(universe.blocks, selected) if solver.value(variable)
        ]
        verification = verify_cover(witness, v=universe.v, k=universe.k, t=universe.t)
        if len(witness) != target or not verification["valid"]:
            raise RuntimeError("CP-SAT returned a witness that failed deterministic validation")
        report["witness"] = [list(block) for block in witness]
        report["verification"] = verification
    return report


def write_cnf(
    universe: Universe,
    target: int,
    path: str | Path,
    fix_first_block: bool = False,
) -> dict:
    """Export covering clauses and a sequential-counter at-most constraint.

    Block ``universe.blocks[i]`` corresponds to DIMACS variable ``i + 1``.
    All cardinality auxiliary variables have higher numbers. At most
    ``target`` is equisatisfiable with exactly ``target`` because any smaller
    distinct covering family can be padded with unused candidate blocks;
    validation therefore requires 0 <= target <= the number of candidates.

    The normalization flag is safe by point relabeling, as in ``solve_exact``.
    A checked UNSAT proof at target 64 for (16, 5, 3) would rule out all covers
    with at most 64 blocks. Merely writing this file proves nothing.
    """
    _check_target(universe, target)
    import pysat
    from pysat.card import CardEnc, EncType

    block_variables = len(universe.blocks)
    cardinality = CardEnc.atmost(
        lits=list(range(1, block_variables + 1)),
        bound=target,
        top_id=block_variables,
        encoding=EncType.seqcounter,
    )
    variables = max(block_variables, cardinality.nv)
    clauses = len(universe.containing) + len(cardinality.clauses) + int(fix_first_block)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with destination.open("wb") as output:
        def emit(line: str) -> None:
            encoded = line.encode("ascii")
            output.write(encoded)
            digest.update(encoded)

        emit(f"c Covering C({universe.v},{universe.k},{universe.t}) at most {target} blocks\n")
        emit("c Block variables are 1-based lexicographic block indices.\n")
        emit("c Auxiliary variables encode an at-most sequential counter.\n")
        emit(f"c fix_first_block {str(fix_first_block).lower()}\n")
        emit(f"p cnf {variables} {clauses}\n")
        for containing in universe.containing:
            emit(" ".join(str(index + 1) for index in containing) + " 0\n")
        if fix_first_block:
            emit("1 0\n")
        for clause in cardinality.clauses:
            emit(" ".join(map(str, clause)) + " 0\n")

    return {
        "path": str(destination),
        "sha256": digest.hexdigest(),
        "parameters": {"v": universe.v, "k": universe.k, "t": universe.t},
        "target": target,
        "variables": variables,
        "block_variables": block_variables,
        "auxiliary_variables": variables - block_variables,
        "clauses": clauses,
        "coverage_clauses": len(universe.containing),
        "cardinality_clauses": len(cardinality.clauses),
        "symmetry_clauses": int(fix_first_block),
        "fix_first_block": fix_first_block,
        "cardinality_encoding": "sequential counter",
        "cardinality_semantics": (
            "at most target; equivalent to exact target by padding with unused blocks"
        ),
        "encoder_version": pysat.__version__,
        "proof_generated": False,
    }
