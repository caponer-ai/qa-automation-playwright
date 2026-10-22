"""Re-records the HTML pages the offline scraper tests replay.

Run when the live smoke test fails because the site changed:
    python -m tests.scraper.record_har
"""

from playwright.sync_api import sync_playwright

from settings import BOOKS_URL
from tests.scraper.har import HAR, HAR_URL_PATTERN

PAGES = ["page-1.html", "page-2.html", "page-50.html"]


def main() -> None:
    HAR.parent.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(record_har_path=HAR, record_har_url_filter=HAR_URL_PATTERN)
        page = context.new_page()
        for name in PAGES:
            page.goto(f"{BOOKS_URL}/catalogue/{name}")
        context.close()
        browser.close()
    print(f"recorded {len(PAGES)} pages to {HAR}")


if __name__ == "__main__":
    main()
