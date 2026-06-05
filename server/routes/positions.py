from fastapi import APIRouter
from public_client import api_get

router = APIRouter()


@router.get("/positions")
async def get_positions():
    data = await api_get("/userapigateway/portfolio/positions")
    raw_positions = data if isinstance(data, list) else data.get("positions", [])
    positions = []
    for p in raw_positions:
        positions.append({
            "symbol": p.get("symbol") or p.get("ticker", ""),
            "quantity": p.get("quantity") or p.get("qty") or 0,
            "cost_basis": p.get("cost_basis") or p.get("costBasis"),
            "current_value": p.get("current_value") or p.get("currentValue") or p.get("market_value"),
            "unrealized_pnl": p.get("unrealized_pnl") or p.get("unrealizedPnl"),
            "unrealized_pnl_pct": p.get("unrealized_pnl_pct") or p.get("unrealizedPnlPercent"),
        })
    return {"positions": positions, "_raw": data}
