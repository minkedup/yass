"""
An AST.
"""

from typing import Sequence, TypeAlias, NewType
import enum
import datetime
import dataclasses


class StopPart(enum.Enum):
    """
    A part of a Stop (e.g. Gleason Circle *Arrival*).
    """

    ARRIVAL = "arrival"
    DEPARTURE = "departure"


Stop: TypeAlias = str
StopIdx = NewType("StopIdx", int)


TimeTableColumn: TypeAlias = tuple[StopIdx, StopPart | None]
TimeTableCell: TypeAlias = datetime.time | None


@dataclasses.dataclass(frozen=True)
class TimeTable:
    """
    A TimeTable (mapping of Stop + StopPart to rows of times).
    """

    cols: Sequence[TimeTableColumn]
    time_matrix: Sequence[Sequence[TimeTableCell]]


TimeTableIdx = NewType("TimeTableIdx", int)


@dataclasses.dataclass(frozen=True)
class SubPeriod:
    """
    A SubPeriod (e.g. Weekday, Weekend).
    """

    name: str


SubPeriodIdx = NewType("SubPeriodIdx", int)


@dataclasses.dataclass(frozen=True)
class Route:
    """
    A Route (e.g. 3 RIT Inn).
    """

    code: int
    name: str
    begins: datetime.date | None


RouteIdx = NewType("RouteIdx", int)


@dataclasses.dataclass(frozen=True)
class Period:
    """
    A Period (e.g. Spring 2025 Shuttle Schedule).
    """

    name: str


PeriodIdx = NewType("PeriodIdx", int)


@dataclasses.dataclass(frozen=True)
class Ast:
    """
    A cohesive collection of Stops, Routes, Periods, SubPeriods, and TimeTables.
    """

    routes: Sequence[Route]
    stops: Sequence[Stop]
    time_tables: Sequence[TimeTable]

    periods: Sequence[Period]
    sub_periods: Sequence[SubPeriod]

    route_stops: dict[RouteIdx, Sequence[StopIdx]]
    route_time_table: dict[RouteIdx, TimeTableIdx]

    period_to_sub_periods: dict[PeriodIdx, Sequence[SubPeriodIdx]]
    sub_period_routes: dict[SubPeriodIdx, Sequence[RouteIdx]]
