"""Targets and test accounts. URLs can be overridden by env vars to point the suite at another stand."""

import os
from enum import StrEnum

SHOP_URL = os.getenv("SHOP_URL", "https://www.saucedemo.com")
BOOKING_API_URL = os.getenv("BOOKING_API_URL", "https://restful-booker.herokuapp.com")
BOOKS_URL = os.getenv("BOOKS_URL", "https://books.toscrape.com")

# public demo credentials, published on the saucedemo login page
SHOP_PASSWORD = "secret_sauce"


class User(StrEnum):
    STANDARD = "standard_user"
    LOCKED_OUT = "locked_out_user"
    PROBLEM = "problem_user"
    PERFORMANCE_GLITCH = "performance_glitch_user"
    ERROR = "error_user"
    VISUAL = "visual_user"


# every user that can log in; standard_user is the reference behaviour
ACTIVE_USERS = [u for u in User if u is not User.LOCKED_OUT]
