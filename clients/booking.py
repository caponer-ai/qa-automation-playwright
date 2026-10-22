"""Typed client for the Restful Booker API on top of Playwright's APIRequestContext.

Tests talk in Booking objects; HTTP details (paths, auth cookie, JSON shape) stay here.
"""

from dataclasses import asdict, dataclass
from typing import Any, Self

from playwright.sync_api import APIRequestContext, APIResponse


class TransientHTTPError(Exception):
    """5xx from the server. The only HTTP failure the test suite is allowed to retry."""


class BookingAPIError(Exception):
    """Unexpected non-2xx response where the caller needed a success."""


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
        """Stores the token on success. The API answers 200 with {"reason": ...} on bad credentials."""
        resp = self._send("post", "/auth", data={"username": username, "password": password})
        token = resp.json().get("token") if resp.ok else None
        self._token = token if isinstance(token, str) and token else None
        return resp

    @property
    def is_authenticated(self) -> bool:
        return bool(self._token)

    def create(self, booking: Booking) -> int:
        resp = self._require_ok(self._send("post", "/booking", data=booking.to_json()))
        booking_id: int = resp.json()["bookingid"]
        return booking_id

    def get(self, booking_id: int) -> APIResponse:
        return self._send("get", f"/booking/{booking_id}")

    def fetch(self, booking_id: int) -> Booking:
        return Booking.from_json(self._require_ok(self.get(booking_id)).json())

    def update(self, booking_id: int, booking: Booking) -> APIResponse:
        return self._send("put", f"/booking/{booking_id}", data=booking.to_json(), headers=self._auth())

    def delete(self, booking_id: int) -> APIResponse:
        return self._send("delete", f"/booking/{booking_id}", headers=self._auth())

    def _auth(self) -> dict[str, str]:
        return {"Cookie": f"token={self._token}"} if self._token else {}

    def _send(self, method: str, path: str, **kwargs: Any) -> APIResponse:
        resp: APIResponse = getattr(self._request, method)(path, **kwargs)
        if resp.status >= 500:
            raise TransientHTTPError(f"{method.upper()} {path} -> {resp.status}")
        return resp

    @staticmethod
    def _require_ok(resp: APIResponse) -> APIResponse:
        if not resp.ok:
            raise BookingAPIError(f"{resp.url} -> {resp.status}: {resp.text()[:200]}")
        return resp
