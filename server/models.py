from pydantic import BaseModel


class AccountResponse(BaseModel):
    cash: float | None = None
    buying_power: float | None = None
    portfolio_value: float | None = None
    account_number: str | None = None


class PositionItem(BaseModel):
    symbol: str
    quantity: float
    cost_basis: float | None = None
    current_value: float | None = None
    unrealized_pnl: float | None = None
    unrealized_pnl_pct: float | None = None


class PositionsResponse(BaseModel):
    positions: list[PositionItem]


class QuoteResponse(BaseModel):
    symbol: str
    last_price: float | None = None
    bid: float | None = None
    ask: float | None = None
    change: float | None = None
    change_pct: float | None = None
    volume: int | None = None


class PortfolioResponse(BaseModel):
    total_value: float | None = None
    cash: float | None = None
    equity_value: float | None = None
    positions: list[PositionItem] = []
