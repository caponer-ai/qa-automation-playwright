"""Playwright scraper for books.toscrape.com, a sandbox site built for scraping practice.

Usage: python -m scraper.books --pages 3 --out books.csv
"""

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass
class Book:
    title: str
    price: float
    rating: int
    in_stock: bool
    url: str


def parse_page(page: Page) -> list[Book]:
    books = []
    for card in page.locator("article.product_pod").all():
        link = card.locator("h3 a")
        rating_class = card.locator("p.star-rating").get_attribute("class")
        books.append(
            Book(
                title=link.get_attribute("title"),
                price=float(card.locator("p.price_color").inner_text().lstrip("£Â")),
                rating=RATINGS[rating_class.split()[-1]],
                in_stock="In stock" in card.locator("p.availability").inner_text(),
                url=urljoin(page.url, link.get_attribute("href")),
            )
        )
    return books


def scrape(page: Page, max_pages: int, start_url: str = START_URL) -> list[Book]:
    books: list[Book] = []
    page.goto(start_url)
    for _ in range(max_pages):
        books.extend(parse_page(page))
        next_link = page.locator("li.next a")
        if not next_link.count():
            break
        page.goto(urljoin(page.url, next_link.get_attribute("href")))
    return books


def save(books: list[Book], path: str):
    rows = [asdict(b) for b in books]
    if path.endswith(".json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--out", default="books.csv")
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # images and fonts are not needed for parsing, skipping them speeds pages up
        page.route("**/*.{png,jpg,jpeg,gif,woff,woff2}", lambda route: route.abort())
        books = scrape(page, args.pages)
        browser.close()

    save(books, args.out)
    print(f"Saved {len(books)} books to {args.out}")


if __name__ == "__main__":
    main()
