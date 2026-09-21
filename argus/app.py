"""Minimal command-line entry point for the ARGUS foundation."""

from __future__ import annotations

import argparse
import json

from argus.config.logging import configure_logging, get_logger
from argus.config.settings import get_settings
from argus.graph.graph import InvestigationGraph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARGUS intelligence investigation foundation")
    parser.add_argument("--query", required=True, help="Executive or analyst question to investigate")
    parser.add_argument("--pretty", action="store_true", help="Print the formatted executive report")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger(__name__)
    state = InvestigationGraph().run(args.query)
    logger.info("initialized_investigation", extra={"query": args.query})
    if args.pretty:
        print(state["final_report"])
    else:
        print(json.dumps(state, separators=(",", ":")))


if __name__ == "__main__":
    main()
