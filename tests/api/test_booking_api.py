"""CRUD and auth checks for the public Restful Booker API."""

from dataclasses import replace

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from clients.booking import Booking, BookingClient, BookingDates
from settings import BOOKING_API_URL

# a shared public sandbox: 5xx and network errors are retried, wrong answers are not
TRANSIENT_ERRORS = ["TransientHTTPError", "Timeout", "ECONNRESET"]
pytestmark = [pytest.mark.api, pytest.mark.flaky(reruns=2, reruns_delay=2, only_rerun=TRANSIENT_ERRORS)]

# public demo credentials from the API docs
ADMIN = ("admin", "password123")

BOOKING = Booking(
    firstname="Test",
    lastname="Automation",
    totalprice=150,
    depositpaid=True,
    bookingdates=BookingDates(checkin="2026-11-01", checkout="2026-11-05"),
    additionalneeds="Breakfast",
)


def _context(playwright: Playwright) -> APIRequestContext:
    return playwright.request.new_context(
        base_url=BOOKING_API_URL, extra_http_headers={"Accept": "application/json"}
    )


@pytest.fixture(scope="session")
def anon(playwright: Playwright):
    # own request context: nothing the admin session sets can leak into anonymous calls
    ctx = _context(playwright)
    yield BookingClient(ctx)
    ctx.dispose()


@pytest.fixture(scope="session")
def admin(playwright: Playwright):
    ctx = _context(playwright)
    client = BookingClient(ctx)
    client.authenticate(*ADMIN)
    assert client.is_authenticated, "admin login returned no token"
    yield client
    ctx.dispose()


@pytest.fixture
def booking_id(admin):
    bid = admin.create(BOOKING)
    yield bid
    if admin.delete(bid).status != 201:  # the test may have deleted it already
        assert admin.get(bid).status == 404, f"booking {bid} was left behind"


def test_created_booking_reads_back_unchanged(anon, booking_id):
    assert anon.fetch(booking_id) == BOOKING


def test_update_requires_token(anon, booking_id):
    resp = anon.update(booking_id, replace(BOOKING, totalprice=999))

    assert resp.status == 403
    assert anon.fetch(booking_id) == BOOKING


def test_update_booking(admin, booking_id):
    updated = replace(BOOKING, totalprice=999, additionalneeds="Late checkout")

    assert admin.update(booking_id, updated).ok
    assert admin.fetch(booking_id) == updated


def test_delete_requires_token(anon, booking_id):
    assert anon.delete(booking_id).status == 403
    assert anon.get(booking_id).status == 200


def test_delete_booking(admin, booking_id):
    assert admin.delete(booking_id).status == 201  # the API documents 201 for delete
    assert admin.get(booking_id).status == 404


def test_auth_rejects_bad_credentials(anon):
    resp = anon.authenticate("admin", "wrong")

    assert resp.json() == {"reason": "Bad credentials"}
    assert not anon.is_authenticated
