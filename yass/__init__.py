"""
Yet Another (RIT Bus) Schedule Scraper.
"""

from typing import MutableSequence, TypeAlias, Iterable, Literal, Any, cast
import re
import sys
import enum
import logging
import argparse
import datetime
import itertools
import dataclasses

import serde.json
import requests
import lxml.html

from yass.parse import parse_ast
from yass.types import ScrapeContext
from yass.scrape.periods import (
    PeriodsScrape,
    ScrapedSubPeriod,
    ScrapedRoute,
    scrape_periods,
)
from yass.scrape.timetables import ScrapedTimeTable, scrape_time_tables


def get_logger(verbose: bool) -> logging.Logger:
    """
    Setup and return a Logger.
    """

    level = logging.INFO if verbose else logging.WARNING

    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)

    return root


def scrape(args: argparse.Namespace) -> None:
    """
    scrape subcomman
    """
    logger = get_logger(args.verbose)
    session = requests.Session()
    ctx = ScrapeContext(logger, session)

    s_periods = scrape_periods(ctx)
    s_time_tables = scrape_time_tables(ctx, s_periods)

    ast = parse_ast(s_periods, s_time_tables)

    serialized = serde.json.to_json(ast, indent=4)
    print(serialized)


COMMANDS = {
    "scrape": scrape,
}


def main() -> None:
    """
    Parse arguments and run Scraper.
    """

    parser = argparse.ArgumentParser(prog="yass")
    parser.add_argument(
        "-v", "--verbose", help="enable more verbose output", action="store_true"
    )

    subparsers = parser.add_subparsers(dest="command")
    _scrape_parser = subparsers.add_parser(
        "scrape", help="scrape rit bus schedule and output an ast"
    )
    args = parser.parse_args()

    if not args.command in COMMANDS:
        print(f"error: unrecognized command: {args.command}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[args.command](args)
