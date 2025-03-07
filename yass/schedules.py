"""
"""

from typing import MutableSequence, cast
import re
import dataclasses

import lxml.html

from yass.types import ScrapeContext

ROUTE_LINK_RE = re.compile(r"^[0-9]{1,2} .*$")
RIT_SCHEDULES_URL = "https://www.rit.edu/parking/campus-shuttles"


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


@dataclasses.dataclass
class ScheduleScrape:
    """
    Scraped routes from the main root page.
    """

    schedules: dict[RawSchedule, dict[RawPeriod, MutableSequence[RawRoute]]]


def scrape_schedules(ctx: ScrapeContext) -> ScheduleScrape:
    """
    Scrape schedules from the root page to discover existing routes.
    """

    response = ctx.session.get(RIT_SCHEDULES_URL)
    assert response.ok

    tree: lxml.html.etree.ElementTree = lxml.html.fromstring(response.text)
    query = tree.xpath("//body/descendant::h3")

    assert isinstance(query, list)
    headers = cast(list[lxml.html.Element], query)

    def is_schedule_header(el: lxml.html.Element) -> bool:
        return el.text.strip().endswith("Shuttle Schedule")

    schedule_els = list(filter(is_schedule_header, headers))

    def get_schedule_neighbor(
        schedule_header_el: lxml.html.Element,
    ) -> lxml.html.Element:
        """
        A schedule is an <h3>; it is wrapped by a <div> (the wrapper); that
        wrapper is inside of another <div>; the child after us (the other <div>
        in the same group as the wrapper) is what we're after.
        """

        wrapper = schedule_header_el.getparent()
        assert wrapper is not None

        group = wrapper.getparent()
        assert group is not None

        # NOTE: assert that it is just the wrapper and another thing in the
        # group; we assume that the element we're looking for comes after us
        assert len(group) == 2
        other = group[1]

        return other

    def try_extract(
        group: lxml.html.Element,
    ) -> RawPeriod | RawRoute | None:
        """
        Extract periods (e.g. weekday shuttle) and routes (e.g. 1 off campus
        express) from deeply nested divs.
        """
        if len(group) != 1:
            return None

        tlt = group[0]
        if tlt.tag == "h4":
            text = tlt.text.strip()
            return RawPeriod(text)

        if len(tlt) != 1:
            return None

        span = tlt[0]
        if len(span) < 1:
            return None

        begins = (
            span[1].text.strip()
            if len(span) > 1 and len(span[1].text.strip()) != 0
            else None
        )

        link = span[0]
        text = link.text.strip()

        if ROUTE_LINK_RE.match(text) is None:
            return None

        attributes = link.attrib
        if "href" not in attributes:
            return None

        return RawRoute(text, attributes["href"], begins)

    schedule_neighbors = map(get_schedule_neighbor, schedule_els)
    schedule_to_periods = {}

    for schedule_el, neighbor in zip(schedule_els, schedule_neighbors):
        schedule = RawSchedule(schedule_el.text)

        cur_period = None
        period_to_routes: dict[RawPeriod, MutableSequence[RawRoute]] = {}

        for div in neighbor:
            maybe_raw = try_extract(div)
            if maybe_raw is None:
                continue

            if isinstance(maybe_raw, RawPeriod):
                period_to_routes[maybe_raw] = []
                cur_period = maybe_raw
                continue

            assert isinstance(maybe_raw, RawRoute)
            if cur_period is None:
                ctx.logger.warning(
                    "could not find a matching period for route %s", maybe_raw
                )
                continue

            period_to_routes[cur_period].append(maybe_raw)

        schedule_to_periods[schedule] = period_to_routes

    return ScheduleScrape(schedule_to_periods)
