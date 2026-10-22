"""The same user journeys run for every saucedemo account that can log in.

standard_user defines correct behaviour. Each test has preconditions (plain asserts, always red on
failure) and one symptom check wrapped in `defects.symptom(...)`, which is matched against
known_defects.py. See docs/decisions.md, decision 5.
"""

import re
import time

import pytest
from playwright.sync_api import expect

from pages.checkout_page import CheckoutPage
from pages.inventory_page import ProductPage
from pages.login_page import LoginPage
from settings import ACTIVE_USERS, SHOP_PASSWORD
from tests.ui.catalog import CATALOG, SLUGS

pytestmark = [pytest.mark.ui, pytest.mark.parametrize("user", ACTIVE_USERS, ids=str)]

LOGIN_BUDGET_S = 3.0
PLACEHOLDER_IMAGE = "sl-404"
BACKPACK = "Sauce Labs Backpack"


@pytest.mark.perf
def test_login_within_budget(page, user, defects):
    login = LoginPage(page).open()

    started = time.perf_counter()
    login.login(user, SHOP_PASSWORD)
    page.get_by_test_id("inventory-item").first.wait_for(timeout=15_000)
    elapsed = time.perf_counter() - started

    with defects.symptom("login_speed"):
        assert elapsed < LOGIN_BUDGET_S, f"login took {elapsed:.1f}s, budget {LOGIN_BUDGET_S}s"


def test_each_product_has_its_own_image(login_as, user, defects):
    inventory = login_as(user)
    expect(inventory.items).to_have_count(len(CATALOG))
    assert inventory.broken_images() == []

    sources = inventory.image_sources()
    with defects.symptom("product_images"):
        assert [s for s in sources if PLACEHOLDER_IMAGE in s] == []
        assert len(set(sources)) == len(CATALOG)


def test_catalog_matches_reference(login_as, user, defects):
    inventory = login_as(user)
    expect(inventory.items).to_have_count(len(CATALOG))

    with defects.symptom("catalog_prices"):
        assert inventory.catalog() == CATALOG


def test_sort_by_price(login_as, user, defects):
    inventory = login_as(user)
    expect(inventory.items).to_have_count(len(CATALOG))
    expected = sorted(inventory.prices.all_inner_texts(), key=lambda p: float(p.lstrip("$")))

    inventory.sort_by("lohi")

    with defects.symptom("sort_by_price"):
        expect(inventory.prices).to_have_text(expected)


@pytest.mark.parametrize("product", list(SLUGS), ids=list(SLUGS.values()))
def test_add_to_cart(login_as, user, defects, product):
    inventory = login_as(user)
    slug = SLUGS[product]

    inventory.add_to_cart(slug)

    with defects.symptom(f"add_to_cart[{slug}]"):
        expect(inventory.remove_button(slug)).to_be_visible()
        expect(inventory.cart_badge).to_have_text("1")


def test_remove_from_cart(login_as, user, defects):
    inventory = login_as(user)
    slug = SLUGS[BACKPACK]
    inventory.add_to_cart(slug)
    expect(inventory.cart_badge).to_have_text("1")

    inventory.remove_from_cart(slug)

    with defects.symptom("remove_from_cart"):
        expect(inventory.add_button(slug)).to_be_visible()
        expect(inventory.cart_badge).to_be_hidden()


def test_product_link_opens_same_product(login_as, user, defects):
    inventory = login_as(user)
    inventory.open_product(BACKPACK)

    # wait for navigation first: the catalogue has six elements with the same test id
    expect(inventory.page).to_have_url(re.compile(r"inventory-item\.html\?id=\d+"))
    with defects.symptom("product_link"):
        expect(ProductPage(inventory.page).name).to_have_text(BACKPACK)


def test_checkout_form_keeps_input(login_as, user, defects):
    checkout = CheckoutPage(login_as(user).page).open()

    checkout.fill_info("Test", "User", "33000")

    with defects.symptom("checkout_form"):
        expect(checkout.first_name).to_have_value("Test")
        expect(checkout.last_name).to_have_value("User")
        expect(checkout.postal_code).to_have_value("33000")


def test_complete_order(login_as, user, defects):
    inventory = login_as(user)
    inventory.add_to_cart(SLUGS[BACKPACK])  # the one item every account can add
    expect(inventory.cart_badge).to_have_text("1")
    checkout = CheckoutPage(inventory.page).open()

    checkout.submit_info("Test", "User", "33000")
    with defects.symptom("reach_overview"):
        expect(checkout.page).to_have_url(re.compile(r"checkout-step-two"))

    checkout.finish.click()
    with defects.symptom("finish_order"):
        expect(checkout.complete_header).to_have_text("Thank you for your order!")
