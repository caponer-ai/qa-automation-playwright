from dataclasses import dataclass

from playwright.sync_api import Page

from pages.base_page import BasePage
from pages.money import parse_money


@dataclass(frozen=True)
class OrderSummary:
    item_prices: list[float]
    subtotal: float
    tax: float
    total: float


class CartPage(BasePage):
    path = "/cart.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.get_by_test_id("inventory-item")
        self.checkout = page.get_by_test_id("checkout")


class CheckoutPage(BasePage):
    path = "/checkout-step-one.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.first_name = page.get_by_test_id("firstName")
        self.last_name = page.get_by_test_id("lastName")
        self.postal_code = page.get_by_test_id("postalCode")
        self.continue_btn = page.get_by_test_id("continue")
        self.error = page.get_by_test_id("error")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.subtotal = page.get_by_test_id("subtotal-label")
        self.tax = page.get_by_test_id("tax-label")
        self.total = page.get_by_test_id("total-label")
        self.finish = page.get_by_test_id("finish")
        self.complete_header = page.get_by_test_id("complete-header")

    def fill_info(self, first: str, last: str, postal: str) -> None:
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(postal)

    def submit_info(self, first: str, last: str, postal: str) -> None:
        self.fill_info(first, last, postal)
        self.continue_btn.click()

    def summary(self) -> OrderSummary:
        return OrderSummary(
            item_prices=[parse_money(p) for p in self.item_prices.all_inner_texts()],
            subtotal=parse_money(self.subtotal.inner_text()),
            tax=parse_money(self.tax.inner_text()),
            total=parse_money(self.total.inner_text()),
        )
