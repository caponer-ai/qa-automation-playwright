import pytest

from scraper.books import save, scrape

pytestmark = pytest.mark.scraper


@pytest.fixture(scope="module")
def books(browser):
    page = browser.new_page()
    page.route("**/*.{png,jpg,jpeg,gif,woff,woff2}", lambda route: route.abort())
    result = scrape(page, max_pages=2)
    page.close()
    return result


def test_scrapes_twenty_books_per_page(books):
    assert len(books) == 40


def test_fields_are_parsed(books):
    for book in books:
        assert book.title
        assert book.price > 0
        assert 1 <= book.rating <= 5
        assert book.url.startswith("https://books.toscrape.com/catalogue/")


def test_titles_are_unique(books):
    assert len({b.url for b in books}) == len(books)


def test_stops_on_last_page(browser):
    page = browser.new_page()
    result = scrape(page, max_pages=5, start_url="https://books.toscrape.com/catalogue/page-50.html")
    page.close()

    assert len(result) == 20


def test_save_csv_and_json(books, tmp_path):
    csv_path, json_path = tmp_path / "books.csv", tmp_path / "books.json"

    save(books, str(csv_path))
    save(books, str(json_path))

    assert len(csv_path.read_text(encoding="utf-8").splitlines()) == len(books) + 1
    assert json_path.read_text(encoding="utf-8").count('"title"') == len(books)
