"""Typed client for the Restful Booker API on top of Playwright's APIRequestContext.

Tests talk in Booking objects; HTTP details (paths, auth cookie, JSON shape) stay here.
"""

from dataclasses import asdict, dataclass
from typing import Any, Self

from playwright.sync_api import APIRequestContext, APIResponse


@dataclass(frozen=True)
class BookingDates:
    checkin: str
    checkout: str


@dataclass(frozen=True)
class Booking:
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str = ""

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        return cls(**{**data, "bookingdates": BookingDates(**data["bookingdates"])})

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class BookingClient:
    def __init__(self, request: APIRequestContext) -> None:
        self._request = request
        self._token: str | None = None

    def authenticate(self, username: str, password: str) -> APIResponse:
        resp = self._request.post("/auth", data={"username": username, "password": password})
        self._token = resp.json().get("token") if resp.ok else None
        return resp

    def _auth_headers(self) -> dict[str, str]:
        return {"Cookie": f"token={self._token}"} if self._token else {}

    def create(self, booking: Booking) -> int:
        resp = self._request.post("/booking", data=booking.to_json())
        _expect_ok(resp)
        booking_id: int = resp.json()["bookingid"]
        return booking_id

    def get(self, booking_id: int) -> APIResponse:
        return self._request.get(f"/booking/{booking_id}")

    def fetch(self, booking_id: int) -> Booking:
        resp = self.get(booking_id)
        _expect_ok(resp)
        return Booking.from_json(resp.json())

    def update(self, booking_id: int, booking: Booking) -> APIResponse:
        return self._request.put(
            f"/booking/{booking_id}", data=booking.to_json(), headers=self._auth_headers()
        )

    def delete(self, booking_id: int) -> APIResponse:
        return self._request.delete(f"/booking/{booking_id}", headers=self._auth_headers())


def _expect_ok(resp: APIResponse) -> None:
    if not resp.ok:
        raise AssertionError(f"{resp.url} -> {resp.status}: {resp.text()[:200]}")
