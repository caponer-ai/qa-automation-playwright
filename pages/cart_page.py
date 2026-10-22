from playwright.sync_api import Page

from pages.base_page import BasePage


class CartPage(BasePage):
    path = "/cart.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.get_by_test_id("inventory-item")
        self.checkout = page.get_by_test_id("checkout")
