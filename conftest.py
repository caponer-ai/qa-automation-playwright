import pytest
from playwright.sync_api import Browser, Playwright

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

SHOP_URL = "https://www.saucedemo.com"
STANDARD_USER = "standard_user"
PASSWORD = "secret_sauce"


@pytest.fixture(scope="session", autouse=True)
def _test_id_attribute(playwright: Playwright):
    # saucedemo marks elements with data-test, not data-testid
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # relative page.goto("/...") calls resolve against the shop, also under xdist workers
    return {**browser_context_args, "base_url": SHOP_URL}


@pytest.fixture(scope="session")
def auth_cookies(browser: Browser, _test_id_attribute) -> list:
    """Logs in once per worker; tests reuse the session cookie instead of the login form."""
    context = browser.new_context(base_url=SHOP_URL)
    page = context.new_page()
    LoginPage(page).open().login(STANDARD_USER, PASSWORD)
    page.wait_for_url("**/inventory.html")
    cookies = context.cookies()
    context.close()
    return cookies


@pytest.fixture
def inventory(page, context, auth_cookies) -> InventoryPage:
    context.add_cookies(auth_cookies)
    return InventoryPage(page).open()
