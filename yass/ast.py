"""
An AST.
"""

from typing import TypeAlias, NewType, Literal
import enum
import datetime
import dataclasses

import serde


class StopPart(enum.Enum):
    """
    A part of a Stop (e.g. Gleason Circle *Arrival*).
    """

    UNKNOWN = 0
    ARRIVAL = 1
    DEPARTURE = 2


Stop: TypeAlias = str
StopIdx = NewType("StopIdx", int)


TimeTableColumn: TypeAlias = tuple[StopIdx, StopPart]
TimeTableCell: TypeAlias = datetime.time | Literal["none"]


@serde.serde
class TimeTable:
    """
    A TimeTable (mapping of Stop + StopPart to rows of times).
    """

    cols: list[TimeTableColumn]
    time_matrix: list[list[TimeTableCell]]


TimeTableIdx = NewType("TimeTableIdx", int)


@serde.serde
class SubPeriod:
    """
    A SubPeriod (e.g. Weekday, Weekend).
    """

    name: str


SubPeriodIdx = NewType("SubPeriodIdx", int)


@serde.serde
class Route:
    """
    A Route (e.g. 3 RIT Inn).
    """

    code: int
    name: str
    begins: datetime.date | None


RouteIdx = NewType("RouteIdx", int)


@serde.serde
class Period:
    """
    A Period (e.g. Spring 2025 Shuttle Schedule).
    """

    name: str


PeriodIdx = NewType("PeriodIdx", int)


@serde.serde
class Ast:
    """
    A cohesive collection of Stops, Routes, Periods, SubPeriods, and TimeTables.
    """

    routes: list[Route]
    stops: list[Stop]
    time_tables: list[TimeTable]

    periods: list[Period]
    sub_periods: list[SubPeriod]

    route_stops: dict[RouteIdx, list[StopIdx]]
    route_time_table: dict[RouteIdx, TimeTableIdx]

    period_to_sub_periods: dict[PeriodIdx, list[SubPeriodIdx]]
    sub_period_routes: dict[SubPeriodIdx, list[RouteIdx]]
