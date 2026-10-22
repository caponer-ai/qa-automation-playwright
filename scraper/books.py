"""Playwright scraper for books.toscrape.com, a sandbox site built for scraping practice.

Usage: python -m scraper.books --pages 3 --out books.csv
"""

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass, fields
from urllib.parse import urljoin

from playwright.sync_api import Locator, Page, sync_playwright

from settings import BOOKS_URL

START_URL = f"{BOOKS_URL}/catalogue/page-1.html"
# the site shows "£51.77"; anything else (negative, thousands separator, text) is a parse error
_PRICE = re.compile(r"£?(\d+\.\d{2})")
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
# images and fonts are not needed for parsing, skipping them speeds pages up
SKIPPED_ASSETS = "**/*.{png,jpg,jpeg,gif,woff,woff2}"


class ParseError(ValueError):
    pass


class ScrapeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Book:
    title: str
    price: float
    rating: int
    in_stock: bool
    url: str


def _attr(locator: Locator, name: str) -> str:
    value = locator.get_attribute(name)
    if not value:
        raise ParseError(f"missing @{name} on {locator}")
    return value


def parse_card(card: Locator, page_url: str) -> Book:
    link = card.locator("h3 a")
    # rating is one of the classes, e.g. "star-rating Three"; order of classes is not relied on
    rating_words = set(_attr(card.locator("p.star-rating"), "class").split()) & RATINGS.keys()
    if len(rating_words) != 1:
        raise ParseError(f"no single rating class in {card.locator('p.star-rating')}")
    price_text = card.locator("p.price_color").inner_text()
    price = _PRICE.fullmatch(price_text.strip())
    if price is None:
        raise ParseError(f"unexpected price format {price_text!r}")
    return Book(
        title=_attr(link, "title"),
        price=float(price.group(1)),
        rating=RATINGS[rating_words.pop()],
        in_stock="In stock" in card.locator("p.availability").inner_text(),
        url=urljoin(page_url, _attr(link, "href")),
    )


def parse_page(page: Page) -> list[Book]:
    cards = page.locator("article.product_pod").all()
    if not cards:
        # an error page or changed markup must not look like a successful empty scrape
        raise ParseError(f"no product cards on {page.url}")
    return [parse_card(card, page.url) for card in cards]


def _open(page: Page, url: str) -> None:
    response = page.goto(url)
    if response is None or not response.ok:
        raise ScrapeError(f"{url} -> {response.status if response else 'no response'}")


def scrape(page: Page, max_pages: int, start_url: str = START_URL) -> list[Book]:
    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    books: list[Book] = []
    _open(page, start_url)
    for page_no in range(1, max_pages + 1):
        books.extend(parse_page(page))
        next_link = page.locator("li.next a")
        if page_no == max_pages or not next_link.count():
            break
        _open(page, urljoin(page.url, _attr(next_link, "href")))
    return books


def save(books: list[Book], path: str) -> None:
    rows = [asdict(b) for b in books]
    if path.endswith(".json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[field.name for field in fields(Book)])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--out", default="books.csv")
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route(SKIPPED_ASSETS, lambda route: route.abort())
        books = scrape(page, args.pages)
        browser.close()

    save(books, args.out)
    print(f"Saved {len(books)} books to {args.out}")


if __name__ == "__main__":
    main()
