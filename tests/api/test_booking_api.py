"""CRUD tests for the public Restful Booker API using Playwright's APIRequestContext."""

import pytest
from playwright.sync_api import APIRequestContext, Playwright

pytestmark = [pytest.mark.api, pytest.mark.flaky(reruns=2, reruns_delay=2)]

API_URL = "https://restful-booker.herokuapp.com"

BOOKING = {
    "firstname": "Test",
    "lastname": "Automation",
    "totalprice": 150,
    "depositpaid": True,
    "bookingdates": {"checkin": "2026-11-01", "checkout": "2026-11-05"},
    "additionalneeds": "Breakfast",
}


@pytest.fixture(scope="session")
def api(playwright: Playwright) -> APIRequestContext:
    ctx = playwright.request.new_context(
        base_url=API_URL,
        extra_http_headers={"Accept": "application/json"},
    )
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def token(api) -> str:
    resp = api.post("/auth", data={"username": "admin", "password": "password123"})
    assert resp.ok
    return resp.json()["token"]


@pytest.fixture
def booking_id(api, token) -> int:
    resp = api.post("/booking", data=BOOKING)
    assert resp.ok
    bid = resp.json()["bookingid"]
    yield bid
    api.delete(f"/booking/{bid}", headers={"Cookie": f"token={token}"})


def test_create_and_read_booking(api, booking_id):
    resp = api.get(f"/booking/{booking_id}")

    assert resp.status == 200
    assert resp.json() == BOOKING


def test_update_booking_requires_token(api, booking_id):
    resp = api.put(f"/booking/{booking_id}", data={**BOOKING, "totalprice": 999})

    assert resp.status == 403


def test_update_booking(api, token, booking_id):
    updated = {**BOOKING, "totalprice": 999, "additionalneeds": "Late checkout"}
    resp = api.put(
        f"/booking/{booking_id}", data=updated, headers={"Cookie": f"token={token}"}
    )

    assert resp.ok
    assert api.get(f"/booking/{booking_id}").json() == updated


def test_delete_booking(api, token):
    bid = api.post("/booking", data=BOOKING).json()["bookingid"]

    resp = api.delete(f"/booking/{bid}", headers={"Cookie": f"token={token}"})

    assert resp.status == 201
    assert api.get(f"/booking/{bid}").status == 404


def test_auth_rejects_bad_credentials(api):
    resp = api.post("/auth", data={"username": "admin", "password": "nope"})

    assert resp.json() == {"reason": "Bad credentials"}
