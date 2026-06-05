from textual.app import ComposeResult
from textual.widgets import Static, DataTable
from textual.reactive import reactive

import tt.api as api


def _dollars(val) -> str:
    if val is None:
        return "—"
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return str(val)


def _pnl_markup(val) -> str:
    if val is None:
        return "—"
    try:
        n = float(val)
        formatted = f"${n:,.2f}"
        if n > 0:
            return f"[green]{formatted}[/green]"
        elif n < 0:
            return f"[red]{formatted}[/red]"
        return formatted
    except (TypeError, ValueError):
        return str(val)


class PortfolioWidget(Static):
    data: reactive[dict] = reactive({}, recompose=True)
    error: reactive[str] = reactive("", recompose=True)

    def on_mount(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        self.error = ""
        self.run_worker(self._load(), exclusive=True)

    async def _load(self) -> None:
        try:
            raw = await api.get_portfolio()
            self.data = raw
        except Exception as e:
            self.error = str(e)

    def compose(self) -> ComposeResult:
        if self.error:
            yield Static(f"[red]Error:[/red] {self.error}")
            return

        if not self.data:
            yield Static("[dim]Loading…[/dim]")
            return

        d = self.data
        total = _dollars(
            d.get("total_value") or d.get("totalValue") or d.get("portfolioValue")
        )
        cash = _dollars(d.get("cash") or d.get("cashBalance"))
        equity = _dollars(d.get("equity_value") or d.get("equityValue"))

        summary = "\n".join([
            "[bold]── Portfolio ─────────────────────────[/bold]",
            f"  [dim]Total Value[/dim]    {total}",
            f"  [dim]Cash[/dim]           {cash}",
            f"  [dim]Equity Value[/dim]   {equity}",
        ])
        yield Static(summary)

        positions = d.get("positions", [])
        if positions:
            yield Static("\n  [bold underline]Holdings[/bold underline]")
            table = DataTable()
            table.add_columns("Symbol", "Mkt Value", "P&L")
            for p in positions:
                symbol = str(
                    p.get("symbol") or p.get("ticker") or p.get("instrumentSymbol") or "?"
                ).upper()
                mkt = _dollars(
                    p.get("current_value") or p.get("currentValue") or p.get("marketValue")
                )
                pnl = _pnl_markup(
                    p.get("unrealized_pnl") or p.get("unrealizedPnl") or p.get("unrealizedProfitLoss")
                )
                table.add_row(symbol, mkt, pnl)
            yield table

        yield Static("\n[dim italic]Press r to refresh[/dim italic]")
