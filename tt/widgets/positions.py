from textual.app import ComposeResult
from textual.widgets import Static, DataTable
from textual.reactive import reactive

import tt.api as api


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


def _pct_markup(val) -> str:
    if val is None:
        return "—"
    try:
        n = float(val)
        # Handle both decimal (0.05) and percentage (5.0) representations
        if abs(n) < 1:
            n *= 100
        formatted = f"{n:+.2f}%"
        if n > 0:
            return f"[green]{formatted}[/green]"
        elif n < 0:
            return f"[red]{formatted}[/red]"
        return formatted
    except (TypeError, ValueError):
        return str(val)


def _dollars(val) -> str:
    if val is None:
        return "—"
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return str(val)


class PositionsWidget(Static):
    raw: reactive[list] = reactive([], recompose=True)
    error: reactive[str] = reactive("", recompose=True)

    def on_mount(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        self.error = ""
        self.run_worker(self._load(), exclusive=True)

    async def _load(self) -> None:
        try:
            result = await api.get_positions()
            if isinstance(result, list):
                self.raw = result
            else:
                self.raw = result.get("positions", [result]) if result else []
        except Exception as e:
            self.error = str(e)

    def compose(self) -> ComposeResult:
        if self.error:
            yield Static(f"[red]Error:[/red] {self.error}")
            return

        if not self.raw and self.raw != []:
            yield Static("[dim]Loading…[/dim]")
            return

        if not self.raw:
            yield Static("[dim]No open positions.[/dim]")
            return

        table = DataTable()
        table.add_columns("Symbol", "Qty", "Cost Basis", "Mkt Value", "P&L", "P&L %")
        for p in self.raw:
            symbol = str(
                p.get("symbol") or p.get("ticker") or p.get("instrumentSymbol") or "?"
            ).upper()
            qty = str(p.get("quantity") or p.get("qty") or p.get("shares") or "—")
            cost = _dollars(p.get("cost_basis") or p.get("costBasis") or p.get("averageBuyPrice"))
            mkt = _dollars(
                p.get("current_value")
                or p.get("currentValue")
                or p.get("market_value")
                or p.get("marketValue")
            )
            pnl = _pnl_markup(
                p.get("unrealized_pnl")
                or p.get("unrealizedPnl")
                or p.get("unrealizedProfitLoss")
            )
            pct = _pct_markup(
                p.get("unrealized_pnl_pct")
                or p.get("unrealizedPnlPercent")
                or p.get("unrealizedProfitLossPercent")
            )
            table.add_row(symbol, qty, cost, mkt, pnl, pct)

        yield table
        yield Static("\n[dim italic]Press r to refresh[/dim italic]")
