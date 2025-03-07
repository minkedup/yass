"""
Scraping Types.
"""

from typing import TypeAlias
import dataclasses


@dataclasses.dataclass(frozen=True)
class ScrapedPeriod:
    """
    A Schedule (e.g. "Spring 2025 Shuttle Schedule").
    """

    name: str


@dataclasses.dataclass(frozen=True)
class ScrapedSubPeriod:
    """
    A Period (e.g. "Weekday Shuttle Schedules and Maps", "Weekend Shuttle
    Schedules and Maps").
    """

    name: str


@dataclasses.dataclass(frozen=True)
class ScrapedRoute:
    """
    A Route (e.g. "1 Off Campus Express").
    """

    name: str
    href: str
    begins: str | None


ScrapedStop: TypeAlias = str
ScrapedStopPart: TypeAlias = str | None

ScrapedColumn: TypeAlias = tuple[ScrapedStop, str | None]
ScrapedCell: TypeAlias = str | None
