from collections.abc import Callable

import pytest
from playwright.sync_api import Browser, BrowserContext, Cookie, Page, Playwright

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from settings import SHOP_PASSWORD, SHOP_URL, User

LoginAs = Callable[[User], InventoryPage]


@pytest.fixture(scope="session", autouse=True)
def _test_id_attribute(playwright: Playwright) -> None:
    # saucedemo marks elements with data-test, not data-testid
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    # relative page.goto("/...") calls resolve against the shop, also under xdist workers
    return {**browser_context_args, "base_url": SHOP_URL}


@pytest.fixture(scope="session")
def session_cookies(browser: Browser, _test_id_attribute: None) -> Callable[[User], list[Cookie]]:
    """Logs each user in through the form once per worker and caches the session cookie.

    Only the login tests exercise the form; everything else starts already logged in,
    which removes one page load and one source of flakiness from every test.
    """
    cache: dict[User, list[Cookie]] = {}

    def get(user: User) -> list[Cookie]:
        if user not in cache:
            context = browser.new_context(base_url=SHOP_URL)
            page = context.new_page()
            LoginPage(page).open().login(user, SHOP_PASSWORD)
            page.wait_for_url("**/inventory.html", timeout=15_000)
            cache[user] = context.cookies()
            context.close()
        return cache[user]

    return get


@pytest.fixture
def login_as(page: Page, context: BrowserContext, session_cookies) -> LoginAs:
    def login(user: User) -> InventoryPage:
        context.add_cookies(session_cookies(user))
        return InventoryPage(page).open()

    return login


@pytest.fixture
def inventory(login_as: LoginAs) -> InventoryPage:
    return login_as(User.STANDARD)
