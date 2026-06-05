import os
import asyncio
import logging
from datetime import datetime, timezone
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
        daily_gain = p.get("positionDailyGain") or {}
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
                "dayChange": daily_gain.get("gainValue"),
                "dayChangePercent": daily_gain.get("gainPercentage"),
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


# ── Market data via yfinance (charts, history, news, search) ─────────
#
# yfinance is synchronous/blocking, so every public coroutine here wraps
# the blocking work in asyncio.to_thread to keep the Textual event loop
# responsive. yfinance itself is imported lazily inside the worker so app
# startup stays fast.


# yfinance period strings keyed by the timeframe labels we show in the UI.
PERIODS = {
    "1D": "1d",
    "1W": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "1Y": "1y",
}

# Emoji glyphs used as dropdown/news icons, keyed by yfinance quoteType.
TYPE_ICONS = {
    "EQUITY": "📈",
    "ETF": "📊",
    "CRYPTOCURRENCY": "🪙",
    "CRYPTO": "🪙",
    "INDEX": "📉",
    "CURRENCY": "💱",
    "MUTUALFUND": "🏦",
    "FUTURE": "⏳",
    "OPTION": "🎲",
}


def _yf_symbol(symbol: str, asset_type: str | None = None) -> str:
    """Map an internal symbol to the form yfinance expects.

    Crypto on Public.com is a bare ticker (e.g. ``BTC``); yfinance needs the
    ``BTC-USD`` pairing.
    """
    symbol = symbol.upper()
    if asset_type and asset_type.upper().startswith("CRYPTO") and "-" not in symbol:
        return f"{symbol}-USD"
    return symbol


def icon_for(asset_type: str | None) -> str:
    return TYPE_ICONS.get((asset_type or "").upper(), "•")


def _interval_for(period: str) -> str:
    """Pick a sensible candle interval for intraday vs longer ranges."""
    return "5m" if period == "1d" else "1d"


def _history_sync(symbol: str, period: str) -> list[tuple[str, float]]:
    import yfinance as yf

    df = yf.Ticker(symbol).history(period=period, interval=_interval_for(period))
    if df.empty:
        return []
    closes = df["Close"].dropna()
    fmt = "%H:%M" if period == "1d" else "%m/%d"
    return [(idx.strftime(fmt), float(val)) for idx, val in closes.items()]


async def get_price_history(
    symbol: str, period: str = "1mo", asset_type: str | None = None
) -> list[tuple[str, float]]:
    """Closing-price series as (label, price) tuples for charting."""
    sym = _yf_symbol(symbol, asset_type)
    return await asyncio.to_thread(_history_sync, sym, period)


def _portfolio_history_sync(
    holdings: list[tuple[str, float]], period: str
) -> list[tuple[str, float]]:
    """Reconstruct total portfolio value over time from per-holding closes.

    holdings is a list of (yfinance_symbol, quantity). Each symbol's close
    series is multiplied by its quantity and summed across a shared, forward
    filled date index so equities (no weekends) and crypto (every day) align.
    """
    import yfinance as yf
    import pandas as pd

    series = []
    interval = _interval_for(period)
    for sym, qty in holdings:
        try:
            df = yf.Ticker(sym).history(period=period, interval=interval)
            if df.empty:
                continue
            series.append(df["Close"].rename(sym) * qty)
        except Exception:
            continue

    if not series:
        return []

    # ffill carries each holding's last close forward; dropna() then keeps only
    # dates where *every* holding has a value, avoiding a misleading ramp at the
    # start where some series haven't begun yet.
    combined = pd.concat(series, axis=1).sort_index().ffill().dropna()
    totals = combined.sum(axis=1)
    fmt = "%H:%M" if period == "1d" else "%m/%d"
    return [(idx.strftime(fmt), float(val)) for idx, val in totals.items()]


async def get_portfolio_history(period: str = "1mo") -> list[tuple[str, float]]:
    """Total portfolio value over time, rebuilt from current holdings."""
    positions = await get_positions()
    holdings = [
        (_yf_symbol(p["symbol"], p.get("type")), float(p.get("quantity") or 0))
        for p in positions
        if p.get("symbol") and float(p.get("quantity") or 0) > 0
    ]
    if not holdings:
        return []
    return await asyncio.to_thread(_portfolio_history_sync, holdings, period)


def _news_sync(symbols: list[str], limit: int) -> list[dict]:
    import yfinance as yf

    articles: dict[str, dict] = {}
    for symbol in symbols:
        try:
            items = yf.Ticker(symbol).news or []
        except Exception:
            continue
        for item in items:
            content = item.get("content") or item
            url = (content.get("canonicalUrl") or {}).get("url") or (
                content.get("clickThroughUrl") or {}
            ).get("url")
            title = content.get("title")
            if not url or not title or url in articles:
                continue
            articles[url] = {
                "symbol": symbol.replace("-USD", ""),
                "title": title,
                "url": url,
                "publisher": (content.get("provider") or {}).get("displayName", ""),
                "published": content.get("pubDate") or content.get("displayTime") or "",
                "summary": content.get("summary") or content.get("description") or "",
            }

    def _sort_key(a: dict):
        try:
            return datetime.fromisoformat(a["published"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.min.replace(tzinfo=timezone.utc)

    ordered = sorted(articles.values(), key=_sort_key, reverse=True)
    return ordered[:limit]


async def get_news(symbols: list[str], limit: int = 20) -> list[dict]:
    """Recent, deduped news for the given symbols, newest first."""
    if not symbols:
        return []
    return await asyncio.to_thread(_news_sync, symbols, limit)


def _search_sync(query: str, limit: int) -> list[dict]:
    import yfinance as yf

    try:
        results = yf.Search(query, max_results=limit).quotes
    except Exception:
        return []
    out = []
    for q in results:
        symbol = q.get("symbol")
        if not symbol:
            continue
        out.append(
            {
                "symbol": symbol,
                "name": q.get("shortname") or q.get("longname") or symbol,
                "type": q.get("quoteType", ""),
                "exchange": q.get("exchange", ""),
            }
        )
    return out


async def search_symbols(query: str, limit: int = 8) -> list[dict]:
    """Symbol search for autocomplete: [{symbol, name, type, exchange}]."""
    query = query.strip()
    if not query:
        return []
    return await asyncio.to_thread(_search_sync, query, limit)
