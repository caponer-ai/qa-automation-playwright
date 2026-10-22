import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


def test_catalog_shows_six_products(inventory):
    expect(inventory.items).to_have_count(6)


@pytest.mark.parametrize(
    ("option", "key", "reverse"),
    [
        ("lohi", "price", False),
        ("hilo", "price", True),
        ("az", "name", False),
        ("za", "name", True),
    ],
)
def test_sorting(inventory, option, key, reverse):
    inventory.sort_by(option)

    values = inventory.price_values() if key == "price" else inventory.name_values()
    assert values == sorted(values, reverse=reverse)


def test_cart_badge_follows_add_and_remove(inventory):
    inventory.add_to_cart("sauce-labs-backpack")
    inventory.add_to_cart("sauce-labs-bike-light")
    expect(inventory.cart_badge).to_have_text("2")

    inventory.remove_from_cart("sauce-labs-backpack")
    expect(inventory.cart_badge).to_have_text("1")

    inventory.remove_from_cart("sauce-labs-bike-light")
    expect(inventory.cart_badge).to_be_hidden()
