"""Reference catalogue as shown to standard_user."""

from decimal import Decimal

CATALOG = {
    "Sauce Labs Backpack": Decimal("29.99"),
    "Sauce Labs Bike Light": Decimal("9.99"),
    "Sauce Labs Bolt T-Shirt": Decimal("15.99"),
    "Sauce Labs Fleece Jacket": Decimal("49.99"),
    "Sauce Labs Onesie": Decimal("7.99"),
    "Test.allTheThings() T-Shirt (Red)": Decimal("15.99"),
}

# data-test suffix of the add/remove buttons
SLUGS = {name: name.lower().replace(" ", "-") for name in CATALOG}

TAX_RATE = Decimal("0.08")
