from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Digits, Label
from textual.reactive import reactive
from textual_plotext import PlotextPlot

import tt.api as api


def _signed_pct(val) -> str:
    try:
        n = float(val)
    except (TypeError, ValueError):
        return "—"
    arrow = "▲" if n > 0 else "▼" if n < 0 else "■"
    color = "green" if n > 0 else "red" if n < 0 else "white"
    return f"[{color}]{arrow} {n:+.2f}%[/{color}]"


def _signed_dollars(val) -> str:
    try:
        n = float(val)
    except (TypeError, ValueError):
        return "—"
    color = "green" if n > 0 else "red" if n < 0 else "white"
    return f"[{color}]{n:+,.2f}[/{color}]"


class HomeWidget(Static):
    """Eye-catching landing zone: portfolio hero value, value chart, movers."""

    DEFAULT_CSS = """
    HomeWidget {
        height: 1fr;
    }
    #hero {
        height: auto;
        align: center top;
        padding: 1 0 0 0;
    }
    #hero-value {
        color: $success;
        text-align: center;
        width: auto;
    }
    #hero-change {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    #portfolio-plot {
        height: 1fr;
        min-height: 12;
        border: round $primary;
        border-title-color: $accent;
    }
    #movers {
        height: auto;
        padding: 1 1 0 1;
    }
    #movers-row {
        height: auto;
        align: center middle;
    }
    .mover {
        width: auto;
        margin: 0 2;
    }
    """

    history: reactive[list] = reactive(list, recompose=False)
    period: reactive[str] = reactive("1M")

    def compose(self) -> ComposeResult:
        with Vertical(id="hero"):
            yield Digits("$0.00", id="hero-value")
            yield Label("[dim]Loading…[/dim]", id="hero-change")
        yield PlotextPlot(id="portfolio-plot")
        with Vertical(id="movers"):
            yield Label("[bold]TOP MOVERS[/bold]")
            yield Horizontal(id="movers-row")

    def on_mount(self) -> None:
        plot = self.query_one("#portfolio-plot", PlotextPlot)
        plot.border_title = f"Portfolio · {self.period}"
        self.refresh_data()

    def refresh_data(self) -> None:
        self.run_worker(self._load(), exclusive=True)

    async def _load(self) -> None:
        # Hero value + today's change + movers come from the live portfolio.
        try:
            portfolio = await api.get_portfolio()
            positions = portfolio.get("positions", [])
        except Exception as e:
            self.query_one("#hero-change", Label).update(f"[red]Error:[/red] {e}")
            return

        total = portfolio.get("totalValue")
        try:
            self.query_one("#hero-value", Digits).update(f"${float(total):,.2f}")
        except (TypeError, ValueError):
            self.query_one("#hero-value", Digits).update("$—")

        # Aggregate today's $ change from each position's daily gain.
        day_change = 0.0
        for p in positions:
            try:
                day_change += float(p.get("dayChange") or 0)
            except (TypeError, ValueError):
                pass
        prior = 0.0
        try:
            prior = float(total) - day_change
        except (TypeError, ValueError):
            pass
        day_pct = (day_change / prior * 100) if prior else 0.0
        self.query_one("#hero-change", Label).update(
            f"{_signed_dollars(day_change)}   ({_signed_pct(day_pct)})  today"
        )

        self._render_movers(positions)

        # Portfolio value chart over the selected period.
        try:
            hist = await api.get_portfolio_history(api.PERIODS[self.period])
        except Exception:
            hist = []
        self._render_chart(hist)

    def _render_movers(self, positions: list[dict]) -> None:
        row = self.query_one("#movers-row", Horizontal)
        row.remove_children()
        movers = sorted(
            positions,
            key=lambda p: abs(float(p.get("unrealizedPnlPercent") or 0)),
            reverse=True,
        )[:5]
        for p in movers:
            sym = str(p.get("symbol") or "?").upper()
            pct = _signed_pct(p.get("unrealizedPnlPercent"))
            row.mount(Label(f"[bold]{sym}[/bold]  {pct}", classes="mover"))

    def _render_chart(self, hist: list) -> None:
        plot = self.query_one("#portfolio-plot", PlotextPlot)
        plt = plot.plt
        plt.clear_data()
        plt.clear_figure()
        if not hist:
            plot.border_title = f"Portfolio · {self.period} · no data"
            plot.refresh()
            return
        labels = [pt[0] for pt in hist]
        values = [pt[1] for pt in hist]
        xs = list(range(len(values)))
        up = values[-1] >= values[0]
        plt.plot(xs, values, color="green" if up else "red", marker="braille")
        # Show a handful of x labels so the axis stays readable.
        step = max(1, len(labels) // 6)
        plt.xticks(xs[::step], labels[::step])
        plt.title("")
        plot.border_title = f"Portfolio · {self.period}"
        plot.refresh()
