import csv
import json
from dataclasses import asdict

import pytest

from scraper.books import START_URL, Book, ParseError, ScrapeError, parse_page, save, scrape
from settings import BOOKS_URL

pytestmark = pytest.mark.scraper

LAST_PAGE = f"{BOOKS_URL}/catalogue/page-50.html"


def card(rating_class: str = "star-rating Three", title: str = "A Book", price: str = "£12.50") -> str:
    return f"""
    <article class="product_pod">
      <p class="{rating_class}"></p>
      <h3><a href="a-book_1/index.html" title="{title}">A Book</a></h3>
      <p class="price_color">{price}</p>
      <p class="instock availability">In stock</p>
    </article>"""


@pytest.fixture
def books(offline_page) -> list[Book]:
    return scrape(offline_page, max_pages=2)


# --- recorded pages ------------------------------------------------------


def test_follows_pagination(books):
    assert len(books) == 40


def test_first_book_parsed_exactly(books):
    assert books[0] == Book(
        title="A Light in the Attic",
        price=51.77,
        rating=3,
        in_stock=True,
        url=f"{BOOKS_URL}/catalogue/a-light-in-the-attic_1000/index.html",
    )


def test_every_book_is_valid(books):
    for book in books:
        assert book.title
        assert book.price > 0
        assert 1 <= book.rating <= 5
        assert book.url.startswith(f"{BOOKS_URL}/catalogue/")


def test_no_duplicates_across_pages(books):
    assert len({b.url for b in books}) == len(books)


def test_stops_on_last_page(offline_page):
    assert len(scrape(offline_page, max_pages=5, start_url=LAST_PAGE)) == 20


def test_rejects_non_positive_page_limit(offline_page):
    with pytest.raises(ValueError, match="at least 1"):
        scrape(offline_page, max_pages=0)


# --- markup edge cases, no network --------------------------------------


def test_rating_does_not_depend_on_class_order(page):
    page.set_content(card(rating_class="Four star-rating"))

    assert parse_page(page)[0].rating == 4


def test_unknown_rating_is_a_parse_error(page):
    page.set_content(card(rating_class="star-rating Six"))

    with pytest.raises(ParseError):
        parse_page(page)


def test_price_without_currency_symbol(page):
    page.set_content(card(price="12.50"))

    assert parse_page(page)[0].price == 12.5


@pytest.mark.parametrize("price", ["£-12.50", "£1,299.99", "error 500", "£12", ""])
def test_malformed_price_is_a_parse_error(page, price):
    page.set_content(card(price=price))

    with pytest.raises(ParseError):
        parse_page(page)


def test_page_without_cards_is_a_parse_error(page):
    page.set_content("<html><body><p>Service unavailable</p></body></html>")

    with pytest.raises(ParseError, match="no product cards"):
        parse_page(page)


def test_http_error_stops_the_scrape(page):
    page.route("**/broken.html", lambda route: route.fulfill(status=500, body="oops"))

    with pytest.raises(ScrapeError, match="500"):
        scrape(page, max_pages=1, start_url=f"{BOOKS_URL}/broken.html")


# --- export --------------------------------------------------------------


def test_csv_round_trips_every_field(books, tmp_path):
    path = tmp_path / "books.csv"

    save(books, str(path))

    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == [{k: str(v) for k, v in asdict(b).items()} for b in books]


def test_csv_keeps_commas_quotes_and_newlines(tmp_path):
    tricky = Book(title='Say "hi", then\nleave', price=1.0, rating=1, in_stock=False, url="u")
    path = tmp_path / "books.csv"

    save([tricky], str(path))

    with path.open(encoding="utf-8", newline="") as f:
        assert next(csv.DictReader(f))["title"] == tricky.title


def test_json_round_trips(books, tmp_path):
    path = tmp_path / "books.json"

    save(books, str(path))

    assert [Book(**row) for row in json.loads(path.read_text(encoding="utf-8"))] == books


@pytest.mark.parametrize("ext", ["csv", "json"])
def test_empty_result_still_writes_a_file(tmp_path, ext):
    path = tmp_path / f"books.{ext}"

    save([], str(path))

    assert path.exists()


# --- live site -----------------------------------------------------------


@pytest.mark.live
def test_live_site_still_matches_parser(page):
    """Smoke check against the real site: fails if the markup changes and the HAR needs re-recording."""
    page.route("**/*.{png,jpg,jpeg,gif,woff,woff2}", lambda route: route.abort())

    books = scrape(page, max_pages=1, start_url=START_URL)

    assert len(books) == 20
    assert all(b.price > 0 and b.title for b in books)
