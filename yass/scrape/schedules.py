"""
Parse Schedules from the main campus shuttles page.
"""

from typing import MutableSequence, cast
import re
import dataclasses

import lxml.html

from yass.types import ScrapeContext
from yass.const import ROOT_SCHEDULE_URL

from yass.scrape.types import ScrapedPeriod, ScrapedSubPeriod, ScrapedRoute

ROUTE_LINK_RE = re.compile(r"^[0-9]{1,2} .*$")


@dataclasses.dataclass
class PeriodScrape:
    """
    Scrapes from the main page.
    """

    periods: dict[ScrapedPeriod, dict[ScrapedSubPeriod, MutableSequence[ScrapedRoute]]]


def _get_h3_group(
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


def scrape_periods(ctx: ScrapeContext) -> PeriodScrape:
    """
    Scrape schedules from the root page to discover existing routes.
    """

    ctx.logger.info(f"GET {ROOT_SCHEDULE_URL}")
    response = ctx.session.get(ROOT_SCHEDULE_URL)
    assert response.ok

    tree: lxml.html.HtmlElement = lxml.html.fromstring(response.text)
    query = tree.xpath("//body/descendant::h3")

    assert isinstance(query, list)
    h3_els = cast(list[lxml.html.Element], query)

    def is_period_el(h3_el: lxml.html.Element) -> bool:
        return h3_el.text.strip().endswith("Shuttle Schedule")

    period_h3_els = list(filter(is_period_el, h3_els))

    def try_extract(
        group: lxml.html.Element,
    ) -> ScrapedSubPeriod | ScrapedRoute | None:
        """
        Extract periods (e.g. weekday shuttle) and routes (e.g. 1 off campus
        express) from deeply nested divs.
        """
        if len(group) != 1:
            return None

        tlt = group[0]
        if tlt.tag == "h4":
            text = tlt.text.strip()
            return ScrapedSubPeriod(text)

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

        return ScrapedRoute(text, attributes["href"], begins)

    period_grps = map(_get_h3_group, period_h3_els)
    period_to_sub_periods = {}

    for period_el, neighbor in zip(period_h3_els, period_grps):
        s_period = ScrapedPeriod(period_el.text)

        current_sub_period = None
        sub_period_to_routes: dict[ScrapedSubPeriod, MutableSequence[ScrapedRoute]] = {}

        for div in neighbor:
            maybe_raw = try_extract(div)
            if maybe_raw is None:
                continue

            if isinstance(maybe_raw, ScrapedSubPeriod):
                sub_period_to_routes[maybe_raw] = []
                current_sub_period = maybe_raw
                continue

            if current_sub_period is None:
                ctx.logger.warning(
                    "could not find a matching period for route %s", maybe_raw
                )
                continue

            sub_period_to_routes[current_sub_period].append(maybe_raw)

        period_to_sub_periods[s_period] = sub_period_to_routes

    return PeriodScrape(period_to_sub_periods)
