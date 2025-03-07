"""
Parse Schedules from the main campus shuttles page.
"""

from typing import Sequence, cast
import re
import dataclasses

import lxml.html

from yass.types import ScrapeContext
from yass.const import ROOT_SCHEDULE_URL

from yass.scrape.types import (
    ScrapedPeriodParts,
    ScrapedSubPeriodIdx,
    ScrapedRouteIdx,
    ScrapedPeriod,
    ScrapedSubPeriod,
    ScrapedRoute,
)

ROUTE_LINK_RE = re.compile(r"^[0-9]{1,2} .*$")


@dataclasses.dataclass
class PeriodsScrape:
    """
    Scrapes from the main page.
    """

    periods: Sequence[ScrapedPeriod]
    period_parts: Sequence[ScrapedPeriodParts]


def _get_h3_group(
    period_h3_el: lxml.html.Element,
) -> lxml.html.Element:
    """
    A schedule is an <h3>; it is wrapped by a <div> (the wrapper); that
    wrapper is inside of another <div>; the child after us (the other <div>
    in the same group as the wrapper) is what we're after.
    """

    wrapper = period_h3_el.getparent()
    assert wrapper is not None

    group = wrapper.getparent()
    assert group is not None

    # NOTE: assert that it is just the wrapper and another thing in the
    # group; we assume that the element we're looking for comes after us
    assert len(group) == 2
    other = group[1]

    return other


def _grp_parts(ctx: ScrapeContext, grp: lxml.html.Element) -> ScrapedPeriodParts:
    def _try_ext_sub_period(tlt: lxml.html.Element) -> ScrapedSubPeriod | None:
        if tlt.tag == "h4":
            text = tlt.text.strip()
            return ScrapedSubPeriod(text)
        return None

    def _try_ext_route(tlt: lxml.html.Element) -> ScrapedRoute | None:
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
            ctx.logger.warning("route '%s' doesn't have a valid href attribute", text)
            return None

        return ScrapedRoute(text, attributes["href"], begins)

    def _try_ext(
        div: lxml.html.Element,
    ) -> ScrapedSubPeriod | ScrapedRoute | None:
        """
        Extract sub-periods (e.g. weekday) and routes (e.g. 1 off campus
        express).
        """
        if len(div) != 1:
            return None

        tlt = div[0]
        m_sub_period = _try_ext_sub_period(tlt)
        if m_sub_period is not None:
            return m_sub_period

        m_route = _try_ext_route(tlt)
        return m_route

    routes: list[ScrapedRoute] = []
    sub_periods: list[ScrapedSubPeriod] = []

    sub_period_to_routes: dict[ScrapedSubPeriodIdx | None, list[ScrapedRouteIdx]] = {}
    sub_period_to_routes[None] = []

    c_sub_period: ScrapedSubPeriodIdx | None = None

    for div in grp:
        m_something = _try_ext(div)
        if m_something is None:
            continue

        if isinstance(m_something, ScrapedSubPeriod):
            i_sub_period = ScrapedSubPeriodIdx(len(sub_periods))
            sub_periods.append(m_something)

            c_sub_period = i_sub_period
            sub_period_to_routes[c_sub_period] = []
            continue

        i_route = ScrapedRouteIdx(len(routes))
        routes.append(m_something)

        sub_period_to_routes[c_sub_period].append(i_route)

    return ScrapedPeriodParts(routes, sub_periods, sub_period_to_routes)


def scrape_periods(ctx: ScrapeContext) -> PeriodsScrape:
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

    def scrape_period(h3_el: lxml.html.Element) -> ScrapedPeriod:
        text = h3_el.text.strip()
        return ScrapedPeriod(text)

    period_h3_els = list(filter(is_period_el, h3_els))

    periods = list(map(scrape_period, period_h3_els))
    period_parts = []

    period_grps = map(_get_h3_group, period_h3_els)
    for period_grp in period_grps:
        parts = _grp_parts(ctx, period_grp)
        period_parts.append(parts)

    return PeriodsScrape(periods, period_parts)
