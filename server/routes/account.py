from fastapi import APIRouter
from public_client import api_get

router = APIRouter()


@router.get("/account")
async def get_account():
    data = await api_get("/userapigateway/account")
    return {
        "cash": data.get("cash"),
        "buying_power": data.get("buying_power") or data.get("buyingPower"),
        "portfolio_value": data.get("portfolio_value") or data.get("portfolioValue"),
        "account_number": data.get("account_number") or data.get("accountNumber"),
        "_raw": data,
    }
