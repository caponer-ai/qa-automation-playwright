import json

import pytest

from scraper.books import START_URL, Book, save, scrape
from settings import BOOKS_URL

pytestmark = pytest.mark.scraper

LAST_PAGE = f"{BOOKS_URL}/catalogue/page-50.html"


@pytest.fixture
def books(offline_page) -> list[Book]:
    return scrape(offline_page, max_pages=2)


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


def test_save_csv_and_json(books, tmp_path):
    csv_path, json_path = tmp_path / "books.csv", tmp_path / "books.json"

    save(books, str(csv_path))
    save(books, str(json_path))

    assert len(csv_path.read_text(encoding="utf-8").splitlines()) == len(books) + 1
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["title"] == books[0].title


@pytest.mark.live
def test_live_site_still_matches_parser(page):
    """Smoke check against the real site: fails if the markup changes and the HAR needs re-recording."""
    page.route("**/*.{png,jpg,jpeg,gif,woff,woff2}", lambda route: route.abort())

    books = scrape(page, max_pages=1, start_url=START_URL)

    assert len(books) == 20
    assert all(b.price > 0 and b.title for b in books)
