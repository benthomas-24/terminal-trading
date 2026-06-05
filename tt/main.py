import sys
import os

from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane, DataTable

from tt.widgets.account import AccountWidget
from tt.widgets.positions import PositionsWidget
from tt.widgets.portfolio import PortfolioWidget
from tt.widgets.quote import QuoteWidget

load_dotenv()

# Ordered list of tab IDs — drives h/l cycling and 1-N shortcuts.
_TABS = [
    "tab-account",
    "tab-positions",
    "tab-portfolio",
    "tab-quote",
]


class TradingApp(App):
    TITLE = "Terminal Trading"
    SUB_TITLE = "Public.com"

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        # Tab navigation
        Binding("h", "previous_tab", "◀ Prev", show=False),
        Binding("l", "next_tab", "Next ▶", show=False),
        # In-widget cursor movement
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        # Direct tab jumps
        Binding("1", "goto_tab(0)", "Account", show=False),
        Binding("2", "goto_tab(1)", "Positions", show=False),
        Binding("3", "goto_tab(2)", "Portfolio", show=False),
        Binding("4", "goto_tab(3)", "Quote", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("Account", id="tab-account"):
                yield AccountWidget(id="account")
            with TabPane("Positions", id="tab-positions"):
                yield PositionsWidget(id="positions")
            with TabPane("Portfolio", id="tab-portfolio"):
                yield PortfolioWidget(id="portfolio")
            with TabPane("Quote", id="tab-quote"):
                yield QuoteWidget(id="quote")
        yield Footer()

    # ── Tab navigation ─────────────────────────────────────────────────

    def _tab_index(self) -> int:
        active = self.query_one(TabbedContent).active
        try:
            return _TABS.index(active)
        except ValueError:
            return 0

    def action_previous_tab(self) -> None:
        idx = (self._tab_index() - 1) % len(_TABS)
        self.query_one(TabbedContent).active = _TABS[idx]

    def action_next_tab(self) -> None:
        idx = (self._tab_index() + 1) % len(_TABS)
        self.query_one(TabbedContent).active = _TABS[idx]

    def action_goto_tab(self, index: int) -> None:
        if 0 <= index < len(_TABS):
            self.query_one(TabbedContent).active = _TABS[index]

    # ── Cursor movement (j/k) ──────────────────────────────────────────

    def action_cursor_down(self) -> None:
        focused = self.focused
        if isinstance(focused, DataTable):
            focused.move_cursor(row=focused.cursor_row + 1)
        elif focused is not None:
            focused.scroll_down()

    def action_cursor_up(self) -> None:
        focused = self.focused
        if isinstance(focused, DataTable):
            focused.move_cursor(row=max(0, focused.cursor_row - 1))
        elif focused is not None:
            focused.scroll_up()

    # ── Refresh ────────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "tab-account":
            self.query_one(AccountWidget).refresh_data()
        elif active == "tab-positions":
            self.query_one(PositionsWidget).refresh_data()
        elif active == "tab-portfolio":
            self.query_one(PortfolioWidget).refresh_data()
        elif active == "tab-quote":
            self.query_one(QuoteWidget).refresh_data()


def main() -> None:
    secret = os.getenv("PUBLIC_API_SECRET")
    token = os.getenv("PUBLIC_ACCESS_TOKEN")
    if not secret and not token:
        print(
            "Error: PUBLIC_API_SECRET is not set.\n"
            "  Add it to a .env file or export it in your shell:\n"
            "  export PUBLIC_API_SECRET=your_secret_key_here",
            file=sys.stderr,
        )
        sys.exit(1)
    TradingApp().run()


if __name__ == "__main__":
    main()
