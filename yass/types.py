"""
Shared type definitions.
"""

import logging
import dataclasses

import requests


@dataclasses.dataclass
class ScrapeContext:
    """
    Scraping Context.
    """

    logger: logging.Logger
    session: requests.Session
