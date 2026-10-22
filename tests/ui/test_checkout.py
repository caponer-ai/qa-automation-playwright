from decimal import ROUND_HALF_UP, Decimal

import pytest
from playwright.sync_api import expect

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from tests.ui.catalog import CATALOG, SLUGS, TAX_RATE

pytestmark = pytest.mark.ui

ITEMS = ["Sauce Labs Backpack", "Sauce Labs Fleece Jacket"]


@pytest.fixture
def cart(inventory) -> CartPage:
    for name in ITEMS:
        inventory.add_to_cart(SLUGS[name])
    inventory.cart_link.click()
    return CartPage(inventory.page)


def test_full_checkout(cart):
    expect(cart.items).to_have_count(len(ITEMS))
    cart.checkout.click()

    checkout = CheckoutPage(cart.page)
    checkout.submit_info("Test", "User", "33000")
    summary = checkout.summary()

    expected_subtotal = sum(CATALOG[name] for name in ITEMS)
    expected_tax = (expected_subtotal * TAX_RATE).quantize(Decimal("0.01"), ROUND_HALF_UP)
    assert summary.item_prices == [CATALOG[name] for name in ITEMS]
    assert summary.subtotal == expected_subtotal
    assert summary.tax == expected_tax
    assert summary.total == expected_subtotal + expected_tax

    checkout.finish.click()
    expect(checkout.complete_header).to_have_text("Thank you for your order!")


@pytest.mark.parametrize(
    ("first", "last", "postal", "message"),
    [
        ("", "User", "33000", "First Name is required"),
        ("Test", "", "33000", "Last Name is required"),
        ("Test", "User", "", "Postal Code is required"),
    ],
    ids=["no-first-name", "no-last-name", "no-postal-code"],
)
def test_checkout_form_validation(cart, first, last, postal, message):
    cart.checkout.click()

    checkout = CheckoutPage(cart.page)
    checkout.submit_info(first, last, postal)

    expect(checkout.error).to_contain_text(message)
