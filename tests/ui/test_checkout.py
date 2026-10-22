import pytest
from playwright.sync_api import expect

from pages.checkout_page import CartPage, CheckoutPage

pytestmark = pytest.mark.ui

ITEMS = ["sauce-labs-backpack", "sauce-labs-fleece-jacket"]


@pytest.fixture
def cart(inventory) -> CartPage:
    for slug in ITEMS:
        inventory.add_to_cart(slug)
    inventory.cart_link.click()
    return CartPage(inventory.page)


def test_full_checkout(cart):
    expect(cart.items).to_have_count(len(ITEMS))
    cart.checkout.click()

    checkout = CheckoutPage(cart.page)
    checkout.fill_info("Test", "User", "33000")
    summary = checkout.summary()

    assert summary["subtotal"] == pytest.approx(sum(summary["items"]))
    assert summary["total"] == pytest.approx(summary["subtotal"] + summary["tax"])

    checkout.finish.click()
    expect(checkout.complete_header).to_have_text("Thank you for your order!")


@pytest.mark.parametrize(
    "first, last, postal, message",
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
    checkout.fill_info(first, last, postal)

    expect(checkout.error).to_contain_text(message)
