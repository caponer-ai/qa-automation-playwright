"""Playwright scraper for books.toscrape.com, a sandbox site built for scraping practice.

Usage: python -m scraper.books --pages 3 --out books.csv
"""

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

from playwright.sync_api import Locator, Page, sync_playwright

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
# images and fonts are not needed for parsing, skipping them speeds pages up
SKIPPED_ASSETS = "**/*.{png,jpg,jpeg,gif,woff,woff2}"


class ParseError(ValueError):
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
    rating_word = _attr(card.locator("p.star-rating"), "class").split()[-1]
    if rating_word not in RATINGS:
        raise ParseError(f"unknown rating {rating_word!r}")
    return Book(
        title=_attr(link, "title"),
        price=float(card.locator("p.price_color").inner_text().lstrip("£Â")),
        rating=RATINGS[rating_word],
        in_stock="In stock" in card.locator("p.availability").inner_text(),
        url=urljoin(page_url, _attr(link, "href")),
    )


def parse_page(page: Page) -> list[Book]:
    return [parse_card(card, page.url) for card in page.locator("article.product_pod").all()]


def scrape(page: Page, max_pages: int, start_url: str = START_URL) -> list[Book]:
    books: list[Book] = []
    page.goto(start_url)
    for _ in range(max_pages):
        books.extend(parse_page(page))
        next_link = page.locator("li.next a")
        if not next_link.count():
            break
        page.goto(urljoin(page.url, _attr(next_link, "href")))
    return books


def save(books: list[Book], path: str) -> None:
    rows = [asdict(b) for b in books]
    if path.endswith(".json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
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
