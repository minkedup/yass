"""
Parse Schedules from the RIT Campus Shuttles page.

Assumes that the main page will have the following layout:

```html
<!-- pair group -->
<div>
    <div>
        <h3>PERIOD_NAME</h3>
    </div>
    <!-- parts group -->
    <div>
        <!-- part_div_n -->
        <div>
            <div>
                <h4>SUB_PERIOD_1</h4>
            </div>
        </div>
        <div>
            <div>
                <span>
                    <a href="ROUTE_HREF">ROUTE_NAME</a>
                    <span>ROUTE_BEGINS</span>
                </span>
            </div>
        </div>
        <!-- ... -->
    </div>
</div>
```
"""

from typing import Sequence, TypeGuard, Optional, cast
import re
import dataclasses

import lxml.html

from yass.types import ScrapeContext
from yass.const import ROOT_SCHEDULE_URL

from yass.scrape.error import ScrapeError
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


def _get_parts_grp_div_el_from_period_h3_el(
    period_h3_el: lxml.html.Element,
) -> lxml.html.Element:
    """
    A schedule is an <h3>; it is wrapped by a <div> (the wrapper); that
    wrapper is inside of another <div>; the child after us (the other <div>
    in the same group as the wrapper) is what we're after.
    """

    def check_el(
        query: Optional[lxml.html.Element], source: lxml.html.Element, e_tag: str
    ) -> TypeGuard[lxml.html.Element]:
        if query is None:
            raise ScrapeError(
                (
                    f"{source.tag} el at line {source.sourceline}"
                    f" has no parent; expected <{e_tag}>"
                )
            ) from None
        if query.tag != e_tag:
            raise ScrapeError(
                (
                    f"{source.tag} el at line {source.sourceline}"
                    f" has tag {query.tag}; expected <{e_tag}>"
                )
            ) from None

        return True

    h3_div_el = period_h3_el.getparent()
    check_el(h3_div_el, period_h3_el, "div")

    pair_grp_div_el = h3_div_el.getparent()
    check_el(pair_grp_div_el, h3_div_el, "div")

    # NOTE: assert that it is just the wrapper and another thing in the
    # group; we assume that the element we're looking for comes after us
    assert len(pair_grp_div_el) == 2
    other_el = pair_grp_div_el[1]

    return other_el


def _scrape_parts_from_part_div_els(
    ctx: ScrapeContext, parts_group_div_el: lxml.html.Element
) -> ScrapedPeriodParts:
    def try_scrape_sub_period(tlt: lxml.html.Element) -> ScrapedSubPeriod | None:
        if tlt.tag == "h4":
            text = tlt.text.strip()
            return ScrapedSubPeriod(text)
        return None

    def try_scrape_route(part_div_el: lxml.html.Element) -> ScrapedRoute | None:
        if len(part_div_el) != 1:
            return None

        span = part_div_el[0]
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

    def try_scrape_part(
        part_div_el: lxml.html.Element,
    ) -> ScrapedSubPeriod | ScrapedRoute | None:
        """
        Extract sub-periods (e.g. weekday) and routes (e.g. 1 off campus
        express).
        """
        if len(part_div_el) != 1:
            return None

        tlt = part_div_el[0]
        m_sub_period = try_scrape_sub_period(tlt)
        if m_sub_period is not None:
            return m_sub_period

        m_route = try_scrape_route(tlt)
        return m_route

    routes: list[ScrapedRoute] = []
    sub_periods: list[ScrapedSubPeriod] = []

    sub_period_to_routes: dict[ScrapedSubPeriodIdx | None, list[ScrapedRouteIdx]] = {}
    sub_period_to_routes[None] = []

    cur_sub_period: ScrapedSubPeriodIdx | None = None

    for part_div_el in parts_group_div_el:
        m_part = try_scrape_part(part_div_el)
        if m_part is None:
            continue

        if isinstance(m_part, ScrapedSubPeriod):
            i_sub_period = ScrapedSubPeriodIdx(len(sub_periods))
            sub_periods.append(m_part)

            cur_sub_period = i_sub_period
            sub_period_to_routes[cur_sub_period] = []
            continue

        i_route = ScrapedRouteIdx(len(routes))
        routes.append(m_part)

        sub_period_to_routes[cur_sub_period].append(i_route)

    return ScrapedPeriodParts(routes, sub_periods, sub_period_to_routes)


def scrape_periods(ctx: ScrapeContext) -> PeriodsScrape:
    """
    Scrape schedules from the root page to discover existing routes.
    """

    ctx.logger.info(f"GET {ROOT_SCHEDULE_URL}")
    response = ctx.session.get(ROOT_SCHEDULE_URL)
    assert response.ok

    root: lxml.html.HtmlElement = lxml.html.fromstring(response.text)
    h3_query = root.xpath("//body/descendant::h3")

    assert isinstance(h3_query, list)
    h3_els = cast(list[lxml.html.Element], h3_query)

    def is_period_h3_el(h3_el: lxml.html.Element) -> bool:
        return h3_el.text.strip().endswith("Shuttle Schedule")

    def scrape_period(h3_el: lxml.html.Element) -> ScrapedPeriod:
        text = h3_el.text.strip()
        return ScrapedPeriod(text)

    period_h3_els = list(filter(is_period_h3_el, h3_els))

    periods = list(map(scrape_period, period_h3_els))
    period_parts = []

    parts_group_div_els = map(_get_parts_grp_div_el_from_period_h3_el, period_h3_els)
    for parts_group_div_el in parts_group_div_els:
        parts = _scrape_parts_from_part_div_els(ctx, parts_group_div_el)
        period_parts.append(parts)

    return PeriodsScrape(periods, period_parts)
