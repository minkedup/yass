"""
Scrape Error Types.
"""

from typing import TypeGuard, TypeAlias
import lxml


class ScrapeError(Exception):
    """
    Root Scraping Error.
    """


SingleQuery: TypeAlias = lxml.html.Element | None


def test_single_query(
    query: SingleQuery, source: lxml.html.Element, expect_tag: str
) -> TypeGuard[lxml.html.Element]:
    """
    Check that the result of a single element query (e.g. getparent in
    lxml.html.Element) is not None and matches some expected tag.
    """

    if query is None:
        raise ScrapeError(
            (
                f"{source.tag} el at line {source.sourceline}"
                f" has no parent; expected <{expect_tag}>"
            )
        ) from None
    if query.tag != expect_tag:
        raise ScrapeError(
            (
                f"{source.tag} el at line {source.sourceline}"
                f" has tag {query.tag}; expected <{expect_tag}>"
            )
        ) from None

    return True
