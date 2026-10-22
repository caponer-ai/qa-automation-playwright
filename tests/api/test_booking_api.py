"""CRUD and auth checks for the public Restful Booker API."""

from dataclasses import replace

import pytest
from playwright.sync_api import Playwright

from clients.booking import Booking, BookingClient, BookingDates
from settings import BOOKING_API_URL

# a shared public sandbox: network hiccups are retried, assertion failures are not
TRANSIENT_ERRORS = ["Timeout", "ECONNRESET", r"-> 5\d\d"]
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


@pytest.fixture(scope="session")
def request_context(playwright: Playwright):
    ctx = playwright.request.new_context(
        base_url=BOOKING_API_URL, extra_http_headers={"Accept": "application/json"}
    )
    yield ctx
    ctx.dispose()


@pytest.fixture
def anon(request_context) -> BookingClient:
    return BookingClient(request_context)


@pytest.fixture
def admin(request_context) -> BookingClient:
    client = BookingClient(request_context)
    assert client.authenticate(*ADMIN).ok
    return client


@pytest.fixture
def booking_id(admin):
    bid = admin.create(BOOKING)
    yield bid
    admin.delete(bid)


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


def test_delete_booking(admin):
    bid = admin.create(BOOKING)

    assert admin.delete(bid).status == 201  # the API documents 201 for delete
    assert admin.get(bid).status == 404


def test_auth_rejects_bad_credentials(anon):
    resp = anon.authenticate("admin", "wrong")

    assert resp.json() == {"reason": "Bad credentials"}
