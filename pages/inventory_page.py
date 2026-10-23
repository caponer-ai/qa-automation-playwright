from decimal import Decimal

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage
from pages.money import parse_money


class InventoryPage(BasePage):
    path = "/inventory.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.title = page.get_by_test_id("title")
        self.items = page.get_by_test_id("inventory-item")
        self.prices = page.get_by_test_id("inventory-item-price")
        self.names = page.get_by_test_id("inventory-item-name")
        self.images = page.locator("img.inventory_item_img")
        self.sort = page.get_by_test_id("product-sort-container")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.cart_link = page.get_by_test_id("shopping-cart-link")

    def add_button(self, slug: str) -> Locator:
        return self.page.get_by_test_id(f"add-to-cart-{slug}")

    def remove_button(self, slug: str) -> Locator:
        return self.page.get_by_test_id(f"remove-{slug}")

    def add_to_cart(self, slug: str) -> None:
        self.add_button(slug).click()

    def remove_from_cart(self, slug: str) -> None:
        self.remove_button(slug).click()

    def sort_by(self, value: str) -> None:
        self.sort.select_option(value)

    def price_values(self) -> list[Decimal]:
        return [parse_money(p) for p in self.prices.all_inner_texts()]

    def name_values(self) -> list[str]:
        return self.names.all_inner_texts()

    def catalog(self) -> dict[str, Decimal]:
        return dict(zip(self.name_values(), self.price_values(), strict=True))

    def image_sources(self) -> list[str]:
        return [img.get_attribute("src") or "" for img in self.images.all()]

    def broken_images(self) -> list[str]:
        """src of images that failed to load. Waits until every image has finished loading first:
        the catalogue renders after the page load event, so images are still in flight at that point."""
        self.page.wait_for_function(
            "() => [...document.querySelectorAll('img.inventory_item_img')].every(i => i.complete)"
        )
        result: list[str] = self.images.evaluate_all(
            "imgs => imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)"
        )
        return result

    def open_product(self, name: str) -> None:
        self.names.filter(has_text=name).click()

    def logout(self) -> None:
        self.page.get_by_role("button", name="Open Menu").click()
        self.page.get_by_test_id("logout-sidebar-link").click()


class ProductPage(BasePage):
    path = "/inventory-item.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.name = page.get_by_test_id("inventory-item-name")
        # only exists on this page; the URL changes before the catalogue is re-rendered
        self.back_button = page.get_by_test_id("back-to-products")
