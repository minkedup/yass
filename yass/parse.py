"""
Parse scraped data into an AST.
"""

import re
import datetime

from yass.ast import (
    Ast,
    Period,
    PeriodIdx,
    Route,
    RouteIdx,
    Stop,
    StopIdx,
    TimeTable,
    TimeTableIdx,
    TimeTableCell,
    SubPeriod,
    SubPeriodIdx,
    StopPart,
)
from yass.scrape.types import (
    ScrapedPeriod,
    ScrapedSubPeriod,
    ScrapedSubPeriodIdx,
    ScrapedRoute,
    ScrapedRouteIdx,
    ScrapedTimeTable,
    ScrapedTimeTableCell,
    ScrapedTimeTableColumn,
)
from yass.scrape.periods import PeriodsScrape
from yass.scrape.timetables import TimeTablesScrape


class AstBuilder:
    """
    Utility class for building an AST.
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

    def __init__(self) -> None:
        self.routes = []
        self.stops = []
        self.time_tables = []

        self.periods = []
        self.sub_periods = []

        self.route_stops = {}
        self.route_time_table = {}

        self.period_to_sub_periods = {}
        self.sub_period_routes = {}

    def finish(self) -> Ast:
        """
        Finish building and create a new AST.
        """

        return Ast(
            routes=self.routes,
            stops=self.stops,
            time_tables=self.time_tables,
            periods=self.periods,
            sub_periods=self.sub_periods,
            route_stops=self.route_stops,
            route_time_table=self.route_time_table,
            period_to_sub_periods=self.period_to_sub_periods,
            sub_period_routes=self.sub_period_routes,
        )


RAW_PERIOD_FLUFF_RE = re.compile(" *[Ss]huttle *[Ss]chedule")


def _period(s_period: ScrapedPeriod) -> Period:
    r_name = s_period.name
    name = RAW_PERIOD_FLUFF_RE.sub("", r_name).strip()

    return Period(name)


RAW_SUB_PERIOD_FLUFF_RE = re.compile("[Ss]huttle [Ss]chedules and [Mm]aps")


def _sub_period(s_sub_period: ScrapedSubPeriod) -> SubPeriod:
    r_name = s_sub_period.name
    name = RAW_SUB_PERIOD_FLUFF_RE.sub("", r_name).strip()

    return SubPeriod(name)


RAW_ROUTE_RE = re.compile("^ *([0-9]*) *(.*)")
RAW_ROUTE_DATE_RE = re.compile(r"^ *Begins *([0-9]*\/[0-9]*\/[0-9]*) *$")


def _route(s_route: ScrapedRoute) -> Route:
    r_name = s_route.name

    match = RAW_ROUTE_RE.match(r_name)
    assert match is not None

    code = int(match[1])
    name = match[2]

    b_match = (
        RAW_ROUTE_DATE_RE.match(s_route.begins) if s_route.begins is not None else None
    )

    if b_match is not None:
        r_date = b_match[1]
        p_date_time = datetime.datetime.strptime(r_date, "%m/%d/%Y")

        p_date = p_date_time.date()
    else:
        p_date = None

    return Route(code, name, p_date)


LAST_WORD_RE = re.compile("(.*) (.*)$")


def _stop(s_time_table_col: ScrapedTimeTableColumn) -> tuple[Stop, StopPart | None]:
    last_match = LAST_WORD_RE.match(s_time_table_col)
    last = last_match[2] if last_match is not None else None

    last_lower = last.lower() if last is not None else None

    try:
        stop_part = StopPart(last_lower)

        assert last_match is not None
        stop = last_match[1].strip()
    except ValueError:
        stop_part = None
        stop = s_time_table_col

    return (stop, stop_part)


RAW_CELL_TIME_FORMAT = "%I:%M %p"


def _time_table_n_stop(
    builder: AstBuilder, s_time_table: ScrapedTimeTable
) -> TimeTable:
    u_stops = set(builder.stops)
    r_columns = list(map(_stop, s_time_table.columns))

    cols = []

    for stop, stop_part in r_columns:
        if stop in u_stops:
            # TODO: avoid having to do this lookup on misses
            stop_idx = StopIdx(builder.stops.index(stop))
        else:
            stop_idx = StopIdx(len(builder.stops))
            builder.stops.append(stop)

            u_stops.add(stop)

        cols.append((stop_idx, stop_part))

    def _time_table_cell(s_time_table_cell: ScrapedTimeTableCell) -> TimeTableCell:
        if s_time_table_cell is None:
            return None

        date_time = datetime.datetime.strptime(s_time_table_cell, RAW_CELL_TIME_FORMAT)
        return date_time.time()

    time_matrix = list(
        map(lambda row: list(map(_time_table_cell, row)), s_time_table.values)
    )
    return TimeTable(cols, time_matrix)


def parse_ast(s_periods: PeriodsScrape, s_time_tables: TimeTablesScrape) -> Ast:
    """
    Parse scraped data into a cohesive AST.
    """

    builder = AstBuilder()

    for s_period_idx, s_period in enumerate(s_periods.periods):
        s_route_idx_to_s_time_table = s_time_tables[s_period_idx]

        period = _period(s_period)

        period_idx = PeriodIdx(len(builder.periods))
        builder.periods.append(period)

        builder.period_to_sub_periods[period_idx] = []

        s_collect = s_periods.period_parts[s_period_idx]

        for s_sub_period_idx, s_sub_period in enumerate(s_collect.sub_periods):
            sub_period = _sub_period(s_sub_period)

            sub_period_idx = SubPeriodIdx(len(builder.sub_periods))
            builder.sub_periods.append(sub_period)

            builder.period_to_sub_periods[period_idx].append(sub_period_idx)
            builder.sub_period_routes[sub_period_idx] = []

            s_route_idxs: list[ScrapedRouteIdx] = s_collect.sub_period_to_routes[
                ScrapedSubPeriodIdx(s_sub_period_idx)
            ]

            for s_route_idx in s_route_idxs:
                s_route: ScrapedRoute = s_collect.routes[s_route_idx]
                route = _route(s_route)

                route_idx = RouteIdx(len(builder.routes))
                builder.routes.append(route)

                builder.sub_period_routes[sub_period_idx].append(route_idx)

                s_time_table = s_route_idx_to_s_time_table[s_route_idx]

                time_table = _time_table_n_stop(builder, s_time_table)

                time_table_idx = TimeTableIdx(len(builder.time_tables))
                builder.time_tables.append(time_table)

                builder.route_time_table[route_idx] = time_table_idx

    return builder.finish()
