"""
Yet Another (RIT Bus) Schedule Scraper.
"""

from typing import MutableSequence, TypeAlias, Literal, cast
import re
import sys
import logging
import argparse
import dataclasses

import requests
import lxml.html

from yass.types import ScrapeContext
from yass.schedules import scrape_schedules


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
    print(schedules)
