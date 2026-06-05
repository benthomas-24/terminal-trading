from textual.app import ComposeResult
from textual.widgets import Static, Input
from textual.reactive import reactive

import tt.api as api


def _dollars(val) -> str:
    if val is None:
        return "—"
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return str(val)


def _change_markup(val) -> str:
    if val is None:
        return "—"
    try:
        n = float(val)
        formatted = f"${n:+,.2f}"
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


class QuoteWidget(Static):
    quote_data: reactive[dict | None] = reactive(None, recompose=True)
    error: reactive[str] = reactive("", recompose=True)
    loading: reactive[bool] = reactive(False, recompose=True)

    def refresh_data(self) -> None:
        inp = self.query_one(Input)
        symbol = inp.value.strip()
        if symbol:
            self._fetch(symbol)

    def _fetch(self, symbol: str) -> None:
        self.error = ""
        self.loading = True
        self.quote_data = None
        self.run_worker(self._load(symbol), exclusive=True)

    async def _load(self, symbol: str) -> None:
        try:
            raw = await api.get_quote(symbol)
            self.quote_data = raw
        except Exception as e:
            self.error = str(e)
        finally:
            self.loading = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        symbol = event.value.strip().upper()
        if symbol:
            self._fetch(symbol)

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter symbol (e.g. AAPL) and press Enter")

        if self.loading:
            yield Static("[dim]Fetching…[/dim]")
            return

        if self.error:
            yield Static(f"[red]Error:[/red] {self.error}")
            return

        if self.quote_data is None:
            yield Static("[dim]Enter a symbol above to get a quote.[/dim]")
            return

        d = self.quote_data
        symbol = str(d.get("symbol") or d.get("ticker") or "").upper()
        last = _dollars(d.get("last_price") or d.get("lastPrice") or d.get("last") or d.get("price"))
        bid = _dollars(d.get("bid") or d.get("bidPrice"))
        ask = _dollars(d.get("ask") or d.get("askPrice"))
        change = _change_markup(d.get("change") or d.get("priceChange") or d.get("netChange"))
        pct = _pct_markup(
            d.get("change_pct")
            or d.get("changePercent")
            or d.get("percentChange")
            or d.get("netChangePercent")
        )
        volume = d.get("volume")
        vol_str = f"{int(volume):,}" if volume is not None else "—"

        lines = [
            f"\n[bold]── {symbol} ─────────────────────────────[/bold]",
            f"  [dim]Last Price[/dim]     [bold]{last}[/bold]",
            f"  [dim]Change[/dim]         {change}  ({pct})",
            f"  [dim]Bid / Ask[/dim]      {bid} / {ask}",
            f"  [dim]Volume[/dim]         {vol_str}",
            "",
            "[dim italic]Press r to refresh current quote[/dim italic]",
        ]
        yield Static("\n".join(lines))
