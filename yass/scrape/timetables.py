"""
Scrape Timetable information from Routes.
"""

from typing import Sequence, TypeAlias, Literal, cast
import re
import dataclasses
import urllib.parse

import lxml.html

from yass.types import ScrapeContext
from yass.const import ROOT_SCHEDULE_URL
from yass.scrape.schedules import RawRoute

STOP_POSTFIX_RE = re.compile("(.*) (Arrival|Departure)$")

RawStop: TypeAlias = str
RawPart: TypeAlias = Literal["Arrival"] | Literal["Departure"] | None

RawColumn: TypeAlias = tuple[RawStop, str | None]
RawCell: TypeAlias = str | None


@dataclasses.dataclass(frozen=True)
class TimetableScrape:
    """
    The Timetable.
    """

    columns: Sequence[RawColumn]
    values: Sequence[Sequence[RawCell]]


def scrape_timetable(ctx: ScrapeContext, route: RawRoute) -> TimetableScrape:
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

    columns: list[RawColumn] = []
    values: list[list[RawCell]] = []

    for th_el in th_els:
        stripped = th_el.text.strip()
        match = STOP_POSTFIX_RE.match(stripped)

        name: RawStop = stripped if match is None else match[1]
        part: RawPart = None if match is None else cast(RawPart, match[2])

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

    return TimetableScrape(columns, values)
