from pages.base_page import BasePage


class InventoryPage(BasePage):
    path = "/inventory.html"

    def __init__(self, page):
        super().__init__(page)
        self.title = page.get_by_test_id("title")
        self.items = page.get_by_test_id("inventory-item")
        self.prices = page.get_by_test_id("inventory-item-price")
        self.names = page.get_by_test_id("inventory-item-name")
        self.sort = page.get_by_test_id("product-sort-container")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.cart_link = page.get_by_test_id("shopping-cart-link")

    def add_to_cart(self, slug: str):
        self.page.get_by_test_id(f"add-to-cart-{slug}").click()

    def remove_from_cart(self, slug: str):
        self.page.get_by_test_id(f"remove-{slug}").click()

    def sort_by(self, value: str):
        self.sort.select_option(value)

    def price_values(self) -> list[float]:
        return [float(p.replace("$", "")) for p in self.prices.all_inner_texts()]

    def name_values(self) -> list[str]:
        return self.names.all_inner_texts()

    def logout(self):
        self.page.get_by_role("button", name="Open Menu").click()
        self.page.get_by_test_id("logout-sidebar-link").click()
