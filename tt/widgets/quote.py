from textual.app import ComposeResult
from textual.widgets import Static, Input, Label
from textual_plotext import PlotextPlot

import tt.api as api
from tt.widgets.symbol_search import SymbolAutoComplete


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
        color = "green" if n > 0 else "red" if n < 0 else "white"
        return f"[{color}]{formatted}[/{color}]"
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
        color = "green" if n > 0 else "red" if n < 0 else "white"
        return f"[{color}]{formatted}[/{color}]"
    except (TypeError, ValueError):
        return str(val)


class QuoteWidget(Static):
    """Symbol search with an icon dropdown, live quote, and a price chart."""

    DEFAULT_CSS = """
    QuoteWidget { height: 1fr; }
    #quote-input { margin-bottom: 1; }
    #quote-details { height: auto; min-height: 6; }
    #quote-plot {
        height: 1fr;
        min-height: 12;
        border: round $primary;
        border-title-color: $accent;
    }
    """

    PERIOD = "3M"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._symbol = ""

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Search a symbol (e.g. AAPL, TSLA, BTC) …",
            id="quote-input",
        )
        yield SymbolAutoComplete(target="#quote-input")
        yield Label(
            "[dim]Search a symbol above to see its quote and chart.[/dim]",
            id="quote-details",
        )
        yield PlotextPlot(id="quote-plot")

    def on_mount(self) -> None:
        self.query_one("#quote-plot", PlotextPlot).border_title = "Price"

    def refresh_data(self) -> None:
        if self._symbol:
            self._fetch(self._symbol)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        symbol = event.value.strip().upper()
        if symbol:
            self._fetch(symbol)

    def _fetch(self, symbol: str) -> None:
        self._symbol = symbol
        self.query_one("#quote-details", Label).update(f"[dim]Fetching {symbol}…[/dim]")
        self.run_worker(self._load(symbol), exclusive=True)

    async def _load(self, symbol: str) -> None:
        details = self.query_one("#quote-details", Label)
        try:
            d = await api.get_quote(symbol)
        except Exception as e:
            details.update(f"[red]Error:[/red] {e}")
            return

        sym = str(d.get("symbol") or symbol).upper()
        last = _dollars(d.get("last"))
        bid = _dollars(d.get("bid"))
        ask = _dollars(d.get("ask"))
        change = _change_markup(d.get("change"))
        pct = _pct_markup(d.get("changePercent"))
        volume = d.get("volume")
        vol_str = f"{int(volume):,}" if volume is not None else "—"

        details.update(
            "\n".join(
                [
                    f"[bold]── {sym} ──────────────────────────[/bold]",
                    f"  [dim]Last Price[/dim]   [bold]{last}[/bold]",
                    f"  [dim]Change[/dim]       {change}  ({pct})",
                    f"  [dim]Bid / Ask[/dim]    {bid} / {ask}",
                    f"  [dim]Volume[/dim]       {vol_str}",
                ]
            )
        )

        # Price chart for the symbol over the default period.
        try:
            hist = await api.get_price_history(symbol, api.PERIODS[self.PERIOD])
        except Exception:
            hist = []
        self._render_chart(sym, hist)

    def _render_chart(self, symbol: str, hist: list) -> None:
        plot = self.query_one("#quote-plot", PlotextPlot)
        plt = plot.plt
        plt.clear_data()
        plt.clear_figure()
        if not hist:
            plot.border_title = f"{symbol} · {self.PERIOD} · no data"
            plot.refresh()
            return
        labels = [pt[0] for pt in hist]
        values = [pt[1] for pt in hist]
        xs = list(range(len(values)))
        up = values[-1] >= values[0]
        plt.plot(xs, values, color="green" if up else "red", marker="braille")
        step = max(1, len(labels) // 6)
        plt.xticks(xs[::step], labels[::step])
        plt.title("")
        plot.border_title = f"{symbol} · {self.PERIOD}"
        plot.refresh()
