"""
Yet Another (RIT Bus) Schedule Scraper.
"""

from typing import MutableSequence, TypeAlias, Iterable, Literal, cast
import re
import sys
import logging
import argparse
import itertools
import dataclasses

import requests
import lxml.html

from yass.types import ScrapeContext
from yass.schedules import ScheduleScrape, RawPeriod, RawRoute, scrape_schedules


def ext_routes(scraped: ScheduleScrape) -> frozenset[RawRoute]:
    """
    Get all RawRoutes in a ScheduleScrape.
    """
    schedules = scraped.schedules

    period_to_routes: Iterable[dict[RawPeriod, MutableSequence[RawRoute]]] = (
        schedules.values()
    )

    def extract(
        mapping: dict[RawPeriod, MutableSequence[RawRoute]]
    ) -> Iterable[RawRoute]:
        return itertools.chain.from_iterable(mapping.values())

    iterable: Iterable[Iterable[RawRoute]] = map(extract, period_to_routes)
    routes: Iterable[RawRoute] = itertools.chain.from_iterable(iterable)

    return frozenset(routes)


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

    schedules = scrape_schedules(ctx)
    routes = ext_routes(scraped)
