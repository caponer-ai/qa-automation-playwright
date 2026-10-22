import pytest
from playwright.sync_api import expect

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from settings import SHOP_PASSWORD, User

pytestmark = pytest.mark.ui


def test_standard_user_logs_in(page):
    LoginPage(page).open().login(User.STANDARD, SHOP_PASSWORD)

    expect(page).to_have_url("/inventory.html")
    expect(InventoryPage(page).title).to_have_text("Products")


@pytest.mark.parametrize(
    ("username", "password", "message"),
    [
        (User.LOCKED_OUT, SHOP_PASSWORD, "Sorry, this user has been locked out."),
        (User.STANDARD, "wrong_password", "Username and password do not match"),
        ("", SHOP_PASSWORD, "Username is required"),
        (User.STANDARD, "", "Password is required"),
    ],
    ids=["locked-out", "wrong-password", "empty-username", "empty-password"],
)
def test_login_rejected(page, username, password, message):
    login = LoginPage(page).open()
    login.login(username, password)

    expect(login.error).to_contain_text(message)
    expect(page).to_have_url("/")


def test_inventory_requires_login(page):
    page.goto("/inventory.html")

    expect(LoginPage(page).error).to_contain_text(
        "You can only access '/inventory.html' when you are logged in"
    )


def test_logout_returns_to_login(inventory):
    inventory.logout()

    expect(LoginPage(inventory.page).submit).to_be_visible()
