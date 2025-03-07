"""
Yet Another (RIT Bus) Schedule Scraper.
"""

from typing import MutableSequence, TypeAlias, Iterable, Literal, cast
import re
import sys
import json
import logging
import argparse
import itertools
import dataclasses

import requests
import lxml.html

from yass.types import ScrapeContext
from yass.scrape.schedules import (
    PeriodScrape,
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
    part_route_to_timetables = scrape_time_tables(ctx, s_periods)
