from fastapi import APIRouter
from public_client import api_get

router = APIRouter()


@router.get("/portfolio")
async def get_portfolio():
    data = await api_get("/userapigateway/portfolio")
    raw_positions = data.get("positions", [])
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
    return {
        "total_value": data.get("total_value") or data.get("totalValue") or data.get("portfolioValue"),
        "cash": data.get("cash"),
        "equity_value": data.get("equity_value") or data.get("equityValue"),
        "positions": positions,
        "_raw": data,
    }
