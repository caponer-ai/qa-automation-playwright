"""Registry of confirmed defects, keyed by (user, check). Details and repro steps: BUGS.md.

A matching test is marked xfail(strict=True): while the bug exists the suite stays green,
and the day it gets fixed the test turns red, so the registry can never silently go stale.
"""

from settings import User

KNOWN_DEFECTS: dict[tuple[User, str], str] = {
    (User.PROBLEM, "product_images"): "BUG-01 every product shows the same 404 image",
    (User.VISUAL, "product_images"): "BUG-02 Backpack shows the 404 image",
    (User.VISUAL, "catalog_prices"): "BUG-03 catalog prices differ from the real ones",
    (User.PROBLEM, "sorting"): "BUG-04 sorting does nothing",
    (User.ERROR, "sorting"): "BUG-04 sorting does nothing, alert 'Sorting is broken!'",
    (User.VISUAL, "sorting"): "BUG-05 sort by price returns an unsorted list",
    (User.PROBLEM, "add_remove_cart"): "BUG-06/07 3 of 6 items cannot be added, Remove does nothing",
    (User.ERROR, "add_remove_cart"): "BUG-06/07 3 of 6 items cannot be added, Remove does nothing",
    (User.PROBLEM, "product_link"): "BUG-08 product name opens a different product",
    (User.PROBLEM, "checkout_form"): "BUG-09 typing Last Name overwrites First Name",
    (User.ERROR, "checkout_form"): "BUG-10 Last Name field ignores input",
    (User.PROBLEM, "complete_order"): "BUG-09 checkout blocked on step one",
    (User.ERROR, "complete_order"): "BUG-11 Finish does not complete the order",
    (User.PERFORMANCE_GLITCH, "login_speed"): "BUG-12 login takes about 5 s",
}
