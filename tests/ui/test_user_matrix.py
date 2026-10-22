"""The same user journeys run for every saucedemo account.

standard_user defines correct behaviour. Other accounts have intentional defects;
the ones confirmed so far are listed in known_defects.py and expected to fail.
"""

import re
import time

import pytest
from playwright.sync_api import expect

from pages.checkout_page import CheckoutPage
from pages.inventory_page import ProductPage
from pages.login_page import LoginPage
from settings import ACTIVE_USERS, SHOP_PASSWORD

pytestmark = [pytest.mark.ui, pytest.mark.parametrize("user", ACTIVE_USERS, ids=str)]

# reference catalogue as shown to standard_user
CATALOG = {
    "Sauce Labs Backpack": 29.99,
    "Sauce Labs Bike Light": 9.99,
    "Sauce Labs Bolt T-Shirt": 15.99,
    "Sauce Labs Fleece Jacket": 49.99,
    "Sauce Labs Onesie": 7.99,
    "Test.allTheThings() T-Shirt (Red)": 15.99,
}
LOGIN_BUDGET_S = 3.0
PLACEHOLDER_IMAGE = "sl-404"


@pytest.mark.check("login_speed")
def test_login_within_budget(page, user):
    login = LoginPage(page).open()

    started = time.perf_counter()
    login.login(user, SHOP_PASSWORD)
    page.get_by_test_id("inventory-item").first.wait_for(timeout=15_000)
    elapsed = time.perf_counter() - started

    assert elapsed < LOGIN_BUDGET_S, f"login took {elapsed:.1f}s, budget {LOGIN_BUDGET_S}s"


@pytest.mark.check("product_images")
def test_each_product_has_its_own_image(login_as, user):
    sources = login_as(user).image_sources()

    assert not [s for s in sources if PLACEHOLDER_IMAGE in s], "placeholder image shown"
    assert len(set(sources)) == len(CATALOG)


@pytest.mark.check("catalog_prices")
def test_catalog_matches_reference(login_as, user):
    assert login_as(user).catalog() == CATALOG


@pytest.mark.check("sorting")
def test_sort_by_price(login_as, user):
    inventory = login_as(user)
    inventory.sort_by("lohi")

    prices = inventory.price_values()
    assert prices == sorted(prices)


@pytest.mark.check("add_remove_cart")
def test_every_item_can_be_added_and_removed(login_as, user):
    inventory = login_as(user)
    slugs = [
        "sauce-labs-backpack",
        "sauce-labs-bike-light",
        "sauce-labs-bolt-t-shirt",
        "sauce-labs-fleece-jacket",
        "sauce-labs-onesie",
        "test.allthethings()-t-shirt-(red)",
    ]
    for slug in slugs:
        inventory.add_to_cart(slug)
        expect(inventory.remove_button(slug), f"could not add {slug}").to_be_visible()

    for slug in slugs:
        inventory.remove_from_cart(slug)
    expect(inventory.cart_badge).to_be_hidden()


@pytest.mark.check("product_link")
def test_product_link_opens_same_product(login_as, user):
    inventory = login_as(user)
    inventory.open_product("Sauce Labs Backpack")

    # wait for navigation first: the catalogue has six elements with the same test id
    expect(inventory.page).to_have_url(re.compile(r"inventory-item\.html\?id=\d+"))
    expect(ProductPage(inventory.page).name).to_have_text("Sauce Labs Backpack")


@pytest.mark.check("checkout_form")
def test_checkout_form_keeps_input(login_as, user):
    page = login_as(user).page
    checkout = CheckoutPage(page).open()
    checkout.fill_info("Test", "User", "33000")

    expect(checkout.first_name).to_have_value("Test")
    expect(checkout.last_name).to_have_value("User")
    expect(checkout.postal_code).to_have_value("33000")


@pytest.mark.check("complete_order")
def test_complete_order(login_as, user):
    inventory = login_as(user)
    inventory.add_to_cart("sauce-labs-backpack")  # the one item every account can add
    checkout = CheckoutPage(inventory.page).open()
    checkout.submit_info("Test", "User", "33000")
    expect(checkout.page).to_have_url(re.compile(r"checkout-step-two"))
    checkout.finish.click()

    expect(checkout.complete_header).to_have_text("Thank you for your order!")
