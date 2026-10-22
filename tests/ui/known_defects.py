"""Registry of confirmed defects, keyed by (user, symptom). Details and repro steps: BUGS.md.

Only a check wrapped in `defects.symptom(name)` can be matched against this registry.
Preconditions outside that block stay red, so a new regression is never filed under an old bug.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from settings import User
from tests.ui.catalog import SLUGS

SYMPTOMS = {
    "login_speed",
    "product_images",
    "catalog_prices",
    "sort_by_price",
    "remove_from_cart",
    "product_link",
    "checkout_form",
    "reach_overview",
    "finish_order",
    *(f"add_to_cart[{slug}]" for slug in SLUGS.values()),
}

_BROKEN_ADD = ["sauce-labs-bolt-t-shirt", "sauce-labs-fleece-jacket", "test.allthethings()-t-shirt-(red)"]

KNOWN_DEFECTS: dict[tuple[User, str], str] = {
    (User.PROBLEM, "product_images"): "BUG-01 every product shows the same 404 image",
    (User.VISUAL, "product_images"): "BUG-02 Backpack shows the 404 image",
    (User.VISUAL, "catalog_prices"): "BUG-03 catalog prices differ from the real ones",
    (User.PROBLEM, "sort_by_price"): "BUG-04 sorting does nothing",
    (User.ERROR, "sort_by_price"): "BUG-04 sorting does nothing, alert 'Sorting is broken!'",
    (User.VISUAL, "sort_by_price"): "BUG-05 sort by price returns an unsorted list",
    **{
        (u, f"add_to_cart[{s}]"): "BUG-06 item cannot be added"
        for u in (User.PROBLEM, User.ERROR)
        for s in _BROKEN_ADD
    },
    (User.PROBLEM, "remove_from_cart"): "BUG-07 Remove does nothing",
    (User.ERROR, "remove_from_cart"): "BUG-07 Remove does nothing",
    (User.PROBLEM, "product_link"): "BUG-08 product name opens a different product",
    (User.PROBLEM, "checkout_form"): "BUG-09 typing Last Name overwrites First Name",
    (User.ERROR, "checkout_form"): "BUG-10 Last Name field ignores input",
    (User.PROBLEM, "reach_overview"): "BUG-09 checkout blocked on step one",
    (User.ERROR, "finish_order"): "BUG-11 Finish does not complete the order",
    (User.PERFORMANCE_GLITCH, "login_speed"): "BUG-12 login takes about 5 s",
}


class Defects:
    def __init__(self, user: User) -> None:
        self.user = user

    @contextmanager
    def symptom(self, name: str) -> Iterator[None]:
        """Wraps the one check that shows a defect.

        registered + check fails  -> xfail with the bug id
        registered + check passes -> fail: the bug is fixed, update the registry
        not registered            -> normal pass/fail
        """
        assert name in SYMPTOMS, f"unknown symptom {name!r}"
        reason = KNOWN_DEFECTS.get((self.user, name))
        try:
            yield
        except AssertionError:
            if reason:
                pytest.xfail(reason)
            raise
        if reason:
            pytest.fail(f"{reason}: no longer reproduces for {self.user}, remove it from KNOWN_DEFECTS")
