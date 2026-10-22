import pytest
from playwright.sync_api import Browser, Page

from tests.scraper.har import HAR, HAR_URL_PATTERN


@pytest.fixture
def offline_page(browser: Browser):
    """Page that answers catalogue requests from a recorded HAR and blocks everything else.

    Parser tests then check parsing logic only: no network, no flakiness, same input every run.
    Site drift is caught separately by the live smoke test; re-record with record_har.py.
    Routes registered later take priority, so the HAR wins for catalogue pages and the
    catch-all abort handles the rest.
    """
    context = browser.new_context()
    context.route("**/*", lambda route: route.abort())
    context.route_from_har(HAR, url=HAR_URL_PATTERN, not_found="abort")
    page: Page = context.new_page()
    yield page
    context.close()
