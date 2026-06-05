import sys
import os

from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane, DataTable

from tt.widgets.home import HomeWidget
from tt.widgets.account import AccountWidget
from tt.widgets.positions import PositionsWidget
from tt.widgets.portfolio import PortfolioWidget
from tt.widgets.quote import QuoteWidget
from tt.widgets.news import NewsWidget
from tt.screens.cheatsheet import CheatsheetScreen
from tt.themes import THEMES, THEME_NAMES
from tt import config

load_dotenv()

# Ordered list of tab IDs — drives h/l cycling and 1-N shortcuts.
_TABS = [
    "tab-home",
    "tab-account",
    "tab-positions",
    "tab-portfolio",
    "tab-quote",
    "tab-news",
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
        Binding("1", "goto_tab(0)", "Home", show=False),
        Binding("2", "goto_tab(1)", "Account", show=False),
        Binding("3", "goto_tab(2)", "Positions", show=False),
        Binding("4", "goto_tab(3)", "Portfolio", show=False),
        Binding("5", "goto_tab(4)", "Quote", show=False),
        Binding("6", "goto_tab(5)", "News", show=False),
        # Theme + help
        Binding("t", "cycle_theme", "Theme"),
        Binding("question_mark", "cheatsheet", "Help"),
    ]

    def on_mount(self) -> None:
        # Register custom themes and apply the persisted choice.
        for theme in THEMES:
            self.register_theme(theme)
        active = config.get_active_theme()
        self.theme = active if active in THEME_NAMES else THEME_NAMES[0]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("🏠 Home", id="tab-home"):
                yield HomeWidget(id="home")
            with TabPane("Account", id="tab-account"):
                yield AccountWidget(id="account")
            with TabPane("Positions", id="tab-positions"):
                yield PositionsWidget(id="positions")
            with TabPane("Portfolio", id="tab-portfolio"):
                yield PortfolioWidget(id="portfolio")
            with TabPane("Quote", id="tab-quote"):
                yield QuoteWidget(id="quote")
            with TabPane("📰 News", id="tab-news"):
                yield NewsWidget(id="news")
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

    # ── Theme + help ───────────────────────────────────────────────────

    def action_cycle_theme(self) -> None:
        try:
            idx = THEME_NAMES.index(self.theme)
        except ValueError:
            idx = -1
        new_theme = THEME_NAMES[(idx + 1) % len(THEME_NAMES)]
        self.theme = new_theme
        config.save_active_theme(new_theme)
        self.notify(f"Theme: {new_theme}", timeout=2)

    def action_cheatsheet(self) -> None:
        # Toggle: don't stack multiple copies of the modal.
        if isinstance(self.screen, CheatsheetScreen):
            self.pop_screen()
        else:
            self.push_screen(CheatsheetScreen())

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
        widget_by_tab = {
            "tab-home": HomeWidget,
            "tab-account": AccountWidget,
            "tab-positions": PositionsWidget,
            "tab-portfolio": PortfolioWidget,
            "tab-quote": QuoteWidget,
            "tab-news": NewsWidget,
        }
        widget_cls = widget_by_tab.get(active)
        if widget_cls is not None:
            self.query_one(widget_cls).refresh_data()


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
