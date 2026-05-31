"""CLI-Einstiegspunkt für genesis-agents.

Befehle:
  genesis-agents start --roles all
  genesis-agents start --roles coordinator,transform
  genesis-agents replay --sigillin-id sig_abc123
  genesis-agents status
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .loop import AgentLoop, AgentLoopConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genesis-agents",
        description="HexaAgent — AI-UI-AI Loop CLI",
    )
    sub = parser.add_subparsers(dest="command")

    start_p = sub.add_parser("start", help="Startet den AgentLoop")
    start_p.add_argument(
        "--roles",
        default="all",
        help="Komma-getrennte Rollen: coordinator,transform,philosophy,ui oder 'all'",
    )
    start_p.add_argument(
        "--initial-state",
        type=int,
        default=0,
        help="Initialer Q4-Zustand (0..15)",
    )
    start_p.add_argument("--mock-nats", action="store_true", default=True)

    replay_p = sub.add_parser("replay", help="Replayed ab einem Sigillin")
    replay_p.add_argument("--sigillin-id", required=True)

    sub.add_parser("status", help="Zeigt Agent-Status")

    return parser


ALL_ROLES = ["coordinator", "transform", "philosophy", "ui"]


async def run_start(args: argparse.Namespace) -> None:
    roles = ALL_ROLES if args.roles == "all" else [r.strip() for r in args.roles.split(",")]
    config = AgentLoopConfig(
        roles=roles,
        initial_state_id=args.initial_state,
        mock_nats=args.mock_nats,
    )
    loop = AgentLoop(config)
    print(f"Starte AgentLoop mit Rollen: {roles}")
    print(f"Initialer Q4-Zustand: {config.initial_state_id:04b}")
    print("Ctrl+C zum Beenden.")
    try:
        await loop.start()
    except KeyboardInterrupt:
        await loop.stop()
        print("AgentLoop gestoppt.")


async def run_replay(args: argparse.Namespace) -> None:
    loop = AgentLoop()
    result = await loop.replay(args.sigillin_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


async def run_status(_args: argparse.Namespace) -> None:
    loop = AgentLoop()
    status = loop.status()
    print(json.dumps(status, indent=2, ensure_ascii=False))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "start":
        asyncio.run(run_start(args))
    elif args.command == "replay":
        asyncio.run(run_replay(args))
    elif args.command == "status":
        asyncio.run(run_status(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
