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
    ScheduleScrape,
    ScrapedSubPeriod,
    ScrapedRoute,
    scrape_schedules,
)
from yass.scrape.timetables import TimetableScrape, scrape_timetable


def ext_routes(scraped: ScheduleScrape) -> frozenset[ScrapedRoute]:
    """
    Get all RawRoutes in a ScheduleScrape.
    """
    schedules = scraped.schedules

    period_to_routes: Iterable[
        dict[ScrapedSubPeriod, MutableSequence[ScrapedRoute]]
    ] = schedules.values()

    def extract(
        mapping: dict[ScrapedSubPeriod, MutableSequence[ScrapedRoute]],
    ) -> Iterable[ScrapedRoute]:
        return itertools.chain.from_iterable(mapping.values())

    iterable: Iterable[Iterable[ScrapedRoute]] = map(extract, period_to_routes)
    routes: Iterable[ScrapedRoute] = itertools.chain.from_iterable(iterable)

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

    schedule_scrape = scrape_schedules(ctx)
    routes = ext_routes(schedule_scrape)

    route_to_timetable: dict[ScrapedRoute, TimetableScrape] = {}

    for route in routes:
        timetable_scrape = scrape_timetable(ctx, route)
        route_to_timetable[route] = timetable_scrape
