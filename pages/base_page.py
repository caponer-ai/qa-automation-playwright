from typing import ClassVar, Self

from playwright.sync_api import Page


class BasePage:
    path: ClassVar[str] = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> Self:
        self.page.goto(self.path)
        return self
