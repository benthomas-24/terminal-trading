import os
import logging
from decimal import Decimal, InvalidOperation

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.public.com"

log = logging.getLogger(__name__)

_cached_token: str | None = None
_cached_account_id: str | None = None

_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "public-dev-docs",
}


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


# ── Auth ────────────────────────────────────────────────────────────


async def _fetch_token(validity_minutes: int = 1440) -> str:
    """Exchange PUBLIC_API_SECRET for a short-lived JWT access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/userapiauthservice/personal/access-tokens",
            headers=_HEADERS,
            json={"secret": _secret(), "validityInMinutes": validity_minutes},
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
            raise AuthError(f"Could not find token in response. Full response: {data}")
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


# ── Low-level HTTP ──────────────────────────────────────────────────


async def _request(method: str, path: str, *, json: dict | None = None) -> dict:
    token = await _get_token()
    headers = {**_HEADERS, "Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method, f"{BASE_URL}{path}", headers=headers, json=json
        )
        if resp.status_code == 401:
            await _invalidate_token()
            token = await _get_token()
            headers = {**_HEADERS, "Authorization": f"Bearer {token}"}
            resp = await client.request(
                method, f"{BASE_URL}{path}", headers=headers, json=json
            )
        if not resp.is_success:
            raise ApiError(resp.status_code, resp.text)
        return resp.json()


async def _get(path: str) -> dict:
    return await _request("GET", path)


async def _post(path: str, body: dict) -> dict:
    return await _request("POST", path, json=body)


# ── Account discovery ───────────────────────────────────────────────


async def list_accounts() -> list[dict]:
    """All accounts on the profile (brokerage, high-yield, etc.)."""
    data = await _get("/userapigateway/trading/account")
    return data.get("accounts", [])


async def get_account_id() -> str:
    """The primary tradable brokerage account id, cached for the session."""
    global _cached_account_id
    if _cached_account_id:
        return _cached_account_id

    accounts = await list_accounts()
    if not accounts:
        raise ApiError(404, "No accounts found on this profile.")

    # Prefer a BROKERAGE account that allows trading; fall back to the first.
    chosen = next(
        (a for a in accounts if a.get("accountType") == "BROKERAGE"),
        accounts[0],
    )
    _cached_account_id = chosen["accountId"]
    return _cached_account_id


# ── Helpers ─────────────────────────────────────────────────────────


def _dec(val) -> Decimal:
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError):
        return Decimal(0)


# ── Public, widget-shaped API ───────────────────────────────────────


async def _raw_portfolio() -> dict:
    account_id = await get_account_id()
    return await _get(f"/userapigateway/trading/{account_id}/portfolio/v2")


def _normalize_positions(raw: dict) -> list[dict]:
    positions = []
    for p in raw.get("positions", []):
        instrument = p.get("instrument", {})
        cost_basis = p.get("costBasis") or {}
        positions.append(
            {
                "symbol": instrument.get("symbol"),
                "name": instrument.get("name"),
                "type": instrument.get("type"),
                "quantity": p.get("quantity"),
                "costBasis": cost_basis.get("totalCost"),
                "currentValue": p.get("currentValue"),
                "unrealizedPnl": cost_basis.get("gainValue"),
                "unrealizedPnlPercent": cost_basis.get("gainPercentage"),
                "lastPrice": (p.get("lastPrice") or {}).get("lastPrice"),
            }
        )
    return positions


async def get_account() -> dict:
    """Flat account summary: cash, buying power, total value, account number."""
    raw = await _raw_portfolio()
    equity = raw.get("equity", [])
    total = sum((_dec(e.get("value")) for e in equity), Decimal(0))
    cash = next(
        (e.get("value") for e in equity if e.get("type") == "CASH"),
        "0",
    )
    return {
        "accountNumber": raw.get("accountId"),
        "buyingPower": (raw.get("buyingPower") or {}).get("buyingPower"),
        "cash": cash,
        "portfolioValue": str(total),
    }


async def get_positions() -> list[dict]:
    raw = await _raw_portfolio()
    return _normalize_positions(raw)


async def get_portfolio() -> dict:
    """Portfolio summary with equity breakdown and normalized holdings."""
    raw = await _raw_portfolio()
    equity = raw.get("equity", [])
    total = sum((_dec(e.get("value")) for e in equity), Decimal(0))
    cash = next((e.get("value") for e in equity if e.get("type") == "CASH"), "0")
    non_cash = sum(
        (_dec(e.get("value")) for e in equity if e.get("type") != "CASH"),
        Decimal(0),
    )
    return {
        "totalValue": str(total),
        "cash": cash,
        "equityValue": str(non_cash),
        "positions": _normalize_positions(raw),
    }


async def get_quote(symbol: str) -> dict:
    """Live quote for a symbol. Tries equity first, then crypto."""
    account_id = await get_account_id()
    symbol = symbol.upper()
    path = f"/userapigateway/marketdata/{account_id}/quotes"

    for instrument_type in ("EQUITY", "CRYPTO"):
        data = await _post(
            path,
            {"instruments": [{"symbol": symbol, "type": instrument_type}]},
        )
        quotes = data.get("quotes", [])
        if quotes and quotes[0].get("outcome") == "SUCCESS":
            q = quotes[0]
            last = q.get("last")
            prev = q.get("previousClose")
            change = change_pct = None
            if last is not None and prev is not None:
                change = float(_dec(last) - _dec(prev))
                if _dec(prev) != 0:
                    change_pct = change / float(_dec(prev)) * 100
            return {
                "symbol": (q.get("instrument") or {}).get("symbol", symbol),
                "last": last,
                "bid": q.get("bid"),
                "ask": q.get("ask"),
                "change": q.get("oneDayChange") or change,
                "changePercent": change_pct,
                "volume": q.get("volume"),
            }

    raise ApiError(404, f"No quote found for '{symbol}'.")
