"""
Scraping Types.
"""

from typing import TypeAlias, Literal
import dataclasses


@dataclasses.dataclass(frozen=True)
class RawSchedule:
    """
    A Schedule (e.g. "Spring 2025 Shuttle Schedule").
    """

    name: str


@dataclasses.dataclass(frozen=True)
class RawPeriod:
    """
    A Period (e.g. "Weekday Shuttle Schedules and Maps", "Weekend Shuttle
    Schedules and Maps").
    """

    name: str


@dataclasses.dataclass(frozen=True)
class RawRoute:
    """
    A Route (e.g. "1 Off Campus Express").
    """

    name: str
    href: str
    begins: str | None


RawStop: TypeAlias = str
RawPart: TypeAlias = Literal["Arrival"] | Literal["Departure"] | None

RawColumn: TypeAlias = tuple[RawStop, str | None]
RawCell: TypeAlias = str | None
