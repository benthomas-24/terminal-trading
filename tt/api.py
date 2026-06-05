import os
import logging

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.public.com"
_cached_token: str | None = None

log = logging.getLogger(__name__)


class AuthError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status: int, body: str):
        self.status = status
        super().__init__(f"HTTP {status}: {body}")


def _secret() -> str:
    secret = os.getenv("PUBLIC_API_SECRET")
    if not secret:
        raise AuthError(
            "PUBLIC_API_SECRET is not set. "
            "Add it to .env or export it in your shell."
        )
    return secret


async def _fetch_token(validity_minutes: int = 1440) -> str:
    """Exchange PUBLIC_API_SECRET for a short-lived JWT access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/userapiauthservice/personal/access-tokens",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "public-dev-docs",
            },
            json={
                "secret": _secret(),
                "validityInMinutes": validity_minutes,
            },
        )
        if not resp.is_success:
            raise AuthError(
                f"Token exchange failed (HTTP {resp.status_code}): {resp.text}"
            )
        data = resp.json()
        token = (
            data.get("accessToken")
            or data.get("access_token")
            or data.get("token")
        )
        if not token:
            raise AuthError(
                f"Could not find token in response. Full response: {data}"
            )
        return token


async def _get_token() -> str:
    global _cached_token
    if env_token := os.getenv("PUBLIC_ACCESS_TOKEN"):
        return env_token
    if _cached_token:
        return _cached_token
    _cached_token = await _fetch_token()
    return _cached_token


async def _invalidate_token() -> None:
    global _cached_token
    _cached_token = None


_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "public-dev-docs",
}


async def _get(path: str, params: dict | None = None) -> dict:
    token = await _get_token()
    headers = {**_HEADERS, "Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}{path}",
            headers=headers,
            params=params or {},
        )
        if resp.status_code == 401:
            await _invalidate_token()
            token = await _get_token()
            headers = {**_HEADERS, "Authorization": f"Bearer {token}"}
            resp = await client.get(
                f"{BASE_URL}{path}",
                headers=headers,
                params=params or {},
            )
        if not resp.is_success:
            raise ApiError(resp.status_code, resp.text)
        return resp.json()


async def get_account() -> dict:
    return await _get("/userapigateway/account")


async def get_positions() -> dict | list:
    return await _get("/userapigateway/portfolio/positions")


async def get_portfolio() -> dict:
    return await _get("/userapigateway/portfolio")


async def get_quote(symbol: str) -> dict:
    return await _get(f"/marketdata/quotes/{symbol.upper()}")
