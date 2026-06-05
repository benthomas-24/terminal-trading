from fastapi import APIRouter
from public_client import api_get

router = APIRouter()


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    data = await api_get(f"/marketdata/quotes/{symbol.upper()}")
    return {
        "symbol": symbol.upper(),
        "last_price": data.get("last_price") or data.get("lastPrice") or data.get("last"),
        "bid": data.get("bid") or data.get("bidPrice"),
        "ask": data.get("ask") or data.get("askPrice"),
        "change": data.get("change") or data.get("priceChange"),
        "change_pct": data.get("change_pct") or data.get("changePercent") or data.get("percentChange"),
        "volume": data.get("volume"),
        "_raw": data,
    }
