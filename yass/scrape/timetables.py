"""
Scrape Timetable information from Routes.
"""

from typing import Sequence, cast
import re
import dataclasses
import urllib.parse

import lxml.html

from yass.types import ScrapeContext
from yass.const import ROOT_SCHEDULE_URL

from yass.scrape.types import (
    ScrapedStop,
    ScrapedStopPart,
    ScrapedTimeTableColumn,
    ScrapedTimeTableCell,
    ScrapedRoute,
    ScrapedRouteIdx,
)
from yass.scrape.schedules import PeriodScrape

STOP_POSTFIX_RE = re.compile("(.*) *(.*)$")


@dataclasses.dataclass(frozen=True)
class ScrapedTimeTable:
    """
    The Timetable.
    """

    columns: Sequence[ScrapedTimeTableColumn]
    values: Sequence[Sequence[ScrapedTimeTableCell]]


def scrape_time_table(ctx: ScrapeContext, route: ScrapedRoute) -> ScrapedTimeTable:
    """
    Scrape Timetables from a route-specific page.
    """
    base = urllib.parse.urlparse(ROOT_SCHEDULE_URL)

    # NOTE: asserts that the route's href is absolute
    assert route.href.startswith("/")
    raw = base._replace(path=route.href)

    href = urllib.parse.urlunparse(raw)

    ctx.logger.info(f"GET {href}")
    response = ctx.session.get(href)

    assert response.ok

    tree: lxml.html.HtmlElement = lxml.html.fromstring(response.text)
    query = tree.xpath("//body/descendant::table[1]")

    assert isinstance(query, list)
    (table, *_) = cast(list[lxml.html.Element], query)

    th_els = table.xpath("//thead[1]//th")
    stops: set[str] = set()

    columns: list[ScrapedTimeTableColumn] = []
    values: list[list[ScrapedTimeTableCell]] = []

    for th_el in th_els:
        stripped = th_el.text.strip()
        match = STOP_POSTFIX_RE.match(stripped)

        name: ScrapedStop = stripped if match is None else match[1]
        part: ScrapedStopPart = (
            None if match is None else cast(ScrapedStopPart, match[2])
        )

        stops.add(name)
        columns.append((name, part))

    row_els = table.xpath("//tbody[1]//tr")
    for i, row_el in enumerate(row_els):
        col_els = list(row_el.iterchildren())

        # pre-fill a list with None values of an appropriate size
        values.append([None] * len(columns))

        for j in range(len(columns)):
            if j >= len(col_els):
                continue

            value = col_els[j].text.strip()
            values[i][j] = value

    return ScrapedTimeTable(columns, values)


def scrape_time_tables(
    ctx: ScrapeContext, scrape: PeriodScrape
) -> Sequence[dict[ScrapedRouteIdx, ScrapedTimeTable]]:
    """
    Scrape the TimeTables for each Route within a ScrapedGroupParts.
    """

    part_timetables = []

    for part in scrape.period_parts:
        route_idx_to_time_table: dict[ScrapedRouteIdx, ScrapedTimeTable] = {}

        for i, route in enumerate(part.routes):
            idx = ScrapedRouteIdx(i)

            time_table = scrape_time_table(ctx, route)
            route_idx_to_time_table[idx] = time_table

        part_timetables.append(route_idx_to_time_table)

    return part_timetables
