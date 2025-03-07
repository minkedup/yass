"""
Scraping Types.
"""

from typing import TypeAlias, Sequence, NewType
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


ScrapedRouteIdx = NewType("ScrapedRouteIdx", int)
ScrapedSubPeriodIdx = NewType("ScrapedSubPeriodIdx", int)


@dataclasses.dataclass(frozen=True)
class ScrapedPeriodParts:
    """
    The scraped sub-components of a period.
    """

    routes: Sequence[ScrapedRoute]
    sub_periods: Sequence[ScrapedSubPeriod]
    sub_period_to_routes: dict[ScrapedSubPeriodIdx | None, list[ScrapedRouteIdx]]


ScrapedStop: TypeAlias = str
ScrapedStopPart: TypeAlias = str | None

ScrapedTimeTableColumn: TypeAlias = tuple[ScrapedStop, str | None]
ScrapedTimeTableCell: TypeAlias = str | None


@dataclasses.dataclass(frozen=True)
class ScrapedTimeTable:
    """
    The Timetable.
    """

    columns: Sequence[ScrapedTimeTableColumn]
    values: Sequence[Sequence[ScrapedTimeTableCell]]
