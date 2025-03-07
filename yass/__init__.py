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


def main() -> None:
    """
    Parse arguments and run Scraper.
    """

    parser = argparse.ArgumentParser(prog="yass")
    _args = parser.parse_args()

    root = logging.getLogger()
    root.setLevel(logging.WARNING)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)

    session = requests.Session()
    ctx = ScrapeContext(root, session)

    schedules = scrape_schedules(ctx)
    routes = ext_routes(scraped)
