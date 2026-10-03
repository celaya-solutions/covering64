#!/usr/bin/env bash
# Verify a solver-produced DRAT proof against the exact CNF used by the solver.
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 INSTANCE.cnf PROOF.drat [CHECK_LOG]" >&2
  echo "Set DRAT_TRIM to a drat-trim executable if it is not on PATH." >&2
  exit 2
fi

cnf=$1
proof=$2
log=${3:-"${proof}.verification.log"}
checker=${DRAT_TRIM:-drat-trim}

[[ -f "$cnf" ]] || { echo "CNF not found: $cnf" >&2; exit 2; }
[[ -f "$proof" ]] || { echo "Proof not found: $proof" >&2; exit 2; }
command -v "$checker" >/dev/null || { echo "Proof checker not found: $checker" >&2; exit 2; }

"$checker" "$cnf" "$proof" >"$log" 2>&1
# Require the checker's explicit success marker as well as its zero exit code.
grep -q '^s VERIFIED' "$log" || { echo "Checker did not report s VERIFIED; see $log" >&2; exit 1; }
echo "DRAT proof verified; checker log: $log"
sha256sum "$cnf" "$proof"
