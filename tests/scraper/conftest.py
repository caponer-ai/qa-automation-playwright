from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page

HAR = Path(__file__).parent / "fixtures" / "books.har"


@pytest.fixture
def offline_page(browser: Browser):
    """Page that answers catalogue requests from a recorded HAR and blocks everything else.

    Parser tests then check parsing logic only: no network, no flakiness, same input every run.
    Site drift is caught separately by the live smoke test; re-record with record_har.py.
    """
    context = browser.new_context()
    context.route("**/*", lambda route: route.abort())
    context.route_from_har(HAR, url="**/catalogue/page-*.html", not_found="abort")
    page: Page = context.new_page()
    yield page
    context.close()
