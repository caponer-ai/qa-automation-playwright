import pytest
from playwright.sync_api import expect

from tests.ui.catalog import CATALOG, SLUGS

pytestmark = pytest.mark.ui

PRICES_ASC = [f"${p}" for p in sorted(CATALOG.values())]
NAMES_ASC = sorted(CATALOG)


def test_catalog_shows_six_products(inventory):
    expect(inventory.items).to_have_count(len(CATALOG))


# expected order comes from the reference catalogue, not from the page itself,
# and to_have_text() waits for it, so an empty or half-rendered list cannot pass
@pytest.mark.parametrize(
    ("option", "locator", "expected"),
    [
        ("lohi", "prices", PRICES_ASC),
        ("hilo", "prices", PRICES_ASC[::-1]),
        ("az", "names", NAMES_ASC),
        ("za", "names", NAMES_ASC[::-1]),
    ],
)
def test_sorting(inventory, option, locator, expected):
    inventory.sort_by(option)

    expect(getattr(inventory, locator)).to_have_text(expected)


def test_cart_badge_follows_add_and_remove(inventory):
    backpack, bike_light = SLUGS["Sauce Labs Backpack"], SLUGS["Sauce Labs Bike Light"]
    inventory.add_to_cart(backpack)
    inventory.add_to_cart(bike_light)
    expect(inventory.cart_badge).to_have_text("2")

    inventory.remove_from_cart(backpack)
    expect(inventory.cart_badge).to_have_text("1")

    inventory.remove_from_cart(bike_light)
    expect(inventory.cart_badge).to_be_hidden()
