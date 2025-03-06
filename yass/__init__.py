"""
Yet Another (RIT Bus) Schedule Scraper.
"""

import argparse

def main() -> None:
    """
    Parse arguments and run Scraper.
    """

    parser = argparse.ArgumentParser(prog="yass")
    _args = parser.parse_args()
