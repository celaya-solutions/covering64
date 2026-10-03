"""Command-line entry points; JSON logs are the default research artifact."""

import argparse
import json
import sys
from pathlib import Path

from covering64.core import Universe, read_blocks, verify_cover, write_blocks


def _parameters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--v", type=int, default=16)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--t", type=int, default=3)
    parser.add_argument("--output", type=Path, help="also save the complete JSON result")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="exhaustively check a witness")
    _parameters(verify)
    verify.add_argument("witness", type=Path)
    verify.add_argument("--expected-blocks", type=int)
    model = commands.add_parser("model", help="describe the complete combinatorial universe")
    _parameters(model)
    audit = commands.add_parser("audit", help="exhaust all deletion and two-to-one exchanges")
    _parameters(audit)
    audit.add_argument("witness", type=Path)
    solve = commands.add_parser("solve", help="bounded unrestricted CP-SAT feasibility search")
    _parameters(solve)
    solve.add_argument("--target", type=int, default=64)
    solve.add_argument("--seconds", type=float, default=30)
    solve.add_argument("--seed", type=int, default=0)
    solve.add_argument("--workers", type=int, default=1)
    solve.add_argument("--hint", type=Path)
    solve.add_argument("--fix-first-block", action="store_true")
    solve.add_argument("--save-witness", type=Path)
    encode = commands.add_parser("encode", help="write a proof-solver DIMACS CNF instance")
    _parameters(encode)
    encode.add_argument("cnf", type=Path)
    encode.add_argument("--target", type=int, default=64)
    encode.add_argument("--fix-first-block", action="store_true")
    search = commands.add_parser("search", help="bounded larger block-exchange search")
    _parameters(search)
    search.add_argument("witness", type=Path)
    search.add_argument("--attempts", type=int, default=20)
    search.add_argument("--remove", type=int, default=4)
    search.add_argument("--seconds-per-attempt", type=float, default=1.0)
    search.add_argument("--seed", type=int, default=0)
    search.add_argument("--save-witness", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = verify_cover(read_blocks(args.witness, args.v, args.k), args.v, args.k, args.t)
            result["expected_blocks"] = args.expected_blocks
            result["expected_block_count_matches"] = (
                args.expected_blocks is None or result["blocks"] == args.expected_blocks
            )
            code = 0 if result["valid"] and result["expected_block_count_matches"] else 1
        else:
            universe = Universe.build(args.v, args.k, args.t)
            code = 0
            if args.command == "model":
                result = universe.summary()
            elif args.command == "audit":
                from covering64.search import audit_small_exchanges

                result = audit_small_exchanges(universe, read_blocks(args.witness, args.v, args.k))
            elif args.command == "solve":
                from covering64.exact import solve_exact

                hint = read_blocks(args.hint, args.v, args.k) if args.hint else None
                result = solve_exact(
                    universe,
                    args.target,
                    seconds=args.seconds,
                    seed=args.seed,
                    workers=args.workers,
                    hint=hint,
                    fix_first_block=args.fix_first_block,
                )
            elif args.command == "encode":
                from covering64.exact import write_cnf

                result = write_cnf(
                    universe, args.target, args.cnf, fix_first_block=args.fix_first_block
                )
            else:
                from covering64.search import run_exchange_search

                result = run_exchange_search(
                    universe,
                    read_blocks(args.witness, args.v, args.k),
                    attempts=args.attempts,
                    remove=args.remove,
                    seconds_per_attempt=args.seconds_per_attempt,
                    seed=args.seed,
                )
            if getattr(args, "save_witness", None) and result.get("witness"):
                write_blocks(args.save_witness, result["witness"])
        serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized)
        print(serialized, end="")
        return code
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
