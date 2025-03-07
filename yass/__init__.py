"""
Yet Another (RIT Bus) Schedule Scraper.
"""

from typing import MutableSequence, TypeAlias, Iterable, Literal, Any, cast
import re
import sys
import json
import enum
import logging
import argparse
import datetime
import itertools
import dataclasses

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


def main() -> None:
    """
    Parse arguments and run Scraper.
    """

    parser = argparse.ArgumentParser(prog="yass")
    parser.add_argument(
        "-v", "--verbose", help="enable more verbose output", action="store_true"
    )
    args = parser.parse_args()

    logger = get_logger(args.verbose)
    session = requests.Session()
    ctx = ScrapeContext(logger, session)

    s_periods = scrape_periods(ctx)
    s_time_tables = scrape_time_tables(ctx, s_periods)

    ast = parse_ast(s_periods, s_time_tables)

    def encode(thing: Any):
        if dataclasses.is_dataclass(thing):
            return dataclasses.asdict(thing)  # type: ignore
        if isinstance(thing, datetime.date):
            return thing.isoformat()
        if isinstance(thing, datetime.time):
            return thing.isoformat()
        if isinstance(thing, enum.Enum):
            return thing.value

        return None

    print(json.dumps(ast, indent=4, default=encode))
