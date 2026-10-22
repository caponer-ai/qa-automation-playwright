from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/"

    def __init__(self, page):
        super().__init__(page)
        self.username = page.get_by_test_id("username")
        self.password = page.get_by_test_id("password")
        self.submit = page.get_by_test_id("login-button")
        self.error = page.get_by_test_id("error")

    def login(self, username: str, password: str):
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()
